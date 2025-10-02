"""Application exceptions."""


class HTTPStatusError(Exception):
    """Exception raised for HTTP status errors."""

    def __init__(self, status_code: int, response_text: str | None = None) -> None:
        """Initializes the HTTPStatusError."""
        self.status_code = status_code
        self.response_text = response_text
        message = f"HTTP Status Error: {status_code}."
        if response_text:
            message += f" {response_text}"
        super().__init__(message)
