from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.utils.timezone import now
from django.core.validators import MinValueValidator


# Create your models here.

class GlobalCO2Level(models.Model):
    date = models.CharField("Date", max_length=11, null=False, blank=False)
    trend = models.FloatField("Trend", max_length=10000, null=False, blank=False)
    cycle = models.FloatField("Cycle", max_length=10000, null=False, blank=False)

    class Meta:
        verbose_name = "Global CO2 Level"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(default="profile_pics/default.png", upload_to="profile_pics")

    def __str__(self):
        return f"{self.user.username} profile"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.photo.path)
        if img.height > 200 or img.width > 200:
            output_size = (200, 200)
            img.thumbnail(output_size)
            img.save(self.photo.path)


class Transport(models.Model):
    name = models.CharField(max_length=100)
    api_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"


class TransportType(models.Model):
    name = models.CharField(max_length=100)
    transport = models.ForeignKey("Transport", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}"


class TravelCO2(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transport = models.ForeignKey("Transport", on_delete=models.CASCADE)
    transport_type = models.ForeignKey("TransportType", on_delete=models.CASCADE)
    distance = models.DecimalField(max_digits=10, decimal_places=2)
    co2_kg = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateField(default=now, blank=True, null=True)

    class Meta:
        verbose_name = "Travel CO2"

    def __str__(self):
        return f"{self.user} {self.transport_type} {self.date_created}"


class FoodCO2(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    name = models.CharField("Name", max_length=200)
    amount_kg = models.DecimalField("Amount, kg", max_digits=10, decimal_places=3,
                                    validators=[MinValueValidator(0.001)])
    co2_kg = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateField("Date created", default=now, blank=True, null=True)

    class Meta:
        verbose_name = "Food CO2"

    def __str__(self):
        return f"{self.user} {self.name} {self.date_created}"


class EnergyCO2(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField("Type", max_length=100)
    location = models.CharField("Location", max_length=200, null=False, blank=True, default="---")
    green_type = models.CharField("Green Energy Type", max_length=200, null=False, blank=True, default="---")
    amount_kwh = models.DecimalField("kWh amount", max_digits=10, decimal_places=2)
    co2_kg = models.DecimalField("CO2 Kg", max_digits=10, decimal_places=2)
    date_created = models.DateField(default=now)

    class Meta:
        verbose_name = "Energy CO2"

    def __str__(self):
        return f"{self.user} {self.type} {self.date_created}"


class Location(models.Model):
    name = models.CharField("Location name", max_length=200)

    def __str__(self):
        return f"{self.name}"


class EnergyType(models.Model):
    name = models.CharField("Energy type", max_length=200)

    def __str__(self):
        return f"{self.name}"
