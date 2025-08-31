from django.apps import AppConfig

 
class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core Application'
    
    def ready(self):
        # Import signals
        from . import signals
        # Import admin to register decorators
        from . import admin 