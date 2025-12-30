from flask import Blueprint, request, jsonify, current_app
from app.extensions import db

from app.mpesa.service import stk_push

bp = Blueprint("mpesa", __name__, url_prefix="/mpesa")


@bp.route("/ping", methods=["GET"])
def ping():
    """
    Health check
    """
    return jsonify({
        "status": "success",
        "message": "Mpesa service is running"
    })


@bp.route("/stk-push", methods=["POST"])
def initiate_stk_push():
    """
    Initiate STK Push and save transaction as PENDING
    """
    data = request.get_json(silent=True) or {}

    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({"error": "phone and amount are required"}), 400

    try:
        response = stk_push(amount, phone)
    except Exception as e:
        current_app.logger.error(f"STK Push failed: {e}")
        return jsonify({"error": "Failed to initiate STK push"}), 500

    txn = MpesaTransaction(
        phone_number=phone,
        amount=amount,
        merchant_request_id=response.get("MerchantRequestID"),
        checkout_request_id=response.get("CheckoutRequestID"),
        status="PENDING"
    )

    db.session.add(txn)
    db.session.commit()

    return jsonify(response), 200


@bp.route("/callback", methods=["POST"])
def mpesa_callback():
    """
    Safaricom STK callback handler
    """
    data = request.get_json(silent=True) or {}

    try:
        stk = data["Body"]["stkCallback"]
        checkout_id = stk["CheckoutRequestID"]
        result_code = stk["ResultCode"]
        result_desc = stk["ResultDesc"]
    except KeyError:
        current_app.logger.error("Invalid callback payload")
        return jsonify({"ResultCode": 0, "ResultDesc": "Invalid payload"})

    txn = MpesaTransaction.query.filter_by(
        checkout_request_id=checkout_id
    ).first()

    if not txn:
        current_app.logger.warning(f"Transaction not found: {checkout_id}")
        return jsonify({"ResultCode": 0, "ResultDesc": "Transaction not found"})

    txn.result_code = str(result_code)
    txn.result_desc = result_desc

    if result_code == 0:
        items = stk.get("CallbackMetadata", {}).get("Item", [])

        receipt = None
        trx_date = None

        for item in items:
            if item["Name"] == "MpesaReceiptNumber":
                receipt = item.get("Value")
            elif item["Name"] == "TransactionDate":
                trx_date = item.get("Value")

        txn.mpesa_receipt_number = receipt
        txn.transaction_date = str(trx_date)
        txn.status = "SUCCESS"
    else:
        txn.status = "FAILED"

    db.session.commit()

    return jsonify({"ResultCode": 0, "ResultDesc": "OK"})
