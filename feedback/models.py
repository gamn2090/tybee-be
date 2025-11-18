
from django.db import models
from users.models import User

class UserFeedback(models.Model):
	FEEDBACK_TYPE_CHOICES = [
		('app_feedback', 'App Feedback'),
		('help_request', 'Help Request'),
		('report_problem', 'Report a Problem'),
		('contact_us', 'Contact Us'),
	]
	STATUS_CHOICES = [
		('new', 'New'),
		('reviewed', 'Reviewed'),
		('resolved', 'Resolved'),
	]
	user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
	feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
	admin_notes = models.TextField(blank=True, null=True)
	def __str__(self):
		return f"{self.feedback_type} - {self.user}"
