
from django.db import models

class Rule(models.Model):
	CATEGORY_CHOICES = [
		('golf_cart', 'Golf Cart'),
		('bicycle', 'Bicycle'),
	]
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
	title = models.CharField(max_length=255)
	description = models.TextField()
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	def __str__(self):
		return f"{self.category}: {self.title}"

# Create your models here.
