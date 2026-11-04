from django.db import models

class DeliverySettings(models.Model):
    """One admin-editable delivery policy. Estimated days are indicative, not courier guarantees."""
    enabled = models.BooleanField(default=True)
    cod_enabled = models.BooleanField(default=True)
    allow_all_india = models.BooleanField(default=False, help_text="Enable only when delivery arrangements exist nationwide.")
    estimated_min_days = models.PositiveSmallIntegerField(default=3)
    estimated_max_days = models.PositiveSmallIntegerField(default=7)
    notice = models.CharField(max_length=200, default="Indicative delivery estimate; not a guaranteed date.")
    def __str__(self): return "OJAS ONE delivery settings"

class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_serviceable = models.BooleanField(default=True)
    cod_available = models.BooleanField(default=True)
    min_days = models.PositiveSmallIntegerField(default=3)
    max_days = models.PositiveSmallIntegerField(default=7)
    def __str__(self): return self.pincode
