"""
ARIA runtime configuration for local and Streamlit Cloud execution.
"""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
PORTFOLIOS_DIR = DATA_DIR / "portfolios"
TMP_DIR = PROJECT_ROOT / "tmp"

RISK_HISTORY_PATH = DATA_DIR / "risk_history.csv"
DEFAULT_PORTFOLIO_PATH = PORTFOLIOS_DIR / "current_portfolio.csv"
DEFAULT_MARKET_DATA_PATH = DATA_DIR / "market_data.csv"


def ensure_runtime_directories() -> None:
    """Create folders that Streamlit Cloud will not create automatically."""

    for directory in (
        DATA_DIR,
        PORTFOLIOS_DIR,
        TMP_DIR,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )


def relative_to_project(path: Path) -> str:
    """Return a stable display path when possible."""

    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def resolve_project_path(path_value: str | Path) -> Path:
    """Resolve user-facing project paths safely from the repository root."""

    path = Path(path_value).expanduser()

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


def _streamlit_secret(name: str) -> Any | None:
    """Read a Streamlit secret when running inside Streamlit."""

    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]

    except Exception:
        return None

    return None


def get_runtime_setting(name: str, default: str | None = None) -> str | None:
    """
    Read configuration from Streamlit secrets first, then local .env/env vars.

    This keeps local development based on .env while allowing Streamlit Cloud
    deployments to use the app settings Secrets panel.
    """

    secret_value = _streamlit_secret(name)

    if secret_value not in (
        None,
        "",
    ):
        return str(secret_value)

    load_dotenv(
        PROJECT_ROOT / ".env",
        override=False,
    )

    return os.getenv(
        name,
        default,
    )
