import random
from datetime import datetime
from flask import current_app
from app import db
from app.models import MpesaTransaction


def initiate_mpesa_payment(phone, amount, order_id, pin=None):
    """
    Entry point used by routes.
    `pin` is required for mock mode.
    """
    mode = current_app.config.get("MPESA_MODE", "mock_live")

    if mode == "mock_live":
        return _mock_stk_push(phone, amount, order_id, pin)

    # ================= PRODUCTION MODE (COMMENTED) =================
    # elif mode == "production":
    #     return _production_stk_push(phone, amount, order_id)
    # ===============================================================

    return {"status": "FAILED", "message": "Invalid payment mode"}


# ---------------- MOCK MODE ----------------
def _mock_stk_push(phone, amount, order_id, pin):
    """
    Fully simulated STK Push requiring PIN.
    """

    # Validate phone number
    if not phone.startswith("254"):
        return _save_tx(order_id, phone, amount, "FAILED", "Invalid phone number")

    # Validate PIN
    if not pin or len(pin) != 4 or not pin.isdigit():
        return _save_tx(order_id, phone, amount, "FAILED", "Invalid PIN entered")

    # Simulate customer acceptance (YES / NO)
    user_accepts = random.choice([True, False])

    if not user_accepts:
        return _save_tx(order_id, phone, amount, "CANCELLED",
                        "Customer declined payment")

    # Simulate balance check
    has_balance = random.choice([True, True, False])  # Higher chance of success

    if not has_balance:
        return _save_tx(order_id, phone, amount, "FAILED",
                        "Insufficient M-Pesa balance")

    # Payment success
    receipt = f"MOCK{random.randint(100000, 999999)}"
    return _save_tx(order_id, phone, amount, "SUCCESS",
                    "Payment successful", receipt)


# ---------------- PRODUCTION MODE (COMMENTED) ----------------
"""
import base64
import requests
from datetime import datetime

def _production_stk_push(phone, amount, order_id):
    # 1. Get access token
    consumer_key = current_app.config.get("MPESA_CONSUMER_KEY")
    consumer_secret = current_app.config.get("MPESA_CONSUMER_SECRET")

    auth = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()

    token_response = requests.get(
        "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {auth}"}
    )

    access_token = token_response.json().get("access_token")

    # 2. Prepare STK payload
    shortcode = current_app.config.get("MPESA_SHORTCODE")
    passkey = current_app.config.get("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(f"{shortcode}{passkey}{timestamp}".encode()).decode()

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": shortcode,
        "PhoneNumber": phone,
        "CallBackURL": current_app.config.get("MPESA_CALLBACK_URL"),
        "AccountReference": f"ORDER-{order_id}",
        "TransactionDesc": "OMS Payment"
    }

    # 3. Call Safaricom STK endpoint
    stk_response = requests.post(
        "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    response_data = stk_response.json()

    # 4. Save response
    tx = MpesaTransaction(
        order_id=order_id,
        phone_number=phone,
        amount=amount,
        status="PENDING",
        checkout_request_id=response_data.get("CheckoutRequestID")
    )

    db.session.add(tx)
    db.session.commit()

    return {
        "status": "PENDING",
        "message": "STK Push sent. Please complete payment on your phone.",
        "reference": response_data.get("CheckoutRequestID")
    }
"""
# -------------------------------------------------------------


# ---------------- TRANSACTION SAVE ----------------
def _save_tx(order_id, phone, amount, status, message, receipt=None):
    tx = MpesaTransaction(
        order_id=order_id,
        phone_number=phone,
        amount=amount,
        status=status,
        mpesa_receipt_number=receipt or message,
        created_at=datetime.utcnow()
    )
    db.session.add(tx)
    db.session.commit()

    return {
        "status": status,
        "message": message,
        "reference": receipt
    }
