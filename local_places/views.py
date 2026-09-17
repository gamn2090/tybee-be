import requests
from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from .models import LocalPlace, CartMap, Category, Tag, Activity, LiveLikeALocal
from .search import parse_id_list, rank_places
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
    # A place is hidden if it's inactive itself, OR if its category was
    # turned off in Admin (places without a category are unaffected).
    queryset = LocalPlace.objects.filter(is_active=True).filter(
        Q(category__isnull=True) | Q(category__is_active=True)
    )
    serializer_class = LocalPlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        # Within a param: OR (any of the given ids). Across params: AND —
        # this mirrors the filtering the app currently does on-device.
        if ids := parse_id_list(params.get("categories")):
            queryset = queryset.filter(category_id__in=ids)
        if ids := parse_id_list(params.get("tags")):
            queryset = queryset.filter(tags__id__in=ids)
        if ids := parse_id_list(params.get("activities")):
            queryset = queryset.filter(activities__id__in=ids)
        if ids := parse_id_list(params.get("live_like_a_local")):
            queryset = queryset.filter(live_like_a_local__id__in=ids)

        # The tags/activities/live_like_a_local joins above can duplicate
        # rows (a place with 2 matching tags would otherwise appear twice).
        # Explicit ordering avoids Django's "unordered object list" warning
        # and keeps pagination stable across pages.
        queryset = queryset.distinct().order_by("name", "id")

        return queryset.select_related("category").prefetch_related(
            "tags", "activities", "live_like_a_local", "images", "operating_hours"
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        term = (request.query_params.get("search") or "").strip()
        did_you_mean = None
        if term:
            # Fuzzy-filters and ranks in Python (small catalog ~150 places) —
            # deliberately not DRF's SearchFilter, which does a plain SQL
            # icontains and would both miss typo matches and, since it runs
            # first, discard results that only match approximately.
            queryset, did_you_mean = rank_places(queryset, term)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["did_you_mean"] = did_you_mean
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data, "did_you_mean": did_you_mean})


class CartMapViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CartMap.objects.all()
    serializer_class = CartMapSerializer
    permission_classes = [permissions.IsAuthenticated]


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
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
    # Not paginated: the map screen consumes this as a single flat list of
    # pins, and existing published app versions call this URL as-is.
    pagination_class = None

    def get_queryset(self):
        queryset = (
            LocalPlace.objects.filter(is_active=True)
            .filter(Q(category__isnull=True) | Q(category__is_active=True))
            .select_related("category")
            .prefetch_related("images")
        )
        if ids := parse_id_list(self.request.query_params.get("categories")):
            queryset = queryset.filter(category_id__in=ids)
        return queryset
