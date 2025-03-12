"""
Utility functions for the ParcelPending API wrapper.
"""

from datetime import datetime


def parse_date(date_str):
    """
    Parse a date string in multiple formats.

    Args:
        date_str (str): Date string to parse

    Returns:
        datetime: Parsed datetime object

    Raises:
        ValueError: If the date string cannot be parsed
    """
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unable to parse date: {date_str}")
