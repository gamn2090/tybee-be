from rest_framework.routers import DefaultRouter
from .views import UserFeedbackViewSet, HelpRequestViewSet, ReportProblemViewSet, ContactUsViewSet

router = DefaultRouter()
router.register(r'app-feedback', UserFeedbackViewSet)
router.register(r'help-request', HelpRequestViewSet)
router.register(r'report-problem', ReportProblemViewSet)
router.register(r'contact-us', ContactUsViewSet)

urlpatterns = router.urls
