#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create database tables
"""

import os
from app import create_app
from app.extensions import db

if __name__ == '__main__':
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Create app using factory
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        print(f"Database file: {os.path.abspath('task_manager.db')}")