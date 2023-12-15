from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('your_footprint/', views.your_footprint, name='your_footprint'),
    path('your_footprint/add_footprint/', views.add_footprint, name='add_footprint'),
    path('your_footprint/add_footprint/travel', views.travel_co2, name='travel_co2'),
    path('your_footprint/add_footprint/food', views.food_co2, name='food_co2'),
    path(
        'your_footprint/add_footprint/food/save_food/',
        views.save_food, name='save_food'),
    path(
        'your_footprint/add_footprint/energy/',
        views.energy_co2, name='energy_co2'),
    path('delete_travel/<int:pk>/', views.travel_delete, name="travel_delete"),
    path('delete_food/<int:pk>/', views.food_delete, name="food_delete"),
    path('delete_energy/<int:pk>/', views.energy_delete, name="energy_delete"),
    path('profile/change_password/', views.change_password, name='change_password'),
    path('footprint_highscore/', views.footprint_highscore, name='footprint_highscore')
]
