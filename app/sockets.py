from flask_socketio import emit, join_room, leave_room, disconnect
from flask_login import current_user
from .extensions import socketio, db
from .models import Project, ProjectMember

@socketio.on('connect')
def on_connect():
    if not current_user.is_authenticated:
        disconnect()
        return False
    
    print(f'User {current_user.username} connected')
    
    # Join user to their project rooms
    if current_user.is_admin():
        # Admin joins all active project rooms
        projects = Project.query.filter_by(is_active=True).all()
    else:
        # Regular users join only their project rooms
        project_ids = db.session.query(ProjectMember.project_id).filter(
            ProjectMember.user_id == current_user.id
        ).subquery()
        projects = Project.query.filter(
            Project.id.in_(project_ids),
            Project.is_active == True
        ).all()
    
    for project in projects:
        join_room(f'project_{project.id}')
        print(f'User {current_user.username} joined room project_{project.id}')
    
    # Join user's personal notification room
    join_room(f'user_{current_user.id}')
    
    emit('connected', {'message': 'اتصال برقرار شد'})

@socketio.on('disconnect')
def on_disconnect():
    if current_user.is_authenticated:
        print(f'User {current_user.username} disconnected')

@socketio.on('join_project')
def on_join_project(data):
    if not current_user.is_authenticated:
        return
    
    project_id = data.get('project_id')
    if not project_id:
        return
    
    project = Project.query.get(project_id)
    if not project:
        return
    
    # Check if user has access to this project
    if not current_user.is_admin() and not project.is_member(current_user):
        return
    
    join_room(f'project_{project_id}')
    emit('joined_project', {'project_id': project_id, 'project_name': project.name})
    print(f'User {current_user.username} joined project room {project_id}')

@socketio.on('leave_project')
def on_leave_project(data):
    if not current_user.is_authenticated:
        return
    
    project_id = data.get('project_id')
    if not project_id:
        return
    
    leave_room(f'project_{project_id}')
    emit('left_project', {'project_id': project_id})
    print(f'User {current_user.username} left project room {project_id}')

@socketio.on('task_status_update')
def on_task_status_update(data):
    """Handle real-time task status updates from drag & drop"""
    if not current_user.is_authenticated:
        return
    
    task_id = data.get('task_id')
    new_status = data.get('new_status')
    project_id = data.get('project_id')
    
    if not all([task_id, new_status, project_id]):
        emit('error', {'message': 'داده‌های ناقص'})
        return
    
    from .models import Task
    from .utils import log_activity, create_notification
    from datetime import datetime
    
    task = Task.query.get(task_id)
    if not task:
        emit('error', {'message': 'کار یافت نشد'})
        return
    
    # Check access
    if not current_user.is_admin() and not task.project.is_member(current_user):
        emit('error', {'message': 'دسترسی غیرمجاز'})
        return
    
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
        
        # Emit notification to assignee
        emit('new_notification', {
            'title': 'وضعیت کار تغییر کرد',
            'message': f'وضعیت کار "{task.title}" تغییر کرد',
            'type': 'task_status_changed'
        }, room=f'user_{task.assignee_id}')
    
    log_activity(
        actor_user_id=current_user.id,
        entity_type='Task',
        entity_id=task.id,
        action='status_changed',
        description=f'وضعیت کار "{task.title}" از "{old_status}" به "{new_status}" تغییر کرد'
    )
    
    # Broadcast to all project members
    emit('task_status_changed', {
        'task_id': task.id,
        'old_status': old_status,
        'new_status': new_status,
        'title': task.title,
        'assignee': task.assignee.full_name if task.assignee else None,
        'updated_by': current_user.full_name
    }, room=f'project_{project_id}')
    
    emit('status_update_success', {
        'task_id': task_id,
        'new_status': new_status,
        'message': 'وضعیت کار با موفقیت تغییر کرد'
    })

@socketio.on('ping')
def on_ping():
    """Handle ping for connection testing"""
    if current_user.is_authenticated:
        from datetime import datetime
        emit('pong', {'timestamp': str(datetime.utcnow())})

# Helper functions that work regardless of socketio availability
def emit_notification_to_user(user_id, notification_data):
    """Emit notification to a specific user"""
    socketio.emit('new_notification', notification_data, room=f'user_{user_id}')

def emit_task_update_to_project(project_id, update_data):
    """Emit task update to all project members"""
    socketio.emit('task_updated', update_data, room=f'project_{project_id}')

def emit_comment_to_project(project_id, comment_data):
    """Emit new comment to all project members"""
    socketio.emit('comment_added', comment_data, room=f'project_{project_id}')