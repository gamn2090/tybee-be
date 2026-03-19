from django.db import models
from django_ckeditor_5.fields import CKEditor5Field


class LegalDocument(models.Model):
    TITLE_CHOICES = [
        ("privacy_policy", "Privacy Policy"),
        ("terms_of_service", "Terms of Service"),
    ]
    title = models.CharField(max_length=32, choices=TITLE_CHOICES, unique=True)
    content = CKEditor5Field("Content", config_name="extends")
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_title_display()


# Create your models here.
