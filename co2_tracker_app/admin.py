from django.contrib import admin
from .models import (GlobalCO2Level, Profile, Transport, TravelCO2, TransportType, FoodCO2, EnergyCO2, EnergyType,
                     Location)


# Register your models here.

class AdminGlobalCO2Level(admin.ModelAdmin):
    list_display = ("date", "trend", "cycle")


class AdminTransportType(admin.ModelAdmin):
    list_display = ("name", "transport")


class AdminTravelCO2(admin.ModelAdmin):
    list_display = ("user", "transport_type", "date_created")


class AdminFoodCO2(admin.ModelAdmin):
    list_display = ("user", "name", "date_created")


class AdminEnergyCO2(admin.ModelAdmin):
    list_display = ("user", "type", "date_created")


admin.site.register(GlobalCO2Level, AdminGlobalCO2Level)
admin.site.register(Profile)
admin.site.register(Transport)
admin.site.register(TravelCO2, AdminTravelCO2)
admin.site.register(TransportType, AdminTransportType)
admin.site.register(FoodCO2, AdminFoodCO2)
admin.site.register(EnergyCO2, AdminEnergyCO2)
admin.site.register(EnergyType)
admin.site.register(Location)
