from django.apps import AppConfig
from django.db.models.signals import post_migrate

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.security'

    def ready(self):
        post_migrate.connect(self.post_migrate_handler, sender=self)

    def post_migrate_handler(self, sender, **kwargs):
        from django.db.models.signals import post_save, post_delete
        from .signals import log_change, should_audit_model
        
        for model in self.apps.get_models():
            if should_audit_model(model):
                post_save.connect(
                    lambda sender, instance, created, **kwargs: log_change(sender, instance, created),
                    sender=model
                )
                post_delete.connect(
                    lambda sender, instance, **kwargs: log_change(sender, instance, deleted=True),
                    sender=model
                )
        
        print("AuditEvent signals connected successfully.")