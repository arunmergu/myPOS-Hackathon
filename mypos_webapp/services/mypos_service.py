import requests
from flask import current_app
import base64
import uuid
import json
def generate_transaction_id():
    return uuid.uuid4().int >> 96 


def generate_oauth_token():
    ecommerce_partner_client_id = current_app.config['ECOMMERCE_PARTNER_CLIENT_ID']
    ecommerce_partner_client_secret = current_app.config['ECOMMERCE_PARTNER_CLIENT_SECRET']
    oauth_url=current_app.config['MYPOS_OAUTH_API_URL']

    # Encode client_id:client_secret as Base64
    credentials = f"{ecommerce_partner_client_id}:{ecommerce_partner_client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    # Prepare request
    response = requests.post(
        url=oauth_url,  # or production URL
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        },
        data={
            "grant_type": "client_credentials"
        }
    )
    token=response.json().get('access_token')
    print(token)
    return token



def generate_session_id():
    """
    Generates a session ID using the provided myPOS API credentials.

    Args:
        bearer_token (str): Bearer token for authorization.
        client_id (str): Client ID for the merchant.
        client_secret (str): Client secret for the merchant.
        session_url (str): The endpoint to create a session.

    Returns:
        str: The session ID.

    Raises:
        ValueError: If 'session' is not found in the response.
        ConnectionError: If the request fails.
    """
    ecommerce_merchant_client_id = current_app.config['ECOMMERCE_MERCHANT_CLIENT_ID']
    ecommerce_merchant_client_secret = current_app.config['ECOMMERCE_MERCHANT_CLIENT_SECRET']
    session_url=current_app.config['MYPOS_SESSION_API_URL']

    bearer_token=generate_oauth_token()

    payload = {
        "client_id": ecommerce_merchant_client_id,
        "client_secret": ecommerce_merchant_client_secret
    }

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(session_url, json=payload, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        session_id = response_data.get("session")
        if session_id:
            print(session_id)
            return session_id
        
        else:
            raise ValueError("Session ID not found in response.")
    else:
        raise ConnectionError(f"Failed to generate session. Status code: {response.status_code}")



def get_merchant_transaction_list():
    """
    Fetches the merchant account number from the myPOS API.

    Args:
        session_id (str): Session ID for the API call.
        partner_id (str): Partner ID provided by myPOS.
        application_id (str): Application ID provided by myPOS.
        bearer_token (str): Bearer token for authorization.

    Returns:
        str: The merchant account number.

    Raises:
        ValueError: If account number is not found in the response.
        ConnectionError: If the request fails.
    """

    partner_id = current_app.config['PARTNER_ID']
    ecommerce_application_id = current_app.config['ECOMMERCE_APPLICATION_ID']
    transaction_list_url=current_app.config['MYPOS_TRANSACTION_API_LIST_URL']

    bearer_token=generate_oauth_token()
    session_id=generate_session_id()

    headers = {
        "X-Session": session_id,
        "X-Partner-Id": partner_id,
        "X-Application-Id": ecommerce_application_id,
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }

    response = requests.get(transaction_list_url, headers=headers)

    if response.status_code == 200:
        try:
            return response.json()["items"][0]["account_number"],response.json()["items"]
        except (KeyError, IndexError):
            raise ValueError("Account number not found in response.")
    else:
        raise ConnectionError(f"Failed to fetch data. Status code: {response.status_code}")


def analyze_transactions(transactions):
    """
    Analyze a list of transactions to compute:
    - Total number of transactions
    - Total revenue (EUR)
    - Average transaction amount (EUR)

    Args:
        transactions (list): List of transaction dictionaries.

    Returns:
        dict: Dictionary with insights.
    """
    if not transactions:
        return {
            "total_transactions": 0,
            "total_revenue_eur": 0.0,
            "average_transaction_eur": 0.0
        }

    total_revenue = sum(txn.get("transaction_amount", 0.0) for txn in transactions)
    total_transactions = len(transactions)
    average_transaction = total_revenue / total_transactions

    return {
        "total_transactions": total_transactions,
        "total_revenue_eur": round(total_revenue, 2),
        "average_transaction_eur": round(average_transaction, 2)
    }


def request_myposdeposit(quotation_id,title,amount, currency, customer_email):
    """
    Request a deposit payment via MyPOS TRANSACTION API
    """

    partner_id = current_app.config['PARTNER_ID']
    ecommerce_application_id = current_app.config['ECOMMERCE_APPLICATION_ID']
    payment_url=current_app.config['MYPOS_PAYMENT_API_URL']

    bearer_token=generate_oauth_token()
    session_id=generate_session_id()

    payment_data = {
    "amount": amount,
    "currency": currency,
    "client_name": "Growth Gurus",
    "reason": "TEST NOW ME",
    "booking_text": title,
    "dba": "company",
    "expiry_date": "2025-06-30",
    "payment_request_lang": "BG",
    "notify_gsm": "+359885885885",
    "qr_generated": False
    }
    
    headers = {
        "X-Session": session_id,
        "X-Partner-Id": partner_id,
        "X-Application-Id": ecommerce_application_id,
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json; x-api-version=1",
        "Accept": "application/json"
    }
    '''
    response = requests.post(payment_url, data=json.dumps(payment_data), headers=headers)
   
    if response.status_code == 200:
        response_json = response.json()
        transaction_id=response_json.get("code")
        success='success'
        url = response_json.get("payment_request_url")
        if url:
            return url
        else:
            raise ValueError("Payment URL not found in response.")
    else:
        raise ConnectionError(f"Failed to generate payment URL. Status code: {response.status_code}")
    '''
    try:
        response = requests.post(payment_url, data=json.dumps(payment_data), headers=headers)

        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'payment_url': response_data.get('payment_request_url'),
                'transaction_id':generate_transaction_id()
            }
        else:
            current_app.logger.error(f"MyPOS API error: {response_data}")
            return {
                'success': False,
                'error': response_data.get('message', 'Unknown error')
            }
    except Exception as e:
        current_app.logger.error(f"MyPOS API request error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
