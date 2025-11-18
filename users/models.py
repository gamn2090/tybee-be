# Custom user and password reset OTP models
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserManager(BaseUserManager):
	def create_user(self, email, password=None, **extra_fields):
		if not email:
			raise ValueError('Email must be set')
		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
	first_name = models.CharField(max_length=60)
	last_name = models.CharField(max_length=60)
	phone_number = models.CharField(max_length=20, blank=True, null=True)
	email = models.EmailField(unique=True)
	zipcode = models.CharField(max_length=10, blank=True, null=True)
	is_active = models.BooleanField(default=True)
	date_joined = models.DateTimeField(default=timezone.now)
	social_provider = models.CharField(max_length=20, choices=[('email','Email'),('google','Google'),('apple','Apple')], default='email')
	is_staff = models.BooleanField(default=False)
	is_superuser = models.BooleanField(default=False)
	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']
	objects = UserManager()
	def __str__(self):
		return self.email

class PasswordResetOTP(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	otp_code = models.CharField(max_length=10)
	expires_at = models.DateTimeField()
	is_used = models.BooleanField(default=False)
	def __str__(self):
		return f"OTP for {self.user.email}"

# Create your models here.
