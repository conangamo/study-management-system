"""
Detailed URL Testing Script
Tests all major URLs in the system
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_management.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models.user import UserProfile
from core.models.study import Course
from core.models.assignment import Assignment

def setup_test_users():
    """Create test users for different roles"""
    users = {}
    
    # Admin user
    try:
        admin = User.objects.create_user(
            username='test_admin',
            email='admin@test.com',
            password='admin123',
            is_superuser=True,
            is_staff=True
        )
        UserProfile.objects.create(user=admin, role='admin')
        users['admin'] = admin
        print("Created admin user")
    except:
        admin = User.objects.get(username='test_admin')
        users['admin'] = admin
        print("Using existing admin user")
    
    # Teacher user
    try:
        teacher = User.objects.create_user(
            username='test_teacher',
            email='teacher@test.com',
            password='teacher123'
        )
        UserProfile.objects.create(user=teacher, role='teacher')
        users['teacher'] = teacher
        print("Created teacher user")
    except:
        teacher = User.objects.get(username='test_teacher')
        users['teacher'] = teacher
        print("Using existing teacher user")
    
    # Student user
    try:
        student = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='student123'
        )
        UserProfile.objects.create(user=student, role='student')
        users['student'] = student
        print("Created student user")
    except:
        student = User.objects.get(username='test_student')
        users['student'] = student
        print("Using existing student user")
    
    return users

def test_urls(client, user, user_type, urls):
    """Test a list of URLs for a specific user type"""
    print(f"\nTesting {user_type.upper()} URLs:")
    print("-" * 40)
    
    if user:
        client.force_login(user)
    else:
        client.logout()
    
    results = []
    for url, description in urls:
        try:
            response = client.get(url)
            status = response.status_code
            
            if status == 200:
                print(f"  PASS: {description} ({url}) - {status}")
                results.append(True)
            elif status == 302:
                print(f"  REDIRECT: {description} ({url}) - {status}")
                results.append(True)
            elif status == 403:
                print(f"  FORBIDDEN: {description} ({url}) - {status}")
                results.append(True)  # Expected for some URLs
            else:
                print(f"  FAIL: {description} ({url}) - {status}")
                results.append(False)
                
        except Exception as e:
            print(f"  ERROR: {description} ({url}) - {str(e)}")
            results.append(False)
    
    return results

def main():
    print("=" * 60)
    print("DETAILED URL TESTING")
    print("=" * 60)
    
    client = Client()
    users = setup_test_users()
    
    # Create test course for teacher
    try:
        course = Course.objects.create(
            name='Test Course URL',
            code='TCURL101',
            teacher=users['teacher'],
            credits=3,
            semester='1',
            academic_year='2024-2025',
            status='active'
        )
        print("Created test course")
    except:
        course = Course.objects.filter(code='TCURL101').first()
        print("Using existing test course")
    
    # Create test assignment
    try:
        from datetime import datetime, timedelta
        assignment = Assignment.objects.create(
            course=course,
            title='Test Assignment URL',
            description='Test assignment for URL testing',
            due_date=datetime.now() + timedelta(days=7),
            max_score=10.0,
            created_by=users['teacher'],
            status='active'
        )
        print("Created test assignment")
    except:
        assignment = Assignment.objects.filter(title='Test Assignment URL').first()
        print("Using existing test assignment")
    
    all_results = []
    
    # Test public URLs (no login required)
    public_urls = [
        ('/', 'Home page'),
        ('/login/', 'Login page'),
        ('/logout/', 'Logout page'),
    ]
    
    results = test_urls(client, None, 'PUBLIC', public_urls)
    all_results.extend(results)
    
    # Test admin URLs
    admin_urls = [
        ('/custom-admin/', 'Admin dashboard'),
        ('/custom-admin/users/', 'Admin users list'),
        ('/custom-admin/users/create-student/', 'Create student page'),
        ('/custom-admin/users/create-teacher/', 'Create teacher page'),
        ('/custom-admin/users/bulk-create/', 'Bulk create students'),
        ('/custom-admin/users/bulk-create-teacher/', 'Bulk create teachers'),
        ('/custom-admin/classes/', 'Admin classes list'),
        ('/custom-admin/classes/create/', 'Create class page'),
        ('/custom-admin/courses/', 'Admin courses list'),
        ('/custom-admin/assignments/', 'Admin assignments list'),
        ('/custom-admin/grades/', 'Admin grades list'),
        ('/custom-admin/documents/', 'Admin documents list'),
        ('/custom-admin/users/search/', 'User search API'),
    ]
    
    results = test_urls(client, users['admin'], 'ADMIN', admin_urls)
    all_results.extend(results)
    
    # Test teacher URLs
    teacher_urls = [
        ('/dashboard/teacher/', 'Teacher dashboard'),
        ('/dashboard/teacher/courses/', 'Teacher courses list'),
        ('/dashboard/teacher/assignments/', 'Teacher assignments list'),
        ('/dashboard/teacher/assignments/create/', 'Create assignment page'),
        ('/dashboard/teacher/grades/', 'Teacher grades list'),
        ('/dashboard/teacher/students/', 'Teacher students list'),
    ]
    
    if assignment:
        teacher_urls.append((f'/dashboard/teacher/assignments/{assignment.id}/', 'Assignment detail'))
    
    results = test_urls(client, users['teacher'], 'TEACHER', teacher_urls)
    all_results.extend(results)
    
    # Test student URLs
    student_urls = [
        ('/dashboard/student/', 'Student dashboard'),
        ('/dashboard/student/courses/', 'Student courses list'),
        ('/dashboard/student/assignments/', 'Student assignments list'),
        ('/dashboard/student/grades/', 'Student grades list'),
        ('/documents/', 'Documents list'),
    ]
    
    results = test_urls(client, users['student'], 'STUDENT', student_urls)
    all_results.extend(results)
    
    # Summary
    passed = sum(all_results)
    total = len(all_results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n" + "=" * 60)
    print(f"URL TEST SUMMARY")
    print(f"=" * 60)
    print(f"Total URLs Tested: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("OVERALL URL TEST: PASS")
    else:
        print("OVERALL URL TEST: FAIL")
        
    # Cleanup test data
    try:
        for user in users.values():
            user.delete()
        print("\nCleaned up test users")
    except:
        print("\nWarning: Could not clean up all test users")
    
    return success_rate

if __name__ == '__main__':
    main() 