# Generated by Django 4.2.7 on 2023-12-04 08:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('co2_tracker_app', '0007_delete_foodco2'),
    ]

    operations = [
        migrations.CreateModel(
            name='FoodCO2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(max_length=200)),
                ('category', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('amount_kg', models.DecimalField(decimal_places=2, max_digits=10)),
                ('co2_level', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_created', models.DateField(blank=True, default=django.utils.timezone.now, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Food CO2',
            },
        ),
    ]
