import base64
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from flask import current_app


def get_access_token():
    cfg = current_app.config
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=HTTPBasicAuth(
            cfg["MPESA_CONSUMER_KEY"],
            cfg["MPESA_CONSUMER_SECRET"]
        ),
        timeout=10
    )

    response.raise_for_status()
    return response.json().get("access_token")


def stk_push(amount, phone):
    cfg = current_app.config
    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{cfg['MPESA_SHORTCODE']}{cfg['MPESA_PASSKEY']}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": cfg["MPESA_SHORTCODE"],
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": cfg["MPESA_SHORTCODE"],
        "PhoneNumber": phone,
        "CallBackURL": cfg["MPESA_CALLBACK_URL"],
        "AccountReference": "OMS_DEV",
        "TransactionDesc": "Order Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers,
        timeout=15
    )

    response.raise_for_status()
    return response.json()
