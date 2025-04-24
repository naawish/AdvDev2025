from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.decorators import role_required # Use the same decorator
from .models import DutyRoster, Clinic
from .forms import RosterUpdateForm, ClinicCreateForm # Need to create these forms
from django.contrib import messages

@login_required
@role_required(['ADMIN', 'MANAGER'])
def manage_roster_view(request):
    # Display current/future roster, maybe with filters
    roster_entries = DutyRoster.objects.filter(date__gte=timezone.now().date()).order_by('date', 'clinic', 'shift')
    # Add form for adding/updating entries? Or link to separate update view
    form = RosterUpdateForm() # Form to add new roster entry
    return render(request, 'clinics/manage_roster.html', {'roster_entries': roster_entries, 'form': form})

@login_required
@role_required(['ADMIN', 'MANAGER'])
def update_roster_view(request):
     # This would typically handle POST requests from manage_roster_view form
    if request.method == 'POST':
        form = RosterUpdateForm(request.POST)
        if form.is_valid():
            # Check for conflicts (doctor already rostered for that date/shift)
            # Use unique_together in model or check here
            try:
                form.save()
                messages.success(request, "Roster entry added successfully.")
            except IntegrityError: # Handle unique constraint violation
                 messages.error(request, "This doctor is already scheduled for this date and shift.")
            except Exception as e:
                 messages.error(request, f"An error occurred: {e}")

        else:
            # Pass form errors back via messages framework or re-render manage_roster with errors
             for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        return redirect('clinics:manage_roster')
    else:
         # Redirect GET requests back
        return redirect('clinics:manage_roster')


@login_required
@role_required(['MANAGER']) # Only Managers can add clinics
def add_clinic_view(request):
    if request.method == 'POST':
        form = ClinicCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Clinic '{form.cleaned_data['name']}' added successfully.")
            # Redirect to a clinic list view or dashboard
            return redirect('appointments:home') # Placeholder redirect
    else:
        form = ClinicCreateForm()
    return render(request, 'clinics/add_clinic.html', {'form': form})