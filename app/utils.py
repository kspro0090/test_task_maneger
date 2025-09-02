import os
import uuid
from datetime import datetime
from functools import wraps
from flask import current_app, flash, redirect, url_for, request, jsonify
from flask_login import current_user
from werkzeug.utils import secure_filename
from .models import User, Notification, ActivityLog
from .extensions import db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('شما اجازه دسترسی به این صفحه را ندارید.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def project_member_required(project):
    """Decorator to require project membership"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            if current_user.is_admin() or project.is_member(current_user):
                return f(*args, **kwargs)
            
            flash('شما عضو این پروژه نیستید.', 'error')
            return redirect(url_for('main.dashboard'))
        return decorated_function
    return decorator

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'docx', 'xlsx', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file and return file info"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return {
            'filename': unique_filename,
            'original_filename': original_filename,
            'path': file_path,
            'size': file_size,
            'mime_type': file.mimetype or 'application/octet-stream'
        }
    return None

def create_notification(user_id, notification_type, title, message, payload=None):
    """Create a new notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message
    )
    if payload:
        notification.set_payload(payload)
    
    db.session.add(notification)
    db.session.commit()
    return notification

def log_activity(actor_user_id, entity_type, entity_id, action, description, meta=None):
    """Log user activity"""
    activity = ActivityLog(
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description
    )
    if meta:
        activity.set_meta(meta)
    
    db.session.add(activity)
    db.session.commit()
    return activity

def send_email(to_email, subject, body, html_body=None):
    """Send email notification (if SMTP is configured)"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        smtp_use_tls = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
        
        if not all([smtp_server, smtp_username, smtp_password]):
            # SMTP not configured, skip silently
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = to_email
        
        # Add text part
        text_part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        if smtp_use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send email: {str(e)}')
        return False

def process_mentions(comment_body, task):
    """Process @mentions in comments and create notifications"""
    import re
    mentions = re.findall(r'@(\w+)', comment_body)
    
    for username in mentions:
        user = User.query.filter_by(username=username).first()
        if user and user.id != current_user.id:
            # Check if user is a member of the task's project
            if task.project.is_member(user) or user.is_admin():
                create_notification(
                    user_id=user.id,
                    notification_type='comment_mention',
                    title='شما در نظری ذکر شدید',
                    message=f'{current_user.full_name} شما را در نظری برای کار "{task.title}" ذکر کرد.',
                    payload={
                        'task_id': task.id,
                        'project_id': task.project_id,
                        'comment_author': current_user.full_name
                    }
                )

def get_persian_date(date_obj):
    """Convert datetime to Persian date string"""
    if not date_obj:
        return ''
    
    # Simple Persian month names
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]
    
    # For simplicity, we'll use Gregorian calendar with Persian month names
    # In a real application, you might want to use a proper Persian calendar library
    month_name = persian_months[date_obj.month - 1] if date_obj.month <= 12 else str(date_obj.month)
    return f'{date_obj.day} {month_name} {date_obj.year}'

def get_task_stats(project=None, user=None):
    """Get task statistics for dashboard"""
    from app.models import Task
    from sqlalchemy import and_, func
    from datetime import datetime, timedelta
    
    query = Task.query
    
    if project:
        query = query.filter(Task.project_id == project.id)
    
    if user and not user.is_admin():
        # For employees, only show tasks from projects they're members of
        from app.models import ProjectMember
        project_ids = db.session.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == user.id
        ).subquery()
        query = query.filter(Task.project_id.in_(project_ids))
    
    total_tasks = query.count()
    
    # Tasks by status
    status_counts = db.session.query(
        Task.status, func.count(Task.id)
    ).filter(
        query.whereclause if query.whereclause is not None else True
    ).group_by(Task.status).all()
    
    # Recent completed tasks (last 7 and 30 days)
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    completed_last_week = query.filter(
        and_(Task.status == 'Done', Task.updated_at >= week_ago)
    ).count()
    
    completed_last_month = query.filter(
        and_(Task.status == 'Done', Task.updated_at >= month_ago)
    ).count()
    
    # Overdue tasks
    overdue_tasks = query.filter(
        and_(
            Task.due_date < now,
            Task.status != 'Done'
        )
    ).count()
    
    return {
        'total_tasks': total_tasks,
        'status_counts': dict(status_counts),
        'completed_last_week': completed_last_week,
        'completed_last_month': completed_last_month,
        'overdue_tasks': overdue_tasks
    }

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def is_ajax_request():
    """Check if request is AJAX/HTMX"""
    return request.headers.get('HX-Request') or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def ajax_response(data=None, status='success', message='', redirect_url=None):
    """Standard AJAX response format"""
    response = {
        'status': status,
        'message': message
    }
    
    if data:
        response['data'] = data
    
    if redirect_url:
        response['redirect'] = redirect_url
    
    return jsonify(response)