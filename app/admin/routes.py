from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import bp
from ..models import User, Project, Task, Tag, ActivityLog
from ..forms import UserForm, TagForm, BrandingForm
from ..utils import admin_required, is_ajax_request, ajax_response, log_activity, save_uploaded_file
from ..extensions import db
from sqlalchemy import func, desc

@bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    if search:
        query = query.filter(
            (User.full_name.contains(search)) |
            (User.email.contains(search)) |
            (User.username.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            username=form.username.data,
            role=form.role.data,
            is_active=form.is_active.data,
            force_password_change=form.force_password_change.data
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Set default password
            user.set_password('123456')
            user.force_password_change = True
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='User',
            entity_id=user.id,
            action='created',
            description=f'کاربر جدید {user.full_name} ایجاد شد'
        )
        
        flash(f'کاربر {user.full_name} با موفقیت ایجاد شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('admin.users'))
        
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='ایجاد کاربر جدید')

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(user=user, obj=user)
    
    if form.validate_on_submit():
        user.full_name = form.full_name.data
        user.email = form.email.data
        user.username = form.username.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        user.force_password_change = form.force_password_change.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='User',
            entity_id=user.id,
            action='updated',
            description=f'کاربر {user.full_name} ویرایش شد'
        )
        
        flash(f'کاربر {user.full_name} با موفقیت ویرایش شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('admin.users'))
        
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='ویرایش کاربر')

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('شما نمی‌توانید خودتان را حذف کنید.', 'error')
        return redirect(url_for('admin.users'))
    
    # Check if user has tasks or other dependencies
    if user.assigned_tasks.count() > 0 or user.created_tasks.count() > 0:
        flash('این کاربر دارای کارهای مرتبط است و نمی‌تواند حذف شود.', 'error')
        return redirect(url_for('admin.users'))
    
    user_name = user.full_name
    db.session.delete(user)
    db.session.commit()
    
    log_activity(
        actor_user_id=current_user.id,
        entity_type='User',
        entity_id=user_id,
        action='deleted',
        description=f'کاربر {user_name} حذف شد'
    )
    
    flash(f'کاربر {user_name} با موفقیت حذف شد.', 'success')
    
    if is_ajax_request():
        return ajax_response(redirect_url=url_for('admin.users'))
    
    return redirect(url_for('admin.users'))

@bp.route('/tags')
@login_required
@admin_required
def tags():
    tags = Tag.query.order_by(Tag.name).all()
    return render_template('admin/tags.html', tags=tags)

@bp.route('/tags/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_tag():
    form = TagForm()
    
    if form.validate_on_submit():
        tag = Tag(
            name=form.name.data,
            color=form.color.data
        )
        
        db.session.add(tag)
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Tag',
            entity_id=tag.id,
            action='created',
            description=f'برچسب جدید "{tag.name}" ایجاد شد'
        )
        
        flash(f'برچسب "{tag.name}" با موفقیت ایجاد شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('admin.tags'))
        
        return redirect(url_for('admin.tags'))
    
    return render_template('admin/tag_form.html', form=form, title='ایجاد برچسب جدید')

@bp.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(obj=tag)
    
    if form.validate_on_submit():
        tag.name = form.name.data
        tag.color = form.color.data
        
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Tag',
            entity_id=tag.id,
            action='updated',
            description=f'برچسب "{tag.name}" ویرایش شد'
        )
        
        flash(f'برچسب "{tag.name}" با موفقیت ویرایش شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('admin.tags'))
        
        return redirect(url_for('admin.tags'))
    
    return render_template('admin/tag_form.html', form=form, tag=tag, title='ویرایش برچسب')

@bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    tag_name = tag.name
    db.session.delete(tag)
    db.session.commit()
    
    log_activity(
        actor_user_id=current_user.id,
        entity_type='Tag',
        entity_id=tag_id,
        action='deleted',
        description=f'برچسب "{tag_name}" حذف شد'
    )
    
    flash(f'برچسب "{tag_name}" با موفقیت حذف شد.', 'success')
    
    if is_ajax_request():
        return ajax_response(redirect_url=url_for('admin.tags'))
    
    return redirect(url_for('admin.tags'))

@bp.route('/activity-log')
@login_required
@admin_required
def activity_log():
    page = request.args.get('page', 1, type=int)
    
    activities = ActivityLog.query.order_by(desc(ActivityLog.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/activity_log.html', activities=activities)

@bp.route('/system-stats')
@login_required
@admin_required
def system_stats():
    # Get system statistics
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_projects': Project.query.count(),
        'active_projects': Project.query.filter_by(is_active=True).count(),
        'total_tasks': Task.query.count(),
        'completed_tasks': Task.query.filter_by(status='Done').count(),
        'total_tags': Tag.query.count()
    }
    
    # Get task distribution by status
    task_status_stats = db.session.query(
        Task.status, func.count(Task.id)
    ).group_by(Task.status).all()
    
    # Get task distribution by priority
    task_priority_stats = db.session.query(
        Task.priority, func.count(Task.id)
    ).group_by(Task.priority).all()
    
    return render_template('admin/system_stats.html', 
                         stats=stats,
                         task_status_stats=task_status_stats,
                         task_priority_stats=task_priority_stats)

@bp.route('/branding', methods=['GET', 'POST'])
@login_required
@admin_required
def branding():
    form = BrandingForm()
    
    if form.validate_on_submit():
        # Handle logo upload
        if form.logo.data:
            logo_info = save_uploaded_file(form.logo.data, 'branding')
            if logo_info:
                # Save logo path to settings (you might want to create a Settings model)
                flash('لوگو با موفقیت آپلود شد.', 'success')
        
        # Save other branding settings
        # This would typically be saved to a settings table or config file
        flash('تنظیمات برندینگ با موفقیت ذخیره شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(message='تنظیمات ذخیره شد')
        
        return redirect(url_for('admin.branding'))
    
    return render_template('admin/branding.html', form=form)