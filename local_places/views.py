import requests
from django.conf import settings
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from .models import LocalPlace, CartMap, Category, Tag, Activity, LiveLikeALocal
from .serializers import (
    LocalPlaceSerializer,
    CartMapSerializer,
    CategorySerializer,
    TagSerializer,
    ActivitySerializer,
    LiveLikeALocalSerializer,
    RestaurantSerializer,
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


class CartMapViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CartMap.objects.all()
    serializer_class = CartMapSerializer
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


class LiveLikeALocalViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LiveLikeALocal.objects.all()
    serializer_class = LiveLikeALocalSerializer
    permission_classes = [permissions.IsAuthenticated]


class RestaurantListView(generics.ListAPIView):
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return LocalPlace.objects.all()
