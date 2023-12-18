from django.apps import AppConfig


class Co2TrackerAppConfig(AppConfig):
    name = "co2_tracker_app"

    def ready(self):
        from .signals import create_profile, save_profile
