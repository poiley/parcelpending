"""
ParcelPending API Wrapper

A Python library for interacting with the ParcelPending website.
"""

from .client import ParcelPendingClient
from .exceptions import (
    ParcelPendingError,
    AuthenticationError,
    ConnectionError
)

__version__ = "0.1.0"
__all__ = ["ParcelPendingClient", "ParcelPendingError", "AuthenticationError", "ConnectionError"] 