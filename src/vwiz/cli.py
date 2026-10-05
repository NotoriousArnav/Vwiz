"""Command-line entrypoint for Vwiz."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Launch the Streamlit frontend."""
    from streamlit.web import cli as streamlit_cli

    sys.argv = ["streamlit", "run", str(Path(__file__).parent / "app.py")]
    streamlit_cli.main()


if __name__ == "__main__":
    main()
