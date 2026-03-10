from rest_framework.routers import DefaultRouter
from .views import (
    LocalPlaceViewSet,
    StaticMapViewSet,
    CategoryViewSet,
    TagViewSet,
    ActivityViewSet,
    TipViewSet,
)

router = DefaultRouter()
router.register(r"places", LocalPlaceViewSet)
router.register(r"static-maps", StaticMapViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"tags", TagViewSet)
router.register(r"activities", ActivityViewSet)
router.register(r"tips", TipViewSet)

urlpatterns = router.urls
