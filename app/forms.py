from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, FloatField, PasswordField, BooleanField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, EqualTo, ValidationError
from wtforms.widgets import TextArea
from .models import User, Project, Tag

class LoginForm(FlaskForm):
    username = StringField('نام کاربری یا ایمیل', validators=[DataRequired(message='نام کاربری یا ایمیل الزامی است')])
    password = PasswordField('رمز عبور', validators=[DataRequired(message='رمز عبور الزامی است')])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('رمز عبور فعلی', validators=[DataRequired(message='رمز عبور فعلی الزامی است')])
    new_password = PasswordField('رمز عبور جدید', validators=[
        DataRequired(message='رمز عبور جدید الزامی است'),
        Length(min=6, message='رمز عبور باید حداقل ۶ کاراکتر باشد')
    ])
    confirm_password = PasswordField('تکرار رمز عبور جدید', validators=[
        DataRequired(message='تکرار رمز عبور الزامی است'),
        EqualTo('new_password', message='رمزهای عبور مطابقت ندارند')
    ])
    submit = SubmitField('تغییر رمز عبور')

class UserForm(FlaskForm):
    full_name = StringField('نام کامل', validators=[DataRequired(message='نام کامل الزامی است'), Length(max=100)])
    email = StringField('ایمیل', validators=[DataRequired(message='ایمیل الزامی است'), Email(message='ایمیل معتبر نیست'), Length(max=120)])
    username = StringField('نام کاربری', validators=[DataRequired(message='نام کاربری الزامی است'), Length(min=3, max=80, message='نام کاربری باید بین ۳ تا ۸۰ کاراکتر باشد')])
    password = PasswordField('رمز عبور', validators=[
        Optional(),
        Length(min=6, message='رمز عبور باید حداقل ۶ کاراکتر باشد')
    ])
    role = SelectField('نقش', choices=[('EMPLOYEE', 'کارمند'), ('ADMIN', 'مدیر')], validators=[DataRequired()])
    is_active = BooleanField('فعال')
    force_password_change = BooleanField('اجبار تغییر رمز عبور در ورود بعدی')
    submit = SubmitField('ذخیره')
    
    def __init__(self, user=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.user = user
        if user:
            self.password.validators = [Optional()]
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and (not self.user or user.id != self.user.id):
            raise ValidationError('این ایمیل قبلاً استفاده شده است')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and (not self.user or user.id != self.user.id):
            raise ValidationError('این نام کاربری قبلاً استفاده شده است')

class ProjectForm(FlaskForm):
    name = StringField('نام پروژه', validators=[DataRequired(message='نام پروژه الزامی است'), Length(max=100)])
    description = TextAreaField('توضیحات', validators=[Optional()])
    is_active = BooleanField('فعال', default=True)
    submit = SubmitField('ذخیره')

class TaskForm(FlaskForm):
    title = StringField('عنوان', validators=[DataRequired(message='عنوان الزامی است'), Length(max=200)])
    description = TextAreaField('توضیحات', validators=[Optional()])
    status = SelectField('وضعیت', choices=[
        ('ToDo', 'انجام نشده'),
        ('Doing', 'در حال انجام'),
        ('Review', 'بررسی'),
        ('Done', 'انجام شده')
    ], validators=[DataRequired()])
    priority = SelectField('اولویت', choices=[
        ('Low', 'کم'),
        ('Med', 'متوسط'),
        ('High', 'بالا')
    ], validators=[DataRequired()])
    assignee_id = SelectField('مسئول', coerce=int, validators=[Optional()])
    estimated_hours = FloatField('تخمین ساعت', validators=[Optional(), NumberRange(min=0, message='ساعت نمی‌تواند منفی باشد')])
    due_date = DateTimeField('تاریخ سررسید', validators=[Optional()], format='%Y-%m-%dT%H:%M')
    tags = StringField('برچسب‌ها (با کاما جدا کنید)', validators=[Optional()])
    submit = SubmitField('ذخیره')
    
    def __init__(self, project=None, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        if project:
            # Get project members for assignee choices
            members = project.get_members()
            self.assignee_id.choices = [(0, 'انتخاب کنید')] + [(u.id, u.full_name) for u in members]
        else:
            self.assignee_id.choices = [(0, 'انتخاب کنید')]

class TaskCommentForm(FlaskForm):
    body = TextAreaField('نظر', validators=[DataRequired(message='متن نظر الزامی است')], widget=TextArea())
    submit = SubmitField('ارسال نظر')

class TaskAttachmentForm(FlaskForm):
    files = FileField('فایل‌ها', validators=[
        FileRequired(message='انتخاب فایل الزامی است'),
        FileAllowed(['png', 'jpg', 'jpeg', 'pdf', 'docx', 'xlsx', 'txt'], 
                   message='فقط فایل‌های png, jpg, jpeg, pdf, docx, xlsx, txt مجاز هستند')
    ])
    submit = SubmitField('آپلود')

class TagForm(FlaskForm):
    name = StringField('نام برچسب', validators=[DataRequired(message='نام برچسب الزامی است'), Length(max=50)])
    color = StringField('رنگ', validators=[DataRequired()], default='#6B7280')
    submit = SubmitField('ذخیره')
    
    def validate_name(self, name):
        tag = Tag.query.filter_by(name=name.data).first()
        if tag:
            raise ValidationError('این برچسب قبلاً وجود دارد')

class ProjectMemberForm(FlaskForm):
    user_id = SelectField('کاربر', coerce=int, validators=[DataRequired()])
    role_in_project = SelectField('نقش در پروژه', choices=[
        ('MEMBER', 'عضو'),
        ('LEAD', 'سرپرست')
    ], validators=[DataRequired()])
    submit = SubmitField('افزودن')
    
    def __init__(self, project=None, *args, **kwargs):
        super(ProjectMemberForm, self).__init__(*args, **kwargs)
        if project:
            # Get users who are not already members
            existing_member_ids = [m.user_id for m in project.members]
            available_users = User.query.filter(~User.id.in_(existing_member_ids), User.is_active == True).all()
            self.user_id.choices = [(u.id, f'{u.full_name} ({u.username})') for u in available_users]
        else:
            self.user_id.choices = []

class TaskFilterForm(FlaskForm):
    search = StringField('جستجو', validators=[Optional()])
    status = SelectField('وضعیت', choices=[('', 'همه')] + [
        ('ToDo', 'انجام نشده'),
        ('Doing', 'در حال انجام'),
        ('Review', 'بررسی'),
        ('Done', 'انجام شده')
    ], validators=[Optional()])
    priority = SelectField('اولویت', choices=[('', 'همه')] + [
        ('Low', 'کم'),
        ('Med', 'متوسط'),
        ('High', 'بالا')
    ], validators=[Optional()])
    assignee_id = SelectField('مسئول', coerce=int, validators=[Optional()])
    tag = StringField('برچسب', validators=[Optional()])
    overdue_only = BooleanField('فقط کارهای عقب‌افتاده')
    submit = SubmitField('فیلتر')
    
    def __init__(self, project=None, *args, **kwargs):
        super(TaskFilterForm, self).__init__(*args, **kwargs)
        if project:
            members = project.get_members()
            self.assignee_id.choices = [(0, 'همه')] + [(u.id, u.full_name) for u in members]
        else:
            self.assignee_id.choices = [(0, 'همه')]

class StatusConfigForm(FlaskForm):
    name = StringField('نام وضعیت (انگلیسی)', validators=[DataRequired(), Length(max=50)])
    display_name = StringField('نام نمایشی (فارسی)', validators=[DataRequired(), Length(max=50)])
    order_index = SelectField('ترتیب', coerce=int, validators=[DataRequired()])
    wip_limit = FloatField('محدودیت WIP', validators=[Optional(), NumberRange(min=1)])
    color = StringField('رنگ', validators=[DataRequired()], default='#6B7280')
    submit = SubmitField('ذخیره')

class BrandingForm(FlaskForm):
    organization_name = StringField('نام سازمان', validators=[Optional(), Length(max=100)])
    primary_color = StringField('رنگ اصلی', validators=[Optional()], default='#059669')
    secondary_color = StringField('رنگ فرعی', validators=[Optional()], default='#DC2626')
    accent_color = StringField('رنگ تاکیدی', validators=[Optional()], default='#1F2937')
    logo = FileField('لوگو', validators=[
        Optional(),
        FileAllowed(['png', 'jpg', 'jpeg', 'svg'], 'فقط فایل‌های تصویری مجاز هستند')
    ])
    submit = SubmitField('ذخیره تنظیمات')