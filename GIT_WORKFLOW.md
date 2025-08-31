# Quy Trình Làm Việc Với Git - Cập Nhật Code Mới

## 🔄 **Quy trình chuẩn khi có code mới**

### **Bước 1: Kiểm tra trạng thái hiện tại**
```bash
# Kiểm tra branch hiện tại và trạng thái
git status

# Xem lịch sử commit gần đây
git log --oneline -5
```

### **Bước 2: Tạo branch mới (khuyến nghị)**
```bash
# Tạo và chuyển sang branch mới cho tính năng
git checkout -b feature/new-feature

# Hoặc tạo branch cho bug fix
git checkout -b fix/bug-description
```

### **Bước 3: Thực hiện thay đổi code**
- Chỉnh sửa code trong dự án
- Test để đảm bảo hoạt động tốt

### **Bước 4: Kiểm tra thay đổi**
```bash
# Xem những file đã thay đổi
git status

# Xem chi tiết thay đổi
git diff

# Xem thay đổi của file cụ thể
git diff filename.py
```

### **Bước 5: Thêm file vào staging**
```bash
# Thêm file cụ thể
git add filename.py

# Hoặc thêm tất cả thay đổi
git add .

# Kiểm tra lại staging area
git status
```

### **Bước 6: Commit thay đổi**
```bash
# Commit với message mô tả rõ ràng
git commit -m "Add new feature: description of what was added

- Detail 1
- Detail 2
- Detail 3"
```

### **Bước 7: Push lên GitHub**
```bash
# Push branch mới lên GitHub
git push -u origin feature/new-feature

# Hoặc nếu đang ở branch main
git push origin main
```

## 🚀 **Quy trình nhanh (cho thay đổi nhỏ)**

### **Thay đổi trực tiếp trên main branch**
```bash
# 1. Kiểm tra trạng thái
git status

# 2. Thêm thay đổi
git add .

# 3. Commit
git commit -m "Quick fix: description"

# 4. Push
git push origin main
```

## 🔄 **Quy trình với Pull Request (khuyến nghị)**

### **Bước 1-6: Như trên**

### **Bước 7: Tạo Pull Request**
1. Push branch lên GitHub: `git push -u origin feature/new-feature`
2. Truy cập repository trên GitHub
3. Click "Compare & pull request"
4. Điền mô tả và tạo PR
5. Review và merge

### **Bước 8: Merge và cleanup**
```bash
# Chuyển về main branch
git checkout main

# Pull changes mới nhất
git pull origin main

# Xóa branch đã merge (tùy chọn)
git branch -d feature/new-feature
```

## 📋 **Các lệnh Git hữu ích**

### **Kiểm tra và theo dõi**
```bash
# Xem trạng thái
git status

# Xem lịch sử commit
git log --oneline

# Xem branch hiện tại
git branch

# Xem tất cả branch
git branch -a
```

### **Quản lý branch**
```bash
# Tạo branch mới
git checkout -b feature-name

# Chuyển branch
git checkout branch-name

# Xóa branch local
git branch -d branch-name

# Xóa branch remote
git push origin --delete branch-name
```

### **Undo và reset**
```bash
# Undo thay đổi chưa staged
git checkout -- filename.py

# Undo thay đổi đã staged
git reset HEAD filename.py

# Undo commit cuối (giữ thay đổi)
git reset --soft HEAD~1

# Undo commit cuối (xóa thay đổi)
git reset --hard HEAD~1
```

### **Sync với remote**
```bash
# Pull changes từ remote
git pull origin main

# Fetch changes (không merge)
git fetch origin

# Xem differences
git diff origin/main
```

## 🐛 **Xử lý lỗi thường gặp**

### **Lỗi merge conflict**
```bash
# 1. Pull changes trước
git pull origin main

# 2. Giải quyết conflict trong code editor
# 3. Add và commit
git add .
git commit -m "Resolve merge conflicts"
```

### **Lỗi push bị từ chối**
```bash
# Pull changes trước
git pull origin main

# Hoặc force push (cẩn thận!)
git push --force-with-lease
```

### **Lỗi authentication**
```bash
# Cấu hình Personal Access Token
git remote set-url origin https://YOUR_TOKEN@github.com/USERNAME/REPO.git
```

## 📝 **Best Practices**

### **Commit Messages**
```bash
# Format chuẩn
git commit -m "type(scope): description

- Detail 1
- Detail 2"

# Ví dụ:
git commit -m "feat(core): add course management models

- Add Course model with CRUD operations
- Add Assignment model with deadline tracking
- Add admin interface for course management"
```

### **Branch Naming**
- `feature/` - Tính năng mới
- `fix/` - Sửa lỗi
- `hotfix/` - Sửa lỗi khẩn cấp
- `docs/` - Cập nhật tài liệu

### **Regular Workflow**
1. **Pull trước khi làm việc**: `git pull origin main`
2. **Tạo branch cho tính năng mới**
3. **Commit thường xuyên** với message rõ ràng
4. **Test trước khi push**
5. **Review code trước khi merge**

## 🎯 **Ví dụ thực tế**

### **Thêm tính năng mới**
```bash
# 1. Tạo branch
git checkout -b feature/add-course-models

# 2. Thêm code mới
# ... chỉnh sửa models.py, views.py, etc.

# 3. Test
docker-compose up --build

# 4. Commit
git add .
git commit -m "feat(core): add course and assignment models

- Add Course model with name, description, dates
- Add Assignment model with title, due_date, status
- Add admin interface for both models
- Add basic CRUD views and templates"

# 5. Push
git push -u origin feature/add-course-models

# 6. Tạo Pull Request trên GitHub
```

### **Sửa lỗi nhỏ**
```bash
# 1. Sửa lỗi trực tiếp
# ... chỉnh sửa code

# 2. Commit và push
git add .
git commit -m "fix: resolve URL namespace warning"
git push origin main
```

## 📊 **Kiểm tra tiến độ**

```bash
# Xem commit history
git log --oneline --graph

# Xem thống kê
git log --stat

# Xem thay đổi của file cụ thể
git log -p filename.py
```

## 🔗 **Liên kết hữu ích**

- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/) 