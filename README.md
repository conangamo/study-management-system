# Hệ Thống Quản Lý Học Tập

Ứng dụng web quản lý học tập cho sinh viên được xây dựng bằng Django, Django REST Framework, PostgreSQL và Bootstrap 5.

## 🎯 Tính năng chính

- **Quản lý khóa học**: Thêm, sửa, xóa và xem danh sách các môn học
- **Quản lý bài tập**: Theo dõi deadline và trạng thái bài tập
- **Quản lý điểm số**: Ghi chép và theo dõi điểm số
- **Ghi chú cá nhân**: Lưu trữ ghi chú và ý tưởng quan trọng
- **Giao diện responsive**: Tương thích với mọi thiết bị
- **Hệ thống đăng nhập**: Phân quyền người dùng

## 🛠️ Công nghệ sử dụng

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL 13
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Containerization**: Docker, Docker Compose
- **Version Control**: Git

## 🚀 Cách chạy dự án

### Yêu cầu hệ thống
- Docker
- Docker Compose

### Bước 1: Clone dự án
```bash
git clone <repository-url>
cd study_management
```

### Bước 2: Chạy với Docker
```bash
# Build và chạy các containers
docker-compose up --build

# Hoặc chạy ở background
docker-compose up -d --build
```

### Bước 3: Truy cập ứng dụng
- **Trang chủ**: http://localhost:8000
- **Admin panel**: http://localhost:8000/admin
  - Username: `admin`
  - Password: `admin123`

## 📁 Cấu trúc dự án

```
study_management/
├── core/                    # App chính
│   ├── models.py           # Models cho Courses, Assignments, Grades, Notes
│   ├── views.py            # Views và API endpoints
│   ├── urls.py             # URL routing
│   └── admin.py            # Admin interface
├── study_management/        # Django project settings
│   ├── settings.py         # Cấu hình Django
│   ├── urls.py             # URL routing chính
│   └── wsgi.py             # WSGI configuration
├── templates/              # HTML templates
│   └── core/
│       └── home.html       # Trang chủ
├── static/                 # Static files (CSS, JS, images)
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
└── README.md              # Tài liệu hướng dẫn
```

## 🔧 Các lệnh Docker hữu ích

```bash
# Chạy dự án
docker-compose up

# Chạy ở background
docker-compose up -d

# Dừng dự án
docker-compose down

# Xem logs
docker-compose logs

# Xem logs của service cụ thể
docker-compose logs web
docker-compose logs db

# Chạy lệnh Django trong container
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Truy cập PostgreSQL
docker-compose exec db psql -U postgres -d study_management
```

## 🐛 Xử lý lỗi thường gặp

### Lỗi kết nối database
```bash
# Kiểm tra container database có chạy không
docker-compose ps

# Restart database service
docker-compose restart db
```

### Lỗi port đã được sử dụng
```bash
# Kiểm tra port đang sử dụng
netstat -an | grep 8000

# Thay đổi port trong docker-compose.yml
ports:
  - "8001:8000"  # Thay đổi từ 8000 thành 8001
```

### Lỗi permissions
```bash
# Chạy với quyền admin (Windows)
docker-compose up --build

# Trên Linux/Mac
sudo docker-compose up --build
```

## 📝 API Endpoints

- `GET /api/courses/` - Danh sách khóa học
- `GET /api/assignments/` - Danh sách bài tập
- `GET /api/grades/` - Danh sách điểm số
- `GET /api/notes/` - Danh sách ghi chú

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

## 📞 Liên hệ

Nếu có câu hỏi hoặc góp ý, vui lòng tạo issue trên GitHub repository. 