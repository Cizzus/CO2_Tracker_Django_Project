# Generated by Django 4.2.7 on 2023-12-01 13:26

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('co2_tracker_app', '0004_alter_travelco2_options_travelco2_date_created'),
    ]

    operations = [
        migrations.AlterField(
            model_name='travelco2',
            name='date_created',
            field=models.DateField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]