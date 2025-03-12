"""
Exceptions for the ParcelPending API wrapper.
"""


class ParcelPendingError(Exception):
    """Base exception for all ParcelPending related errors."""

    pass


class AuthenticationError(ParcelPendingError):
    """Raised when authentication fails."""

    pass


class ConnectionError(ParcelPendingError):
    """Raised when connection to ParcelPending fails."""

    pass
