from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class StaticMap(models.Model):
	title = models.CharField(max_length=255)
	image = models.ImageField(upload_to='static_maps/')
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title



class Category(models.Model):
	title = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	def __str__(self):
		return self.title

class Tag(models.Model):
	title = models.CharField(max_length=100, unique=True)
	def __str__(self):
		return self.title

class Activity(models.Model):
	title = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	tags = models.ManyToManyField(Tag, blank=True, related_name='activities')
	def __str__(self):
		return self.title

class Tip(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	tags = models.ManyToManyField(Tag, blank=True, related_name='tips')
	def __str__(self):
		return self.name

class LocalPlace(models.Model):
	name = models.CharField(max_length=255)
	image = models.ImageField(upload_to='local_places/', blank=True, null=True)
	image_2 = models.ImageField(upload_to='local_places/', blank=True, null=True)
	image_3 = models.ImageField(upload_to='local_places/', blank=True, null=True)
	image_4 = models.ImageField(upload_to='local_places/', blank=True, null=True)
	image_5 = models.ImageField(upload_to='local_places/', blank=True, null=True)
	highlight = models.CharField(max_length=255, blank=True)
	description = models.TextField()
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='places')
	tags = models.ManyToManyField(Tag, blank=True, related_name='places')
	activities = models.ManyToManyField(Activity, blank=True, related_name='places')
	tips = models.ManyToManyField(Tip, blank=True, related_name='places')
	latitude = models.FloatField()
	longitude = models.FloatField()
	popularity_score = models.DecimalField(
		max_digits=3,
		decimal_places=1,
		default=0.0,
		validators=[MinValueValidator(0), MaxValueValidator(5)]
	)
	review_count = models.IntegerField(default=0)
	google_places_id = models.CharField(max_length=255, blank=True)
	google_places_link = models.URLField(blank=True)
	web_domain = models.URLField(blank=True)
	contact_number = models.CharField(max_length=50, blank=True)
	address = models.TextField(blank=True)
	operating_hours = models.JSONField(
		blank=True,
		default=dict,
		help_text=(
			'Weekly schedule. Example: '
			'{"monday": {"open": "08:00", "close": "20:00", "is_closed": false}, '
			'"tuesday": {"open": "09:00", "close": "18:00", "is_closed": false}, '
			'"sunday": {"open": null, "close": null, "is_closed": true}}'
		)
	)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	def __str__(self):
		return self.name
