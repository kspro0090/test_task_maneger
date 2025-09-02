# KSP Task Manager Flask Application
from flask import Flask
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Ensure upload directory exists
    os.makedirs('uploads', exist_ok=True)
    
    # Configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///task_manager.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER='uploads',
        MAX_CONTENT_LENGTH=int(os.environ.get('UPLOAD_MAX_MB', 20)) * 1024 * 1024,
        WTF_CSRF_TIME_LIMIT=None
    )
    
    # Initialize extensions
    from .extensions import db, login_manager, csrf, socketio
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, async_mode='threading')
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'لطفاً برای دسترسی به این صفحه وارد شوید.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints AFTER init_app
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from .projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    from .tasks import bp as tasks_bp
    app.register_blueprint(tasks_bp, url_prefix='/tasks')
    
    from .notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    from .main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Register socket events
    from . import sockets
    
    # Database tables will be created separately
    
    return app