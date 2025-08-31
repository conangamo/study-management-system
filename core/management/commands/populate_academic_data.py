"""
Django management command to populate academic structure data
Usage: python manage.py populate_academic_data
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from datetime import date
from core.models import (
    AcademicYear, Department, Major, CourseCategory, 
    StudentClass, Curriculum, UserProfile
)

class Command(BaseCommand):
    help = 'Populate academic structure data (years, departments, majors, etc.)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing data before creating new data',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting academic data population...')
        )
        
        if options['reset']:
            self.stdout.write('🗑️  Resetting existing data...')
            self.reset_data()
        
        try:
            self.create_academic_years()
            self.create_departments()
            self.create_majors()
            self.create_course_categories()
            self.create_student_classes()
            self.create_curriculums()
            self.create_admin_user()
            
            self.show_statistics()
            
            self.stdout.write(
                self.style.SUCCESS('🎉 Academic data populated successfully!')
            )
            
        except Exception as e:
            raise CommandError(f'Error: {e}')
    
    def reset_data(self):
        """Delete existing academic data"""
        models_to_reset = [
            StudentClass, Curriculum, Major, Department, 
            CourseCategory, AcademicYear
        ]
        
        for model in models_to_reset:
            count = model.objects.count()
            model.objects.all().delete()
            self.stdout.write(f'   🗑️  Deleted {count} {model._meta.verbose_name}(s)')
    
    def create_academic_years(self):
        """Create academic years"""
        self.stdout.write('📅 Creating academic years...')
        
        years = [
            ('2023-2024', date(2023, 9, 1), date(2024, 7, 31), False),
            ('2024-2025', date(2024, 9, 1), date(2025, 7, 31), True),  # Current
            ('2025-2026', date(2025, 9, 1), date(2026, 7, 31), False),
        ]
        
        for name, start_date, end_date, is_current in years:
            year, created = AcademicYear.objects.get_or_create(
                name=name,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_current': is_current
                }
            )
            if created:
                self.stdout.write(f'   ✅ Created: {name}')
    
    def create_departments(self):
        """Create departments"""
        self.stdout.write('🏢 Creating departments...')
        
        departments = [
            {
                'name': 'Khoa Công nghệ thông tin',
                'code': 'CNTT',
                'description': 'Đào tạo nguồn nhân lực công nghệ thông tin chất lượng cao',
                'phone': '024-38521212',
                'email': 'cntt@university.edu.vn',
                'address': 'Tầng 5, Tòa nhà chính'
            },
            {
                'name': 'Khoa Kinh tế', 
                'code': 'KT',
                'description': 'Đào tạo cử nhân, thạc sĩ kinh tế và quản trị kinh doanh',
                'phone': '024-38521213',
                'email': 'kt@university.edu.vn',
                'address': 'Tầng 3, Tòa nhà B'
            },
            {
                'name': 'Khoa Ngoại ngữ',
                'code': 'NN', 
                'description': 'Đào tạo ngôn ngữ Anh, Trung, Nhật, Hàn chuyên nghiệp',
                'phone': '024-38521214',
                'email': 'nn@university.edu.vn',
                'address': 'Tầng 2, Tòa nhà C'
            },
        ]
        
        for dept_data in departments:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults=dept_data
            )
            if created:
                self.stdout.write(f'   ✅ Created: {dept.name}')
    
    def create_majors(self):
        """Create majors"""
        self.stdout.write('🎓 Creating majors...')
        
        cntt = Department.objects.get(code='CNTT')
        kt = Department.objects.get(code='KT')
        
        majors = [
            {
                'name': 'Công nghệ thông tin',
                'code': 'ITE',
                'department': cntt,
                'degree_type': 'bachelor',
                'duration_years': 4,
                'total_credits': 140,
                'description': 'Đào tạo kỹ sư CNTT toàn diện'
            },
            {
                'name': 'An toàn thông tin',
                'code': 'ATTT',
                'department': cntt,
                'degree_type': 'bachelor',
                'duration_years': 4,
                'total_credits': 140,
                'description': 'Chuyên sâu về bảo mật thông tin'
            },
            {
                'name': 'Kinh tế',
                'code': 'ECO',
                'department': kt,
                'degree_type': 'bachelor',
                'duration_years': 4,
                'total_credits': 130,
                'description': 'Lý thuyết kinh tế và phân tích'
            },
        ]
        
        for major_data in majors:
            major, created = Major.objects.get_or_create(
                code=major_data['code'],
                defaults=major_data
            )
            if created:
                self.stdout.write(f'   ✅ Created: {major.name}')
    
    def create_course_categories(self):
        """Create course categories"""
        self.stdout.write('📚 Creating course categories...')
        
        categories = [
            {
                'name': 'Giáo dục đại cương',
                'code': 'GDC',
                'category_type': 'general',
                'description': 'Các môn học đại cương bắt buộc',
                'min_credits': 30,
                'max_credits': 40
            },
            {
                'name': 'Cơ sở ngành',
                'code': 'CSN',
                'category_type': 'foundation',
                'description': 'Các môn học cơ sở của ngành',
                'min_credits': 30,
                'max_credits': 50
            },
            {
                'name': 'Chuyên ngành',
                'code': 'CN',
                'category_type': 'major',
                'description': 'Các môn học chuyên ngành bắt buộc',
                'min_credits': 40,
                'max_credits': 60
            },
        ]
        
        for cat_data in categories:
            category, created = CourseCategory.objects.get_or_create(
                code=cat_data['code'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'   ✅ Created: {category.name}')
    
    def create_student_classes(self):
        """Create student classes"""
        self.stdout.write('👥 Creating student classes...')
        
        current_year = AcademicYear.objects.get(is_current=True)
        ite_major = Major.objects.get(code='ITE')
        
        classes = [
            ('ITE2024A', ite_major, current_year, 1, 40),
            ('ITE2024B', ite_major, current_year, 1, 40),
        ]
        
        for name, major, academic_year, year_of_study, max_students in classes:
            student_class, created = StudentClass.objects.get_or_create(
                name=name,
                defaults={
                    'major': major,
                    'academic_year': academic_year,
                    'year_of_study': year_of_study,
                    'max_students': max_students
                }
            )
            if created:
                self.stdout.write(f'   ✅ Created: {name}')
    
    def create_curriculums(self):
        """Create curriculums"""
        self.stdout.write('📖 Creating curriculums...')
        
        current_year = AcademicYear.objects.get(is_current=True)
        ite_major = Major.objects.get(code='ITE')
        
        curriculum, created = Curriculum.objects.get_or_create(
            major=ite_major,
            academic_year=current_year,
            version='v2024.1',
            defaults={
                'name': 'Chương trình đào tạo Công nghệ thông tin',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(f'   ✅ Created: {curriculum.name}')
    
    def create_admin_user(self):
        """Create admin user"""
        self.stdout.write('👤 Creating admin user...')
        
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@university.edu.vn',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'   ✅ Created admin user: {admin_user.username}')
        
        # Create profile
        cntt_dept = Department.objects.get(code='CNTT')
        admin_profile, created = UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'role': 'admin',
                'is_verified': True,
                'academic_department': cntt_dept
            }
        )
        if created:
            self.stdout.write('   ✅ Created admin profile')
    
    def show_statistics(self):
        """Show creation statistics"""
        self.stdout.write('\n📊 Statistics:')
        self.stdout.write(f'   📅 Academic Years: {AcademicYear.objects.count()}')
        self.stdout.write(f'   🏢 Departments: {Department.objects.count()}')
        self.stdout.write(f'   🎓 Majors: {Major.objects.count()}')
        self.stdout.write(f'   📚 Course Categories: {CourseCategory.objects.count()}')
        self.stdout.write(f'   👥 Student Classes: {StudentClass.objects.count()}')
        self.stdout.write(f'   📖 Curriculums: {Curriculum.objects.count()}')
        self.stdout.write(f'   👤 Admin Users: {User.objects.filter(is_superuser=True).count()}') 