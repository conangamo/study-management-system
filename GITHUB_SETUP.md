# Hướng Dẫn Tạo Repository GitHub và Đẩy Mã Nguồn

## 🚀 Bước 1: Tạo Repository trên GitHub

### 1.1. Đăng nhập GitHub
- Truy cập https://github.com
- Đăng nhập vào tài khoản của bạn

### 1.2. Tạo Repository mới
1. Click nút **"New"** hoặc **"+"** ở góc trên bên phải
2. Chọn **"New repository"**
3. Điền thông tin:
   - **Repository name**: `study-management-system`
   - **Description**: `Hệ thống quản lý học tập cho sinh viên - Django + Docker`
   - **Visibility**: Public (hoặc Private tùy chọn)
   - **Initialize with**: Không chọn gì (để trống)
4. Click **"Create repository"**

## 🔧 Bước 2: Cấu hình Git trong dự án

### 2.1. Khởi tạo Git repository
```bash
# Đảm bảo đang ở thư mục dự án
cd F:\laptrinhPython\web_quan_ly_hoc_sinh\quanLy2

# Khởi tạo Git repository
git init
```

### 2.2. Cấu hình Git user (nếu chưa có)
```bash
# Cấu hình tên và email
git config user.name "Tên của bạn"
git config user.email "email@example.com"

# Hoặc cấu hình global
git config --global user.name "Tên của bạn"
git config --global user.email "email@example.com"
```

### 2.3. Thêm remote repository
```bash
# Thay thế YOUR_USERNAME bằng username GitHub của bạn
git remote add origin https://github.com/YOUR_USERNAME/study-management-system.git
```

## 📝 Bước 3: Commit và Push mã nguồn

### 3.1. Kiểm tra trạng thái
```bash
# Xem các file đã thay đổi
git status
```

### 3.2. Thêm tất cả file vào staging
```bash
# Thêm tất cả file (trừ những file trong .gitignore)
git add .
```

### 3.3. Commit đầu tiên
```bash
# Tạo commit đầu tiên
git commit -m "Initial commit: Django study management system

- Setup Django 4.2 with Django REST Framework
- PostgreSQL database configuration
- Docker and Docker Compose setup
- Bootstrap 5 frontend
- Basic project structure and templates
- Admin interface setup"
```

### 3.4. Push lên GitHub
```bash
# Push lên branch main
git push -u origin main
```

## 🔄 Bước 4: Các lệnh Git hữu ích

### 4.1. Kiểm tra trạng thái
```bash
# Xem trạng thái repository
git status

# Xem lịch sử commit
git log --oneline
```

### 4.2. Thêm thay đổi mới
```bash
# Thêm file cụ thể
git add filename.py

# Thêm tất cả thay đổi
git add .

# Commit với message
git commit -m "Mô tả thay đổi"

# Push lên GitHub
git push
```

### 4.3. Tạo branch mới
```bash
# Tạo và chuyển sang branch mới
git checkout -b feature/new-feature

# Push branch mới lên GitHub
git push -u origin feature/new-feature
```

### 4.4. Merge branch
```bash
# Chuyển về branch main
git checkout main

# Merge branch feature
git merge feature/new-feature

# Push lên GitHub
git push
```

## 📋 Bước 5: Kiểm tra Repository

### 5.1. Truy cập repository
- Mở trình duyệt và truy cập: `https://github.com/YOUR_USERNAME/study-management-system`
- Kiểm tra xem tất cả file đã được upload chưa

### 5.2. Cập nhật README.md
- Repository sẽ hiển thị nội dung từ file `README.md`
- Có thể chỉnh sửa trực tiếp trên GitHub hoặc local

## 🐛 Xử lý lỗi thường gặp

### Lỗi authentication
```bash
# Nếu gặp lỗi authentication, sử dụng Personal Access Token
# Hoặc cấu hình SSH key
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/study-management-system.git
```

### Lỗi push bị từ chối
```bash
# Pull changes trước khi push
git pull origin main

# Hoặc force push (cẩn thận!)
git push --force-with-lease
```

### Lỗi large file
```bash
# Nếu có file quá lớn, thêm vào .gitignore
echo "large_file.zip" >> .gitignore
git add .gitignore
git commit -m "Add large file to gitignore"
```

## 📁 Cấu trúc Repository sau khi push

```
study-management-system/
├── core/                    # Django app
├── study_management/        # Django project
├── templates/              # HTML templates
├── static/                 # Static files
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── README.md              # Project documentation
└── GITHUB_SETUP.md        # This file
```

## 🎯 Kết quả mong đợi

Sau khi hoàn thành, bạn sẽ có:
- ✅ Repository GitHub với mã nguồn đầy đủ
- ✅ README.md hiển thị trên GitHub
- ✅ Cấu trúc dự án rõ ràng
- ✅ Hướng dẫn chạy dự án với Docker
- ✅ Khả năng clone và chạy dự án trên máy khác

## 🔗 Liên kết hữu ích

- [GitHub Documentation](https://docs.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Django Documentation](https://docs.djangoproject.com/)
- [Docker Documentation](https://docs.docker.com/) 