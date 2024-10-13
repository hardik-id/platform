from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from .models import AuditEvent
import json

from .models import User


@receiver(pre_save, sender=User)
def pre_save_receiver(sender, instance, **kwargs):
    """
    The function checks if the password of a user instance has been changed and updates some fields
    accordingly.

    :param sender: The `sender` parameter in this context refers to the model class that is sending the
    signal. In this case, it is the `User` model
    :param instance: The `instance` parameter refers to the instance of the model that is being saved.
    In this case, it refers to an instance of the `User` model
    :return: In this code snippet, the `pre_save_receiver` function is returning `None` if the
    `old_user` is `None`.
    """
    old_user = User.objects.get_or_none(pk=instance.pk)
    if old_user is None:
        return

    if instance.password != old_user.password:
        instance.remaining_budget_for_failed_logins = 3
        instance.password_reset_required = False

def get_current_user():
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.auth.middleware import get_user
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        return get_user(None)
    except:
        return None

def should_audit_model(model):
    return (
        model._meta.app_label not in ['contenttypes', 'auth', 'sessions', 'admin'] and
        model is not AuditEvent
    )

def get_serializable_fields(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if isinstance(value, (str, int, float, bool, type(None))):
            data[field.name] = value
    return data

def log_change(sender, instance, created=False, deleted=False):
    if not should_audit_model(sender):
        return

    try:
        content_type = ContentType.objects.get_for_model(sender)
    except Exception:
        return

    action = 'CREATE' if created else 'DELETE' if deleted else 'UPDATE'

    try:
        AuditEvent.objects.create(
            user=get_current_user(),
            action=action,
            content_type=content_type,
            object_id=instance.pk,
            changes=json.dumps(get_serializable_fields(instance))
        )
    except Exception as e:
        print(f"Error creating AuditEvent entry: {e}")

# Signal handlers will be connected in apps.py after migrations