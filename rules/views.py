from rest_framework import viewsets, permissions
from .models import Rule
from .serializers import RuleSerializer


class RuleViewSet(viewsets.ReadOnlyModelViewSet):
    # Hide rules that were turned off directly, and rules whose parent
    # category was turned off — previously this returned everything and
    # relied entirely on the frontend to filter, so a rule/category toggled
    # off in Admin kept showing up in the API response.
    queryset = Rule.objects.filter(is_active=True, category__is_active=True)
    serializer_class = RuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
