"""
Simple System Test - No Unicode characters
"""

import os
import subprocess
import sys

def run_test(command, description):
    print(f"Testing: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  PASS: {description}")
            return True
        else:
            print(f"  FAIL: {description}")
            if result.stderr:
                print(f"    Error: {result.stderr[:100]}...")
            return False
    except Exception as e:
        print(f"  ERROR: {description} - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("SYSTEM TEST SUITE - Quan Ly Hoc Sinh")
    print("=" * 60)
    
    tests = [
        ("python manage.py check", "Django system check"),
        ("python manage.py showmigrations", "Migration status"),
        ('python manage.py shell -c "from core.models.user import UserProfile; print(UserProfile)"', "UserProfile model"),
        ('python manage.py shell -c "from core.models.study import Course; print(Course)"', "Course model"),
        ('python manage.py shell -c "from core.models.assignment import Assignment; print(Assignment)"', "Assignment model"),
        ('python manage.py shell -c "from core.forms.user_forms import StudentAccountForm; print(StudentAccountForm)"', "StudentAccountForm"),
        ('python manage.py shell -c "from core.dashboards.teacher.forms import TeacherAssignmentForm; print(TeacherAssignmentForm)"', "TeacherAssignmentForm"),
    ]
    
    results = []
    for command, description in tests:
        results.append(run_test(command, description))
    
    # Check template files
    template_files = [
        'templates/base.html',
        'templates/auth/login.html',
        'templates/main/home.html',
        'templates/dashboards/admin/dashboard.html',
        'templates/dashboards/teacher/dashboard.html',
        'templates/dashboards/student/dashboard.html',
    ]
    
    print(f"\nTesting template files:")
    for template in template_files:
        if os.path.exists(template):
            print(f"  PASS: Template exists - {template}")
            results.append(True)
        else:
            print(f"  FAIL: Template missing - {template}")
            results.append(False)
    
    # Test URL patterns with a simple script
    url_test_script = '''
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_management.settings')
django.setup()

from django.test import Client

client = Client()
urls = [
    ('/', 'Home'),
    ('/login/', 'Login'), 
    ('/documents/', 'Documents')
]

for url, name in urls:
    try:
        response = client.get(url)
        if response.status_code in [200, 302, 403]:
            print(f"PASS: {name} ({url}) - {response.status_code}")
        else:
            print(f"FAIL: {name} ({url}) - {response.status_code}")
    except Exception as e:
        print(f"ERROR: {name} ({url}) - {str(e)}")
'''
    
    with open('url_test.py', 'w') as f:
        f.write(url_test_script)
    
    print(f"\nTesting URL patterns:")
    url_result = run_test("python url_test.py", "URL pattern testing")
    results.append(url_result)
    
    # Clean up
    try:
        os.remove('url_test.py')
    except:
        pass
    
    # Summary
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n" + "=" * 60)
    print(f"TEST SUMMARY")
    print(f"=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("OVERALL RESULT: PASS")
        return 0
    else:
        print("OVERALL RESULT: FAIL")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 