from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import bp
from ..models import User
from ..forms import LoginForm, ChangePasswordForm
from ..utils import is_ajax_request, ajax_response
from ..extensions import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Try to find user by username or email
        user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            
            # Check if user needs to change password
            if user.force_password_change:
                flash('لطفاً رمز عبور خود را تغییر دهید.', 'warning')
                return redirect(url_for('auth.change_password'))
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            
            flash(f'خوش آمدید، {user.full_name}!', 'success')
            return redirect(next_page)
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'error')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('شما با موفقیت خارج شدید.', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.force_password_change = False
            db.session.commit()
            
            flash('رمز عبور شما با موفقیت تغییر کرد.', 'success')
            
            if is_ajax_request():
                return ajax_response(redirect_url=url_for('main.dashboard'))
            
            return redirect(url_for('main.dashboard'))
        else:
            flash('رمز عبور فعلی اشتباه است.', 'error')
    
    return render_template('auth/change_password.html', form=form)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            flash('رمز عبور شما با موفقیت تغییر کرد.', 'success')
            
            if is_ajax_request():
                return ajax_response(message='رمز عبور با موفقیت تغییر کرد')
        else:
            flash('رمز عبور فعلی اشتباه است.', 'error')
            if is_ajax_request():
                return ajax_response(status='error', message='رمز عبور فعلی اشتباه است')
    
    return render_template('auth/profile.html', form=form)