from rest_framework import serializers

from uploader.helpers.files import MAX_IMAGE_UPLOAD_SIZE, MAX_VIDEO_UPLOAD_SIZE, get_content_type
from uploader.models import Image


ALLOWED_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/avif',
}
ALLOWED_VIDEO_TYPES = {
    'video/mp4',
    'video/webm',
    'video/quicktime',
}


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["attachment_key", "file", "description", "uploaded_on", "url"]
        read_only_fields = ["attachment_key", "uploaded_on", "url"]
        extra_kwargs = {"file": {"write_only": True}}

    def validate_file(self, value):
        content_type = get_content_type(value)
        if content_type in ALLOWED_IMAGE_TYPES:
            max_size = MAX_IMAGE_UPLOAD_SIZE
            media_type = "image"
        elif content_type in ALLOWED_VIDEO_TYPES:
            max_size = MAX_VIDEO_UPLOAD_SIZE
            media_type = "video"
        else:
            raise serializers.ValidationError("Only approved image and video formats are allowed.")

        if value.size > max_size:
            max_size_mb = max_size // (1024 * 1024)
            raise serializers.ValidationError(f"The {media_type} file must be at most {max_size_mb} MB.")

        return value


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["url", "description", "uploaded_on"]
        read_only_fields = ["url", "attachment_key", "uploaded_on"]

    def create(self, validated_data):
        raise NotImplementedError("Use ImageUploadSerializer to create images.")
