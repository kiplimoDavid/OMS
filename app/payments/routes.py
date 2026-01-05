from flask import Blueprint, render_template, request, jsonify, current_app
from app.payments.mpesa_mock_and_production_mode import initiate_mpesa_payment
import logging

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/mpesa", methods=["GET", "POST"])
def pay_mpesa():
    """
    Route to handle M-Pesa payments.

    GET:
        - Renders the M-Pesa payment UI (Bootstrap responsive)
    POST:
        - Validates input
        - Initiates M-Pesa payment (mock_live or production)
        - Returns JSON response
    """
    if request.method == "POST":
        try:
            # ---------------- INPUT COLLECTION ----------------
            phone = request.form.get("phone", "").strip()
            amount = request.form.get("amount", "").strip()
            order_id = request.form.get("order_id", "").strip()
            pin = request.form.get("pin", "").strip()  # Collect PIN from frontend modal

            # ---------------- VALIDATION ----------------
            if not phone or not amount or not order_id:
                return jsonify({
                    "status": "FAILED",
                    "message": "Phone number, amount, and order ID are required."
                }), 400

            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                return jsonify({
                    "status": "FAILED",
                    "message": "Amount must be a valid positive number."
                }), 400

            # Optional: Validate PIN in mock mode
            if current_app.config.get("MPESA_MODE", "mock_live") == "mock_live":
                if not pin or len(pin) != 4 or not pin.isdigit():
                    return jsonify({
                        "status": "FAILED",
                        "message": "Please enter a valid 4-digit PIN for mock payment."
                    }), 400

            # ---------------- PAYMENT INITIATION ----------------
            current_app.logger.info(
                f"Initiating M-Pesa payment | Order: {order_id} | Phone: {phone} | Amount: {amount} | PIN: {pin}"
            )

            # Pass PIN to initiate_mpesa_payment for mock mode
            result = initiate_mpesa_payment(phone, amount, order_id, pin=pin)

            # Ensure result is a dictionary with expected keys
            if not isinstance(result, dict) or "status" not in result or "message" not in result:
                current_app.logger.error(f"Invalid response from payment processor: {result}")
                return jsonify({
                    "status": "FAILED",
                    "message": "Payment request failed. Please try again."
                }), 500

            return jsonify(result), 200

        except Exception as e:
            # ---------------- ERROR HANDLING ----------------
            current_app.logger.error(f"M-Pesa payment error: {str(e)}", exc_info=True)
            return jsonify({
                "status": "FAILED",
                "message": "An internal error occurred while processing payment."
            }), 500

    # ---------------- GET REQUEST ----------------
    return render_template(
        "payments/pay_mpesa.html",
        mpesa_mode=current_app.config.get("MPESA_MODE", "mock_live")
    )
