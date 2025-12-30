from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from app.auth.forms import LoginForm, UserForm
from app.models import User, CartItem
from app.auth import bp
from app import db

# ─── USER LOGIN ───────────────────────────────────────────────────────────────
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active_user:
            flash('Your account is deactivated. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        # ─── MERGE GUEST CART TO DB ───────────────────────────────────────────
        guest_cart = session.get('cart', [])
        if guest_cart and user.is_customer():
            for item in guest_cart:
                product_id = item.get('product_id')
                quantity = max(1, item.get('quantity', 1))

                existing = CartItem.query.filter_by(user_id=user.id, product_id=product_id).first()
                if existing:
                    existing.quantity += quantity
                else:
                    db.session.add(CartItem(user_id=user.id, product_id=product_id, quantity=quantity))

            db.session.commit()
            session.pop('cart', None)

        return redirect(request.args.get('next') or url_for('main.index'))

    return render_template('auth/login.html', form=form)

# ─── USER LOGOUT ──────────────────────────────────────────────────────────────
@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    logout_user()
    flash('You have been successfully logged out.', 'info')
    return redirect(url_for('main.home'))

# ─── MANAGE USERS (ADMIN ONLY) ────────────────────────────────────────────────
@bp.route('/auth/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if not current_user.is_admin():
        flash("Access denied", "danger")
        return redirect(url_for('main.index'))

    users = User.query.filter_by(is_deleted=False).all()
    form = UserForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_active_user=True,
            is_deleted=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} added successfully!', 'success')
        return redirect(url_for('auth.manage_users'))

    return render_template('auth/manage_users.html', users=users, form=form)

# ─── DELETE SINGLE USER (SOFT DELETE) ─────────────────────────────────────────
@bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin():
        flash('Unauthorized action', 'danger')
        return redirect(url_for('auth.manage_users'))

    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Cannot delete your own account.', 'warning')
        return redirect(url_for('auth.manage_users'))

    user.is_deleted = True
    db.session.commit()
    flash(f'User {user.username} archived (soft-deleted).', 'success')
    return redirect(url_for('auth.manage_users'))

# ─── BULK DELETE USERS (SOFT DELETE) ──────────────────────────────────────────
@bp.route('/bulk_delete_users', methods=['POST'])
@login_required
def bulk_delete_users():
    if not current_user.is_admin():
        flash('Unauthorized action', 'danger')
        return redirect(url_for('auth.manage_users'))

    ids = request.form.getlist('user_ids')
    count = 0
    for uid in ids:
        user = User.query.get(int(uid))
        if user and user != current_user:
            user.is_deleted = True
            count += 1

    db.session.commit()
    flash(f'{count} user(s) archived successfully.', 'success')
    return redirect(url_for('auth.manage_users'))

# ─── TOGGLE USER ACTIVE STATUS ────────────────────────────────────────────────
@bp.route('/toggle_active/<int:user_id>', methods=['POST'])
@login_required
def toggle_active(user_id):
    if not current_user.is_admin():
        flash('Unauthorized action', 'danger')
        return redirect(url_for('auth.manage_users'))

    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('Cannot change your own activation status.', 'warning')
        return redirect(url_for('auth.manage_users'))

    user.is_active_user = not user.is_active_user
    db.session.commit()
    status = 'activated' if user.is_active_user else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'info')
    return redirect(url_for('auth.manage_users'))

# ─── USER PROFILE PAGE (PLACEHOLDER) ──────────────────────────────────────────
@bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)

# ─── PASSWORD RESET (NOT IMPLEMENTED) ─────────────────────────────────────────
@bp.route('/password_reset_request', methods=['GET', 'POST'])
def password_reset_request():
    flash("Password reset is not implemented yet.", "info")
    return redirect(url_for('auth.login'))

# ─── USER REGISTRATION ────────────────────────────────────────────────────────
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created. Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)



