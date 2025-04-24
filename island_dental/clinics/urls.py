from django.urls import path
from . import views

app_name = 'clinics' # Namespace for URLs

urlpatterns = [
    path('roster/', views.manage_roster_view, name='manage_roster'),
    path('roster/update/', views.update_roster_view, name='update_roster'), # Example POST endpoint
    path('add/', views.add_clinic_view, name='add_clinic'),
    # Add more URLs for editing clinics, rooms etc.
]