#!/bin/bash

# Đợi database sẵn sàng
echo "Waiting for database..."
until pg_isready -h db -p 5432 -U postgres; do
  echo "Database is not ready - waiting..."
  sleep 2
done
echo "Database is ready!"

# Chạy migrations
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

# Tạo superuser nếu chưa có
echo "Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000 