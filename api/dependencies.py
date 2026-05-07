"""Shared dependencies for FastAPI routers."""

from pathlib import Path

from fastapi import Request


def get_base_path(request: Request) -> Path:
    """Resolve the Oracle project root from the API runtime."""
    # The API runs from oracle/api/main.py, so project root is two levels up
    return Path(__file__).resolve().parent.parent
