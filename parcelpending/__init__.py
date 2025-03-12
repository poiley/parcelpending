"""
ParcelPending API Client.

A Python wrapper for the ParcelPending website to get information about packages.
"""

from parcelpending.client import ParcelPendingClient
from parcelpending.exceptions import AuthenticationError, ConnectionError, ParcelPendingError

__version__ = "0.1.1"
__all__ = ["ParcelPendingClient", "AuthenticationError", "ConnectionError", "ParcelPendingError"]
