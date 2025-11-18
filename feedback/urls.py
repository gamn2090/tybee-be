from rest_framework.routers import DefaultRouter
from .views import UserFeedbackViewSet

router = DefaultRouter()
router.register(r'', UserFeedbackViewSet)

urlpatterns = router.urls
