from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/courses/', views.course_list, name='course_list'),
    path('api/assignments/', views.assignment_list, name='assignment_list'),
    path('api/grades/', views.grade_list, name='grade_list'),
    path('api/notes/', views.note_list, name='note_list'),
] 