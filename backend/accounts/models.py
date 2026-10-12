from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, mobile, name, email, **extra):
        if not mobile: raise ValueError("Mobile is required")
        user = self.model(mobile=mobile, name=name, email=self.normalize_email(email), **extra)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, mobile, name, email, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if not extra["is_staff"] or not extra["is_superuser"]: raise ValueError("Superuser must be staff and superuser")
        return self.create_user(mobile, name, email, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    objects = UserManager()
    USERNAME_FIELD = "mobile"
    REQUIRED_FIELDS = ["name", "email"]
    def __str__(self): return self.mobile

class OTPChallenge(models.Model):
    mobile = models.CharField(max_length=15, db_index=True)
    code_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"OTP for {self.mobile}"
