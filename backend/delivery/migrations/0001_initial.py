from django.db import migrations, models
class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(name="DeliverySettings",fields=[("id",models.BigAutoField(primary_key=True,serialize=False)),("enabled",models.BooleanField(default=True)),("cod_enabled",models.BooleanField(default=True)),("allow_all_india",models.BooleanField(default=False,help_text="Enable only when delivery arrangements exist nationwide.")),("estimated_min_days",models.PositiveSmallIntegerField(default=3)),("estimated_max_days",models.PositiveSmallIntegerField(default=7)),("notice",models.CharField(default="Indicative delivery estimate; not a guaranteed date.",max_length=200))]),
        migrations.CreateModel(name="DeliveryPincode",fields=[("id",models.BigAutoField(primary_key=True,serialize=False)),("pincode",models.CharField(max_length=6,unique=True)),("city",models.CharField(blank=True,max_length=100)),("state",models.CharField(blank=True,max_length=100)),("is_serviceable",models.BooleanField(default=True)),("cod_available",models.BooleanField(default=True)),("min_days",models.PositiveSmallIntegerField(default=3)),("max_days",models.PositiveSmallIntegerField(default=7))])]
