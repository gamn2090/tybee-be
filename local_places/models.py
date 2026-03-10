from django.db import models
from django.core.validators import FileExtensionValidator


class StaticMap(models.Model):
	title = models.CharField(max_length=255)
	image = models.ImageField(
		upload_to='static_maps/',
		validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])],
	)
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title

	class Meta:
		verbose_name = 'Static Map'
		verbose_name_plural = 'Static Maps'



class Category(models.Model):
	title = models.CharField(max_length=100, unique=True)
	description = models.TextField(blank=True)
	def __str__(self):
		return self.title

	class Meta:
		verbose_name = 'Category'
		verbose_name_plural = 'Categories'

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

	class Meta:
		verbose_name = 'Activity'
		verbose_name_plural = 'Activities'

class Tip(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	tags = models.ManyToManyField(Tag, blank=True, related_name='tips')
	def __str__(self):
		return self.name

class LocalPlace(models.Model):
	name = models.CharField(max_length=255)
	image = models.ImageField(
		upload_to='local_places/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif'])],
	)
	highlight = models.CharField(max_length=255, blank=True)
	description = models.TextField()
	category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='places')
	tags = models.ManyToManyField(Tag, blank=True, related_name='places')
	activities = models.ManyToManyField(Activity, blank=True, related_name='places')
	tips = models.ManyToManyField(Tip, blank=True, related_name='places')
	latitude = models.FloatField()
	longitude = models.FloatField()
	popularity_score = models.IntegerField(default=1)
	google_places_id = models.CharField(max_length=255, blank=True)
	google_places_link = models.URLField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	def __str__(self):
		return self.name

	class Meta:
		verbose_name = 'Local Place'
		verbose_name_plural = 'Local Places'
