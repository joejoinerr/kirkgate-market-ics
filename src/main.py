"""Main application entry point."""

import calendar
import json
import uuid
from datetime import date, datetime, time
from pathlib import Path

import httpx
import pydantic
from bs4 import BeautifulSoup
from loguru import logger

import logconfig
from exceptions import HTTPStatusError
from settings import load_settings

settings = load_settings()
logconfig.setup()


class Event(pydantic.BaseModel):
    """Represents an event with relevant details."""

    date: date
    title: str
    description: str | None = None
    start_time: time
    end_time: time


def get_page_html(url: str, user_agent: str | None = None) -> str:
    """Fetches the HTML content of a webpage.

    Args:
        url: The URL of the webpage to fetch.
        user_agent: Optional User-Agent string to include in the request headers.

    Returns:
        The HTML content of the webpage as a string.

    Raises:
        HTTPStatusError: If the HTTP request fails or returns a non-200 status code.
    """
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    response = httpx.get(url, headers=headers)
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPStatusError(
            status_code=e.response.status_code, response_text=e.response.text
        ) from e
    return response.text


def find_html_events_table(html: str) -> str:
    """Finds and returns the HTML of the events table from the given HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    return str(soup.find("main").find("table"))


def get_openrouter_response(prompt: str, model: str, api_key: str) -> str:
    """Sends a prompt to the OpenRouter API and returns the response content."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = httpx.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=body,
    )
    try:
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        raise HTTPStatusError(
            status_code=e.response.status_code, response_text=e.response.text
        ) from e
    except Exception:
        raise


def get_events_month(html: str, openrouter_api_key: str, model: str) -> int:
    """Gets the month number from the events page HTML."""
    prompt = """\
    Can you tell me which month the events in this HTML calendar are for? I want you to
    reply with the number of a month in the year, from 1-12, where 1 is January, 2 is
    February, and so on.

    Reply only with a number, no commentary or anything else.

    Here is the HTML to parse:

    ```html
    {events_table_html}
    ```
    """
    formatted_prompt = prompt.format(events_table_html=html)
    ai_response = get_openrouter_response(
        prompt=formatted_prompt,
        model=model,
        api_key=openrouter_api_key,
    )
    return int(ai_response)


def create_events_from_html(
    html: str, month: int, openrouter_api_key: str, model: str
) -> list[Event]:
    """Creates a list of Event objects from the given HTML content.

    Args:
        html: The HTML content containing the events table.
        month: The month number (1-12) for the events.
        openrouter_api_key: The API key for OpenRouter.
        model: The OpenRouter model to use.

    Returns:
        A list of Event objects parsed from the HTML.
    """
    prompt = """\
    Can you please format the following HTML into a JSON array? DO NOT include any
    commentary, only the JSON response.

    The returned object should be as follows:

    Use the following schemas:

    - date: ISO date
    - title (from Event field in table): string
    - description (from Event field in table): string OR null
    - start_time (half of Time field in table): ISO time
    - end_time (half of Time field in table): ISO time

    If the event is on weekly throughout the month (e.g. "every Thursday"), please create a
    JSON object for every applicable date. Here's a calendar for the month for you to
    reference:

    {month_cal}

    Here is the HTML to format:

    ```html
    {events_table_html}
    ```
    """
    month_cal = calendar.TextCalendar().formatmonth(2025, month)
    formatted_prompt = prompt.format(month_cal=month_cal, events_table_html=html)
    ai_response = get_openrouter_response(
        prompt=formatted_prompt,
        model=model,
        api_key=openrouter_api_key,
    )
    parsed_ai_response = json.loads(ai_response)
    return [Event.model_validate(event_detail) for event_detail in parsed_ai_response]


def create_ics_from_events(events: list[Event]) -> str:
    """Creates an ICS file string from a list of Event objects.

    Args:
        events: A list of Event objects to include in the calendar.

    Returns:
        A string containing the calendar data in ICS format.
    """
    # Standard ICS file header
    ics_header = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MyPythonScript//EN",
        "CALSCALE:GREGORIAN",
    ]

    # Standard ICS file footer
    ics_footer = ["END:VCALENDAR"]

    # Get the current time in UTC for the DTSTAMP field
    creation_timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

    event_entries = []
    for event in events:
        # Combine the date and time objects into datetime objects
        start_datetime = datetime.combine(event.date, event.start_time)
        end_datetime = datetime.combine(event.date, event.end_time)

        # Escape newlines in the description for ICS format
        description = (event.description or "").replace("\n", "\\n")

        # Create the VEVENT block for the current event
        event_entry = [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}",
            f"DTSTAMP:{creation_timestamp}",
            f"DTSTART:{start_datetime.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end_datetime.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{event.title}",
            f"DESCRIPTION:{description}",
            "LOCATION:Leeds Kirkgate Market, Kirkgate, Leeds LS2 7HY, UK",
            "END:VEVENT",
        ]
        event_entries.extend(event_entry)

    # Combine header, events, and footer
    full_ics_list = ics_header + event_entries + ics_footer

    # Join all lines with CRLF endings, as required by the standard
    return "\r\n".join(full_ics_list)


def file_content_matches_existing(file_path: Path, content: str) -> bool:
    """Checks if the given content matches the existing file content.

    Args:
        file_path: Path to the file to check.
        content: Content to compare against the file's content.

    Returns:
        True if the content matches the file's content, False otherwise, or if the
        file doesn't exist.
    """
    if not file_path.exists():
        return False
    existing_content = file_path.read_text(encoding="utf-8")
    return existing_content == content


def main() -> None:
    """Main application entry point."""
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    html = get_page_html("https://markets.leeds.gov.uk/whats-kirkgate")
    events_table_html = find_html_events_table(html)
    events_html_file_path = settings.artifacts_dir / settings.html_file_name
    if file_content_matches_existing(
        file_path=events_html_file_path, content=events_table_html
    ):
        logger.info("No changes detected in events HTML. Exiting.")
        return
    events_html_file_path.write_text(events_table_html, encoding="utf-8")

    openrouter_api_key = settings.openrouter_api_key.get_secret_value()
    model = settings.openrouter_model
    month_number = get_events_month(
        events_table_html, openrouter_api_key=openrouter_api_key, model=model
    )
    events = create_events_from_html(
        html=events_table_html,
        month=month_number,
        openrouter_api_key=openrouter_api_key,
        model=model,
    )

    ics_content = create_ics_from_events(events)
    ics_file_path = settings.artifacts_dir / settings.ics_file_name
    ics_file_path.write_text(ics_content, encoding="utf-8")
    logger.info("ICS file written to path: {}", str(ics_file_path))


if __name__ == "__main__":
    main()
