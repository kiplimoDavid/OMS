# ───────────────────────────────────────────────
# Contact Support (Modal Submission)
# ──────────────────────────────────────────────
from flask import Blueprint, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import Order, db

bp = Blueprint('support', __name__)  # 👈 ADD THIS


@bp.route('/<int:order_id>/contact-support', methods=['POST'], endpoint='contact_support')
@login_required
def contact_support(order_id):
    o = Order.query.get_or_404(order_id)
    if not current_user.is_customer() or o.customer.user_id != current_user.id:
        abort(403)

    message = request.form.get('message', '').strip()
    if not message:
        flash("Message cannot be empty.", "toast-danger")
        return redirect(url_for('orders.view_order', order_id=o.id))

    # Assume SupportTicket model exists
    from app.models import SupportTicket
    ticket = SupportTicket(order_id=o.id, user_id=current_user.id, message=message, status='OPEN')
    db.session.add(ticket)
    db.session.commit()
    flash("Support request sent.", "toast-success")
    return redirect(url_for('orders.view_order', order_id=order_id))