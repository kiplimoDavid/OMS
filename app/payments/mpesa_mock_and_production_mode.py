import random
from datetime import datetime
from flask import current_app
from app import db
from app.models import MpesaTransaction

def initiate_mpesa_payment(phone, amount, order_id):
    """
    Entry point used by routes
    """
    mode = current_app.config.get("MPESA_MODE", "mock_live")

    if mode == "mock_live":
        return _mock_stk_push(phone, amount, order_id)

    # ================= PRODUCTION MODE (COMMENTED) =================
    # elif mode == "production":
    #     return _production_stk_push(phone, amount, order_id)
    # ===============================================================

    return {"status": "FAILED", "message": "Invalid payment mode"}


# ---------------- MOCK MODE ----------------
def _mock_stk_push(phone, amount, order_id):
    """
    Simulated STK Push for mock_live mode.
    Mimics real M-Pesa flow:
      1. Prompt user to accept payment
      2. Ask for confirmation (1=YES, 2=NO)
      3. Check balance
      4. Complete transaction
    """

    if not phone.startswith("254"):
        return _save_tx(order_id, phone, amount, "FAILED", "Invalid phone")

    # Prompt user
    prompt_message = f"Do you want to pay ACME Company KES {amount:.2f}? Reply 1 for YES, 2 for NO."
    print(f"[MOCK STK] Prompt to user ({phone}): {prompt_message}")

    # Simulate user response (1=YES, 2=NO)
    user_response = random.choice([1, 2])
    print(f"[MOCK STK] User response: {user_response}")

    if user_response != 1:
        return _save_tx(order_id, phone, amount, "CANCELLED",
                        "Customer declined payment")

    # Simulate balance check
    has_balance = random.choice([True, True, False])  # 66% chance sufficient balance
    if not has_balance:
        return _save_tx(order_id, phone, amount, "FAILED",
                        "Insufficient M-Pesa balance")

    # Success
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

    auth = base64.b64encode(
        f"{consumer_key}:{consumer_secret}".encode()
    ).decode()

    token_response = requests.get(
        "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
        headers={"Authorization": f"Basic {auth}"}
    )

    access_token = token_response.json().get("access_token")

    # 2. Prepare STK payload
    shortcode = current_app.config.get("MPESA_SHORTCODE")
    passkey = current_app.config.get("MPESA_PASSKEY")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password = base64.b64encode(
        f"{shortcode}{passkey}{timestamp}".encode()
    ).decode()

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
