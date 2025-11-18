
from rest_framework import viewsets
from .models import UserFeedback
from .serializers import UserFeedbackSerializer

class UserFeedbackViewSet(viewsets.ModelViewSet):
	queryset = UserFeedback.objects.all()
	serializer_class = UserFeedbackSerializer
	http_method_names = ['get', 'post', 'delete', "put"]
