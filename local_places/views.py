from rest_framework import viewsets, permissions
from .models import LocalPlace, StaticMap, Category, Tag, Activity, Tip
from .serializers import (
    LocalPlaceSerializer,
    StaticMapSerializer,
    CategorySerializer,
    TagSerializer,
    ActivitySerializer,
    TipSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["list", "retrieve"]:
            return True
        return request.user and request.user.is_staff


class LocalPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LocalPlace.objects.all()
    serializer_class = LocalPlaceSerializer
    permission_classes = [permissions.IsAuthenticated]


class StaticMapViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StaticMap.objects.all()
    serializer_class = StaticMapSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]


class TipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tip.objects.all()
    serializer_class = TipSerializer
    permission_classes = [permissions.IsAuthenticated]
