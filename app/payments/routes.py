from flask import Blueprint, render_template, request, jsonify, current_app
from app.payments.mpesa_mock_and_production_mode import initiate_mpesa_payment

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/mpesa", methods=["GET", "POST"])
def pay_mpesa():
    """
    Route to handle M-Pesa payment.
    GET: Displays the payment form (Bootstrap responsive UI)
    POST: Initiates payment via mock or production mode
    """
    if request.method == "POST":
        # Get form data
        phone = request.form.get("phone")
        amount = request.form.get("amount")
        order_id = request.form.get("order_id")

        # Validate inputs
        if not phone or not amount or not order_id:
            return jsonify({
                "status": "FAILED",
                "message": "Phone, amount, and order ID are required."
            }), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({
                "status": "FAILED",
                "message": "Invalid amount. Must be a number."
            }), 400

        # Call payment service
        result = initiate_mpesa_payment(phone, amount, order_id)
        return jsonify(result)

    # ------------------- GET REQUEST -------------------
    # Render payment UI template
    return render_template("payments/pay_mpesa.html", mpesa_mode=current_app.config.get("MPESA_MODE", "mock_live"))
