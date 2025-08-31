"""
Django management command for database operations
Usage: python manage.py manage_database --help
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import transaction
import io
import sys
from core.models import *
from django.utils import timezone

class Command(BaseCommand):
    help = 'Comprehensive database management operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Reset entire database (DANGEROUS)',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create database backup',
        )
        parser.add_argument(
            '--init-sample-data',
            action='store_true',
            help='Initialize with sample data for development',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show database statistics',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up orphaned data',
        )
    
    def handle(self, *args, **options):
        if options['reset_all']:
            self.reset_database()
        elif options['backup']:
            self.backup_database()
        elif options['init_sample_data']:
            self.init_sample_data()
        elif options['stats']:
            self.show_statistics()
        elif options['cleanup']:
            self.cleanup_database()
        else:
            self.stdout.write(
                self.style.WARNING('Please specify an operation. Use --help for options.')
            )
    
    def reset_database(self):
        """Reset entire database"""
        self.stdout.write(
            self.style.WARNING('⚠️  This will delete ALL data. Are you sure? (type "yes" to confirm)')
        )
        
        confirmation = input()
        if confirmation != 'yes':
            self.stdout.write('Operation cancelled.')
            return
        
        self.stdout.write('🗑️  Resetting database...')
        
        # Delete all data
        models_to_reset = [
            # Study data
            AssignmentSubmission, Grade, Assignment, CourseEnrollment, Course,
            Note, Tag,
            # Academic structure
            StudentClass, Curriculum, Major, Department, CourseCategory, AcademicYear,
            # User data
            UserProfile, UserRole,
            # Auth data  
            LoginHistory, PasswordReset, AccountLockout,
            # Other
            StudentAccountRequest,
        ]
        
        with transaction.atomic():
            for model in models_to_reset:
                count = model.objects.count()
                model.objects.all().delete()
                self.stdout.write(f'   🗑️  Deleted {count} {model._meta.verbose_name}(s)')
            
            # Delete users except superusers
            count = User.objects.filter(is_superuser=False).count()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f'   🗑️  Deleted {count} regular users')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Database reset completed!')
        )
    
    def backup_database(self):
        """Create database backup"""
        self.stdout.write('💾 Creating database backup...')
        
        # Create backup using dumpdata
        backup_file = f'backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(backup_file, 'w') as f:
            call_command('dumpdata', stdout=f, indent=2, exclude=['contenttypes', 'auth.permission'])
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Backup created: {backup_file}')
        )
    
    def init_sample_data(self):
        """Initialize database with sample data"""
        self.stdout.write('🚀 Initializing sample data...')
        
        try:
            # Call academic data population command
            call_command('populate_academic_data')
            
            # Create sample courses and users
            self.create_sample_courses()
            self.create_sample_users()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Sample data initialized!')
            )
            
        except Exception as e:
            raise CommandError(f'Error initializing sample data: {e}')
    
    def create_sample_courses(self):
        """Create sample courses"""
        self.stdout.write('📚 Creating sample courses...')
        
        current_year = AcademicYear.objects.get(is_current=True)
        cntt_dept = Department.objects.get(code='CNTT')
        gdc_category = CourseCategory.objects.get(code='GDC')
        
        # Create teacher
        teacher_user, created = User.objects.get_or_create(
            username='teacher1',
            defaults={
                'email': 'teacher1@university.edu.vn',
                'first_name': 'Nguyễn',
                'last_name': 'Văn Giáo'
            }
        )
        if created:
            teacher_user.set_password('teacher123')
            teacher_user.save()
        
        teacher_profile, created = UserProfile.objects.get_or_create(
            user=teacher_user,
            defaults={
                'role': 'teacher',
                'academic_department': cntt_dept,
                'is_verified': True
            }
        )
        
        # Create courses
        from datetime import date
        courses = [
            {
                'name': 'Toán cao cấp A1',
                'code': 'MATH101',
                'description': 'Giải tích hàm một biến',
                'credits': 4,
                'department': cntt_dept,
                'category': gdc_category,
                'academic_year': current_year,
                'semester': '1',
                'start_date': date(2024, 9, 1),
                'end_date': date(2025, 1, 15),
                'teacher': teacher_user,
                'max_students': 80,
                'status': 'active'
            }
        ]
        
        for course_data in courses:
            course, created = Course.objects.get_or_create(
                code=course_data['code'],
                defaults=course_data
            )
            if created:
                self.stdout.write(f'   ✅ Created course: {course.name}')
    
    def create_sample_users(self):
        """Create sample users"""
        self.stdout.write('👥 Creating sample users...')
        
        cntt_dept = Department.objects.get(code='CNTT')
        ite_major = Major.objects.get(code='ITE')
        current_year = AcademicYear.objects.get(is_current=True)
        ite_class = StudentClass.objects.get(name='ITE2024A')
        
        # Create students
        students = [
            {
                'username': 'student1',
                'email': 'student1@university.edu.vn',
                'first_name': 'Nguyễn',
                'last_name': 'Văn An',
                'student_id': 'ITE2024001'
            },
            {
                'username': 'student2',
                'email': 'student2@university.edu.vn',
                'first_name': 'Trần',
                'last_name': 'Thị Bình',
                'student_id': 'ITE2024002'
            }
        ]
        
        for student_data in students:
            user, created = User.objects.get_or_create(
                username=student_data['username'],
                defaults={
                    'email': student_data['email'],
                    'first_name': student_data['first_name'],
                    'last_name': student_data['last_name']
                }
            )
            if created:
                user.set_password('student123')
                user.save()
            
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'student',
                    'student_id': student_data['student_id'],
                    'academic_department': cntt_dept,
                    'major': ite_major,
                    'academic_year': current_year,
                    'student_class': ite_class,
                    'is_verified': True
                }
            )
            if created:
                self.stdout.write(f'   ✅ Created student: {student_data["student_id"]}')
    
    def show_statistics(self):
        """Show database statistics"""
        self.stdout.write('📊 Database Statistics:')
        self.stdout.write('=' * 50)
        
        # Users
        self.stdout.write('\n👥 Users:')
        self.stdout.write(f'   Total Users: {User.objects.count()}')
        self.stdout.write(f'   Students: {User.objects.filter(profile__role="student").count()}')
        self.stdout.write(f'   Teachers: {User.objects.filter(profile__role="teacher").count()}')
        self.stdout.write(f'   Admins: {User.objects.filter(profile__role="admin").count()}')
        
        # Academic Structure
        self.stdout.write('\n🏛️  Academic Structure:')
        self.stdout.write(f'   Academic Years: {AcademicYear.objects.count()}')
        self.stdout.write(f'   Departments: {Department.objects.count()}')
        self.stdout.write(f'   Majors: {Major.objects.count()}')
        self.stdout.write(f'   Student Classes: {StudentClass.objects.count()}')
        self.stdout.write(f'   Course Categories: {CourseCategory.objects.count()}')
        
        # Study Data
        self.stdout.write('\n📚 Study Data:')
        self.stdout.write(f'   Courses: {Course.objects.count()}')
        self.stdout.write(f'   Course Enrollments: {CourseEnrollment.objects.count()}')
        self.stdout.write(f'   Assignments: {Assignment.objects.count()}')
        self.stdout.write(f'   Assignment Submissions: {AssignmentSubmission.objects.count()}')
        self.stdout.write(f'   Grades: {Grade.objects.count()}')
        self.stdout.write(f'   Notes: {Note.objects.count()}')
        
        # Current semester info
        current_year = AcademicYear.objects.filter(is_current=True).first()
        if current_year:
            self.stdout.write(f'\n📅 Current Academic Year: {current_year.name}')
            active_courses = Course.objects.filter(academic_year=current_year, status='active')
            self.stdout.write(f'   Active Courses: {active_courses.count()}')
            
            for course in active_courses:
                enrollment_count = course.enrollments.filter(status='enrolled').count()
                self.stdout.write(f'     📖 {course.name}: {enrollment_count}/{course.max_students} students')
    
    def cleanup_database(self):
        """Clean up orphaned data"""
        self.stdout.write('🧹 Cleaning up database...')
        
        # Clean up orphaned enrollments
        orphaned_enrollments = CourseEnrollment.objects.filter(
            course__isnull=True
        ) | CourseEnrollment.objects.filter(
            student__isnull=True
        )
        count = orphaned_enrollments.count()
        orphaned_enrollments.delete()
        self.stdout.write(f'   🗑️  Cleaned {count} orphaned enrollments')
        
        # Clean up grades without students/courses
        orphaned_grades = Grade.objects.filter(
            student__isnull=True
        ) | Grade.objects.filter(
            course__isnull=True
        )
        count = orphaned_grades.count()
        orphaned_grades.delete()
        self.stdout.write(f'   🗑️  Cleaned {count} orphaned grades')
        
        # Clean up profiles without users
        orphaned_profiles = UserProfile.objects.filter(user__isnull=True)
        count = orphaned_profiles.count()
        orphaned_profiles.delete()
        self.stdout.write(f'   🗑️  Cleaned {count} orphaned profiles')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Database cleanup completed!')
        ) 