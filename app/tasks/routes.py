from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from . import bp
from ..models import Task, Project, User, Tag, TaskComment, TaskAttachment, ProjectMember
from ..forms import TaskForm, TaskCommentForm, TaskAttachmentForm, TaskFilterForm
from ..utils import project_member_required, is_ajax_request, ajax_response, log_activity, create_notification, save_uploaded_file, process_mentions
from ..extensions import db, socketio
from sqlalchemy import desc, and_, or_
from datetime import datetime
import os

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    project_id = request.args.get('project_id', type=int)
    
    # Get filter form
    project = None
    if project_id:
        project = Project.query.get_or_404(project_id)
        # Check access
        if not current_user.is_admin() and not project.is_member(current_user):
            flash('شما عضو این پروژه نیستید.', 'error')
            return redirect(url_for('tasks.index'))
    
    form = TaskFilterForm(project=project)
    
    # Build query
    query = Task.query.join(Project)
    
    # For employees, only show tasks from projects they're members of
    if not current_user.is_admin():
        project_ids = db.session.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).subquery()
        query = query.filter(Task.project_id.in_(project_ids))
    
    # Apply filters
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    if form.validate():
        if form.search.data:
            search_term = form.search.data
            query = query.filter(
                or_(
                    Task.title.contains(search_term),
                    Task.description.contains(search_term)
                )
            )
        
        if form.status.data:
            query = query.filter(Task.status == form.status.data)
        
        if form.priority.data:
            query = query.filter(Task.priority == form.priority.data)
        
        if form.assignee_id.data:
            query = query.filter(Task.assignee_id == form.assignee_id.data)
        
        if form.tag.data:
            query = query.join(Task.tags).filter(Tag.name.contains(form.tag.data))
        
        if form.overdue_only.data:
            query = query.filter(
                and_(
                    Task.due_date < datetime.utcnow(),
                    Task.status != 'Done'
                )
            )
    
    tasks = query.order_by(desc(Task.updated_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get available projects for filter
    projects_query = Project.query.filter_by(is_active=True)
    if not current_user.is_admin():
        project_ids = db.session.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).subquery()
        projects_query = projects_query.filter(Project.id.in_(project_ids))
    
    projects = projects_query.all()
    
    return render_template('tasks/index.html',
                         tasks=tasks,
                         form=form,
                         projects=projects,
                         current_project=project)

@bp.route('/new')
@login_required
def create():
    project_id = request.args.get('project_id', type=int)
    if not project_id:
        flash('لطفاً پروژه‌ای را انتخاب کنید.', 'error')
        return redirect(url_for('projects.index'))
    
    project = Project.query.get_or_404(project_id)
    
    # Check access
    if not current_user.is_admin() and not project.is_member(current_user):
        flash('شما عضو این پروژه نیستید.', 'error')
        return redirect(url_for('projects.index'))
    
    form = TaskForm(project=project)
    
    if form.validate_on_submit():
        task = Task(
            project_id=project.id,
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            assignee_id=form.assignee_id.data if form.assignee_id.data else None,
            estimated_hours=form.estimated_hours.data,
            due_date=form.due_date.data,
            created_by=current_user.id
        )
        
        db.session.add(task)
        db.session.flush()  # To get the task ID
        
        # Handle tags
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name, color='#6B7280')
                    db.session.add(tag)
                task.tags.append(tag)
        
        db.session.commit()
        
        # Create notification for assignee
        if task.assignee_id and task.assignee_id != current_user.id:
            create_notification(
                user_id=task.assignee_id,
                notification_type='task_assigned',
                title='کار جدیدی به شما اختصاص یافت',
                message=f'کار "{task.title}" در پروژه "{project.name}" به شما اختصاص یافت.',
                payload={
                    'task_id': task.id,
                    'project_id': project.id
                }
            )
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Task',
            entity_id=task.id,
            action='created',
            description=f'کار جدید "{task.title}" در پروژه "{project.name}" ایجاد شد'
        )
        
        # Emit socket event for real-time updates
        socketio.emit('task_created', {
            'task_id': task.id,
            'project_id': project.id,
            'title': task.title,
            'status': task.status,
            'assignee': task.assignee.full_name if task.assignee else None
        }, room=f'project_{project.id}')
        
        flash(f'کار "{task.title}" با موفقیت ایجاد شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('tasks.detail', task_id=task.id))
        
        return redirect(url_for('tasks.detail', task_id=task.id))
    
    return render_template('tasks/form.html', form=form, project=project, title='ایجاد کار جدید')

@bp.route('/<int:task_id>')
@login_required
def detail(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        flash('شما عضو این پروژه نیستید.', 'error')
        return redirect(url_for('tasks.index'))
    
    # Get comments
    comments = task.comments.order_by(TaskComment.created_at.asc()).all()
    
    # Get attachments
    attachments = task.attachments.order_by(TaskAttachment.uploaded_at.desc()).all()
    
    # Forms
    comment_form = TaskCommentForm()
    attachment_form = TaskAttachmentForm()
    
    return render_template('tasks/detail.html',
                         task=task,
                         comments=comments,
                         attachments=attachments,
                         comment_form=comment_form,
                         attachment_form=attachment_form)

@bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        flash('شما عضو این پروژه نیستید.', 'error')
        return redirect(url_for('tasks.index'))
    
    form = TaskForm(project=task.project, obj=task)
    
    # Set current tags
    if task.tags:
        form.tags.data = ', '.join([tag.name for tag in task.tags])
    
    if form.validate_on_submit():
        old_status = task.status
        old_assignee_id = task.assignee_id
        
        task.title = form.title.data
        task.description = form.description.data
        task.status = form.status.data
        task.priority = form.priority.data
        task.assignee_id = form.assignee_id.data if form.assignee_id.data else None
        task.estimate_hours = form.estimate_hours.data
        task.due_date = form.due_date.data
        task.updated_at = datetime.utcnow()
        
        # Handle tags
        task.tags.clear()
        if form.tags.data:
            tag_names = [name.strip() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                task.tags.append(tag)
        
        db.session.commit()
        
        # Create notifications for status or assignee changes
        if old_status != task.status:
            # Notify assignee about status change
            if task.assignee_id and task.assignee_id != current_user.id:
                create_notification(
                    user_id=task.assignee_id,
                    notification_type='task_status_changed',
                    title='وضعیت کار تغییر کرد',
                    message=f'وضعیت کار "{task.title}" به "{task.get_status_display()}" تغییر کرد.',
                    payload={
                        'task_id': task.id,
                        'project_id': task.project_id,
                        'old_status': old_status,
                        'new_status': task.status
                    }
                )
        
        if old_assignee_id != task.assignee_id:
            # Notify new assignee
            if task.assignee_id and task.assignee_id != current_user.id:
                create_notification(
                    user_id=task.assignee_id,
                    notification_type='task_assigned',
                    title='کاری به شما اختصاص یافت',
                    message=f'کار "{task.title}" به شما اختصاص یافت.',
                    payload={
                        'task_id': task.id,
                        'project_id': task.project_id
                    }
                )
            
            # Notify old assignee
            if old_assignee_id and old_assignee_id != current_user.id:
                create_notification(
                    user_id=old_assignee_id,
                    notification_type='task_unassigned',
                    title='کاری از شما گرفته شد',
                    message=f'کار "{task.title}" دیگر به شما اختصاص ندارد.',
                    payload={
                        'task_id': task.id,
                        'project_id': task.project_id
                    }
                )
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Task',
            entity_id=task.id,
            action='updated',
            description=f'کار "{task.title}" ویرایش شد'
        )
        
        # Emit socket event for real-time updates
        socketio.emit('task_updated', {
            'task_id': task.id,
            'project_id': task.project_id,
            'title': task.title,
            'status': task.status,
            'assignee': task.assignee.full_name if task.assignee else None
        }, room=f'project_{task.project_id}')
        
        flash(f'کار "{task.title}" با موفقیت ویرایش شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('tasks.detail', task_id=task.id))
        
        return redirect(url_for('tasks.detail', task_id=task.id))
    
    return render_template('tasks/form.html', form=form, task=task, title='ویرایش کار')

@bp.route('/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_status(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        return ajax_response(status='error', message='دسترسی غیرمجاز')
    
    new_status = request.json.get('status')
    if not new_status:
        return ajax_response(status='error', message='وضعیت جدید مشخص نشده')
    
    old_status = task.status
    task.status = new_status
    task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    # Create notification for assignee
    if task.assignee_id and task.assignee_id != current_user.id:
        create_notification(
            user_id=task.assignee_id,
            notification_type='task_status_changed',
            title='وضعیت کار تغییر کرد',
            message=f'وضعیت کار "{task.title}" به "{task.get_status_display()}" تغییر کرد.',
            payload={
                'task_id': task.id,
                'project_id': task.project_id,
                'old_status': old_status,
                'new_status': new_status
            }
        )
    
    log_activity(
        actor_user_id=current_user.id,
        entity_type='Task',
        entity_id=task.id,
        action='status_changed',
        description=f'وضعیت کار "{task.title}" از "{old_status}" به "{new_status}" تغییر کرد'
    )
    
    # Emit socket event for real-time updates
    socketio.emit('task_status_changed', {
        'task_id': task.id,
        'project_id': task.project_id,
        'old_status': old_status,
        'new_status': new_status,
        'title': task.title
    }, room=f'project_{task.project_id}')
    
    return ajax_response(message='وضعیت کار با موفقیت تغییر کرد')

@bp.route('/<int:task_id>/comments', methods=['POST'])
@login_required
def add_comment(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        return ajax_response(status='error', message='دسترسی غیرمجاز')
    
    form = TaskCommentForm()
    
    if form.validate_on_submit():
        comment = TaskComment(
            task_id=task.id,
            body=form.body.data,
            created_by=current_user.id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Process mentions
        process_mentions(comment.body, task)
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='TaskComment',
            entity_id=comment.id,
            action='created',
            description=f'نظر جدیدی برای کار "{task.title}" اضافه شد'
        )
        
        # Emit socket event for real-time updates
        socketio.emit('comment_added', {
            'task_id': task.id,
            'project_id': task.project_id,
            'comment_id': comment.id,
            'author': current_user.full_name,
            'body': comment.body,
            'created_at': comment.created_at.isoformat()
        }, room=f'project_{task.project_id}')
        
        if is_ajax_request():
            return ajax_response(message='نظر با موفقیت اضافه شد')
        
        flash('نظر با موفقیت اضافه شد.', 'success')
    
    return redirect(url_for('tasks.detail', task_id=task.id))

@bp.route('/<int:task_id>/attachments', methods=['POST'])
@login_required
def add_attachment(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        return ajax_response(status='error', message='دسترسی غیرمجاز')
    
    form = TaskAttachmentForm()
    
    if form.validate_on_submit():
        file_info = save_uploaded_file(form.files.data, f'tasks/{task.id}')
        
        if file_info:
            attachment = TaskAttachment(
                task_id=task.id,
                filename=file_info['filename'],
                original_filename=file_info['original_filename'],
                path=file_info['path'],
                size=file_info['size'],
                mime_type=file_info['mime_type'],
                uploaded_by=current_user.id
            )
            
            db.session.add(attachment)
            db.session.commit()
            
            log_activity(
                actor_user_id=current_user.id,
                entity_type='TaskAttachment',
                entity_id=attachment.id,
                action='created',
                description=f'فایل "{attachment.original_filename}" به کار "{task.title}" اضافه شد'
            )
            
            if is_ajax_request():
                return ajax_response(message='فایل با موفقیت آپلود شد')
            
            flash('فایل با موفقیت آپلود شد.', 'success')
        else:
            if is_ajax_request():
                return ajax_response(status='error', message='خطا در آپلود فایل')
            
            flash('خطا در آپلود فایل.', 'error')
    
    return redirect(url_for('tasks.detail', task_id=task.id))