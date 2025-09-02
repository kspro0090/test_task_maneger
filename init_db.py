#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize database and create demo data
"""

import os
import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

def create_database():
    """Create database and tables"""
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'EMPLOYEE',
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            force_password_change BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Create projects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NOT NULL,
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
    ''')
    
    # Create tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'ToDo',
            priority VARCHAR(20) NOT NULL DEFAULT 'Med',
            project_id INTEGER NOT NULL,
            assignee_id INTEGER,
            created_by INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            due_date DATETIME,
            estimated_hours FLOAT,
            FOREIGN KEY (project_id) REFERENCES project (id),
            FOREIGN KEY (assignee_id) REFERENCES user (id),
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
    ''')
    
    # Create project_member table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_member (
            user_id INTEGER NOT NULL,
            project_id INTEGER NOT NULL,
            role_in_project VARCHAR(50) DEFAULT 'MEMBER',
            joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, project_id),
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (project_id) REFERENCES project (id)
        )
    ''')
    
    # Create status_config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name VARCHAR(50) NOT NULL,
            display_name VARCHAR(50) NOT NULL,
            order_index INTEGER NOT NULL,
            wip_limit INTEGER,
            color VARCHAR(7) DEFAULT '#6B7280',
            FOREIGN KEY (project_id) REFERENCES project (id)
        )
    ''')
    
    # Create task_attachment table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_attachment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            path VARCHAR(500) NOT NULL,
            size INTEGER NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            uploaded_by INTEGER NOT NULL,
            uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task (id),
            FOREIGN KEY (uploaded_by) REFERENCES user (id)
        )
    ''')
    
    # Create task_comment table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task (id),
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
    ''')
    
    # Create tag table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) UNIQUE NOT NULL,
            color VARCHAR(7) DEFAULT '#6B7280',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create task_tags association table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES task (id),
            FOREIGN KEY (tag_id) REFERENCES tag (id)
        )
    ''')
    
    # Create notification table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            payload_json TEXT,
            is_read BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')
    
    # Create activity_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor_user_id INTEGER NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            description VARCHAR(500) NOT NULL,
            meta_json TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (actor_user_id) REFERENCES user (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database tables created successfully!")

def create_demo_data():
    """Create demo data"""
    conn = sqlite3.connect('task_manager.db')
    cursor = conn.cursor()
    
    # Check if admin user already exists
    cursor.execute("SELECT COUNT(*) FROM user WHERE username = 'admin'")
    if cursor.fetchone()[0] > 0:
        print("Demo data already exists!")
        conn.close()
        return
    
    # Create admin user
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT INTO user (full_name, email, username, password_hash, role, force_password_change)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('مدیر سیستم', 'admin@ksp.com', 'admin', admin_password, 'ADMIN', 1))
    
    admin_id = cursor.lastrowid
    
    # Create employee users
    employee_names = [
        'علی احمدی', 'فاطمه محمدی', 'حسن رضایی', 'زهرا کریمی', 'محمد حسینی',
        'مریم نوری', 'رضا مرادی', 'سارا احمدی', 'امیر حسن‌زاده', 'نرگس صادقی'
    ]
    
    employee_password = generate_password_hash('123456')
    employee_ids = []
    
    for i, name in enumerate(employee_names, 1):
        cursor.execute('''
            INSERT INTO user (full_name, email, username, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, f'employee{i}@ksp.com', f'employee{i}', employee_password, 'EMPLOYEE'))
        employee_ids.append(cursor.lastrowid)
    
    # Create projects
    projects = [
        ('سیستم مدیریت محتوا', 'توسعه سیستم مدیریت محتوای جدید برای وب‌سایت شرکت'),
        ('اپلیکیشن موبایل', 'طراحی و توسعه اپلیکیشن موبایل برای مشتریان')
    ]
    
    project_ids = []
    for name, desc in projects:
        cursor.execute('''
            INSERT INTO project (name, description, created_by)
            VALUES (?, ?, ?)
        ''', (name, desc, admin_id))
        project_ids.append(cursor.lastrowid)
    
    # Create tasks
    task_titles = [
        'طراحی رابط کاربری', 'توسعه API', 'تست عملکرد', 'بهینه‌سازی پایگاه داده',
        'پیاده‌سازی احراز هویت', 'ایجاد داکیومنت', 'تست امنیتی', 'بررسی کیفیت کد',
        'تنظیم سرور', 'آموزش کاربران'
    ]
    
    statuses = ['ToDo', 'Doing', 'Review', 'Done']
    priorities = ['Low', 'Med', 'High']
    
    for i, title in enumerate(task_titles):
        project_id = random.choice(project_ids)
        assignee_id = random.choice(employee_ids)
        status = random.choice(statuses)
        priority = random.choice(priorities)
        
        cursor.execute('''
            INSERT INTO task (title, description, status, priority, project_id, assignee_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, f'توضیحات مربوط به {title}', status, priority, project_id, assignee_id, admin_id))
    
    # Create project members
    for project_id in project_ids:
        # Add admin to all projects
        cursor.execute('''
            INSERT OR IGNORE INTO project_member (user_id, project_id, role_in_project)
            VALUES (?, ?, ?)
        ''', (admin_id, project_id, 'LEAD'))
        
        # Add some employees to projects
        for i in range(3):
            employee_id = random.choice(employee_ids)
            cursor.execute('''
                INSERT OR IGNORE INTO project_member (user_id, project_id, role_in_project)
                VALUES (?, ?, ?)
            ''', (employee_id, project_id, 'MEMBER'))
    
    # Create status configs for projects
    for project_id in project_ids:
        status_configs = [
            ('ToDo', 'انجام نشده', 1, 5, '#6B7280'),
            ('Doing', 'در حال انجام', 2, 3, '#3B82F6'),
            ('Review', 'بررسی', 3, 2, '#F59E0B'),
            ('Done', 'انجام شده', 4, None, '#10B981')
        ]
        
        for name, display_name, order_index, wip_limit, color in status_configs:
            cursor.execute('''
                INSERT INTO status_config (project_id, name, display_name, order_index, wip_limit, color)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (project_id, name, display_name, order_index, wip_limit, color))
    
    # Create some tags
    tags = [
        ('بگ', '#EF4444'),
        ('ویژگی', '#10B981'),
        ('مستندات', '#3B82F6'),
        ('بهینه‌سازی', '#F59E0B'),
        ('امنیت', '#8B5CF6')
    ]
    
    for name, color in tags:
        cursor.execute('''
            INSERT OR IGNORE INTO tag (name, color)
            VALUES (?, ?)
        ''', (name, color))
    
    # Add tags to some tasks
    cursor.execute('SELECT id FROM task LIMIT 5')
    task_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id FROM tag LIMIT 3')
    tag_ids = [row[0] for row in cursor.fetchall()]
    
    for task_id in task_ids:
        for tag_id in random.sample(tag_ids, random.randint(1, 2)):
            cursor.execute('''
                INSERT OR IGNORE INTO task_tags (task_id, tag_id)
                VALUES (?, ?)
            ''', (task_id, tag_id))
    
    conn.commit()
    conn.close()
    
    print("✅ Demo data created successfully!")
    print("\n📋 Login Information:")
    print("   Admin: admin / admin123")
    print("   Employees: employee1-10 / 123456")
    print("\n🚀 You can now run the server:")
    print("   python app.py")

if __name__ == '__main__':
    print("Creating database...")
    create_database()
    print("Creating demo data...")
    create_demo_data()
    print("\nDatabase initialization complete!")