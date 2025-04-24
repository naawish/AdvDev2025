from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from clinics.models import Clinic, Room, Shift, DutyRoster # Import from clinics app
import uuid

class Service(models.Model):
    # Naming based on the requirement description categories
    class ServiceType(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Preventive Care'
        BASIC_RESTORATIVE = 'BASIC_RESTORATIVE', 'Basic Restorative'
        MAJOR_RESTORATIVE = 'MAJOR_RESTORATIVE', 'Major Restorative/Cosmetic'
        SPECIALTY = 'SPECIALTY', 'Specialty Services'
        SURGERY = 'SURGERY', 'Surgery' # Add surgery as a distinct type

    name = models.CharField(max_length=20, choices=ServiceType.choices, unique=True)
    description = models.TextField(blank=True, null=True)
    # Requires_surgery_room: Flag if service needs surgery room
    requires_surgery_room = models.BooleanField(default=False)

    def __str__(self):
        return self.get_name_display()

class ServicePrice(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='pricing')
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='pricing')
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('service', 'shift')

    def __str__(self):
        return f"{self.service.name} - {self.shift.name}: {self.price}"

class Appointment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = 'SCHEDULED', 'Scheduled'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        MISSED = 'MISSED', 'Missed' # Added state

    # Unique reference, UUID is good practice
    booking_reference = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='appointments_as_customer', limit_choices_to={'role': 'CUSTOMER'})
    # Doctor assigned based on DutyRoster for that clinic/date/shift
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='appointments_as_doctor', limit_choices_to={'role': 'DOCTOR'})
    clinic = models.ForeignKey(Clinic, on_delete=models.PROTECT)
    room = models.ForeignKey(Room, on_delete=models.PROTECT) # Assigned during booking based on availability
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    appointment_date = models.DateField()
    # Link to shift instead of specific time for simplicity based on requirements
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT)
    # Price is determined at booking time based on service and shift
    price = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Optional: Notes (e.g., reason for surgery booking)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['appointment_date', 'shift']
        # Constraints: Ensure room type matches service requirement?
        # Ensure doctor is actually on duty via DutyRoster? (Validation needed in view/form)

    def __str__(self):
        return f"Booking {self.booking_reference} for {self.customer.first_name} with Dr. {self.doctor.last_name}"