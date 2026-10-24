from rest_framework import mixins, parsers, viewsets
from rest_framework.permissions import IsAuthenticated

from uploader.models import Document, Image
from uploader.serializers import DocumentUploadSerializer, ImageUploadSerializer


class CreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Uploads são somente criação; arquivos não podem ser enumerados globalmente."""
    permission_classes = [IsAuthenticated]


class DocumentUploadViewSet(CreateViewSet):
    queryset = Document.objects.all()  # pylint: disable=no-member
    serializer_class = DocumentUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]


class ImageUploadViewSet(CreateViewSet):
    queryset = Image.objects.all()  # pylint: disable=no-member
    serializer_class = ImageUploadSerializer
    parser_classes = [parsers.FormParser, parsers.MultiPartParser]
