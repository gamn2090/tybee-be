from rest_framework import viewsets
from .models import Rule
from .serializers import RuleSerializer

from rest_framework import viewsets, permissions
from .models import Rule
from .serializers import RuleSerializer


class RuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [permissions.IsAuthenticated]
