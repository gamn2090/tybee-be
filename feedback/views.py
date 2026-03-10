from rest_framework import viewsets, permissions
from .models import UserFeedback, HelpRequest, ReportProblem, ContactUs
from .serializers import (
    UserFeedbackSerializer,
    HelpRequestSerializer,
    ReportProblemSerializer,
    ContactUsSerializer,
)


class UserFeedbackViewSet(viewsets.ModelViewSet):
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "put"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HelpRequestViewSet(viewsets.ModelViewSet):
    queryset = HelpRequest.objects.all()
    serializer_class = HelpRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "put"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReportProblemViewSet(viewsets.ModelViewSet):
    queryset = ReportProblem.objects.all()
    serializer_class = ReportProblemSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "put"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ContactUsViewSet(viewsets.ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "put"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
