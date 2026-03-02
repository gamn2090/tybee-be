# Custom user and password reset OTP models
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
	def create_user(self, phone_number, password=None, **extra_fields):
		if not phone_number:
			raise ValueError('The Phone Number must be set')
		user = self.model(phone_number=phone_number, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, phone_number, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(phone_number, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
	profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
	first_name = models.CharField(max_length=60)
	last_name = models.CharField(max_length=60)
	phone_number = models.CharField(max_length=20, unique=True)
	email = models.EmailField(blank=True, null=True)
	zipcode = models.CharField(max_length=10, blank=True, null=True)
	is_active = models.BooleanField(default=True)
	date_joined = models.DateTimeField(default=timezone.now)
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	USERNAME_FIELD = 'phone_number'
	REQUIRED_FIELDS = ['first_name', 'last_name']
	objects = UserManager()
	def __str__(self):
		return self.phone_number

class PasswordResetOTP(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	otp_code = models.CharField(max_length=10)
	expires_at = models.DateTimeField()
	is_used = models.BooleanField(default=False)
	def __str__(self):
		return f"OTP for {self.user.email}"

class signupOTP(models.Model):
	phone_number = models.CharField(max_length=20, blank=True, null=True)
	otp_code = models.CharField(max_length=10)
	expires_at = models.DateTimeField()
	is_used = models.BooleanField(default=False)
	def __str__(self):
		return f"OTP for {self.phone_number}"

