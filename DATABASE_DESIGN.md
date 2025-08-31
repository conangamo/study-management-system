# Thiết Kế Cơ Sở Dữ Liệu - Hệ Thống Quản Lý Học Tập

## 🎯 **Tổng quan hệ thống**

Hệ thống quản lý học tập cho sinh viên với các chức năng chính:
- Quản lý khóa học và môn học
- Theo dõi bài tập và deadline
- Ghi chép điểm số và tiến độ
- Lưu trữ ghi chú cá nhân
- Hệ thống người dùng và phân quyền

## 📊 **Sơ đồ ERD (Entity Relationship Diagram) - Cải tiến**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     User        │    │     Course      │    │   Assignment    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ username        │    │ name            │    │ title           │
│ email           │    │ description     │    │ description     │
│ first_name      │    │ start_date      │    │ course (FK)     │
│ last_name       │    │ end_date        │    │ due_date        │
│ is_active       │    │ user (FK)       │    │ submission_date │
│ date_joined     │    │ created_at      │    │ status          │
│ last_login      │    │ updated_at      │    │ priority        │
└─────────────────┘    └─────────────────┘    │ category        │
         │                       │             │ created_at      │
         │                       │             │ updated_at      │
         │                       │             └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Grade       │              │
         │              ├─────────────────┤              │
         │              │ id (PK)         │              │
         │              │ course (FK)     │              │
         │              │ assignment (FK) │              │
         │              │ score           │              │
         │              │ max_score       │              │
         │              │ weight          │              │
         │              │ date            │              │
         │              │ comment         │              │
         │              │ created_at      │              │
         │              │ updated_at      │              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       │                       │
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Note        │
                    ├─────────────────┤
                    │ id (PK)         │
                    │ user (FK)       │
                    │ title           │
                    │ content         │
                    │ is_important    │
                    │ created_at      │
                    │ updated_at      │
                    └─────────────────┘
                                 │
                                 │
                    ┌─────────────────┐
                    │   Note_Tag      │
                    ├─────────────────┤
                    │ note_id (FK)    │
                    │ tag_id (FK)     │
                    └─────────────────┘
                                 │
                                 │
                    ┌─────────────────┐
                    │      Tag        │
                    ├─────────────────┤
                    │ id (PK)         │
                    │ name            │
                    │ color           │
                    │ created_at      │
                    └─────────────────┘
```

## 🗄️ **Chi tiết các bảng - Cải tiến**

### **1. Bảng User (Người dùng)**
```sql
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);
```

**Mô tả:**
- Lưu trữ thông tin người dùng (sinh viên, giảng viên, admin)
- Sử dụng Django User model mặc định
- Hỗ trợ phân quyền và authentication

### **2. Bảng Course (Khóa học)**
```sql
CREATE TABLE core_course (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Mô tả:**
- Quản lý các môn học/khóa học của sinh viên
- Mỗi khóa học thuộc về một người dùng
- Có thời gian bắt đầu và kết thúc
- Hỗ trợ mô tả chi tiết

### **3. Bảng Assignment (Bài tập) - Cải tiến**
```sql
CREATE TABLE core_assignment (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    course_id INTEGER REFERENCES core_course(id) ON DELETE CASCADE,
    due_date TIMESTAMP,
    submission_date TIMESTAMP NULL,  -- Thời điểm nộp bài
    status VARCHAR(20) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    category VARCHAR(50) DEFAULT 'individual',  -- Phân loại bài tập
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Mô tả:**
- Quản lý bài tập và deadline
- Liên kết với khóa học
- Trạng thái: pending, in_progress, completed, overdue
- Độ ưu tiên: low, medium, high
- Category: individual, group, exam, quiz, project
- Hỗ trợ theo dõi thời điểm nộp bài chính xác

### **4. Bảng Grade (Điểm số) - Cải tiến**
```sql
CREATE TABLE core_grade (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES core_course(id) ON DELETE CASCADE,
    assignment_id INTEGER REFERENCES core_assignment(id) ON DELETE SET NULL,
    score DECIMAL(5,2),
    max_score DECIMAL(5,2) DEFAULT 100.00,
    weight DECIMAL(3,2) DEFAULT 1.00,  -- Trọng số cho tính điểm TB
    date DATE,
    comment TEXT,  -- Ghi chú về điểm số
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Mô tả:**
- Lưu trữ điểm số cho từng bài tập hoặc khóa học
- Hỗ trợ điểm tối đa tùy chỉnh
- Trọng số để tính điểm trung bình có trọng số
- Comment để ghi chú về điểm số
- Liên kết với bài tập hoặc khóa học

### **5. Bảng Tag (Thẻ) - Mới**
```sql
CREATE TABLE core_tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',  -- Màu hex
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Mô tả:**
- Quản lý tags cho ghi chú
- Mỗi tag có màu sắc riêng
- Hỗ trợ tìm kiếm và phân loại

### **6. Bảng Note (Ghi chú) - Cải tiến**
```sql
CREATE TABLE core_note (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    title VARCHAR(200),
    content TEXT NOT NULL,
    is_important BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Mô tả:**
- Ghi chú cá nhân của sinh viên
- Quan hệ N:N với Tag thông qua bảng Note_Tag
- Có thể đánh dấu quan trọng
- Tìm kiếm và lọc theo tags

### **7. Bảng Note_Tag (Quan hệ N:N) - Mới**
```sql
CREATE TABLE core_note_tag (
    id SERIAL PRIMARY KEY,
    note_id INTEGER REFERENCES core_note(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES core_tag(id) ON DELETE CASCADE,
    UNIQUE(note_id, tag_id)
);
```

**Mô tả:**
- Quan hệ nhiều-nhiều giữa Note và Tag
- Hỗ trợ một ghi chú có nhiều tag
- Một tag có thể được sử dụng cho nhiều ghi chú

## 🔗 **Mối quan hệ (Relationships) - Cải tiến**

### **1. User ↔ Course (1:N)**
- Một người dùng có thể có nhiều khóa học
- Mỗi khóa học thuộc về một người dùng

### **2. Course ↔ Assignment (1:N)**
- Một khóa học có thể có nhiều bài tập
- Mỗi bài tập thuộc về một khóa học

### **3. Course ↔ Grade (1:N)**
- Một khóa học có thể có nhiều điểm số
- Mỗi điểm số thuộc về một khóa học

### **4. Assignment ↔ Grade (1:N)**
- Một bài tập có thể có nhiều điểm số
- Mỗi điểm số có thể liên kết với một bài tập

### **5. User ↔ Note (1:N)**
- Một người dùng có thể có nhiều ghi chú
- Mỗi ghi chú thuộc về một người dùng

### **6. Note ↔ Tag (N:N)**
- Một ghi chú có thể có nhiều tag
- Một tag có thể được sử dụng cho nhiều ghi chú

## 📋 **Constraints và Indexes - Cải tiến**

### **Constraints:**
```sql
-- Foreign Key Constraints
ALTER TABLE core_course ADD CONSTRAINT fk_course_user 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;

ALTER TABLE core_assignment ADD CONSTRAINT fk_assignment_course 
    FOREIGN KEY (course_id) REFERENCES core_course(id) ON DELETE CASCADE;

ALTER TABLE core_grade ADD CONSTRAINT fk_grade_course 
    FOREIGN KEY (course_id) REFERENCES core_course(id) ON DELETE CASCADE;

ALTER TABLE core_grade ADD CONSTRAINT fk_grade_assignment 
    FOREIGN KEY (assignment_id) REFERENCES core_assignment(id) ON DELETE SET NULL;

ALTER TABLE core_note ADD CONSTRAINT fk_note_user 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE;

ALTER TABLE core_note_tag ADD CONSTRAINT fk_note_tag_note 
    FOREIGN KEY (note_id) REFERENCES core_note(id) ON DELETE CASCADE;

ALTER TABLE core_note_tag ADD CONSTRAINT fk_note_tag_tag 
    FOREIGN KEY (tag_id) REFERENCES core_tag(id) ON DELETE CASCADE;

-- Check Constraints
ALTER TABLE core_assignment ADD CONSTRAINT chk_assignment_status 
    CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue'));

ALTER TABLE core_assignment ADD CONSTRAINT chk_assignment_priority 
    CHECK (priority IN ('low', 'medium', 'high'));

ALTER TABLE core_assignment ADD CONSTRAINT chk_assignment_category 
    CHECK (category IN ('individual', 'group', 'exam', 'quiz', 'project'));

ALTER TABLE core_grade ADD CONSTRAINT chk_grade_score 
    CHECK (score >= 0 AND score <= max_score);

ALTER TABLE core_grade ADD CONSTRAINT chk_grade_max_score 
    CHECK (max_score > 0);

ALTER TABLE core_grade ADD CONSTRAINT chk_grade_weight 
    CHECK (weight >= 0 AND weight <= 10);

-- Logic Constraints
ALTER TABLE core_assignment ADD CONSTRAINT chk_submission_date 
    CHECK (submission_date IS NULL OR submission_date <= due_date);
```

### **Indexes - Cải tiến:**
```sql
-- Performance Indexes
CREATE INDEX idx_course_user ON core_course(user_id);
CREATE INDEX idx_assignment_course ON core_assignment(course_id);
CREATE INDEX idx_assignment_due_date ON core_assignment(due_date);
CREATE INDEX idx_assignment_status ON core_assignment(status);
CREATE INDEX idx_assignment_category ON core_assignment(category);
CREATE INDEX idx_assignment_submission ON core_assignment(submission_date);
CREATE INDEX idx_grade_course ON core_grade(course_id);
CREATE INDEX idx_grade_assignment ON core_grade(assignment_id);
CREATE INDEX idx_note_user ON core_note(user_id);
CREATE INDEX idx_note_important ON core_note(is_important);
CREATE INDEX idx_note_created ON core_note(created_at);
CREATE INDEX idx_tag_name ON core_tag(name);
CREATE INDEX idx_note_tag_note ON core_note_tag(note_id);
CREATE INDEX idx_note_tag_tag ON core_note_tag(tag_id);

-- Full-text search cho tiếng Việt
CREATE INDEX idx_note_content_search ON core_note 
    USING GIN(to_tsvector('simple', content));
CREATE INDEX idx_note_title_search ON core_note 
    USING GIN(to_tsvector('simple', title));
```

## 🎯 **Tính năng đặc biệt - Cải tiến**

### **1. Deadline Tracking nâng cao**
- Tự động cập nhật trạng thái bài tập dựa trên due_date và submission_date
- Cảnh báo bài tập sắp đến hạn (3 ngày, 1 ngày, 1 giờ)
- Thống kê bài tập trễ hạn và đã nộp
- Phân loại bài tập theo category

### **2. Grade Analytics nâng cao**
- Tính điểm trung bình có trọng số theo khóa học
- Biểu đồ tiến độ học tập theo thời gian
- So sánh điểm với các bài tập trước
- Thống kê điểm theo category bài tập

### **3. Search và Filter nâng cao**
- Tìm kiếm ghi chú theo tags với màu sắc
- Lọc bài tập theo trạng thái, category, khóa học
- Sắp xếp theo deadline, điểm số, submission_date
- Full-text search cho tiếng Việt

### **4. Data Integrity nâng cao**
- CASCADE delete cho các mối quan hệ chính
- SET NULL cho grade khi assignment bị xóa
- Check constraints đảm bảo dữ liệu hợp lệ
- Logic constraints cho submission_date

### **5. Triggers và Functions - Mới**
```sql
-- Trigger tự động cập nhật status thành overdue
CREATE OR REPLACE FUNCTION update_assignment_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.due_date < CURRENT_TIMESTAMP AND NEW.status != 'completed' THEN
        NEW.status := 'overdue';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_assignment_status
    BEFORE UPDATE ON core_assignment
    FOR EACH ROW
    EXECUTE FUNCTION update_assignment_status();

-- Function tính điểm trung bình có trọng số
CREATE OR REPLACE FUNCTION calculate_weighted_average(course_id INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    total_weighted_score DECIMAL := 0;
    total_weight DECIMAL := 0;
    weighted_avg DECIMAL;
BEGIN
    SELECT 
        COALESCE(SUM(score * weight), 0),
        COALESCE(SUM(weight), 0)
    INTO total_weighted_score, total_weight
    FROM core_grade
    WHERE course_id = $1;
    
    IF total_weight > 0 THEN
        weighted_avg := total_weighted_score / total_weight;
    ELSE
        weighted_avg := 0;
    END IF;
    
    RETURN weighted_avg;
END;
$$ LANGUAGE plpgsql;
```

## 🚀 **Kế hoạch triển khai - Cải tiến**

### **Phase 1: Core Models**
1. Tạo Django models cho tất cả bảng (bao gồm Tag và Note_Tag)
2. Tạo migrations với constraints và indexes
3. Test relationships và constraints
4. Implement triggers và functions

### **Phase 2: Admin Interface**
1. Cấu hình Django Admin cho tất cả models
2. Tạo custom admin views cho analytics
3. Thêm filters và search nâng cao
4. Implement inline editing cho Note_Tag

### **Phase 3: API Development**
1. Tạo serializers cho DRF với nested relationships
2. Implement CRUD views với permissions
3. Thêm authentication và rate limiting
4. API endpoints cho analytics và search

### **Phase 4: Frontend Integration**
1. Tạo templates cho từng model với Bootstrap 5
2. Implement JavaScript cho dynamic features
3. Responsive design với color-coded tags
4. Real-time updates cho deadline tracking

### **Phase 5: Advanced Features**
1. Email notifications cho deadlines
2. Export data to PDF/Excel
3. Mobile-responsive design
4. Performance optimization

Bạn có muốn tôi bắt đầu tạo các Django models dựa trên thiết kế cải tiến này không? 