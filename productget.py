import os
import sys
import json
import time
import logging
import requests
import hashlib
from dotenv import load_dotenv

load_dotenv()

app_key = os.getenv('APP_KEY')
app_secret = os.getenv('APP_SECRET')
session_key = os.getenv('SESSION_KEY')

LOG_DIR = 'api_logs/'
os.makedirs(LOG_DIR, exist_ok=True)

url = 'https://eco.taobao.com/router/rest'

if len(sys.argv) < 2:
    print("Usage: python script.py <product_id>")
    sys.exit(1)

product_id = sys.argv[1]

log_file = f"{LOG_DIR}productget_logs_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
error_log_file = f"{LOG_DIR}productget_error_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(f"{LOG_DIR}/productget.log")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def remove_sensitive_info(params):
    safe_params = {k: v for k, v in params.items() if k not in ('app_key', 'session', 'sign')}
    return safe_params

def calculate_sign(params, secret):
    sorted_params = sorted(params.items())
    sign_string = secret + ''.join(f'{k}{v}' for k, v in sorted_params) + secret
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest().upper()

def log_request(params):
    request_log_file = f"{LOG_DIR}request_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(request_log_file, "w") as f:
        json.dump({
            "request_params": remove_sensitive_info(params),
        }, f, indent=4)

def log_response(response_data):
    response_log_file = f"{LOG_DIR}response_{time.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    with open(response_log_file, "w") as f:
        json.dump({
            "response": response_data,
        }, f, indent=4)

try:
    params = {
        'app_key': app_key,
        'format': 'json',
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

    log_request(params)

    response = requests.get(url, params=params)
    response_data = response.json()

    log_response(response_data)

    with open(log_file, "w") as f:
        json.dump({
            "request_params": remove_sensitive_info(params),
            "response": response_data,
        }, f, indent=4)

    logger.debug(f"Response: {response_data}")

    if 'error_response' in response_data:
        with open(error_log_file, "w") as f:
            json.dump({
                "request_params": remove_sensitive_info(params),
                "response": response_data,
            }, f, indent=4)
        print(f"Error: {response_data['error_response']['msg']}")
    else:
        print("API call successful.")
        print(json.dumps(response_data, indent=4))

except requests.exceptions.RequestException as e:
    with open(error_log_file, "w") as f:
        json.dump({
            "request_params": remove_sensitive_info(params),
            "error_message": str(e),
        }, f, indent=4)
    logger.error(f"Request failed: {e}")
    print(f"Request failed: {e}")

