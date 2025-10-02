"""Main application entry point."""

import logconfig
from settings import load_settings

settings = load_settings()
logconfig.setup()


def main() -> None:
    """Main application entry point."""
    pass


if __name__ == "__main__":
    main()
