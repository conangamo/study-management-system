"""
Admin Dashboard Utilities
- Database backup functions
- Report generation
- System utilities
"""
import os
import json
import csv
import shutil
import zipfile
from datetime import datetime, timedelta
from io import StringIO
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db.models import Count, Avg
from django.utils import timezone

from core.models.user import UserProfile
from core.models.study import Course, Grade
from core.models.assignment import Assignment
from core.models.authentication import LoginHistory


def backup_database():
    """
    Create a database backup
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Database backup file
    db_backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.json')
    
    try:
        # Use Django's dumpdata command
        with open(db_backup_file, 'w') as f:
            call_command('dumpdata', stdout=f, indent=2)
        
        # Create a compressed backup
        zip_backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        with zipfile.ZipFile(zip_backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(db_backup_file, f'database_{timestamp}.json')
            
            # Add media files if they exist
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if media_root and os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, settings.BASE_DIR)
                        zipf.write(file_path, archive_path)
        
        # Clean up the temporary database file
        os.remove(db_backup_file)
        
        return zip_backup_file
        
    except Exception as e:
        # Clean up on error
        if os.path.exists(db_backup_file):
            os.remove(db_backup_file)
        raise e


def generate_user_report(format_type='csv', user_role=None, date_from=None, date_to=None):
    """
    Generate user report in specified format
    """
    # Build queryset
    queryset = User.objects.select_related('profile')
    
    if user_role:
        queryset = queryset.filter(profile__role=user_role)
    
    if date_from:
        queryset = queryset.filter(date_joined__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(date_joined__lte=date_to)
    
    # Generate report
    if format_type == 'csv':
        return generate_user_csv_report(queryset)
    elif format_type == 'json':
        return generate_user_json_report(queryset)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def generate_user_csv_report(queryset):
    """
    Generate CSV report for users
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = [
        'ID', 'Username', 'Email', 'First Name', 'Last Name',
        'Role', 'Student ID', 'Department', 'Phone', 'Is Active',
        'Date Joined', 'Last Login'
    ]
    writer.writerow(headers)
    
    # Write data
    for user in queryset:
        profile = getattr(user, 'profile', None)
        
        row = [
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            profile.role if profile else '',
            profile.student_id if profile else '',
            profile.get_department_display() if profile else '',
            profile.phone if profile else '',
            'Yes' if user.is_active else 'No',
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else ''
        ]
        writer.writerow(row)
    
    return output.getvalue()


def generate_user_json_report(queryset):
    """
    Generate JSON report for users
    """
    data = []
    
    for user in queryset:
        profile = getattr(user, 'profile', None)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
        
        if profile:
            user_data.update({
                'role': profile.role,
                'student_id': profile.student_id,
                'department': profile.department,
                'phone': profile.phone,
                'year_of_study': profile.year_of_study,
                'bio': profile.bio,
            })
        
        data.append(user_data)
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_system_statistics():
    """
    Generate comprehensive system statistics
    """
    stats = {}
    
    # User statistics
    stats['users'] = {
        'total': User.objects.count(),
        'active': User.objects.filter(is_active=True).count(),
        'inactive': User.objects.filter(is_active=False).count(),
        'by_role': dict(
            User.objects.filter(profile__isnull=False)
            .values('profile__role')
            .annotate(count=Count('id'))
            .values_list('profile__role', 'count')
        ),
        'recent_signups': User.objects.filter(
            date_joined__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }
    
    # Course statistics
    stats['courses'] = {
        'total': Course.objects.count(),
        'by_status': dict(
            Course.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        ),
        'by_semester': dict(
            Course.objects.values('semester')
            .annotate(count=Count('id'))
            .values_list('semester', 'count')
        ),
        'average_students_per_course': Course.objects.annotate(
            student_count=Count('students')
        ).aggregate(avg=Avg('student_count'))['avg'] or 0,
    }
    
    # Assignment statistics
    stats['assignments'] = {
        'total': Assignment.objects.count(),
        'by_status': dict(
            Assignment.objects.values('status')
            .annotate(count=Count('id'))
            .values_list('status', 'count')
        ),
        'by_type': dict(
            Assignment.objects.values('assignment_type')
            .annotate(count=Count('id'))
            .values_list('assignment_type', 'count')
        ),
    }
    
    # Grade statistics
    grades = Grade.objects.all()
    if grades.exists():
        stats['grades'] = {
            'total': grades.count(),
            'average': grades.aggregate(avg=Avg('score'))['avg'],
            'by_type': dict(
                grades.values('grade_type')
                .annotate(count=Count('id'))
                .values_list('grade_type', 'count')
            ),
            'distribution': get_grade_distribution(grades),
        }
    else:
        stats['grades'] = {
            'total': 0,
            'average': 0,
            'by_type': {},
            'distribution': {},
        }
    
    # Activity statistics
    stats['activity'] = {
        'total_logins': LoginHistory.objects.count(),
        'logins_today': LoginHistory.objects.filter(
            login_time__date=timezone.now().date()
        ).count(),
        'logins_this_week': LoginHistory.objects.filter(
            login_time__gte=timezone.now() - timedelta(days=7)
        ).count(),
        'unique_users_today': LoginHistory.objects.filter(
            login_time__date=timezone.now().date()
        ).values('user').distinct().count(),
    }
    
    return stats


def get_grade_distribution(grades_queryset):
    """
    Get grade distribution by ranges
    """
    distribution = {
        'A+ (9.0-10)': grades_queryset.filter(score__gte=9.0).count(),
        'A (8.0-8.9)': grades_queryset.filter(score__gte=8.0, score__lt=9.0).count(),
        'B+ (7.0-7.9)': grades_queryset.filter(score__gte=7.0, score__lt=8.0).count(),
        'B (6.0-6.9)': grades_queryset.filter(score__gte=6.0, score__lt=7.0).count(),
        'C+ (5.0-5.9)': grades_queryset.filter(score__gte=5.0, score__lt=6.0).count(),
        'C (4.0-4.9)': grades_queryset.filter(score__gte=4.0, score__lt=5.0).count(),
        'D+ (3.0-3.9)': grades_queryset.filter(score__gte=3.0, score__lt=4.0).count(),
        'D (2.0-2.9)': grades_queryset.filter(score__gte=2.0, score__lt=3.0).count(),
        'F (0-1.9)': grades_queryset.filter(score__lt=2.0).count(),
    }
    
    return distribution


def get_user_activity_data(days=30):
    """
    Get user activity data for the last N days
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    activity_data = []
    current_date = start_date
    
    while current_date <= end_date:
        # User registrations
        new_users = User.objects.filter(date_joined__date=current_date).count()
        
        # Logins
        logins = LoginHistory.objects.filter(login_time__date=current_date).count()
        
        # Unique active users
        unique_users = LoginHistory.objects.filter(
            login_time__date=current_date
        ).values('user').distinct().count()
        
        activity_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'new_users': new_users,
            'logins': logins,
            'unique_users': unique_users,
        })
        
        current_date += timedelta(days=1)
    
    return activity_data


def cleanup_old_backups(keep_days=30):
    """
    Clean up old backup files
    """
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    
    if not os.path.exists(backup_dir):
        return
    
    cutoff_date = datetime.now() - timedelta(days=keep_days)
    
    for filename in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, filename)
        
        if os.path.isfile(filepath):
            file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            if file_modified < cutoff_date:
                try:
                    os.remove(filepath)
                except OSError:
                    pass  # File might be in use or permission denied


def get_disk_usage():
    """
    Get disk usage information
    """
    try:
        total, used, free = shutil.disk_usage(settings.BASE_DIR)
        
        return {
            'total': total,
            'used': used,
            'free': free,
            'total_gb': round(total / (1024**3), 2),
            'used_gb': round(used / (1024**3), 2),
            'free_gb': round(free / (1024**3), 2),
            'used_percentage': round((used / total) * 100, 2),
        }
    except Exception:
        return {
            'total': 0,
            'used': 0,
            'free': 0,
            'total_gb': 0,
            'used_gb': 0,
            'free_gb': 0,
            'used_percentage': 0,
        }


def validate_csv_import_file(csv_file):
    """
    Validate CSV file for user import
    """
    errors = []
    
    # Check file extension
    if not csv_file.name.endswith('.csv'):
        errors.append('File phải có định dạng CSV.')
    
    # Check file size (5MB limit)
    if csv_file.size > 5 * 1024 * 1024:
        errors.append('File không được vượt quá 5MB.')
    
    # Check CSV structure
    try:
        csv_file.seek(0)
        content = csv_file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(content))
        
        # Required columns
        required_columns = ['username', 'email', 'first_name', 'last_name', 'role']
        
        if not all(col in csv_reader.fieldnames for col in required_columns):
            missing_cols = [col for col in required_columns if col not in csv_reader.fieldnames]
            errors.append(f'Thiếu các cột bắt buộc: {", ".join(missing_cols)}')
        
        # Check first few rows for basic validation
        row_count = 0
        for row in csv_reader:
            row_count += 1
            
            # Check for empty required fields
            for col in required_columns:
                if col in row and not row[col].strip():
                    errors.append(f'Dòng {row_count + 1}: Cột "{col}" không được để trống.')
            
            # Check email format
            if 'email' in row and row['email']:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, row['email']):
                    errors.append(f'Dòng {row_count + 1}: Email không hợp lệ.')
            
            # Check role
            if 'role' in row and row['role']:
                valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
                if row['role'] not in valid_roles:
                    errors.append(f'Dòng {row_count + 1}: Vai trò không hợp lệ. Chỉ chấp nhận: {", ".join(valid_roles)}')
            
            # Only check first 10 rows for performance
            if row_count >= 10:
                break
        
        # Reset file pointer
        csv_file.seek(0)
        
    except UnicodeDecodeError:
        errors.append('Không thể đọc file. Vui lòng đảm bảo file được lưu với encoding UTF-8.')
    except Exception as e:
        errors.append(f'Lỗi khi đọc file CSV: {str(e)}')
    
    return errors


def send_bulk_email(user_list, subject, message, from_email=None):
    """
    Send bulk email to users
    """
    from django.core.mail import send_mass_mail
    from django.conf import settings
    
    if not from_email:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    messages = []
    for user in user_list:
        if user.email:
            messages.append((
                subject,
                message,
                from_email,
                [user.email]
            ))
    
    try:
        send_mass_mail(messages, fail_silently=False)
        return len(messages)
    except Exception as e:
        raise Exception(f'Lỗi khi gửi email: {str(e)}')


def generate_activity_log_csv(days=30):
    """
    Generate activity log CSV for the last N days
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    activities = LoginHistory.objects.filter(
        login_time__gte=start_date
    ).select_related('user').order_by('-login_time')
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Date Time', 'User', 'Email', 'Role', 'IP Address', 'User Agent'
    ])
    
    # Data
    for activity in activities:
        profile = getattr(activity.user, 'profile', None)
        
        writer.writerow([
            activity.login_time.strftime('%Y-%m-%d %H:%M:%S'),
            activity.user.get_full_name() or activity.user.username,
            activity.user.email,
            profile.get_role_display() if profile else 'N/A',
            activity.ip_address or 'N/A',
            activity.user_agent or 'N/A'
        ])
    
    return output.getvalue() 