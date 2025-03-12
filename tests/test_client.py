"""
Tests for the ParcelPending client.
"""

from datetime import datetime
import re

import pytest
import responses
import requests

from parcelpending import ParcelPendingClient
from parcelpending.exceptions import AuthenticationError, ConnectionError


class TestParcelPendingClient:
    """Tests for the ParcelPendingClient class."""

    def setup_method(self):
        self.client = ParcelPendingClient(email="test@example.com", password="password123")
        self.base_url = "https://my.parcelpending.com"
        self.login_url = f"{self.base_url}/login"
        self.history_url = f"{self.base_url}/parcel-history"

    @responses.activate
    def test_login_success(self):
        """Test successful login."""
        # Mock login page response with a form
        login_html = """
        <html>
            <form method="POST" name="login" id="login">
                <input type="hidden" name="token" value="abc123">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit" name="signin" value="signin">Sign In</button>
            </form>
        </html>
        """
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        # Mock login submission response
        responses.add(
            responses.POST,
            self.login_url,
            body="<html><div>Welcome</div><a href='/logout'>Sign Out</a></html>",
            status=200,
            content_type="text/html",
        )

        # Test login
        assert self.client.login() is True
        assert self.client.authenticated is True

    @responses.activate
    def test_login_failure(self):
        """Test login failure with invalid credentials."""
        # Mock login page response
        login_html = """
        <html>
            <form method="POST" name="login" id="login">
                <input type="hidden" name="token" value="abc123">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit" name="signin" value="signin">Sign In</button>
            </form>
        </html>
        """
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        # Mock failed login response
        responses.add(
            responses.POST,
            self.login_url,
            body="<html><div>Invalid username or password</div></html>",
            status=200,
            content_type="text/html",
        )

        # Test login failure
        with pytest.raises(AuthenticationError):
            self.client.login()

    @responses.activate
    def test_login_no_form(self):
        """Test login with missing form."""
        # Mock login page response with no form
        login_html = "<html><div>Welcome</div></html>"
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        # Test login with no form
        with pytest.raises(AuthenticationError):
            self.client.login()

    @responses.activate
    def test_connection_error(self):
        """Test connection error handling."""
        # Mock connection error
        responses.add(
            responses.GET,
            self.login_url,
            body=requests.exceptions.RequestException("Failed to connect"),
            status=500
        )

        # Test connection error
        with pytest.raises(ConnectionError):
            self.client.login()

    @responses.activate
    def test_get_parcel_history(self):
        """Test retrieving parcel history."""
        # Login setup
        login_html = """
        <html>
            <form method="POST" name="login" id="login">
                <input type="hidden" name="token" value="abc123">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit" name="signin" value="signin">Sign In</button>
            </form>
        </html>
        """
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        responses.add(
            responses.POST,
            self.login_url,
            body="<html><div>Welcome</div><a href='/logout'>Sign Out</a></html>",
            status=200,
            content_type="text/html",
        )

        # HTML that works with the client's parsing logic
        history_html = """
        <html>
            <div class="parcel-section">
                <div>Package Code: 12345678</div>
                <div>Package Status: Picked up</div>
                <div>Locker Box #: 42 (Medium)</div>
                <div>Courier: USPS</div>
                <div>Delivered: 2023-06-01 10:00:00</div>
                <div>Status Change: 2023-06-02 15:30:00</div>
                <div>290132647</div>
            </div>
            <div class="parcel-section">
                <div>Package Code: 87654321</div>
                <div>Package Status: Ready for pickup</div>
                <div>Locker Box #: 24 (Large)</div>
                <div>Courier: Amazon</div>
                <div>Delivered: 2023-06-05 09:15:00</div>
                <div>290132648</div>
            </div>
        </html>
        """

        responses.add(
            responses.GET,
            re.compile(f"{self.history_url}.*"),
            body=history_html,
            status=200,
            content_type="text/html",
        )

        # Login
        self.client.login()

        # Test parcel history retrieval
        start_date = datetime(2023, 6, 1)
        end_date = datetime(2023, 6, 10)
        parcels = self.client.get_parcel_history(start_date, end_date)

        assert len(parcels) == 2
        assert parcels[0].get("package_code") == "12345678"
        assert parcels[0].get("status") == "Picked up"
        assert parcels[0].get("locker_box") == "42"
        assert parcels[0].get("size") == "Medium"
        assert parcels[0].get("courier") == "USPS"

    @responses.activate
    def test_get_active_parcels(self):
        """Test retrieving active parcels."""
        # Login and setup as in previous test
        login_html = """
        <html>
            <form method="POST" name="login" id="login">
                <input type="hidden" name="token" value="abc123">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit" name="signin" value="signin">Sign In</button>
            </form>
        </html>
        """
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        responses.add(
            responses.POST,
            self.login_url,
            body="<html><div>Welcome</div><a href='/logout'>Sign Out</a></html>",
            status=200,
            content_type="text/html",
        )

        # Use div structure that works with the client's parsing logic
        history_html = """
        <html>
            <div class="parcel-section">
                <div>Package Code: 12345678</div>
                <div>Package Status: Picked up</div>
                <div>Locker Box #: 42 (Medium)</div>
                <div>Courier: USPS</div>
                <div>Delivered: 2023-06-01 10:00:00</div>
            </div>
            <div class="parcel-section">
                <div>Package Code: 87654321</div>
                <div>Package Status: Ready for pickup</div>
                <div>Locker Box #: 24 (Large)</div>
                <div>Courier: Amazon</div>
                <div>Delivered: 2023-06-05 09:15:00</div>
            </div>
        </html>
        """

        # Add wildcard mock for any parcel history request
        responses.add(
            responses.GET,
            re.compile(f"{self.history_url}.*"),
            body=history_html,
            status=200,
            content_type="text/html",
        )

        # Login
        self.client.login()

        # Test active parcels
        active_parcels = self.client.get_active_parcels(days=30)

        assert len(active_parcels) == 1
        assert active_parcels[0].get("package_code") == "87654321"
        assert active_parcels[0].get("status") == "Ready for pickup"

    @responses.activate
    def test_get_parcels_by_courier(self):
        """Test filtering parcels by courier."""
        # Login and setup as before
        login_html = """
        <html>
            <form method="POST" name="login" id="login">
                <input type="hidden" name="token" value="abc123">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit" name="signin" value="signin">Sign In</button>
            </form>
        </html>
        """
        responses.add(
            responses.GET, self.login_url, body=login_html, status=200, content_type="text/html"
        )

        responses.add(
            responses.POST,
            self.login_url,
            body="<html><div>Welcome</div><a href='/logout'>Sign Out</a></html>",
            status=200,
            content_type="text/html",
        )

        # Use div structure that works with the client's parsing logic
        history_html = """
        <html>
            <div class="parcel-section">
                <div>Package Code: 12345678</div>
                <div>Package Status: Picked up</div>
                <div>Locker Box #: 42 (Medium)</div>
                <div>Courier: USPS</div>
                <div>Delivered: 2023-06-01 10:00:00</div>
            </div>
            <div class="parcel-section">
                <div>Package Code: 87654321</div>
                <div>Package Status: Ready for pickup</div>
                <div>Locker Box #: 24 (Large)</div>
                <div>Courier: Amazon</div>
                <div>Delivered: 2023-06-05 09:15:00</div>
            </div>
            <div class="parcel-section">
                <div>Package Code: 11223344</div>
                <div>Package Status: Delivered</div>
                <div>Locker Box #: 15 (Small)</div>
                <div>Courier: USPS</div>
                <div>Delivered: 2023-06-03 14:30:00</div>
            </div>
        </html>
        """

        # Add mock for any parcel history request
        responses.add(
            responses.GET,
            re.compile(f"{self.history_url}.*"),
            body=history_html,
            status=200,
            content_type="text/html",
        )

        # Login
        self.client.login()

        # Test parcels by courier
        usps_parcels = self.client.get_parcels_by_courier("USPS", days=30)

        assert len(usps_parcels) == 2
        assert all(p.get("courier") == "USPS" for p in usps_parcels)

    def test_export_to_csv(self, tmp_path):
        """Test exporting parcels to CSV."""
        # Create sample parcels
        parcels = [
            {
                "package_code": "12345678",
                "status": "Picked up",
                "locker_box": "42",
                "size": "Medium",
                "courier": "USPS",
            },
            {
                "package_code": "87654321",
                "status": "Ready for pickup",
                "locker_box": "24",
                "size": "Large",
                "courier": "Amazon",
            },
        ]

        # Export to temporary file
        filepath = tmp_path / "test_export.csv"
        result = self.client.export_to_csv(parcels, filepath)

        # Check result
        assert result == filepath
        assert filepath.exists()

        # Read CSV content
        content = filepath.read_text()
        for parcel in parcels:
            for value in parcel.values():
                assert str(value) in content

    def test_export_to_json(self, tmp_path):
        """Test exporting parcels to JSON."""
        import json

        # Create sample parcels
        parcels = [
            {
                "package_code": "12345678",
                "status": "Picked up",
                "locker_box": "42",
                "size": "Medium",
                "courier": "USPS",
            },
            {
                "package_code": "87654321",
                "status": "Ready for pickup",
                "locker_box": "24",
                "size": "Large",
                "courier": "Amazon",
            },
        ]

        # Export to temporary file
        filepath = tmp_path / "test_export.json"
        result = self.client.export_to_json(parcels, filepath)

        # Check result
        assert result == filepath
        assert filepath.exists()

        # Read JSON content
        with open(filepath, "r") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["package_code"] == "12345678"
        assert data[1]["courier"] == "Amazon"
