from django import forms
from .models import Appointment, Service
from clinics.models import Clinic, Shift
from django.utils import timezone
import datetime

class BookingForm(forms.Form): # Use forms.Form for complex validation/availability checks
    clinic = forms.ModelChoiceField(queryset=Clinic.objects.all(), empty_label="Select Clinic")
    service = forms.ModelChoiceField(queryset=Service.objects.exclude(name=Service.ServiceType.SURGERY), empty_label="Select Service") # Exclude surgery for regular booking
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
        help_text="Select a date (Clinic closed on Fridays)."
    )
    shift = forms.ModelChoiceField(queryset=Shift.objects.all(), empty_label="Select Shift")

    # Add __init__ if needed to filter choices dynamically based on user or other fields
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) # Pass user for context if needed
        super().__init__(*args, **kwargs)
        self.fields['appointment_date'].widget.attrs['min'] = str(datetime.date.today())


    def clean_appointment_date(self):
        date = self.cleaned_data.get('appointment_date')
        if date and date < datetime.date.today():
            raise forms.ValidationError("Cannot book appointments in the past.")
        if date and date.weekday() == 4: # Friday is 4
            raise forms.ValidationError("Sorry, the clinic is closed on Fridays.")
        return date

    # Add clean method to validate service against room type implicitly later if needed
    # Or handle the logic entirely in the view after basic validation

# Add SurgeryBookingForm later if needed (may need customer selection)