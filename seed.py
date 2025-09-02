#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed script for KSP Task Manager
This script creates demo data for testing and demonstration purposes.
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import (
    User, Project, ProjectMember, Task, TaskComment, TaskAttachment, 
    Tag, Notification, StatusConfig, ActivityLog
)
from app.utils import create_notification, log_activity

def create_demo_data():
    """Create demo data for the application"""
    
    print("🚀 شروع ایجاد داده‌های نمونه...")
    
    # Create admin user
    admin = User(
        full_name='مدیر سیستم',
        email='admin@ksp.com',
        username='admin',
        role='ADMIN',
        is_active=True,
        force_password_change=True
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    print("✅ کاربر مدیر ایجاد شد (admin/admin123)")
    
    # Create employee users with Persian names
    persian_names = [
        ('علی احمدی', 'ali.ahmadi@ksp.com', 'employee1'),
        ('فاطمه محمدی', 'fateme.mohammadi@ksp.com', 'employee2'),
        ('حسن رضایی', 'hasan.rezaei@ksp.com', 'employee3'),
        ('مریم کریمی', 'maryam.karimi@ksp.com', 'employee4'),
        ('محمد حسینی', 'mohammad.hosseini@ksp.com', 'employee5'),
        ('زهرا نوری', 'zahra.nouri@ksp.com', 'employee6'),
        ('رضا موسوی', 'reza.mousavi@ksp.com', 'employee7'),
        ('سارا جعفری', 'sara.jafari@ksp.com', 'employee8'),
        ('امیر صادقی', 'amir.sadeghi@ksp.com', 'employee9'),
        ('نرگس باقری', 'narges.bagheri@ksp.com', 'employee10')
    ]
    
    employees = []
    for full_name, email, username in persian_names:
        employee = User(
            full_name=full_name,
            email=email,
            username=username,
            role='EMPLOYEE',
            is_active=True
        )
        employee.set_password('123456')
        employees.append(employee)
        db.session.add(employee)
    
    print(f"✅ {len(employees)} کارمند ایجاد شد (رمز عبور: 123456)")
    
    # Commit users first to get IDs
    db.session.commit()
    
    # Create tags
    tag_data = [
        ('فوری', '#ef4444'),
        ('باگ', '#f97316'),
        ('ویژگی جدید', '#22c55e'),
        ('بهبود', '#3b82f6'),
        ('مستندات', '#8b5cf6'),
        ('تست', '#06b6d4'),
        ('طراحی', '#ec4899'),
        ('بازبینی کد', '#84cc16')
    ]
    
    tags = []
    for name, color in tag_data:
        tag = Tag(name=name, color=color)
        tags.append(tag)
        db.session.add(tag)
    
    print(f"✅ {len(tags)} برچسب ایجاد شد")
    
    # Create projects
    project_data = [
        {
            'name': 'سیستم مدیریت فروش',
            'description': 'توسعه سیستم جامع مدیریت فروش و مشتریان شرکت'
        },
        {
            'name': 'اپلیکیشن موبایل',
            'description': 'طراحی و توسعه اپلیکیشن موبایل برای مشتریان'
        }
    ]
    
    projects = []
    for i, proj_data in enumerate(project_data):
        project = Project(
            name=proj_data['name'],
            description=proj_data['description'],
            is_active=True,
            created_by=admin.id
        )
        projects.append(project)
        db.session.add(project)
        
        # Flush to get project ID
        db.session.flush()
        
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
        
        # Add admin as project lead
        admin_member = ProjectMember(
            user_id=admin.id,
            project_id=project.id,
            role_in_project='LEAD'
        )
        db.session.add(admin_member)
        
        # Add random employees as project members
        project_employees = random.sample(employees, random.randint(4, 7))
        for employee in project_employees:
            member = ProjectMember(
                user_id=employee.id,
                project_id=project.id,
                role_in_project='MEMBER'
            )
            db.session.add(member)
    
    print(f"✅ {len(projects)} پروژه ایجاد شد")
    
    # Commit to get all IDs
    db.session.commit()
    
    # Create tasks
    task_titles = [
        'طراحی رابط کاربری صفحه اصلی',
        'پیاده‌سازی سیستم احراز هویت',
        'ایجاد پایگاه داده مشتریان',
        'تست عملکرد سیستم',
        'نوشتن مستندات API',
        'بهینه‌سازی کوئری‌های پایگاه داده',
        'اضافه کردن قابلیت جستجو',
        'رفع باگ در سیستم پرداخت',
        'طراحی لوگو و هویت بصری',
        'پیاده‌سازی سیستم گزارش‌گیری',
        'ایجاد پنل مدیریت',
        'تست امنیت سیستم',
        'بهبود تجربه کاربری',
        'اضافه کردن قابلیت چت',
        'پیاده‌سازی نوتیفیکیشن',
        'بهینه‌سازی سرعت بارگذاری',
        'ایجاد سیستم بکاپ',
        'طراحی صفحه پروفایل کاربر',
        'پیاده‌سازی سیستم امتیازدهی',
        'تست سازگاری با مرورگرها',
        'ایجاد راهنمای کاربری',
        'بهبود سیستم جستجو',
        'اضافه کردن قابلیت فیلتر',
        'رفع مشکلات موبایل',
        'پیاده‌سازی سیستم کش',
        'بهینه‌سازی تصاویر',
        'ایجاد سیستم لاگ',
        'طراحی صفحه خطا 404',
        'پیاده‌سازی سیستم کامنت',
        'تست بار سیستم',
        'ایجاد سیستم تگ',
        'بهبود سیستم آپلود فایل',
        'اضافه کردن قابلیت اکسپورت',
        'رفع باگ در سیستم ایمیل',
        'پیاده‌سازی سیستم تقویم',
        'بهینه‌سازی کد CSS',
        'ایجاد سیستم آمار',
        'طراحی صفحه تماس با ما',
        'پیاده‌سازی سیستم رای‌گیری',
        'تست قابلیت دسترسی',
        'ایجاد سیستم پشتیبان‌گیری خودکار',
        'بهبود سیستم ورود',
        'اضافه کردن قابلیت چندزبانه',
        'رفع مشکلات عملکرد',
        'پیاده‌سازی سیستم پیش‌نمایش',
        'بهینه‌سازی پایگاه داده',
        'ایجاد سیستم مانیتورینگ',
        'طراحی ایمیل‌های سیستم',
        'پیاده‌سازی سیستم محدودیت دسترسی',
        'تست امنیت API'
    ]
    
    task_descriptions = [
        'این کار نیاز به بررسی دقیق و طراحی مناسب دارد.',
        'باید با استانداردهای امنیتی مطابقت داشته باشد.',
        'نیاز به هماهنگی با تیم طراحی دارد.',
        'این کار اولویت بالایی دارد و باید سریع انجام شود.',
        'لطفاً قبل از شروع با مدیر پروژه هماهنگ کنید.',
        'این کار نیاز به تست کامل دارد.',
        'باید مستندات مربوطه نیز تهیه شود.',
        'نیاز به بررسی کدهای موجود دارد.',
        'این کار باید با سایر بخش‌ها هماهنگ باشد.',
        'لطفاً از بهترین روش‌ها استفاده کنید.'
    ]
    
    statuses = ['ToDo', 'Doing', 'Review', 'Done']
    priorities = ['Low', 'Med', 'High']
    
    all_tasks = []
    
    for project in projects:
        # Get project members
        project_members = [m.user for m in project.members]
        
        # Create 20-30 tasks per project
        num_tasks = random.randint(20, 30)
        project_tasks = random.sample(task_titles, min(num_tasks, len(task_titles)))
        
        for i, title in enumerate(project_tasks):
            # Create task with random data
            task = Task(
                project_id=project.id,
                title=title,
                description=random.choice(task_descriptions),
                status=random.choice(statuses),
                priority=random.choice(priorities),
                assignee_id=random.choice(project_members).id if random.random() > 0.2 else None,
                estimated_hours=random.choice([None, 2, 4, 8, 16, 24]),
                due_date=datetime.utcnow() + timedelta(days=random.randint(-10, 30)) if random.random() > 0.3 else None,
                created_by=random.choice(project_members).id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 60)),
                updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 10))
            )
            
            all_tasks.append(task)
            db.session.add(task)
            
            # Flush to get task ID
            db.session.flush()
            
            # Add random tags to task
            if random.random() > 0.4:
                task_tags = random.sample(tags, random.randint(1, 3))
                for tag in task_tags:
                    task.tags.append(tag)
    
    print(f"✅ {len(all_tasks)} کار ایجاد شد")
    
    # Commit tasks
    db.session.commit()
    
    # Create comments for some tasks
    comment_texts = [
        'کار خوبی انجام دادید! 👍',
        'لطفاً این بخش را بررسی کنید.',
        'نیاز به تغییرات جزئی دارد.',
        'عالی! ادامه دهید.',
        'این قسمت مشکل دارد، لطفاً رفع کنید.',
        'با تیم طراحی هماهنگ کنید.',
        'تست شده و مشکلی ندارد.',
        'نیاز به بهینه‌سازی بیشتر دارد.',
        'مستندات را فراموش نکنید.',
        'زمان‌بندی را رعایت کنید لطفاً.'
    ]
    
    comments_created = 0
    for task in random.sample(all_tasks, min(len(all_tasks) // 2, 100)):
        # Get project members for this task
        project_members = [m.user for m in task.project.members]
        
        # Create 1-3 comments per selected task
        num_comments = random.randint(1, 3)
        for _ in range(num_comments):
            comment = TaskComment(
                task_id=task.id,
                body=random.choice(comment_texts),
                created_by=random.choice(project_members).id,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.session.add(comment)
            comments_created += 1
    
    print(f"✅ {comments_created} نظر ایجاد شد")
    
    # Create notifications for users
    notification_types = [
        ('task_assigned', 'کار جدیدی به شما اختصاص یافت'),
        ('task_status_changed', 'وضعیت کار تغییر کرد'),
        ('comment_mention', 'در نظری ذکر شدید'),
        ('project_added', 'به پروژه جدیدی اضافه شدید')
    ]
    
    notifications_created = 0
    for employee in employees[:5]:  # Create notifications for first 5 employees
        for _ in range(random.randint(2, 5)):
            notif_type, title = random.choice(notification_types)
            notification = Notification(
                user_id=employee.id,
                type=notif_type,
                title=title,
                message=f'این یک اعلان نمونه برای {employee.full_name} است.',
                is_read=random.choice([True, False]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 7))
            )
            db.session.add(notification)
            notifications_created += 1
    
    print(f"✅ {notifications_created} اعلان ایجاد شد")
    
    # Create activity logs
    activities_created = 0
    for _ in range(50):
        activity = ActivityLog(
            actor_user_id=random.choice([admin] + employees).id,
            entity_type=random.choice(['Task', 'Project', 'User']),
            entity_id=random.randint(1, 100),
            action=random.choice(['created', 'updated', 'deleted', 'assigned']),
            description=f'فعالیت نمونه شماره {activities_created + 1}',
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
        )
        db.session.add(activity)
        activities_created += 1
    
    print(f"✅ {activities_created} لاگ فعالیت ایجاد شد")
    
    # Final commit
    db.session.commit()
    
    print("\n🎉 داده‌های نمونه با موفقیت ایجاد شد!")
    print("\n📋 اطلاعات ورود:")
    print("   مدیر: admin / admin123")
    print("   کارمندان: employee1 تا employee10 / 123456")
    print("\n🚀 حالا می‌توانید سرور را اجرا کنید:")
    print("   python app.py")

def main():
    """Main function to run the seed script"""
    app = create_app()
    
    with app.app_context():
        # Create tables first
        db.create_all()
        
        # Check if data already exists
        try:
            user_count = User.query.count()
            if user_count > 0:
                response = input("⚠️  داده‌هایی در پایگاه داده وجود دارد. آیا می‌خواهید آن‌ها را حذف کنید؟ (y/N): ")
                if response.lower() in ['y', 'yes', 'بله']:
                    print("🗑️  در حال حذف داده‌های موجود...")
                    # Drop all tables and recreate
                    db.drop_all()
                    db.create_all()
                    print("✅ داده‌های قدیمی حذف شد")
                else:
                    print("❌ عملیات لغو شد")
                    return
        except Exception as e:
            print(f"Creating new database: {e}")
            db.create_all()
        
        # Create demo data
        create_demo_data()

if __name__ == '__main__':
    main()