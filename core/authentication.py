from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailBackend(ModelBackend):
    """
    Custom authentication backend để đăng nhập bằng email hoặc username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Xác thực user bằng email hoặc username
        """
        if username is None:
            username = kwargs.get('username')
        if password is None:
            password = kwargs.get('password')
        
        if username is None or password is None:
            return None
        
        try:
            # Tìm user bằng email hoặc username
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        return None
    
    def get_user(self, user_id):
        """
        Lấy user theo ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None 