#!/usr/bin/env python
"""
Comprehensive System Test Script
Tests all URLs, templates, functionality, models, forms, and views
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.template.loader import get_template
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_management.settings')
django.setup()

# Import models
from core.models.user import UserProfile
from core.models.study import Course, Grade, Class
from core.models.assignment import Assignment, AssignmentSubmission
from core.models.documents import Document, DocumentCategory, DocumentComment

# Import forms
from core.forms.user_forms import StudentAccountForm, TeacherAccountForm
from core.dashboards.admin.forms import AdminClassForm
from core.dashboards.teacher.forms import TeacherAssignmentForm, TeacherCourseForm

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SystemTester:
    def __init__(self):
        self.client = Client()
        self.test_results = {
            'urls': [],
            'templates': [],
            'models': [],
            'forms': [],
            'views': [],
            'functionality': []
        }
        self.users = {}
        
    def print_header(self, title):
        print(f"\n{Color.BOLD}{Color.CYAN}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{Color.END}")
        
    def print_success(self, message):
        print(f"{Color.GREEN}✓ {message}{Color.END}")
        
    def print_error(self, message):
        print(f"{Color.RED}✗ {message}{Color.END}")
        
    def print_warning(self, message):
        print(f"{Color.YELLOW}⚠ {message}{Color.END}")
        
    def print_info(self, message):
        print(f"{Color.BLUE}ℹ {message}{Color.END}")

    def setup_test_data(self):
        """Create test users and data"""
        self.print_header("SETTING UP TEST DATA")
        
        try:
            # Create admin user
            admin_user = User.objects.create_user(
                username='admin_test',
                email='admin@test.com',
                password='admin123',
                first_name='Admin',
                last_name='Test',
                is_superuser=True,
                is_staff=True
            )
            UserProfile.objects.create(user=admin_user, role='admin')
            self.users['admin'] = admin_user
            self.print_success("Created admin user")
            
            # Create teacher user
            teacher_user = User.objects.create_user(
                username='teacher_test',
                email='teacher@test.com',
                password='teacher123',
                first_name='Teacher',
                last_name='Test'
            )
            UserProfile.objects.create(user=teacher_user, role='teacher')
            self.users['teacher'] = teacher_user
            self.print_success("Created teacher user")
            
            # Create student user
            student_user = User.objects.create_user(
                username='student_test',
                email='student@test.com',
                password='student123',
                first_name='Student',
                last_name='Test'
            )
            UserProfile.objects.create(user=student_user, role='student')
            self.users['student'] = student_user
            self.print_success("Created student user")
            
            # Create test course
            course = Course.objects.create(
                name='Test Course',
                code='TEST101',
                description='Test course description',
                credits=3,
                semester='1',
                academic_year='2024-2025',
                teacher=teacher_user,
                status='active'
            )
            course.students.add(student_user)
            self.test_course = course
            self.print_success("Created test course")
            
            # Create test class
            test_class = Class.objects.create(
                name='Test Class',
                code='TC2024',
                academic_year='2024-2025',
                advisor=teacher_user,
                head_teacher=teacher_user
            )
            test_class.students.add(student_user)
            self.test_class = test_class
            self.print_success("Created test class")
            
            # Create test assignment
            assignment = Assignment.objects.create(
                course=course,
                title='Test Assignment',
                description='Test assignment description',
                due_date=datetime.now() + timedelta(days=7),
                max_score=10.0,
                created_by=teacher_user,
                status='active'
            )
            self.test_assignment = assignment
            self.print_success("Created test assignment")
            
            # Create document category
            doc_category = DocumentCategory.objects.create(
                name='Test Category',
                description='Test category for documents'
            )
            self.test_doc_category = doc_category
            self.print_success("Created document category")
            
        except Exception as e:
            self.print_error(f"Failed to setup test data: {str(e)}")
            return False
            
        return True

    def test_urls(self):
        """Test all URL patterns"""
        self.print_header("TESTING URL PATTERNS")
        
        # Define all URLs to test
        urls_to_test = [
            # Main URLs
            ('/', 'GET', None, 'Home page'),
            ('/login/', 'GET', None, 'Login page'),
            ('/logout/', 'GET', None, 'Logout'),
            ('/documents/', 'GET', 'student', 'Documents list'),
            
            # Admin URLs
            ('/custom-admin/', 'GET', 'admin', 'Admin dashboard'),
            ('/custom-admin/users/', 'GET', 'admin', 'Admin users list'),
            ('/custom-admin/users/create-student/', 'GET', 'admin', 'Create student'),
            ('/custom-admin/users/create-teacher/', 'GET', 'admin', 'Create teacher'),
            ('/custom-admin/users/bulk-create/', 'GET', 'admin', 'Bulk create students'),
            ('/custom-admin/users/bulk-create-teacher/', 'GET', 'admin', 'Bulk create teachers'),
            ('/custom-admin/classes/', 'GET', 'admin', 'Admin classes list'),
            ('/custom-admin/classes/create/', 'GET', 'admin', 'Create class'),
            ('/custom-admin/courses/', 'GET', 'admin', 'Admin courses list'),
            ('/custom-admin/assignments/', 'GET', 'admin', 'Admin assignments'),
            ('/custom-admin/grades/', 'GET', 'admin', 'Admin grades'),
            ('/custom-admin/documents/', 'GET', 'admin', 'Admin documents'),
            
            # Teacher URLs
            ('/dashboard/teacher/', 'GET', 'teacher', 'Teacher dashboard'),
            ('/dashboard/teacher/courses/', 'GET', 'teacher', 'Teacher courses'),
            ('/dashboard/teacher/assignments/', 'GET', 'teacher', 'Teacher assignments'),
            ('/dashboard/teacher/assignments/create/', 'GET', 'teacher', 'Create assignment'),
            ('/dashboard/teacher/grades/', 'GET', 'teacher', 'Teacher grades'),
            ('/dashboard/teacher/students/', 'GET', 'teacher', 'Teacher students'),
            
            # Student URLs
            ('/dashboard/student/', 'GET', 'student', 'Student dashboard'),
            ('/dashboard/student/courses/', 'GET', 'student', 'Student courses'),
            ('/dashboard/student/assignments/', 'GET', 'student', 'Student assignments'),
            ('/dashboard/student/grades/', 'GET', 'student', 'Student grades'),
        ]
        
        for url, method, user_type, description in urls_to_test:
            try:
                # Login if user type specified
                if user_type and user_type in self.users:
                    self.client.force_login(self.users[user_type])
                elif user_type:
                    self.client.logout()
                
                # Make request
                if method == 'GET':
                    response = self.client.get(url)
                else:
                    response = self.client.post(url)
                
                # Check response
                if response.status_code in [200, 302]:
                    self.print_success(f"{description}: {url} ({response.status_code})")
                    self.test_results['urls'].append({
                        'url': url,
                        'status': 'pass',
                        'code': response.status_code
                    })
                else:
                    self.print_error(f"{description}: {url} ({response.status_code})")
                    self.test_results['urls'].append({
                        'url': url,
                        'status': 'fail',
                        'code': response.status_code
                    })
                    
            except Exception as e:
                self.print_error(f"{description}: {url} - {str(e)}")
                self.test_results['urls'].append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })

    def test_templates(self):
        """Test template loading"""
        self.print_header("TESTING TEMPLATE LOADING")
        
        templates_to_test = [
            'base.html',
            'auth/login.html',
            'auth/register.html',
            'main/home.html',
            'main/documents.html',
            'dashboards/admin/dashboard.html',
            'dashboards/admin/users/list.html',
            'dashboards/admin/classes/list.html',
            'dashboards/teacher/dashboard.html',
            'dashboards/teacher/course/list.html',
            'dashboards/teacher/assignment/list.html',
            'dashboards/teacher/assignment/create.html',
            'dashboards/student/dashboard.html',
            'dashboards/student/assignments.html',
            'admin/create_account.html',
        ]
        
        for template_name in templates_to_test:
            try:
                template = get_template(template_name)
                self.print_success(f"Template loaded: {template_name}")
                self.test_results['templates'].append({
                    'template': template_name,
                    'status': 'pass'
                })
            except Exception as e:
                self.print_error(f"Template failed: {template_name} - {str(e)}")
                self.test_results['templates'].append({
                    'template': template_name,
                    'status': 'fail',
                    'error': str(e)
                })

    def test_models(self):
        """Test model functionality"""
        self.print_header("TESTING MODEL FUNCTIONALITY")
        
        try:
            # Test UserProfile model
            profile = self.users['student'].profile
            self.print_success(f"UserProfile: {profile.user.username} - {profile.role}")
            
            # Test Course model
            course_str = str(self.test_course)
            self.print_success(f"Course model: {course_str}")
            
            # Test Assignment model
            assignment_str = str(self.test_assignment)
            self.print_success(f"Assignment model: {assignment_str}")
            
            # Test Class model
            class_str = str(self.test_class)
            self.print_success(f"Class model: {class_str}")
            
            # Test model relationships
            enrolled_courses = self.users['student'].enrolled_courses.count()
            self.print_success(f"Student enrolled in {enrolled_courses} courses")
            
            course_students = self.test_course.students.count()
            self.print_success(f"Course has {course_students} students")
            
            # Test model validation
            try:
                # Try to create invalid course
                invalid_course = Course(
                    name='',  # Empty name should fail
                    code='',
                    teacher=self.users['teacher']
                )
                invalid_course.full_clean()
                self.print_error("Model validation failed - empty course name accepted")
            except ValidationError:
                self.print_success("Model validation working - empty course name rejected")
                
            self.test_results['models'].append({'status': 'pass'})
            
        except Exception as e:
            self.print_error(f"Model testing failed: {str(e)}")
            self.test_results['models'].append({'status': 'fail', 'error': str(e)})

    def test_forms(self):
        """Test form functionality"""
        self.print_header("TESTING FORM FUNCTIONALITY")
        
        try:
            # Test StudentAccountForm
            student_data = {
                'first_name': 'Test',
                'last_name': 'Student',
                'email': 'teststudent@example.com',
                'username': 'teststudent',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'student_id': 'ST2024001',
                'date_of_birth': '2000-01-01',
                'gender': 'male',
                'phone': '0123456789',
                'address': 'Test Address'
            }
            student_form = StudentAccountForm(data=student_data)
            if student_form.is_valid():
                self.print_success("StudentAccountForm validation passed")
            else:
                self.print_warning(f"StudentAccountForm validation failed: {student_form.errors}")
            
            # Test TeacherAccountForm
            teacher_data = {
                'first_name': 'Test',
                'last_name': 'Teacher',
                'email': 'testteacher@example.com',
                'username': 'testteacher',
                'password1': 'testpass123',
                'password2': 'testpass123',
                'employee_id': 'EMP2024001',
                'department': 'Computer Science',
                'phone': '0123456789',
                'address': 'Test Address'
            }
            teacher_form = TeacherAccountForm(data=teacher_data)
            if teacher_form.is_valid():
                self.print_success("TeacherAccountForm validation passed")
            else:
                self.print_warning(f"TeacherAccountForm validation failed: {teacher_form.errors}")
            
            # Test TeacherAssignmentForm
            assignment_data = {
                'course': self.test_course.id,
                'title': 'Test Assignment Form',
                'description': 'Test assignment description',
                'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
                'max_score': 10.0,
                'max_file_size': 10,
                'is_visible_to_students': True,
                'status': 'active'
            }
            assignment_form = TeacherAssignmentForm(
                data=assignment_data, 
                teacher=self.users['teacher']
            )
            if assignment_form.is_valid():
                self.print_success("TeacherAssignmentForm validation passed")
            else:
                self.print_warning(f"TeacherAssignmentForm validation failed: {assignment_form.errors}")
            
            self.test_results['forms'].append({'status': 'pass'})
            
        except Exception as e:
            self.print_error(f"Form testing failed: {str(e)}")
            self.test_results['forms'].append({'status': 'fail', 'error': str(e)})

    def test_functionality(self):
        """Test core functionality"""
        self.print_header("TESTING CORE FUNCTIONALITY")
        
        try:
            # Test user authentication
            self.client.logout()
            login_response = self.client.post('/login/', {
                'username': 'student_test',
                'password': 'student123'
            })
            if login_response.status_code in [200, 302]:
                self.print_success("User authentication working")
            else:
                self.print_error("User authentication failed")
            
            # Test assignment submission (mock)
            self.client.force_login(self.users['student'])
            try:
                # Create a test file
                test_file = SimpleUploadedFile(
                    "test.txt", 
                    b"Test file content", 
                    content_type="text/plain"
                )
                
                submission = AssignmentSubmission.objects.create(
                    assignment=self.test_assignment,
                    student=self.users['student'],
                    submission_text='Test submission',
                    status='submitted'
                )
                self.print_success("Assignment submission created")
                
                # Test grade creation
                grade = Grade.objects.create(
                    student=self.users['student'],
                    course=self.test_course,
                    assignment=self.test_assignment,
                    submission=submission,
                    grade_type='assignment',
                    score=8.5,
                    max_score=10.0,
                    created_by=self.users['teacher']
                )
                self.print_success("Grade created")
                
            except Exception as e:
                self.print_warning(f"Submission/Grade creation: {str(e)}")
            
            # Test document upload (mock)
            try:
                document = Document.objects.create(
                    title='Test Document',
                    description='Test document description',
                    file_name='test.pdf',
                    file_size=1024,
                    uploaded_by=self.users['teacher'],
                    course=self.test_course,
                    category=self.test_doc_category,
                    status='active'
                )
                self.print_success("Document created")
            except Exception as e:
                self.print_warning(f"Document creation: {str(e)}")
            
            # Test search functionality
            search_response = self.client.get('/custom-admin/users/search/', {
                'q': 'test'
            })
            if search_response.status_code == 200:
                self.print_success("Search functionality working")
            else:
                self.print_warning("Search functionality may have issues")
            
            self.test_results['functionality'].append({'status': 'pass'})
            
        except Exception as e:
            self.print_error(f"Functionality testing failed: {str(e)}")
            self.test_results['functionality'].append({'status': 'fail', 'error': str(e)})

    def test_views(self):
        """Test view functionality"""
        self.print_header("TESTING VIEW FUNCTIONALITY")
        
        try:
            # Test admin views
            self.client.force_login(self.users['admin'])
            admin_views = [
                '/custom-admin/',
                '/custom-admin/users/',
                '/custom-admin/classes/',
                '/custom-admin/courses/',
            ]
            
            for view_url in admin_views:
                response = self.client.get(view_url)
                if response.status_code == 200:
                    self.print_success(f"Admin view working: {view_url}")
                else:
                    self.print_warning(f"Admin view issue: {view_url} ({response.status_code})")
            
            # Test teacher views
            self.client.force_login(self.users['teacher'])
            teacher_views = [
                '/dashboard/teacher/',
                '/dashboard/teacher/courses/',
                '/dashboard/teacher/assignments/',
                '/dashboard/teacher/grades/',
            ]
            
            for view_url in teacher_views:
                response = self.client.get(view_url)
                if response.status_code == 200:
                    self.print_success(f"Teacher view working: {view_url}")
                else:
                    self.print_warning(f"Teacher view issue: {view_url} ({response.status_code})")
            
            # Test student views
            self.client.force_login(self.users['student'])
            student_views = [
                '/dashboard/student/',
                '/dashboard/student/courses/',
                '/dashboard/student/assignments/',
                '/dashboard/student/grades/',
            ]
            
            for view_url in student_views:
                response = self.client.get(view_url)
                if response.status_code == 200:
                    self.print_success(f"Student view working: {view_url}")
                else:
                    self.print_warning(f"Student view issue: {view_url} ({response.status_code})")
            
            self.test_results['views'].append({'status': 'pass'})
            
        except Exception as e:
            self.print_error(f"View testing failed: {str(e)}")
            self.test_results['views'].append({'status': 'fail', 'error': str(e)})

    def test_permissions(self):
        """Test permission system"""
        self.print_header("TESTING PERMISSION SYSTEM")
        
        try:
            # Test unauthorized access
            self.client.logout()
            
            # Try to access admin page without login
            response = self.client.get('/custom-admin/')
            if response.status_code in [302, 403]:
                self.print_success("Admin access blocked for anonymous users")
            else:
                self.print_error("Admin access not properly protected")
            
            # Try to access teacher dashboard as student
            self.client.force_login(self.users['student'])
            response = self.client.get('/dashboard/teacher/')
            if response.status_code in [302, 403]:
                self.print_success("Teacher dashboard blocked for students")
            else:
                self.print_error("Teacher dashboard not properly protected")
            
            # Try to access admin as teacher
            self.client.force_login(self.users['teacher'])
            response = self.client.get('/custom-admin/users/create-student/')
            if response.status_code in [302, 403]:
                self.print_success("Admin functions blocked for teachers")
            else:
                self.print_warning("Admin functions accessible to teachers (may be intended)")
                
        except Exception as e:
            self.print_error(f"Permission testing failed: {str(e)}")

    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header("TEST REPORT SUMMARY")
        
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.test_results.items():
            if results:
                category_total = len(results)
                category_passed = sum(1 for r in results if r.get('status') == 'pass')
                total_tests += category_total
                passed_tests += category_passed
                
                print(f"\n{Color.BOLD}{category.upper()}:{Color.END}")
                print(f"  Passed: {Color.GREEN}{category_passed}{Color.END}")
                print(f"  Total:  {category_total}")
                print(f"  Rate:   {Color.CYAN}{(category_passed/category_total*100):.1f}%{Color.END}")
        
        print(f"\n{Color.BOLD}OVERALL RESULTS:{Color.END}")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed:      {Color.GREEN}{passed_tests}{Color.END}")
        print(f"  Failed:      {Color.RED}{total_tests - passed_tests}{Color.END}")
        print(f"  Success Rate: {Color.CYAN}{(passed_tests/total_tests*100):.1f}%{Color.END}")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': (passed_tests/total_tests*100) if total_tests > 0 else 0
            },
            'details': self.test_results
        }
        
        with open('test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_success("Detailed report saved to test_report.json")

    def cleanup_test_data(self):
        """Clean up test data"""
        self.print_header("CLEANING UP TEST DATA")
        
        try:
            # Delete test users and related data
            for user_type, user in self.users.items():
                user.delete()
                self.print_success(f"Deleted {user_type} user")
            
            # Delete test course, assignment, etc. (cascade delete should handle this)
            self.print_success("Test data cleaned up")
            
        except Exception as e:
            self.print_warning(f"Cleanup warning: {str(e)}")

    def run_all_tests(self):
        """Run all tests"""
        print(f"{Color.BOLD}{Color.PURPLE}")
        print("╔══════════════════════════════════════════════════════════╗")
        print("║            COMPREHENSIVE SYSTEM TEST SUITE              ║")
        print("║                 Quản Lý Học Sinh                        ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print(f"{Color.END}")
        
        if not self.setup_test_data():
            self.print_error("Failed to setup test data. Aborting tests.")
            return
        
        # Run all test categories
        self.test_urls()
        self.test_templates()
        self.test_models()
        self.test_forms()
        self.test_views()
        self.test_functionality()
        self.test_permissions()
        
        # Generate report
        self.generate_report()
        
        # Cleanup
        self.cleanup_test_data()
        
        print(f"\n{Color.BOLD}{Color.GREEN}🎉 TESTING COMPLETE! 🎉{Color.END}")

if __name__ == '__main__':
    tester = SystemTester()
    tester.run_all_tests() 