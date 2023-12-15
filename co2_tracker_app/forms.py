from .models import Profile
from django import forms
from django.contrib.auth.models import User
from .models import FoodCO2
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo']


class DateInput(forms.DateInput):
    input_type = 'date'


class FoodCO2Form(forms.ModelForm):
    date_created = forms.DateField(
        validators=[MaxValueValidator(limit_value=datetime.date.today())],
        widget=DateInput()
    )

    class Meta:
        model = FoodCO2
        fields = ['name', 'amount_kg', 'date_created']
