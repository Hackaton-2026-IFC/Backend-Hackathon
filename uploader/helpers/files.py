import re

import magic
from PIL import Image as PillowImage

MAX_IMAGE_UPLOAD_SIZE = 20 * 1024 * 1024
MAX_VIDEO_UPLOAD_SIZE = 100 * 1024 * 1024

CONTENT_TYPE_PDF = "application/pdf"

CONTENT_TYPE_UNKNOWN = "application/octet-stream"

SVG_ROOT_PATTERN = re.compile(rb"\A\s*(?:<\?xml[^>]*>\s*)?<svg(?:\s|>)", re.IGNORECASE)


def _fallback_content_type(file):
    sample = file.read(8192)
    if sample.startswith(b"%PDF-"):
        return CONTENT_TYPE_PDF
    if SVG_ROOT_PATTERN.match(sample.lstrip(b"\xef\xbb\xbf")):
        return "image/svg+xml"
    if sample.startswith(b"FLV"):
        return "video/x-flv"
    if sample.startswith(b"\x1a\x45\xdf\xa3"):
        return "video/webm" if b"webm" in sample.lower() else "video/x-matroska"
    if sample.startswith(b"RIFF") and sample[8:12] == b"AVI ":
        return "video/x-msvideo"
    if sample.startswith(b"\x00\x00\x01\xba"):
        return "video/mpeg"
    if sample.startswith(bytes.fromhex("3026b2758e66cf11a6d900aa0062ce6c")):
        return "video/x-ms-wmv"
    if len(sample) >= 12 and sample[4:8] == b"ftyp":
        brand = sample[8:12]
        if brand == b"qt  ":
            return "video/quicktime"
        if brand.startswith(b"3gp"):
            return "video/3gpp"
        if brand.startswith(b"3g2"):
            return "video/3gpp2"
        if brand == b"M4V ":
            return "video/x-m4v"
        return "video/mp4"

    file.seek(0)
    try:
        with PillowImage.open(file) as image:
            return PillowImage.MIME.get(image.format, CONTENT_TYPE_UNKNOWN)
    except (OSError, PillowImage.DecompressionBombError):
        return CONTENT_TYPE_UNKNOWN


def get_content_type(file):
    try:
        if hasattr(file, "temporary_file_path"):
            content_type = magic.from_file(file.temporary_file_path(), mime=True)
        else:
            content_type = magic.from_buffer(file.read(2048), mime=True)
    except magic.MagicException:
        file.seek(0)
        content_type = _fallback_content_type(file)
    finally:
        if hasattr(file, "seek") and callable(file.seek):
            file.seek(0)

    return content_type
