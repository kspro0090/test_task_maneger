from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from . import bp
from ..models import Project, ProjectMember, User, Task, StatusConfig
from ..forms import ProjectForm, ProjectMemberForm, StatusConfigForm
from ..utils import admin_required, project_member_required, is_ajax_request, ajax_response, log_activity, create_notification
from ..extensions import db
from sqlalchemy import desc, and_

@bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Project.query
    
    # For employees, only show projects they're members of
    if not current_user.is_admin():
        project_ids = db.session.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).subquery()
        query = query.filter(Project.id.in_(project_ids))
    
    if search:
        query = query.filter(
            (Project.name.contains(search)) |
            (Project.description.contains(search))
        )
    
    projects = query.filter_by(is_active=True).order_by(desc(Project.created_at)).paginate(
        page=page, per_page=12, error_out=False
    )
    
    return render_template('projects/index.html', projects=projects, search=search)

@bp.route('/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            is_active=form.is_active.data,
            created_by=current_user.id
        )
        
        db.session.add(project)
        db.session.flush()  # To get the project ID
        
        # Create default status configurations
        default_statuses = [
            {'name': 'ToDo', 'display_name': 'انجام نشده', 'order_index': 1, 'color': '#6B7280'},
            {'name': 'Doing', 'display_name': 'در حال انجام', 'order_index': 2, 'color': '#3B82F6'},
            {'name': 'Review', 'display_name': 'بررسی', 'order_index': 3, 'color': '#F59E0B'},
            {'name': 'Done', 'display_name': 'انجام شده', 'order_index': 4, 'color': '#10B981'}
        ]
        
        for status_data in default_statuses:
            status_config = StatusConfig(
                project_id=project.id,
                **status_data
            )
            db.session.add(status_config)
        
        # Add creator as project member
        member = ProjectMember(
            user_id=current_user.id,
            project_id=project.id,
            role_in_project='LEAD'
        )
        db.session.add(member)
        
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Project',
            entity_id=project.id,
            action='created',
            description=f'پروژه جدید "{project.name}" ایجاد شد'
        )
        
        flash(f'پروژه "{project.name}" با موفقیت ایجاد شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('projects.detail', project_id=project.id))
        
        return redirect(url_for('projects.detail', project_id=project.id))
    
    return render_template('projects/form.html', form=form, title='ایجاد پروژه جدید')

@bp.route('/<int:project_id>')
@login_required
def detail(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check access
    if not current_user.is_admin() and not project.is_member(current_user):
        flash('شما عضو این پروژه نیستید.', 'error')
        return redirect(url_for('projects.index'))
    
    # Get project statistics
    total_tasks = project.tasks.count()
    completed_tasks = project.tasks.filter_by(status='Done').count()
    
    # Get tasks by status
    status_counts = db.session.query(
        Task.status, db.func.count(Task.id)
    ).filter(Task.project_id == project.id).group_by(Task.status).all()
    
    # Get recent tasks
    recent_tasks = project.tasks.order_by(desc(Task.updated_at)).limit(10).all()
    
    # Get project members
    members = project.get_members()
    
    return render_template('projects/detail.html',
                         project=project,
                         total_tasks=total_tasks,
                         completed_tasks=completed_tasks,
                         status_counts=dict(status_counts),
                         recent_tasks=recent_tasks,
                         members=members)

@bp.route('/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.is_active = form.is_active.data
        
        db.session.commit()
        
        log_activity(
            actor_user_id=current_user.id,
            entity_type='Project',
            entity_id=project.id,
            action='updated',
            description=f'پروژه "{project.name}" ویرایش شد'
        )
        
        flash(f'پروژه "{project.name}" با موفقیت ویرایش شد.', 'success')
        
        if is_ajax_request():
            return ajax_response(redirect_url=url_for('projects.detail', project_id=project.id))
        
        return redirect(url_for('projects.detail', project_id=project.id))
    
    return render_template('projects/form.html', form=form, project=project, title='ویرایش پروژه')

@bp.route('/<int:project_id>/board')
@login_required
def board(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Check access
    if not current_user.is_admin() and not project.is_member(current_user):
        flash('شما عضو این پروژه نیستید.', 'error')
        return redirect(url_for('projects.index'))
    
    # Get status configurations
    status_configs = StatusConfig.query.filter_by(project_id=project.id).order_by(StatusConfig.order_index).all()
    
    # Get tasks grouped by status
    tasks_by_status = {}
    for status_config in status_configs:
        tasks = project.tasks.filter_by(status=status_config.name).order_by(Task.created_at.desc()).all()
        tasks_by_status[status_config.name] = {
            'config': status_config,
            'tasks': tasks
        }
    
    # Get project members for task assignment
    members = project.get_members()
    
    return render_template('projects/board.html',
                         project=project,
                         status_configs=status_configs,
                         tasks_by_status=tasks_by_status,
                         members=members)

@bp.route('/<int:project_id>/members')
@login_required
@admin_required
def members(project_id):
    project = Project.query.get_or_404(project_id)
    members = db.session.query(User, ProjectMember).join(
        ProjectMember, User.id == ProjectMember.user_id
    ).filter(ProjectMember.project_id == project.id).all()
    
    return render_template('projects/members.html', project=project, members=members)

@bp.route('/<int:project_id>/members/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_member(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectMemberForm(project=project)
    
    if form.validate_on_submit():
        # Check if user is already a member
        existing_member = ProjectMember.query.filter_by(
            user_id=form.user_id.data,
            project_id=project.id
        ).first()
        
        if existing_member:
            flash('این کاربر قبلاً عضو پروژه است.', 'error')
        else:
            member = ProjectMember(
                user_id=form.user_id.data,
                project_id=project.id,
                role_in_project=form.role_in_project.data
            )
            
            db.session.add(member)
            db.session.commit()
            
            user = User.query.get(form.user_id.data)
            
            # Create notification for the new member
            create_notification(
                user_id=user.id,
                notification_type='project_added',
                title='به پروژه جدیدی اضافه شدید',
                message=f'شما به پروژه "{project.name}" اضافه شدید.',
                payload={'project_id': project.id}
            )
            
            log_activity(
                actor_user_id=current_user.id,
                entity_type='Project',
                entity_id=project.id,
                action='member_added',
                description=f'{user.full_name} به پروژه "{project.name}" اضافه شد'
            )
            
            flash(f'{user.full_name} با موفقیت به پروژه اضافه شد.', 'success')
            
            if is_ajax_request():
                return ajax_response(redirect_url=url_for('projects.members', project_id=project.id))
            
            return redirect(url_for('projects.members', project_id=project.id))
    
    return render_template('projects/add_member.html', form=form, project=project)

@bp.route('/<int:project_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_member(project_id, user_id):
    project = Project.query.get_or_404(project_id)
    member = ProjectMember.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first_or_404()
    
    user = User.query.get(user_id)
    
    # Don't allow removing the project creator
    if user_id == project.created_by:
        flash('نمی‌توانید سازنده پروژه را حذف کنید.', 'error')
        return redirect(url_for('projects.members', project_id=project.id))
    
    db.session.delete(member)
    db.session.commit()
    
    # Create notification
    create_notification(
        user_id=user.id,
        notification_type='project_removed',
        title='از پروژه‌ای حذف شدید',
        message=f'شما از پروژه "{project.name}" حذف شدید.',
        payload={'project_id': project.id}
    )
    
    log_activity(
        actor_user_id=current_user.id,
        entity_type='Project',
        entity_id=project.id,
        action='member_removed',
        description=f'{user.full_name} از پروژه "{project.name}" حذف شد'
    )
    
    flash(f'{user.full_name} از پروژه حذف شد.', 'success')
    
    if is_ajax_request():
        return ajax_response(redirect_url=url_for('projects.members', project_id=project.id))
    
    return redirect(url_for('projects.members', project_id=project.id))

@bp.route('/<int:project_id>/status-config')
@login_required
@admin_required
def status_config(project_id):
    project = Project.query.get_or_404(project_id)
    status_configs = StatusConfig.query.filter_by(project_id=project.id).order_by(StatusConfig.order_index).all()
    
    return render_template('projects/status_config.html', project=project, status_configs=status_configs)