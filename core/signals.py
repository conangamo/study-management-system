"""
Django signals for core app
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Tự động tạo UserProfile khi tạo User mới"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Lưu UserProfile khi User được cập nhật"""
    if hasattr(instance, 'profile'):
        # Kiểm tra xem có phải chỉ cập nhật một số trường cụ thể không
        update_fields = kwargs.get('update_fields', [])
        
        # Nếu chỉ cập nhật is_active hoặc password, bỏ qua hoàn toàn
        if update_fields and all(field in ['is_active', 'password'] for field in update_fields):
            # Không làm gì cả - bỏ qua signal
            pass
        else:
            # Lưu bình thường
            try:
                instance.profile.save()
            except Exception:
                # Nếu có lỗi, tạo profile mới
                UserProfile.objects.get_or_create(user=instance) 