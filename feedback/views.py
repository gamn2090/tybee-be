from rest_framework import viewsets
from .models import UserFeedback, HelpRequest, ReportProblem, ContactUs
from .serializers import UserFeedbackSerializer, HelpRequestSerializer, ReportProblemSerializer, ContactUsSerializer

class UserFeedbackViewSet(viewsets.ModelViewSet):
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer
    http_method_names = ['get', 'post', 'delete', 'put']

class HelpRequestViewSet(viewsets.ModelViewSet):
    queryset = HelpRequest.objects.all()
    serializer_class = HelpRequestSerializer
    http_method_names = ['get', 'post', 'delete', 'put']

class ReportProblemViewSet(viewsets.ModelViewSet):
    queryset = ReportProblem.objects.all()
    serializer_class = ReportProblemSerializer
    http_method_names = ['get', 'post', 'delete', 'put']

class ContactUsViewSet(viewsets.ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    http_method_names = ['get', 'post', 'delete', 'put']
