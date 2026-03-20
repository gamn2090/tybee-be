from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    LocalPlaceViewSet,
    CartMapViewSet,
    CategoryViewSet,
    TagViewSet,
    ActivityViewSet,
    LiveLikeALocalViewSet,
    RestaurantListView,
    RestaurantRetrieveView,
)

router = DefaultRouter()
router.register(r"places", LocalPlaceViewSet)
router.register(r"cart-maps", CartMapViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"tags", TagViewSet)
router.register(r"activities", ActivityViewSet)
router.register(r"live-like-a-local", LiveLikeALocalViewSet)


urlpatterns = router.urls + [
    path("restaurants/", RestaurantListView.as_view(), name="restaurant-list"),
    path("restaurants/<int:pk>/", RestaurantRetrieveView.as_view(), name="restaurant-detail"),
]
