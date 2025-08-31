#!/usr/bin/env python
"""
Quick Check - Verify all fixes are working
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_management.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from core.models.user import UserProfile

def main():
    print("=" * 50)
    print("QUICK SYSTEM CHECK - FIXES VERIFICATION")
    print("=" * 50)
    
    client = Client()
    
    # Test 1: Previously problematic admin URLs
    print("\n1. Testing Previously Problematic Admin URLs:")
    
    # Create admin user
    try:
        admin = User.objects.create_user(
            username='quick_admin_check',
            password='admin123',
            is_superuser=True,
            is_staff=True
        )
        client.force_login(admin)
        print("   Admin user created and logged in")
    except:
        admin = User.objects.get(username='quick_admin_check')
        client.force_login(admin)
        print("   Using existing admin user")
    
    problematic_urls = [
        ('/custom-admin/users/create-student/', 'Create Student'),
        ('/custom-admin/users/create-teacher/', 'Create Teacher'),
        ('/custom-admin/users/bulk-create/', 'Bulk Create Students'),
        ('/custom-admin/users/bulk-create-teacher/', 'Bulk Create Teachers'),
        ('/custom-admin/classes/create/', 'Create Class'),
    ]
    
    fixed_count = 0
    for url, name in problematic_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"   ✅ {name}: FIXED")
                fixed_count += 1
            else:
                print(f"   ❌ {name}: Still failing ({response.status_code})")
        except Exception as e:
            print(f"   ❌ {name}: Error - {str(e)[:50]}")
    
    print(f"   Fixed URLs: {fixed_count}/{len(problematic_urls)}")
    
    # Test 2: Form imports
    print("\n2. Testing Form Imports:")
    form_tests = [
        ("StudentAccountForm", "from core.forms.user_forms import StudentAccountForm; StudentAccountForm()"),
        ("TeacherAccountForm", "from core.forms.user_forms import TeacherAccountForm; TeacherAccountForm()"),
        ("AdminClassForm", "from core.dashboards.admin.forms import AdminClassForm; AdminClassForm()"),
    ]
    
    form_count = 0
    for form_name, test_code in form_tests:
        try:
            exec(test_code)
            print(f"   ✅ {form_name}: Import working")
            form_count += 1
        except Exception as e:
            print(f"   ❌ {form_name}: Import failed - {str(e)[:50]}")
    
    print(f"   Working Forms: {form_count}/{len(form_tests)}")
    
    # Test 3: Document functionality
    print("\n3. Testing Document System:")
    try:
        response = client.get('/documents/')
        if response.status_code == 200:
            print("   ✅ Document list: Working")
            doc_working = True
        else:
            print(f"   ❌ Document list: Error ({response.status_code})")
            doc_working = False
    except Exception as e:
        print(f"   ❌ Document list: Exception - {str(e)[:50]}")
        doc_working = False
    
    # Test 4: Search functionality
    print("\n4. Testing Search Functions:")
    try:
        response = client.get('/custom-admin/users/search/', {'q': 'admin'})
        if response.status_code == 200:
            print("   ✅ User search: Working")
            search_working = True
        else:
            print(f"   ❌ User search: Error ({response.status_code})")
            search_working = False
    except Exception as e:
        print(f"   ❌ User search: Exception - {str(e)[:50]}")
        search_working = False
    
    # Test 5: Model integrity
    print("\n5. Testing Model Integrity:")
    try:
        from core.models.user import UserProfile
        from core.models.study import Course
        from core.models.assignment import Assignment
        from core.models.documents import Document
        
        models = [
            (UserProfile, "UserProfile"),
            (Course, "Course"),
            (Assignment, "Assignment"),
            (Document, "Document")
        ]
        
        model_count = 0
        for model, name in models:
            try:
                model.objects.count()  # Simple query test
                print(f"   ✅ {name}: Working")
                model_count += 1
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)[:50]}")
        
        print(f"   Working Models: {model_count}/{len(models)}")
        
    except Exception as e:
        print(f"   ❌ Model testing failed: {str(e)[:50]}")
        model_count = 0
    
    # Calculate overall score
    total_tests = len(problematic_urls) + len(form_tests) + 1 + 1 + len(models)
    passed_tests = fixed_count + form_count + (1 if doc_working else 0) + (1 if search_working else 0) + model_count
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Summary
    print("\n" + "=" * 50)
    print("QUICK CHECK SUMMARY")
    print("=" * 50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("\n🎉 EXCELLENT! All major fixes are working!")
        status = "EXCELLENT"
    elif success_rate >= 80:
        print("\n✅ GOOD! Most fixes are working, minor issues remain.")
        status = "GOOD"
    elif success_rate >= 70:
        print("\n⚠️  FAIR! Some fixes working, needs attention.")
        status = "FAIR"
    else:
        print("\n❌ POOR! Major issues still present.")
        status = "POOR"
    
    # Cleanup
    try:
        admin.delete()
        print("\nCleaned up test user")
    except:
        pass
    
    print(f"\nFinal Status: {status}")
    print("For detailed testing, run: python test_urls_detailed.py")
    
    return success_rate

if __name__ == '__main__':
    main() 