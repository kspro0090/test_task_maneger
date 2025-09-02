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
            priority VARCHAR(20) NOT NULL DEFAULT 'Medium',
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
    priorities = ['Low', 'Medium', 'High']
    
    for i, title in enumerate(task_titles):
        project_id = random.choice(project_ids)
        assignee_id = random.choice(employee_ids)
        status = random.choice(statuses)
        priority = random.choice(priorities)
        
        cursor.execute('''
            INSERT INTO task (title, description, status, priority, project_id, assignee_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, f'توضیحات مربوط به {title}', status, priority, project_id, assignee_id, admin_id))
    
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