import mimetypes
import uuid

from django.db import models

from uploader.helpers.files import get_content_type


def image_file_path(image, _) -> str:
    content_type = get_content_type(image.file)
    extension: str = mimetypes.guess_extension(content_type)
    if extension == ".jpe":
        extension = ".jpg"
    media_type = "videos" if content_type.startswith("video/") else "images"
    return f"{media_type}/{image.public_id}{extension or ''}"


class Image(models.Model):
    attachment_key = models.UUIDField(
        max_length=255,
        default=uuid.uuid4,
        unique=True,
        help_text=("Used to attach the image to another object. " "Cannot be used to retrieve the image file."),
    )
    public_id = models.UUIDField(
        max_length=255,
        default=uuid.uuid4,
        unique=True,
        help_text=(
            "Used to retrieve the image itself. "
            "Should not be readable until the image is attached to another object."
        ),
    )
    file = models.FileField(upload_to=image_file_path)
    description = models.CharField(max_length=255, blank=True)
    uploaded_on = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.description} - {self.attachment_key}"

    @property
    def url(self) -> str:
        return self.file.url  # pylint: disable=no-member
