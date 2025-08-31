"""
Validation functions
"""

def validate_student_id_if_provided(value):
    """Validator cho student_id - chỉ kiểm tra khi có giá trị"""
    if value and value.strip():
        # Không kiểm tra định dạng, chỉ đảm bảo không trống
        pass 