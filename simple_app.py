#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Flask app for testing and seeding
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('UPLOAD_MAX_MB', 20)) * 1024 * 1024
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    
    # Ensure upload directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    from app.tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)