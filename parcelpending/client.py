"""
Client for interacting with the ParcelPending website.
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime, timedelta
from .exceptions import AuthenticationError, ConnectionError, ParcelPendingError

logger = logging.getLogger(__name__)

class ParcelPendingClient:
    """
    Client for interacting with the ParcelPending website.
    
    This client handles authentication and retrieval of parcel history data.
    """
    
    BASE_URL = "https://my.parcelpending.com"
    LOGIN_URL = f"{BASE_URL}/login"
    PARCEL_HISTORY_URL = f"{BASE_URL}/parcel-history"
    
    def __init__(self, email=None, password=None):
        """
        Initialize the ParcelPending client.
        
        Args:
            email (str): Email or username for authentication
            password (str): Password for authentication
        """
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.authenticated = False
    
    def login(self, email=None, password=None):
        """
        Log in to the ParcelPending website.
        
        Args:
            email (str, optional): Email or username for authentication.
                If not provided, uses the one set during initialization.
            password (str, optional): Password for authentication.
                If not provided, uses the one set during initialization.
                
        Returns:
            bool: True if login was successful
            
        Raises:
            AuthenticationError: If authentication fails
            ConnectionError: If connection to the server fails
        """
        email = email or self.email
        password = password or self.password
        
        if not email or not password:
            raise AuthenticationError("Email and password are required")
        
        try:
            # Clear any existing session
            self.session = requests.Session()
            self.authenticated = False
            
            # First, get the login page to extract CSRF token and form details
            logger.info("Fetching login page")
            response = self.session.get(self.LOGIN_URL)
            response.raise_for_status()
            
            # Save HTML for debugging
            if logger.isEnabledFor(logging.DEBUG):
                with open('login_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.debug("Saved login page HTML to 'login_page_debug.html' for debugging")
            
            # Parse the login page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the login form - ParcelPending uses id="login"
            login_form = soup.find('form', id='login')
            
            if not login_form:
                # Try by name if id doesn't work
                login_form = soup.find('form', {'name': 'login'})
            
            if not login_form:
                # More generic approach - look for any form with username and password fields
                for form in soup.find_all('form'):
                    username_field = form.find('input', {'name': 'username'})
                    password_field = form.find('input', {'name': 'password'})
                    if username_field and password_field:
                        login_form = form
                        logger.debug("Found login form using username/password field detection")
                        break
            
            if not login_form:
                logger.error("Could not find login form - the website structure may have changed")
                raise AuthenticationError("Could not find login form")
            
            # Extract form data including hidden fields
            form_data = {}
            for input_field in login_form.find_all('input'):
                name = input_field.get('name')
                if name and name not in ['username', 'password', 'signin', 'signin_mobile']:
                    value = input_field.get('value', '')
                    form_data[name] = value
                    logger.debug(f"Found form field: {name} = {value}")
            
            # Add credentials - ParcelPending uses 'username' for email field
            form_data['username'] = email
            form_data['password'] = password
            
            # Add signin field - this is the submit button value
            form_data['signin'] = 'signin'
            
            logger.debug(f"Prepared form data (without password): {form_data}")
            
            # Determine the form submission URL
            form_action = login_form.get('action', '')
            login_url = self.LOGIN_URL  # Default
            
            if form_action:
                if form_action.startswith('http'):
                    login_url = form_action
                elif form_action.startswith('/'):
                    login_url = f"{self.BASE_URL}{form_action}"
                else:
                    login_url = f"{self.BASE_URL}/{form_action}"
            
            # Submit login form
            logger.info(f"Submitting login form to {login_url}")
            login_response = self.session.post(
                login_url,
                data=form_data,
                headers={
                    'Referer': self.LOGIN_URL,
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            login_response.raise_for_status()
            
            # Check for login success indicators
            if "invalid username or password" in login_response.text.lower():
                logger.error("Login failed - authentication error message detected")
                raise AuthenticationError("Invalid username or password")
            
            # Verify login success
            self.authenticated = True
            logger.info("Login successful!")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error during login: {str(e)}")
            raise ConnectionError(f"Failed to connect to ParcelPending: {str(e)}")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}")
            raise ParcelPendingError(f"Unexpected error during login: {str(e)}")
    
    def get_parcel_history(self, start_date, end_date):
        """
        Retrieve parcel history within a specified date range.
        
        Args:
            start_date (str or datetime): Start date for parcel history
            end_date (str or datetime): End date for parcel history
            
        Returns:
            list: List of parcels within the specified date range
            
        Raises:
            AuthenticationError: If not logged in
            ConnectionError: If connection to the server fails
        """
        if not self.authenticated:
            raise AuthenticationError("You must login before retrieving parcel history")
        
        # Convert datetime objects to strings in MM/DD/YYYY format
        if isinstance(start_date, datetime):
            start_date = start_date.strftime('%m/%d/%Y')
        if isinstance(end_date, datetime):
            end_date = end_date.strftime('%m/%d/%Y')
        
        try:
            # Navigate to parcel history page with the correct parameters
            params = {
                'occupant_first_name': '',
                'occupant_last_name': '',
                'occupant_email': '',
                'parcel_delivery_date_start': start_date,
                'parcel_delivery_date_end': end_date,
                'parcel_pickup_date_start': '',
                'parcel_pickup_date_end': '',
                'parcel_id': '',
                'tracking_number': '',
                'package_code': '',
                'order_number': '',
                'package_status': '',
                'pick_up_origin': '',
                'sort_by': 'deliveryDate',
                'sort_order': 'DESC'
            }
            
            logger.info(f"Requesting parcel history with delivery dates from {start_date} to {end_date}")
            logger.debug(f"Full params: {params}")
            
            response = self.session.get(self.PARCEL_HISTORY_URL, params=params)
            response.raise_for_status()
            
            # Save HTML for debugging
            if logger.isEnabledFor(logging.DEBUG):
                with open('parcel_history_debug.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.debug("Saved parcel history HTML to 'parcel_history_debug.html' for debugging")
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            parcels = self._parse_parcels(soup)
            
            return parcels
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error retrieving parcel history: {str(e)}")
            raise ConnectionError(f"Failed to retrieve parcel history: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving parcel history: {str(e)}")
            raise ParcelPendingError(f"Failed to retrieve parcel history: {str(e)}")
    
    def _parse_parcels(self, soup):
        """
        Parse parcels from the HTML content.
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            list: Extracted parcels with structured data
        """
        parcels = []
        
        # First try looking for tables
        tables = soup.find_all('table')
        for table in tables:
            logger.debug(f"Found table: {table.get('class', 'No class')}")
            
            # Extract table headers
            headers = []
            header_row = table.find('thead')
            if header_row:
                headers = [th.text.strip().lower() for th in header_row.find_all('th')]
                logger.debug(f"Table headers: {headers}")
            
            # Process rows if we have headers
            if headers:
                data_rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
                for row in data_rows:
                    cells = row.find_all('td')
                    
                    # Create dictionary with column names as keys
                    if len(cells) == len(headers):
                        parcel = {headers[i]: cell.text.strip() for i, cell in enumerate(cells)}
                        parcels.append(parcel)
                        logger.debug(f"Extracted parcel from table: {parcel}")
        
        # If no parcels found in tables, look for package data in other formats
        if not parcels:
            # The site seems to structure package details in sections
            # Look for package code sections which indicate the start of package data
            package_code_elements = soup.find_all(string=lambda s: s and "Package Code:" in s)
            
            for code_element in package_code_elements:
                # Find the nearest container that holds all package info
                container = code_element.find_parent('div')
                
                if container:
                    parcel = {}
                    
                    # Extract package code
                    package_code = code_element.strip()
                    if package_code:
                        parcel['package_code'] = package_code.replace("Package Code:", "").strip()
                    
                    # Extract package status
                    status_elem = container.find(string=lambda s: s and "Package Status:" in s)
                    if status_elem:
                        next_elem = status_elem.find_next(string=True)
                        if next_elem:
                            parcel['status'] = next_elem.strip()
                    
                    # Extract locker box
                    locker_box = container.find(string=lambda s: s and "Locker Box #:" in s)
                    if locker_box:
                        box_text = locker_box.strip()
                        parcel['locker_box'] = box_text.split("Locker Box #:")[1].strip().split("(")[0].strip()
                        
                        # Extract size
                        if "(" in box_text and ")" in box_text:
                            parcel['size'] = box_text.split("(")[1].split(")")[0].strip()
                    
                    # Extract courier
                    courier_elem = container.find(string=lambda s: s and "Courier:" in s)
                    if courier_elem:
                        next_elem = courier_elem.find_next(string=True)
                        if next_elem and next_elem.strip():
                            parcel['courier'] = next_elem.strip()
                    
                    # Extract delivery date
                    delivered_elem = container.find(string=lambda s: s and "Delivered:" in s)
                    if delivered_elem:
                        parcel['delivered'] = delivered_elem.replace("Delivered:", "").strip()
                    
                    # Extract status change date
                    status_change_elem = container.find(string=lambda s: s and "Status Change:" in s)
                    if status_change_elem:
                        parcel['status_change'] = status_change_elem.replace("Status Change:", "").strip()
                    
                    # Extract package ID
                    id_elements = container.find_all(string=True)
                    for elem in id_elements:
                        if elem.strip().isdigit() and len(elem.strip()) > 5:
                            parcel['package_id'] = elem.strip()
                            break
                    
                    # Add parcel if we found data
                    if parcel:
                        parcels.append(parcel)
            
            # If still no parcels, try extracting from raw content
            if not parcels:
                # Look for sections with parcel-like content
                parcel_sections = soup.find_all('div', class_=lambda c: c and ('parcel' in c.lower() or 'package' in c.lower()))
                
                for section in parcel_sections:
                    raw_content = ' '.join(section.stripped_strings)
                    if raw_content:
                        parcel = {'raw_content': raw_content}
                        
                        # Try to extract courier
                        courier_match = re.search(r"Courier:[\s]*([\w\s]+)", raw_content)
                        if courier_match:
                            parcel['courier'] = courier_match.group(1).strip()
                        
                        # Try to extract box number
                        box_match = re.search(r"Locker Box #:[\s]*(\d+)", raw_content)
                        if box_match:
                            parcel['locker_box'] = box_match.group(1).strip()
                        
                        # Try to extract size
                        size_match = re.search(r"\((Small|Medium|Large|X-?large)\)", raw_content, re.IGNORECASE)
                        if size_match:
                            parcel['size'] = size_match.group(1).strip()
                        
                        # Add parcel if we extracted something useful
                        if len(parcel) > 1:  # More than just raw_content
                            parcels.append(parcel)
        
        logger.info(f"Found {len(parcels)} parcels")
        return parcels
    
    def get_active_parcels(self, days=30):
        """
        Get parcels that haven't been picked up yet.
        
        Args:
            days (int): Number of days to look back for active parcels
            
        Returns:
            list: Active parcels awaiting pickup
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_parcels = self.get_parcel_history(start_date, end_date)
        
        # Filter for parcels that haven't been picked up
        active_parcels = [
            parcel for parcel in all_parcels 
            if 'status' in parcel and parcel['status'].lower() != 'picked up'
        ]
        
        return active_parcels

    def get_parcels_by_courier(self, courier_name, days=30):
        """
        Get parcels delivered by a specific courier.
        
        Args:
            courier_name (str): Name of the courier (e.g., "USPS", "Amazon")
            days (int): Number of days to look back
            
        Returns:
            list: Parcels delivered by the specified courier
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_parcels = self.get_parcel_history(start_date, end_date)
        
        # Filter for parcels from the specified courier
        courier_parcels = [
            parcel for parcel in all_parcels 
            if 'courier' in parcel and courier_name.lower() in parcel['courier'].lower()
        ]
        
        return courier_parcels

    def get_parcel_by_code(self, package_code, days=90):
        """
        Find a specific parcel by its package code.
        
        Args:
            package_code (str): The package code to search for
            days (int): Number of days to look back
            
        Returns:
            dict or None: The parcel if found, None otherwise
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_parcels = self.get_parcel_history(start_date, end_date)
        
        # Look for the package code
        for parcel in all_parcels:
            if 'package_code' in parcel and parcel['package_code'] == package_code:
                return parcel
        
        return None

    def export_to_csv(self, parcels, filepath='parcels.csv'):
        """
        Export parcel data to a CSV file.
        
        Args:
            parcels (list): List of parcel dictionaries
            filepath (str): Path to save the CSV file
            
        Returns:
            str: Path to the saved file
        """
        import csv
        
        if not parcels:
            logger.warning("No parcels to export")
            return None
        
        # Get all field names across all parcels
        fieldnames = set()
        for parcel in parcels:
            fieldnames.update(parcel.keys())
        
        fieldnames = sorted(list(fieldnames))
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for parcel in parcels:
                    writer.writerow(parcel)
            
            logger.info(f"Exported {len(parcels)} parcels to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return None

    def export_to_json(self, parcels, filepath='parcels.json'):
        """
        Export parcel data to a JSON file.
        
        Args:
            parcels (list): List of parcel dictionaries
            filepath (str): Path to save the JSON file
            
        Returns:
            str: Path to the saved file
        """
        import json
        
        if not parcels:
            logger.warning("No parcels to export")
            return None
        
        try:
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(parcels, jsonfile, indent=2)
            
            logger.info(f"Exported {len(parcels)} parcels to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting to JSON: {str(e)}")
            return None 