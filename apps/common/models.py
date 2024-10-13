from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

class AttachmentAbstract(models.Model):
    attachments = models.ManyToManyField("product_management.FileAttachment", blank=True)

    class Meta:
        abstract = True
