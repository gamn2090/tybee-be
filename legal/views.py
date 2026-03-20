from rest_framework import viewsets
from .models import LegalDocument
from .serializers import LegalDocumentSerializer

from rest_framework import viewsets, permissions
from .models import LegalDocument
from .serializers import LegalDocumentSerializer


class LegalDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LegalDocument.objects.all()
    serializer_class = LegalDocumentSerializer
    permission_classes = [permissions.AllowAny]
