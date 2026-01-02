from flask import Blueprint, render_template, request, jsonify
from app.payments.mpesa_mock_and_production_mode import initiate_mpesa_payment

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/mpesa", methods=["GET", "POST"])
def pay_mpesa():
    if request.method == "POST":
        phone = request.form.get("phone")
        amount = float(request.form.get("amount"))
        order_id = request.form.get("order_id")

        result = initiate_mpesa_payment(phone, amount, order_id)
        return jsonify(result)

    return render_template("payments/pay_mpesa.html")

