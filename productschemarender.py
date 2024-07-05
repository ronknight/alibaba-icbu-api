import os
import sys
import requests
import hashlib
import time
import json
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

# Load environment variables from .env file
load_dotenv()

# Retrieve variables from environment
app_key = os.getenv('APP_KEY')
app_secret = os.getenv('APP_SECRET')
session_key = os.getenv('SESSION_KEY')

# Define the log directory
LOG_DIR = 'api_logs/'  # Directory to store log files
os.makedirs(LOG_DIR, exist_ok=True)  # Create directory if it doesn't exist

# API endpoint and parameters
url = 'https://eco.taobao.com/router/rest'

# Check if necessary command-line arguments are provided
if len(sys.argv) < 3:
    print("Usage: python script.py <cat_id> <product_id>")
    sys.exit(1)

cat_id = sys.argv[1]  # Get cat_id from command-line argument
product_id = sys.argv[2]  # Get product_id from command-line argument

# Parameters for the API call
params = {
    "app_key": app_key,
    "format": "xml",  # Request XML response
    "method": "alibaba.icbu.product.schema.render",
    "partner_id": "apidoc",
    "session": session_key,
    "sign_method": "md5",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "v": "2.0",
    "cat_id": cat_id,  # Replace with the actual cat_id
    "language": "en_US",  # Replace with the desired language
    "product_id": product_id,  # Replace with the actual product_id
}

# Calculate sign
def calculate_sign(params, secret):
    sorted_params = sorted(params.items())
    sign_string = secret + ''.join([f'{k}{v}' for k, v in sorted_params]) + secret
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

# Add sign to parameters
params["sign"] = calculate_sign(params, app_secret)

# Remove sensitive information for logging
def remove_sensitive_info(params):
    safe_params = params.copy()
    safe_params.pop("app_key", None)
    safe_params.pop("session", None)
    safe_params.pop("sign", None)
    return safe_params

# Prettify XML
def prettify_xml(xml_str):
    xml = parseString(xml_str)
    return xml.toprettyxml(indent="  ")

# Log file names
log_file = f"{LOG_DIR}product_schema_render_logs_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xml"
error_log_file = f"{LOG_DIR}product_schema_render_error_{time.strftime('%Y-%m-%d_%H-%M-%S')}.xml"

try:
    # Make the API request
    render_product_schema_request = requests.get(url, params=params)
    render_product_schema_response = render_product_schema_request.text

    # Prettify the response XML
    prettified_response = prettify_xml(render_product_schema_response)

    # Log API request and response
    with open(log_file, "w") as f:
        f.write(prettified_response)

    # Parse the XML response
    response_dict = ET.fromstring(render_product_schema_response)
    error_response = response_dict.find('error_response')

    # Example of handling the response data
    if error_response is not None:
        error_message = error_response.find('msg').text
        with open(error_log_file, "w") as f:
            f.write(prettified_response)
        print(f"Error: {error_message}")
    else:
        print("API call successful.")
        print(prettified_response)

except requests.exceptions.RequestException as e:
    error_message = f"<error><message>{str(e)}</message></error>"
    prettified_error_message = prettify_xml(error_message)
    with open(error_log_file, "w") as f:
        f.write(prettified_error_message)
    print(f"Request failed: {e}")
