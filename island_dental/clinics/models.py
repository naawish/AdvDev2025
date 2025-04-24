from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings # To reference settings.AUTH_USER_MODEL
import datetime

class Clinic(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, unique=True) # e.g., 'Male', 'Kulhudhufushi', 'Addu City'

    def __str__(self):
        return f"{self.name} ({self.location})"

class Room(models.Model):
    class RoomType(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal Room'
        SURGERY = 'SURGERY', 'Surgery Room'

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=10) # e.g., 'Room 1', 'Surgery A'
    room_type = models.CharField(max_length=10, choices=RoomType.choices, default=RoomType.NORMAL)

    class Meta:
        unique_together = ('clinic', 'room_number') # Room numbers unique within a clinic

    def __str__(self):
        return f"{self.clinic.name} - {self.room_number} ({self.get_room_type_display()})"

class Shift(models.Model):
    class ShiftName(models.TextChoices):
        MORNING = 'MORNING', 'Morning (08:00-12:00 / S:09:00-12:00)'
        AFTERNOON = 'AFTERNOON', 'Afternoon (13:00-17:00 / S:14:00-17:00)'
        EVENING = 'EVENING', 'Evening (18:00-22:00 / S:14:00-17:00)' # Note surgery time overlap

    name = models.CharField(max_length=10, choices=ShiftName.choices, unique=True)
    # Store times for reference or logic, adjust as needed
    normal_start_time = models.TimeField()
    normal_end_time = models.TimeField()
    surgery_start_time = models.TimeField()
    surgery_end_time = models.TimeField()

    def __str__(self):
        return self.get_name_display()

class DutyRoster(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'DOCTOR'}, related_name='roster_entries')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='roster_entries')
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('doctor', 'date', 'shift') # Doctor can only work one shift at a time
        # Add constraint: Ensure date is not a Friday? Could be done here or in form validation.
        # constraints = [
        #     models.CheckConstraint(check=~models.Q(date__week_day=6), name='no_friday_work') # Django 4+
        # ]

    def __str__(self):
        return f"Dr. {self.doctor.last_name} at {self.clinic.location} on {self.date} ({self.shift.name})"

# Consider adding a DoctorProfile model if more doctor-specific fields needed
# class DoctorProfile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True, limit_choices_to={'role': 'DOCTOR'})
#     specialization = models.CharField(max_length=100, blank=True)
#     # other details