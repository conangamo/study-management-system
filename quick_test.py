#!/usr/bin/env python
"""
Quick Test Script - Test specific functionalities immediately
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth.models import User

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'study_management.settings')
django.setup()

def test_problematic_urls():
    """Test the URLs that were previously problematic"""
    client = Client()
    
    # Create admin user for testing
    try:
        admin_user = User.objects.create_user(
            username='quick_admin',
            email='admin@test.com',
            password='admin123',
            is_superuser=True,
            is_staff=True
        )
        client.force_login(admin_user)
    except:
        admin_user = User.objects.get(username='quick_admin')
        client.force_login(admin_user)
    
    problematic_urls = [
        '/custom-admin/users/create-student/',
        '/custom-admin/users/create-teacher/',
        '/custom-admin/users/bulk-create/',
        '/custom-admin/users/bulk-create-teacher/',
        '/custom-admin/classes/create/',
    ]
    
    print("🔍 Testing Previously Problematic URLs:")
    print("=" * 50)
    
    for url in problematic_urls:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {url} - OK ({response.status_code})")
            elif response.status_code == 302:
                print(f"🔄 {url} - Redirect ({response.status_code})")
            else:
                print(f"❌ {url} - Error ({response.status_code})")
        except Exception as e:
            print(f"💥 {url} - Exception: {str(e)}")
    
    # Test document download
    print(f"\n🔍 Testing Document Functionality:")
    print("=" * 50)
    
    try:
        response = client.get('/documents/')
        if response.status_code == 200:
            print("✅ Documents list - OK")
        else:
            print(f"❌ Documents list - Error ({response.status_code})")
    except Exception as e:
        print(f"💥 Documents list - Exception: {str(e)}")
    
    # Clean up
    try:
        admin_user.delete()
    except:
        pass

def test_teacher_assignment_flow():
    """Test teacher assignment creation flow"""
    client = Client()
    
    # Create teacher user
    try:
        teacher_user = User.objects.create_user(
            username='quick_teacher',
            email='teacher@test.com',
            password='teacher123'
        )
        from core.models.user import UserProfile
        UserProfile.objects.create(user=teacher_user, role='teacher')
        
        # Create a course
        from core.models.study import Course
        course = Course.objects.create(
            name='Quick Test Course',
            code='QTC101',
            teacher=teacher_user,
            credits=3,
            semester='1',
            academic_year='2024-2025',
            status='active'
        )
        
        client.force_login(teacher_user)
        
        print(f"\n🔍 Testing Teacher Assignment Flow:")
        print("=" * 50)
        
        # Test assignment list
        response = client.get('/dashboard/teacher/assignments/')
        if response.status_code == 200:
            print("✅ Assignment list - OK")
        else:
            print(f"❌ Assignment list - Error ({response.status_code})")
        
        # Test assignment creation page
        response = client.get('/dashboard/teacher/assignments/create/')
        if response.status_code == 200:
            print("✅ Assignment creation page - OK")
        else:
            print(f"❌ Assignment creation page - Error ({response.status_code})")
        
        # Test creating an assignment
        from datetime import datetime, timedelta
        assignment_data = {
            'course': course.id,
            'title': 'Quick Test Assignment',
            'description': 'Test assignment description',
            'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'max_score': 10.0,
            'max_file_size': 10,
            'is_visible_to_students': True,
            'status': 'active'
        }
        
        response = client.post('/dashboard/teacher/assignments/create/', assignment_data)
        if response.status_code in [200, 302]:
            print("✅ Assignment creation - OK")
            
            # If successful, test accessing the created assignment
            from core.models.assignment import Assignment
            try:
                created_assignment = Assignment.objects.filter(title='Quick Test Assignment').first()
                if created_assignment:
                    detail_url = f'/dashboard/teacher/assignments/{created_assignment.id}/'
                    response = client.get(detail_url)
                    if response.status_code == 200:
                        print(f"✅ Assignment detail view - OK ({detail_url})")
                    else:
                        print(f"❌ Assignment detail view - Error ({response.status_code})")
            except Exception as e:
                print(f"💥 Assignment detail test failed: {str(e)}")
        else:
            print(f"❌ Assignment creation - Error ({response.status_code})")
        
    except Exception as e:
        print(f"💥 Teacher assignment flow failed: {str(e)}")
    finally:
        # Clean up
        try:
            teacher_user.delete()
        except:
            pass

def test_search_functionality():
    """Test search functionality"""
    client = Client()
    
    try:
        # Create admin user
        admin_user = User.objects.create_user(
            username='search_admin',
            email='search@test.com',
            password='admin123',
            is_superuser=True
        )
        client.force_login(admin_user)
        
        print(f"\n🔍 Testing Search Functionality:")
        print("=" * 50)
        
        # Test user search
        response = client.get('/custom-admin/users/search/', {'q': 'admin'})
        if response.status_code == 200:
            print("✅ User search - OK")
        else:
            print(f"❌ User search - Error ({response.status_code})")
        
    except Exception as e:
        print(f"💥 Search functionality failed: {str(e)}")
    finally:
        try:
            admin_user.delete()
        except:
            pass

if __name__ == '__main__':
    print("🚀 QUICK SYSTEM TEST")
    print("=" * 50)
    
    test_problematic_urls()
    test_teacher_assignment_flow()
    test_search_functionality()
    
    print(f"\n✨ Quick test completed!") 