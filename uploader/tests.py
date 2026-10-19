from io import BytesIO
from unittest.mock import patch

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import storages
from django.test import TestCase
import magic
from PIL import Image as PillowImage

from uploader.helpers.files import get_content_type
from uploader.serializers.image import ImageUploadSerializer
from uploader.storage import MediaCloudinaryStorage


class ContentTypeFallbackTests(TestCase):
    def detect(self, filename, content):
        upload = SimpleUploadedFile(filename, content)
        with patch("uploader.helpers.files.magic.from_buffer", side_effect=magic.MagicException("No magic database")):
            content_type = get_content_type(upload)
        self.assertEqual(upload.read(), content)
        return content_type

    def test_fallback_detects_supported_media_and_documents(self):
        png = BytesIO()
        PillowImage.new("RGB", (1, 1)).save(png, format="PNG")
        samples = (
            ("image.png", png.getvalue(), "image/png"),
            ("image.svg", b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>', "image/svg+xml"),
            ("video.mp4", bytes.fromhex("000000186674797069736f6d") + b"\x00" * 32, "video/mp4"),
            ("document.pdf", b"%PDF-1.7\n", "application/pdf"),
        )

        for filename, content, expected_type in samples:
            with self.subTest(filename=filename):
                self.assertEqual(self.detect(filename, content), expected_type)


class ImageUploadSerializerTests(TestCase):
    def validate_file(self, content_type, size=1):
        upload = SimpleUploadedFile("upload.bin", b"x" * size)
        serializer = ImageUploadSerializer(data={"file": upload})
        with patch("uploader.serializers.image.get_content_type", return_value=content_type):
            is_valid = serializer.is_valid()
        return is_valid, serializer.errors

    def test_accepts_image_and_video_mime_types(self):
        for content_type in ("image/gif", "image/svg+xml", "video/mp4"):
            with self.subTest(content_type=content_type):
                is_valid, errors = self.validate_file(content_type)
                self.assertTrue(is_valid, errors)

    def test_rejects_non_media_files(self):
        is_valid, errors = self.validate_file("application/pdf")

        self.assertFalse(is_valid)
        self.assertIn("file", errors)

    def test_rejects_images_over_the_size_limit(self):
        with patch("uploader.serializers.image.MAX_IMAGE_UPLOAD_SIZE", 2 * 1024 * 1024):
            is_valid, errors = self.validate_file("image/png", size=(2 * 1024 * 1024) + 1)

        self.assertFalse(is_valid)
        self.assertIn("2 MB", str(errors["file"][0]))

    def test_rejects_videos_over_the_size_limit(self):
        with patch("uploader.serializers.image.MAX_VIDEO_UPLOAD_SIZE", 3 * 1024 * 1024):
            is_valid, errors = self.validate_file("video/mp4", size=(3 * 1024 * 1024) + 1)

        self.assertFalse(is_valid)
        self.assertIn("3 MB", str(errors["file"][0]))


class MediaCloudinaryStorageTests(TestCase):
    @patch("cloudinary_storage.storage.cloudinary.uploader.upload", return_value={"public_id": "videos/sample"})
    def test_uploads_video_files_as_cloudinary_videos(self, upload):
        storage = MediaCloudinaryStorage()

        storage._upload("videos/sample.mp4", BytesIO(b"video"))

        self.assertEqual(upload.call_args.kwargs["resource_type"], "video")

    def test_uploads_prefixed_video_files_as_cloudinary_videos(self):
        storage = MediaCloudinaryStorage()

        self.assertEqual(storage._get_resource_type("media/videos/sample.mp4"), "video")
        self.assertEqual(storage._get_resource_type("/media/videos/sample.mp4"), "video")

    @patch("cloudinary_storage.storage.cloudinary.uploader.upload", return_value={"public_id": "images/sample"})
    def test_keeps_image_files_as_cloudinary_images(self, upload):
        storage = MediaCloudinaryStorage()

        storage._upload("images/sample.png", BytesIO(b"image"))

        self.assertEqual(upload.call_args.kwargs["resource_type"], "image")

    def test_configured_default_storage_uses_video_resource_for_video_paths(self):
        if not settings.CLOUDINARY_URL:
            self.skipTest("Cloudinary is not configured.")

        storage = storages["default"]
        self.assertIsInstance(storage, MediaCloudinaryStorage)
        self.assertEqual(storage._get_resource_type("videos/sample.mp4"), "video")
