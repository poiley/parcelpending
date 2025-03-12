#!/usr/bin/env python3
"""
Command line interface for the ParcelPending client.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from parcelpending import ParcelPendingClient
from parcelpending.exceptions import AuthenticationError, ConnectionError


def setup_logging(debug=False):
    """Set up logging configuration based on debug mode."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)


def list_parcels(client, days, active_only=False, courier=None, debug=False):
    """List parcels with optional filtering."""
    logger = setup_logging(debug)

    try:
        if active_only:
            logger.info(f"Retrieving active parcels from the last {days} days...")
            parcels = client.get_active_parcels(days=days)
        elif courier:
            logger.info(f"Retrieving parcels from {courier} from the last {days} days...")
            parcels = client.get_parcels_by_courier(courier, days=days)
        else:
            # Get all parcels for the specified days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            logger.info(
                f"Retrieving parcel history from {start_date.date()} to {end_date.date()}..."
            )
            parcels = client.get_parcel_history(start_date, end_date)

        # Display results
        if parcels:
            logger.info(f"Found {len(parcels)} parcels:")
            for i, parcel in enumerate(parcels, 1):
                logger.info(f"Parcel {i}:")
                for key, value in parcel.items():
                    logger.info(f"  {key.capitalize()}: {value}")
                logger.info("---")
            return parcels
        else:
            logger.info("No parcels found matching your criteria.")
            return []

    except Exception as e:
        logger.error(f"Error listing parcels: {e}")
        return []


def main():
    """Main function for the command line interface."""
    parser = argparse.ArgumentParser(description="ParcelPending Client CLI")
    parser.add_argument("email", help="Email for authentication")
    parser.add_argument("password", help="Password for authentication")

    # Common options
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--days", type=int, default=30, help="Number of days in the past to check (default: 30)"
    )

    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List parcels")
    list_parser.add_argument(
        "--active", "-a", action="store_true", help="Show only active (not picked up) parcels"
    )
    list_parser.add_argument("--courier", "-c", help="Filter by courier name")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export parcels to a file")
    export_parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json"],
        default="csv",
        help="Export format (default: csv)",
    )
    export_parser.add_argument("--output", "-o", help="Output file path")
    export_parser.add_argument(
        "--active", "-a", action="store_true", help="Export only active (not picked up) parcels"
    )
    export_parser.add_argument("--courier", "-c", help="Filter by courier name")

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, default to list
    if not args.command:
        args.command = "list"

    # Set up logging
    logger = setup_logging(args.debug)

    # Initialize client
    client = ParcelPendingClient()

    try:
        # Login
        logger.info("Attempting to log in...")
        client.login(email=args.email, password=args.password)
        logger.info("Login successful!")

        # Execute command
        if args.command == "list":
            list_parcels(client, args.days, args.active, args.courier, args.debug)

        elif args.command == "export":
            parcels = list_parcels(client, args.days, args.active, args.courier, args.debug)

            if parcels:
                if args.format == "csv":
                    output_file = (
                        args.output or f"parcels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    )
                    client.export_to_csv(parcels, output_file)
                    logger.info(f"Exported {len(parcels)} parcels to {output_file}")
                else:  # json
                    output_file = (
                        args.output or f"parcels_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    )
                    client.export_to_json(parcels, output_file)
                    logger.info(f"Exported {len(parcels)} parcels to {output_file}")
            else:
                logger.warning("No parcels to export")

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
