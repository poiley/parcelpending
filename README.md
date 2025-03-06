# ParcelPending

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Versions](https://img.shields.io/pypi/pyversions/parcelpending.svg)](https://pypi.org/project/parcelpending/)
[![Build Status](https://github.com/poiley/parcelpending/workflows/ParcelPending%20Python%20package/badge.svg)](https://github.com/poiley/parcelpending/actions)

A Python client for the ParcelPending website that allows you to retrieve and manage your package delivery information programmatically.

## Features

- Authenticate with ParcelPending website
- Retrieve parcel history for any date range
- Filter parcels by status (active/picked up)
- Filter parcels by courier (USPS, Amazon, FedEx, etc.)
- Export parcel data to CSV or JSON
- Command-line interface for easy access

## Installation

### Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`

### Install from GitHub

```bash
# Clone the repository
git clone https://github.com/poiley/parcelpending.git
cd parcelpending

# Create and activate a virtual environment (recommended)
python -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

## Usage

### Basic Usage

```python
from parcelpending import ParcelPendingClient
from datetime import datetime, timedelta

# Initialize client and login
client = ParcelPendingClient()
client.login(email="your.email@example.com", password="your-password")

# Get parcel history for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)
parcels = client.get_parcel_history(start_date, end_date)

# Print parcels
for parcel in parcels:
    print(f"Package code: {parcel.get('package_code', 'N/A')}")
    print(f"Status: {parcel.get('status', 'N/A')}")
    print(f"Locker: {parcel.get('locker_box', 'N/A')}")
    print(f"Size: {parcel.get('size', 'N/A')}")
    print(f"Courier: {parcel.get('courier', 'N/A')}")
    print("---")
```

### Advanced Usage

```python
# Get only active parcels (not picked up)
active_parcels = client.get_active_parcels(days=90)

# Get parcels from a specific courier
amazon_parcels = client.get_parcels_by_courier("Amazon", days=60)

# Find a specific parcel by package code
specific_parcel = client.get_parcel_by_code("12345678")

# Export parcels to CSV
client.export_to_csv(parcels, "my_parcels.csv")

# Export parcels to JSON
client.export_to_json(active_parcels, "active_parcels.json")
```

## Command Line Interface

The package includes a command-line interface for convenient access to your parcel data.

### List Parcels

```bash
# List all parcels from the last 30 days
parcelpending your.email@example.com your-password list

# List only active parcels
parcelpending your.email@example.com your-password list --active

# List USPS parcels from the last 90 days
parcelpending your.email@example.com your-password list --courier USPS --days 90

# Enable debug mode for more detailed logs
parcelpending your.email@example.com your-password list --debug
```

### Export Parcels

```bash
# Export all parcels to CSV
parcelpending your.email@example.com your-password export

# Export active parcels to JSON
parcelpending your.email@example.com your-password export --active --format json

# Specify output file
parcelpending your.email@example.com your-password export --output my_deliveries.csv
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/poiley/parcelpending.git
cd parcelpending

# Create and activate virtual environment
python -m venv .env
source .env/bin/activate  # On Windows: .env\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=parcelpending
```

### Code Style

This project uses flake8, black, and isort for code formatting:

```bash
# Check code style
flake8 parcelpending tests

# Format code
black parcelpending tests
isort parcelpending tests
```

## Data Structure

The parcel data is returned as a list of dictionaries. Each dictionary may contain these fields (when available):

| Field | Description |
|-------|-------------|
| `package_code` | Unique code for the package |
| `status` | Status of the package (e.g., "Picked up") |
| `locker_box` | Locker box number |
| `size` | Size of the package (Small, Medium, Large, etc.) |
| `courier` | Delivery service (USPS, Amazon, FedEx, etc.) |
| `delivered` | Date and time of delivery |
| `status_change` | Date and time of the last status change |
| `package_id` | Internal ID for the package |
| `tracking` | Tracking number (if available) |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This package is not affiliated with, maintained, authorized, endorsed, or sponsored by ParcelPending or any of its affiliates or subsidiaries. This is an unofficial wrapper that interacts with the publicly available ParcelPending website.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Author

[poiley](https://github.com/poiley)
