# سیستم مدیریت کار KSP

سیستم جامع مدیریت کار و پروژه با رابط کاربری فارسی و قابلیت‌های پیشرفته

## ویژگی‌ها

### 🔐 احراز هویت و مجوزها
- سیستم ورود با نام کاربری/ایمیل و رمز عبور
- دو نقش کاربری: مدیر (ADMIN) و کارمند (EMPLOYEE)
- کنترل دسترسی بر اساس نقش کاربری
- امکان تغییر اجباری رمز عبور

### 📊 مدیریت پروژه
- ایجاد و مدیریت پروژه‌ها
- اضافه کردن اعضا به پروژه‌ها
- تابلو کانبان با قابلیت کشیدن و رها کردن
- وضعیت‌های قابل تنظیم (انجام نشده، در حال انجام، بررسی، انجام شده)

### ✅ مدیریت کار
- ایجاد، ویرایش و حذف کارها
- تخصیص کار به کاربران
- اولویت‌بندی (کم، متوسط، بالا)
- تاریخ سررسید و تخمین ساعت
- برچسب‌گذاری کارها
- فیلتر و جستجوی پیشرفته

### 💬 تعامل و همکاری
- سیستم نظرات با قابلیت @mention
- آپلود فایل‌های ضمیمه
- اعلان‌های بلادرنگ
- بروزرسانی‌های زنده با Socket.IO

### 📈 گزارش‌گیری و آمار
- داشبورد با آمار کلی
- نمودارهای توزیع کارها
- خروجی Excel از کارها
- لاگ فعالیت‌های سیستم

### 🎨 رابط کاربری
- طراحی فارسی و راست‌چین (RTL)
- فونت Vazirmatn
- طراحی ریسپانسیو با Tailwind CSS
- تم‌بندی قابل تنظیم

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.12 یا بالاتر
- pip (مدیر بسته‌های Python)

### نصب سریع (بدون محیط مجازی)

1. **دانلود پروژه:**
```bash
# اگر Git دارید:
git clone <repository-url>
cd "task maneger"

# یا فایل ZIP را دانلود و استخراج کنید
```

2. **نصب وابستگی‌ها:**
```bash
pip install -r requirements.txt
```

3. **ایجاد داده‌های نمونه:**
```bash
python seed.py
```

4. **اجرای سرور:**
```bash
python app.py
```

5. **دسترسی به سیستم:**
   - آدرس: http://localhost:5000
   - مدیر: `admin` / `admin123`
   - کارمند: `employee1` / `123456`

### نصب با محیط مجازی (توصیه شده)

1. **ایجاد محیط مجازی:**
```bash
python -m venv venv
```

2. **فعال‌سازی محیط مجازی:**
```bash
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate
```

3. **نصب وابستگی‌ها:**
```bash
pip install -r requirements.txt
```

4. **ایجاد داده‌های نمونه:**
```bash
python seed.py
```

5. **اجرای سرور:**
```bash
python app.py
```

## تنظیمات

### فایل .env
برای تنظیمات پیشرفته، فایل `.env` را ویرایش کنید:

```env
# تنظیمات Flask
SECRET_KEY=your-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# پایگاه داده
DATABASE_URL=sqlite:///instance/app.db

# آپلود فایل
UPLOAD_MAX_MB=20

# تنظیمات SMTP (اختیاری)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True

# تنظیمات برنامه
APP_NAME=KSP Task Manager
ORGANIZATION_NAME=سازمان شما
```

### تغییر لوگو و رنگ‌ها
1. وارد بخش "مدیریت" شوید
2. روی "تنظیمات برندینگ" کلیک کنید
3. لوگو و رنگ‌های دلخواه را انتخاب کنید

### فعال‌سازی ایمیل
برای فعال‌سازی اعلان‌های ایمیلی:
1. تنظیمات SMTP را در فایل `.env` وارد کنید
2. سرور را مجدداً راه‌اندازی کنید

## استقرار در سرور Linux

### با Gunicorn و Nginx

1. **نصب Gunicorn:**
```bash
pip install gunicorn eventlet
```

2. **اجرای برنامه:**
```bash
gunicorn -k eventlet -w 1 "app:create_app()" --bind 0.0.0.0:8000
```

3. **تنظیم Nginx:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ساختار پروژه

```
task maneger/
├── app/
│   ├── __init__.py
│   ├── models.py          # مدل‌های پایگاه داده
│   ├── forms.py           # فرم‌های WTForms
│   ├── utils.py           # توابع کمکی
│   ├── sockets.py         # رویدادهای Socket.IO
│   ├── auth/              # احراز هویت
│   ├── admin/             # پنل مدیریت
│   ├── main/              # صفحات اصلی
│   ├── projects/          # مدیریت پروژه
│   ├── tasks/             # مدیریت کار
│   └── notifications/     # اعلان‌ها
├── templates/             # قالب‌های HTML
├── static/               # فایل‌های استاتیک
├── uploads/              # فایل‌های آپلود شده
├── instance/             # پایگاه داده و تنظیمات
├── app.py                # فایل اصلی برنامه
├── seed.py               # ایجاد داده‌های نمونه
├── requirements.txt      # وابستگی‌ها
├── .env                  # تنظیمات محیط
└── README.md             # این فایل
```

## کاربران نمونه

پس از اجرای `seed.py`، کاربران زیر ایجاد می‌شوند:

### مدیر
- **نام کاربری:** admin
- **رمز عبور:** admin123
- **دسترسی:** کامل به همه بخش‌ها

### کارمندان
- **نام کاربری:** employee1 تا employee10
- **رمز عبور:** 123456
- **دسترسی:** فقط پروژه‌ها و کارهای مربوطه

## فایل‌های مجاز برای آپلود

- تصاویر: PNG, JPG, JPEG
- اسناد: PDF, DOCX, XLSX, TXT
- حداکثر حجم: 20 مگابایت (قابل تنظیم)

## محدودیت‌ها و نکات

### محدودیت‌های فعلی
- پایگاه داده SQLite (برای محیط تولید PostgreSQL توصیه می‌شود)
- عدم پشتیبانی از تقویم شمسی (فعلاً تاریخ میلادی)
- عدم پشتیبانی از چندین سازمان

### نکات امنیتی
- حتماً `SECRET_KEY` را در محیط تولید تغییر دهید
- از HTTPS استفاده کنید
- پوشه `uploads` را از دسترسی مستقیم محافظت کنید
- رمزهای عبور پیش‌فرض را تغییر دهید

### بهینه‌سازی عملکرد
- برای محیط تولید از Redis برای کش استفاده کنید
- پایگاه داده را به PostgreSQL مهاجرت دهید
- از CDN برای فایل‌های استاتیک استفاده کنید

## عیب‌یابی

### مشکلات رایج

**خطای "ModuleNotFoundError":**
```bash
pip install -r requirements.txt
```

**خطای پایگاه داده:**
```bash
# حذف پایگاه داده و ایجاد مجدد
rm -rf instance/
python seed.py
```

**مشکل در Socket.IO:**
- مطمئن شوید eventlet نصب است
- فایروال را بررسی کنید

**مشکل در آپلود فایل:**
- مجوزهای پوشه `uploads` را بررسی کنید
- حجم فایل را کنترل کنید

## مشارکت در توسعه

برای مشارکت در توسعه این پروژه:

1. پروژه را Fork کنید
2. شاخه جدیدی ایجاد کنید
3. تغییرات خود را اعمال کنید
4. Pull Request ارسال کنید

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## پشتیبانی

برای گزارش باگ یا درخواست ویژگی جدید، لطفاً Issue ایجاد کنید.

---

**نسخه:** 1.0.0  
**تاریخ:** ۱۴۰۳/۱۰/۲۷  
**توسعه‌دهنده:** تیم KSP"# test_task_maneger" 
