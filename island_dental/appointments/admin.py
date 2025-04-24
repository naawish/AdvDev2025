from django.contrib import admin

# Register your models here.
# Example: appointments/admin.py
from django.contrib import admin
from .models import Service, ServicePrice, Appointment

admin.site.register(Service)
admin.site.register(ServicePrice)
admin.site.register(Appointment)