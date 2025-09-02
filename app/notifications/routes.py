from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import bp
from ..models import Notification
from ..utils import is_ajax_request, ajax_response
from ..extensions import db
from sqlalchemy import desc

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    
    notifications = current_user.notifications.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Mark all notifications as read when viewing the page
    unread_notifications = current_user.notifications.filter_by(is_read=False).all()
    for notification in unread_notifications:
        notification.is_read = True
    
    if unread_notifications:
        db.session.commit()
    
    return render_template('notifications/index.html', notifications=notifications)

@bp.route('/unread-count')
@login_required
def unread_count():
    """Get unread notifications count for AJAX requests"""
    count = current_user.get_unread_notifications_count()
    return jsonify({'count': count})

@bp.route('/recent')
@login_required
def recent():
    """Get recent notifications for dropdown/popup"""
    notifications = current_user.notifications.order_by(desc(Notification.created_at)).limit(10).all()
    
    if is_ajax_request():
        return render_template('notifications/recent_partial.html', notifications=notifications)
    
    return jsonify({
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'payload': n.get_payload()
        } for n in notifications]
    })

@bp.route('/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_read(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    notification.is_read = True
    db.session.commit()
    
    if is_ajax_request():
        return ajax_response(message='اعلان به عنوان خوانده شده علامت‌گذاری شد')
    
    flash('اعلان به عنوان خوانده شده علامت‌گذاری شد.', 'success')
    return redirect(url_for('notifications.index'))

@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    current_user.notifications.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    
    if is_ajax_request():
        return ajax_response(message='همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند')
    
    flash('همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند.', 'success')
    return redirect(url_for('notifications.index'))

@bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    if is_ajax_request():
        return ajax_response(message='اعلان حذف شد')
    
    flash('اعلان حذف شد.', 'success')
    return redirect(url_for('notifications.index'))

@bp.route('/clear-all', methods=['POST'])
@login_required
def clear_all():
    current_user.notifications.delete()
    db.session.commit()
    
    if is_ajax_request():
        return ajax_response(message='همه اعلان‌ها حذف شدند')
    
    flash('همه اعلان‌ها حذف شدند.', 'success')
    return redirect(url_for('notifications.index'))