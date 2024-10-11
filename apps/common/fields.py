# common/fields.py
import uuid
import base58
from django.db import models

class Base58UUIDField(models.CharField):
    """
    A custom Django field that generates a Base58 encoded UUID as the primary key.
    """
    description = "A Base58 encoded UUID field."

    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 22  # Length of Base58 encoded UUID
        kwargs['unique'] = True    # Ensure uniqueness
        kwargs['primary_key'] = kwargs.get('primary_key', False)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Automatically assign a Base58 encoded UUID when creating a new record.
        """
        value = getattr(model_instance, self.attname, None)
        if not value:
            # Generate a new UUID
            uuid_obj = uuid.uuid4()
            # Encode the UUID using Base58
            value = base58.b58encode(uuid_obj.bytes).decode('ascii')
            setattr(model_instance, self.attname, value)
        return value

    def deconstruct(self):
        """
        Ensure the field can be serialized by migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        # Remove kwargs that are enforced in __init__
        kwargs.pop('max_length', None)
        kwargs.pop('unique', None)
        return name, path, args, kwargs
