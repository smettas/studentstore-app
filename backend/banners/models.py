from django.db import models

class Banner(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="banners/%Y/%m/")
    target_url = models.CharField(max_length=500, blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["position", "id"]
    def __str__(self): return self.title
