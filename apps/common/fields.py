import uuid
import base58
from django.db import models
from django.conf import settings

class Base58UUIDv5Field(models.CharField):
    """
    A reusable custom Django field that generates a Base58 encoded UUIDv5
    based on a custom namespace (UUIDv4 from environment or settings)
    and a per-record UUIDv4.
    """
    description = "A Base58 encoded UUIDv5 field based on a custom namespace and per-record UUIDv4."

    def __init__(self, *args, **kwargs):
        # Set the max length for Base58 encoded UUIDs and ensure uniqueness
        kwargs['max_length'] = 22  # Base58-encoded UUID is 22 characters long
        kwargs['unique'] = True  # Ensure unique UUIDs
        if kwargs.get('primary_key', False):
            kwargs['primary_key'] = True  # Set as primary key if needed
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        """
        Automatically assign a Base58 encoded UUIDv5 when creating a new record.
        Combines the custom namespace (retrieved from environment/settings) and a per-record UUIDv4.
        """
        value = getattr(model_instance, self.attname, None)
        if not value:  # If no value is set, generate one
            # Retrieve the custom namespace from settings (or use a default)
            custom_namespace = settings.PLATFORM_NAMESPACE

            # Generate a UUIDv4 for this record
            record_uuid = uuid.uuid4()

            # Generate a UUIDv5 using the custom namespace and the record-specific UUIDv4 as the name
            uuid_obj = uuid.uuid5(custom_namespace, str(record_uuid))

            # Encode the UUIDv5 as Base58
            value = base58.b58encode(uuid_obj.bytes).decode('ascii')
            setattr(model_instance, self.attname, value)
        return value

    def deconstruct(self):
        """
        Ensure the field can be serialized by migrations.
        """
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop('max_length', None)
        kwargs.pop('unique', None)
        return name, path, args, kwargs