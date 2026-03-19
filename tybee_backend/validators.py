from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_image_size(value):
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError("File size cannot exceed 5MB.")


# Reusable extension validator
validate_image_extension = FileExtensionValidator(
    allowed_extensions=["jpg", "jpeg", "png", "webp", "heic", "heif"]
)

validate_pdf_extension = FileExtensionValidator(allowed_extensions=["pdf"])
