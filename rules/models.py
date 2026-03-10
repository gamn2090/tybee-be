
from django.db import models


class RuleCategory(models.Model):
	name = models.CharField(max_length=100, unique=True)
	slug = models.SlugField(max_length=100, unique=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name = 'Rule Category'
		verbose_name_plural = 'Rule Categories'
		ordering = ['name']

	def __str__(self):
		return self.name


class Rule(models.Model):
	category = models.ForeignKey(RuleCategory, on_delete=models.CASCADE, related_name='rules')
	title = models.CharField(max_length=255)
	description = models.TextField()
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.category.name}: {self.title}"

	class Meta:
		verbose_name = 'Rule'
		verbose_name_plural = 'Rules'
		ordering = ['category', 'title']
