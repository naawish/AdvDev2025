from django import forms
from .models import DutyRoster, Clinic
from users.models import CustomUser
import datetime
from django.utils import timezone

class ClinicCreateForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = ['name', 'location']

class RosterUpdateForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role=CustomUser.Role.DOCTOR))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}))

    class Meta:
        model = DutyRoster
        fields = ['doctor', 'clinic', 'date', 'shift']

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < datetime.date.today():
            raise forms.ValidationError("Cannot create roster entries for past dates.")
        if date and date.weekday() == 4: # Friday is 4
            raise forms.ValidationError("Clinic is closed on Fridays, cannot schedule duty.")
        return date

    # Add clean method to check for conflicts if not relying solely on DB constraint
    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        date = cleaned_data.get("date")
        shift = cleaned_data.get("shift")

        if doctor and date and shift:
            # Exclude current instance if editing existing entry (not applicable for this basic form)
            if DutyRoster.objects.filter(doctor=doctor, date=date, shift=shift).exists():
                 raise forms.ValidationError(f"Dr. {doctor.last_name} is already scheduled for this date and shift.")
        return cleaned_data