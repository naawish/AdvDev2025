from django.contrib import admin

# Register your models here.
# Example: clinics/admin.py
from django.contrib import admin
from .models import Clinic, Room, Shift, DutyRoster

admin.site.register(Clinic)
admin.site.register(Room)
admin.site.register(Shift)
admin.site.register(DutyRoster)