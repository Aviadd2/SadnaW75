from datetime import datetime
import random
import string

import time
from constants import OPTIONS_DETAILS, MAX_RETRIES, TIMEOUT, ORDER_STAGES, ORDER_NUMBER_LENGTH, AUTH_TOKEN, API_URL
import re
import requests
from requests.exceptions import Timeout


def request_with_retry(method, url, **kwargs):
    """Make an HTTP request with a retry mechanism for timeouts."""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Make the request with the specified timeout
            response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
            return response
        except Timeout:
            retries += 1
            print(f"Timeout occurred, retrying {retries}/{MAX_RETRIES}...")
    print("Max retries reached. Request failed.")
    return None


def fetch_messages(timestamp):
    """Fetch new messages from the WhatsApp API from a specific timestamp."""
    print(f'Fetching messages from {timestamp}')
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {AUTH_TOKEN}'
    }
    response = request_with_retry('GET', f'{API_URL}/list?count=100&time_from={timestamp}', headers=headers)

    if response:
        print('Fetched messages from WhatsApp API')
        return response.json()
    else:
        print('Failed to fetch messages after multiple retries.')
        return {}


def send_message(to, body):
    """Send a message to a WhatsApp user."""
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {AUTH_TOKEN}',
        'content-type': 'application/json'
    }
    data = {
        "typing_time": 0,
        "to": to,
        "body": body
    }
    print('Sending message with WhatsApp API')
    response = request_with_retry('POST', f"{API_URL}/text", json=data, headers=headers)

    if response and response.status_code == 200:
        print('Sent message with WhatsApp API')
        return True
    else:
        print('Failed to send message after multiple retries.')
        return False


def calculate_price(order):
    """Calculate the total price of the order based on user choices."""
    size_price = OPTIONS_DETAILS['size'][order['size']][1]
    type_price = OPTIONS_DETAILS['type'][order['type']][1]
    pack_price = OPTIONS_DETAILS['pack'][order['pack']][1]

    amount = int(OPTIONS_DETAILS['amount'][order['amount']][0])
    pack_quantity = order['pack_quantity']

    total_price_per_pack = (size_price + type_price) * amount + pack_price

    total_price = total_price_per_pack * pack_quantity

    return total_price

def get_time():
    return round(time.time())


def validate_address(address):
    """Validate that the address contains both Hebrew letters and numbers."""
    return bool(re.search(r'[\u0590-\u05FF]', address) and re.search(r'\d', address))


def validate_name(name):
    """Validate that the name contains no numbers."""
    return not bool(re.search(r'\d', name))


def generate_order_number():
    characters = string.ascii_uppercase + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(ORDER_NUMBER_LENGTH))
    return random_string


def get_message_from_stage(stage):
    message = ''
    if stage == ORDER_STAGES['ACCEPTED']:
        message = 'ההזמנה אושרה ותישלח בקרוב!'
    if stage == ORDER_STAGES['DELIVERY']:
        message = 'ההזמנה במשלוח והיא כבר בדרך!'
    if stage == ORDER_STAGES['DELIVERED']:
        message = ('ההזמנה הגיעה ליעדה בהצלחה :) במידה ויש בעיה ניתן לפנות אלינו'
                   )
    return message


def format_order_name(order_number, phone_number):
    timestamp = datetime.now().strftime("%d/%m/%y(%H:%M)")
    formatted_order = f"{order_number}-{timestamp}-{phone_number}"
    return formatted_order
