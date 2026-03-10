"""
Centralized S3 presigned URL utilities for file uploads.

Provides helpers to generate presigned PUT URLs for direct browser-to-S3
uploads, along with validation constants for file size and type.
"""

import uuid
import os

import boto3
from botocore.config import Config
from django.conf import settings

# ── Constants ────────────────────────────────────────────────────────────────

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
]

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

# Maps upload_type → S3 folder prefix
UPLOAD_FOLDERS = {
    "profile_pic": "profile_pics",
    "local_place": "local_places",
    "static_map": "static_maps",
}

PRESIGNED_URL_EXPIRY = 300  # 5 minutes


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_s3_client():
    """Return a boto3 S3 client configured from Django settings."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(signature_version="s3v4"),
    )


def validate_file_extension(filename: str) -> str:
    """
    Validate that *filename* has an allowed image extension.

    Returns the lowercase extension (without dot) on success.
    Raises ``ValueError`` with a user-friendly message on failure.
    """
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"File type '.{ext}' is not allowed. "
            f"Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )
    return ext


def validate_content_type(content_type: str) -> str:
    """
    Validate that *content_type* is an allowed MIME type.

    Returns the content type on success.
    Raises ``ValueError`` with a user-friendly message on failure.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(
            f"Content type '{content_type}' is not allowed. "
            f"Accepted types: {', '.join(ALLOWED_CONTENT_TYPES)}."
        )
    return content_type


def generate_presigned_upload_url(
    upload_type: str,
    filename: str,
    content_type: str,
) -> dict:
    """
    Generate a presigned S3 PUT URL for direct browser upload.

    Parameters
    ----------
    upload_type : str
        One of the keys in ``UPLOAD_FOLDERS`` (e.g. ``"profile_pic"``).
    filename : str
        Original file name from the client (used to extract the extension).
    content_type : str
        MIME type the client will send (e.g. ``"image/jpeg"``).

    Returns
    -------
    dict
        ``upload_url``  – presigned PUT URL the client should use.
        ``file_url``    – public URL of the object after upload.
        ``key``         – the S3 object key.
        ``expires_in``  – seconds until the presigned URL expires.

    Raises
    ------
    ValueError
        If ``upload_type``, extension, or content type is invalid.
    """
    if upload_type not in UPLOAD_FOLDERS:
        raise ValueError(
            f"Invalid upload_type '{upload_type}'. "
            f"Must be one of: {', '.join(UPLOAD_FOLDERS.keys())}."
        )

    ext = validate_file_extension(filename)
    validate_content_type(content_type)

    folder = UPLOAD_FOLDERS[upload_type]
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    key = f"{folder}/{unique_name}"

    s3_client = _get_s3_client()
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )

    # Build the public file URL
    domain = f"{bucket}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
    file_url = f"https://{domain}/{key}"

    return {
        "upload_url": upload_url,
        "file_url": file_url,
        "key": key,
        "expires_in": PRESIGNED_URL_EXPIRY,
    }
