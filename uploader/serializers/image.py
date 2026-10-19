from rest_framework import serializers

from uploader.helpers.files import MAX_IMAGE_UPLOAD_SIZE, MAX_VIDEO_UPLOAD_SIZE, get_content_type
from uploader.models import Image


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["attachment_key", "file", "description", "uploaded_on", "url"]
        read_only_fields = ["attachment_key", "uploaded_on", "url"]
        extra_kwargs = {"file": {"write_only": True}}

    def validate_file(self, value):
        content_type = get_content_type(value)
        if content_type.startswith("image/"):
            max_size = MAX_IMAGE_UPLOAD_SIZE
            media_type = "image"
        elif content_type.startswith("video/"):
            max_size = MAX_VIDEO_UPLOAD_SIZE
            media_type = "video"
        else:
            raise serializers.ValidationError("Only valid image and video files are allowed.")

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
