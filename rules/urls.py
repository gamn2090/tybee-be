from rest_framework.routers import DefaultRouter
from .views import RuleViewSet

router = DefaultRouter()
router.register(r'', RuleViewSet)

urlpatterns = router.urls
