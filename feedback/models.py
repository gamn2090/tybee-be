
from django.db import models
from users.models import User


# App Feedback
class UserFeedback(models.Model):
	STATUS_CHOICES = [
		('new', 'New'),
		('reviewed', 'Reviewed'),
		('resolved', 'Resolved'),
	]
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
	admin_notes = models.TextField(blank=True, null=True)
	def __str__(self):
		return f"App Feedback - {self.user}"

# Help Request
class HelpRequest(models.Model):
	STATUS_CHOICES = [
		('new', 'New'),
		('reviewed', 'Reviewed'),
		('resolved', 'Resolved'),
	]
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
	admin_notes = models.TextField(blank=True, null=True)
	def __str__(self):
		return f"Help Request - {self.user}"

# Report a Problem
class ReportProblem(models.Model):
	STATUS_CHOICES = [
		('new', 'New'),
		('reviewed', 'Reviewed'),
		('resolved', 'Resolved'),
	]
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
	admin_notes = models.TextField(blank=True, null=True)
	def __str__(self):
		return f"Report Problem - {self.user}"

# Contact Us
class ContactUs(models.Model):
	STATUS_CHOICES = [
		('new', 'New'),
		('reviewed', 'Reviewed'),
		('resolved', 'Resolved'),
	]
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
	admin_notes = models.TextField(blank=True, null=True)
	def __str__(self):
		return f"Contact Us - {self.user}"
