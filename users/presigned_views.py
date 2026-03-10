"""
API view for generating presigned S3 upload URLs.
"""

from rest_framework import generics, permissions, serializers, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tybee_backend.upload_utils import (
    ALLOWED_CONTENT_TYPES,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    UPLOAD_FOLDERS,
    generate_presigned_upload_url,
)


class PresignedUploadUrlSerializer(serializers.Serializer):
    """Request body for generating a presigned upload URL."""

    file_name = serializers.CharField(
        max_length=255,
        help_text="Original file name including extension (e.g. photo.jpg).",
    )
    content_type = serializers.ChoiceField(
        choices=[(ct, ct) for ct in ALLOWED_CONTENT_TYPES],
        help_text="MIME type of the file to upload.",
    )
    upload_type = serializers.ChoiceField(
        choices=[(k, k) for k in UPLOAD_FOLDERS],
        help_text="Target upload category (profile_pic, local_place, static_map).",
    )


class PresignedUploadUrlResponseSerializer(serializers.Serializer):
    """Response body with presigned URL details."""

    upload_url = serializers.URLField(help_text="Presigned PUT URL for uploading.")
    file_url = serializers.URLField(help_text="Public URL of the file after upload.")
    key = serializers.CharField(help_text="S3 object key.")
    expires_in = serializers.IntegerField(help_text="URL expiry in seconds.")
    max_file_size = serializers.IntegerField(help_text="Maximum file size in bytes.")
    allowed_types = serializers.ListField(
        child=serializers.CharField(),
        help_text="List of allowed MIME types.",
    )


@extend_schema(tags=["Uploads"])
class GeneratePresignedUploadUrlView(generics.GenericAPIView):
    """
    Generate a presigned S3 PUT URL for direct browser upload.

    The frontend should:
    1. Call this endpoint to get the presigned URL.
    2. Use the ``upload_url`` to PUT the file directly to S3 with the
       ``Content-Type`` header matching the requested ``content_type``.
    3. Store the returned ``file_url`` or ``key`` to reference the uploaded file.

    **Constraints:**
    - Maximum file size: 5 MB
    - Allowed types: JPEG, PNG, WebP, GIF
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PresignedUploadUrlSerializer

    @extend_schema(
        request=PresignedUploadUrlSerializer,
        responses={200: PresignedUploadUrlResponseSerializer},
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_name = serializer.validated_data["file_name"]
        content_type = serializer.validated_data["content_type"]
        upload_type = serializer.validated_data["upload_type"]

        try:
            result = generate_presigned_upload_url(
                upload_type=upload_type,
                filename=file_name,
                content_type=content_type,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result["max_file_size"] = MAX_FILE_SIZE
        result["allowed_types"] = ALLOWED_CONTENT_TYPES

        return Response(result, status=status.HTTP_200_OK)
