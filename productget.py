import os
import sys
import json
import time
import logging
import requests
import hashlib
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# Load environment variables
load_dotenv()

app_key = os.getenv('APP_KEY')
app_secret = os.getenv('APP_SECRET')
session_key = os.getenv('SESSION_KEY')

# Directory for logs
LOG_DIR = 'api_logs/'
os.makedirs(LOG_DIR, exist_ok=True)

# URL for the API endpoint
url = 'https://eco.taobao.com/router/rest'

# Check for the required command line argument
if len(sys.argv) < 2:
    print("Usage: python script.py <product_id>")
    sys.exit(1)

product_id = sys.argv[1]

# Define log file names
log_file = f"{LOG_DIR}productget_logs_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xml"
error_log_file = f"{LOG_DIR}productget_error_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xml"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(f"{LOG_DIR}/productget.log")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def remove_sensitive_info(params):
    """Remove sensitive information from params."""
    safe_params = {k: v for k, v in params.items() if k not in ('app_key', 'session', 'sign')}
    return safe_params

def calculate_sign(params, secret):
    """Calculate the MD5 sign for the request."""
    sorted_params = sorted(params.items())
    sign_string = secret + ''.join(f'{k}{v}' for k, v in sorted_params) + secret
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

def log_request(params):
    """Log the API request."""
    request_log_file = f"{LOG_DIR}request_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(request_log_file, "w") as f:
        json.dump({
            "request_params": remove_sensitive_info(params),
        }, f, indent=4)

def log_response(response_data, is_error=False):
    """Log the API response."""
    response_log_file = f"{LOG_DIR}{'error_' if is_error else ''}response_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xml"
    with open(response_log_file, "w") as f:
        f.write(response_data)

def prettify_xml(xml_str):
    """Prettify the XML string."""
    xml = parseString(xml_str)
    return xml.toprettyxml(indent="  ")

try:
    # Prepare the parameters for the request
    params = {
        'app_key': app_key,
        'format': 'xml',
        'method': 'alibaba.icbu.product.get',
        'partner_id': 'apidoc',
        'session': session_key,
        'sign_method': 'md5',
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'v': '2.0',
        'language': 'ENGLISH',
        'product_id': product_id,
    }
    params['sign'] = calculate_sign(params, app_secret)

    # Log the request
    log_request(params)

    # Make the API request
    response = requests.get(url, params=params)
    response_data = response.text
    prettified_response = prettify_xml(response_data)

    # Log the response
    log_response(prettified_response)

    # Write the logs to file
    with open(log_file, "w") as f:
        f.write(prettified_response)

    logger.debug(f"Response: {prettified_response}")

    # Parse the XML response to a dictionary for handling
    response_dict = ET.fromstring(response_data)
    error_response = response_dict.find('error_response')

    # Check for errors in the response
    if error_response is not None:
        error_message = error_response.find('msg').text
        with open(error_log_file, "w") as f:
            f.write(prettified_response)
        print(f"Error: {error_message}")
    else:
        print("API call successful.")
        print(prettified_response)

except requests.exceptions.RequestException as e:
    # Handle request exceptions
    error_message = f"<error><message>{str(e)}</message></error>"
    prettified_error_message = prettify_xml(error_message)
    with open(error_log_file, "w") as f:
        f.write(prettified_error_message)
    logger.error(f"Request failed: {e}")
    print(f"Request failed: {e}")
