from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

from .extensions import db

# Association table for many-to-many relationship between tasks and tags
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='EMPLOYEE')  # ADMIN or EMPLOYEE
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    force_password_change = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    created_projects = db.relationship('Project', backref='creator', lazy='dynamic', foreign_keys='Project.created_by')
    assigned_tasks = db.relationship('Task', backref='assignee', lazy='dynamic', foreign_keys='Task.assignee_id')
    created_tasks = db.relationship('Task', backref='creator', lazy='dynamic', foreign_keys='Task.created_by')
    comments = db.relationship('TaskComment', backref='author', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    uploaded_attachments = db.relationship('TaskAttachment', backref='uploader', lazy='dynamic')
    project_memberships = db.relationship('ProjectMember', backref='user', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='actor', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def get_unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    members = db.relationship('ProjectMember', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    status_configs = db.relationship('StatusConfig', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_members(self):
        return User.query.join(ProjectMember).filter(ProjectMember.project_id == self.id).all()
    
    def is_member(self, user):
        return ProjectMember.query.filter_by(user_id=user.id, project_id=self.id).first() is not None
    
    def __repr__(self):
        return f'<Project {self.name}>'

class ProjectMember(db.Model):
    __tablename__ = 'project_member'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), primary_key=True)
    role_in_project = db.Column(db.String(50), default='MEMBER')  # MEMBER, LEAD, etc.
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class StatusConfig(db.Model):
    __tablename__ = 'status_config'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # ToDo, Doing, Review, Done
    display_name = db.Column(db.String(50), nullable=False)  # Persian names
    order_index = db.Column(db.Integer, nullable=False)
    wip_limit = db.Column(db.Integer, nullable=True)  # Work In Progress limit
    color = db.Column(db.String(7), default='#6B7280')  # Hex color
    
    def __repr__(self):
        return f'<StatusConfig {self.name}>'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), nullable=False, default='ToDo')
    priority = db.Column(db.String(20), nullable=False, default='Med')  # Low, Med, High
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    estimated_hours = db.Column(db.Float, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    attachments = db.relationship('TaskAttachment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('TaskComment', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary=task_tags, lazy='subquery', backref=db.backref('tasks', lazy=True))
    
    def is_overdue(self):
        if self.due_date and self.status != 'Done':
            return datetime.utcnow() > self.due_date
        return False
    
    def get_priority_display(self):
        priority_map = {'Low': 'کم', 'Med': 'متوسط', 'High': 'بالا'}
        return priority_map.get(self.priority, self.priority)
    
    def get_status_display(self):
        status_map = {
            'ToDo': 'انجام نشده',
            'Doing': 'در حال انجام', 
            'Review': 'بررسی',
            'Done': 'انجام شده'
        }
        return status_map.get(self.status, self.status)
    
    def __repr__(self):
        return f'<Task {self.title}>'

class TaskAttachment(db.Model):
    __tablename__ = 'task_attachment'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    size = db.Column(db.Integer, nullable=False)  # Size in bytes
    mime_type = db.Column(db.String(100), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_size_display(self):
        """Return human readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} TB"
    
    def __repr__(self):
        return f'<TaskAttachment {self.filename}>'

class TaskComment(db.Model):
    __tablename__ = 'task_comment'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_mentions(self):
        """Extract @username mentions from comment body"""
        import re
        mentions = re.findall(r'@(\w+)', self.body)
        return mentions
    
    def __repr__(self):
        return f'<TaskComment {self.id}>'

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    color = db.Column(db.String(7), default='#6B7280')  # Hex color
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Tag {self.name}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # task_assigned, task_updated, comment_mention, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    payload_json = db.Column(db.Text)  # JSON data for additional info
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_payload(self):
        """Get payload as Python dict"""
        if self.payload_json:
            try:
                return json.loads(self.payload_json)
            except:
                return {}
        return {}
    
    def set_payload(self, data):
        """Set payload from Python dict"""
        self.payload_json = json.dumps(data) if data else None
    
    def __repr__(self):
        return f'<Notification {self.type}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_log'
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # Task, Project, User, etc.
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, deleted, etc.
    description = db.Column(db.String(500), nullable=False)
    meta_json = db.Column(db.Text)  # JSON data for additional metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def get_meta(self):
        """Get meta as Python dict"""
        if self.meta_json:
            try:
                return json.loads(self.meta_json)
            except:
                return {}
        return {}
    
    def set_meta(self, data):
        """Set meta from Python dict"""
        self.meta_json = json.dumps(data) if data else None
    
    def __repr__(self):
        return f'<ActivityLog {self.action} {self.entity_type}>'