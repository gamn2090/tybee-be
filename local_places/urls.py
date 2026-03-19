from rest_framework.routers import DefaultRouter
from .views import (
    LocalPlaceViewSet,
    CartMapViewSet,
    CategoryViewSet,
    TagViewSet,
    ActivityViewSet,
    LiveLikeALocalViewSet,
)

router = DefaultRouter()
router.register(r"places", LocalPlaceViewSet)
router.register(r"cart-maps", CartMapViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"tags", TagViewSet)
router.register(r"activities", ActivityViewSet)
router.register(r"live-like-a-local", LiveLikeALocalViewSet)

urlpatterns = router.urls
