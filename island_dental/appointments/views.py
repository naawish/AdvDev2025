from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, F, Q
from django.utils import timezone
import datetime
from .models import Appointment, Service, ServicePrice
from clinics.models import Clinic, Room, DutyRoster, Shift
from .forms import BookingForm # Need to create this form
from users.decorators import role_required # Custom decorator for role checks

@login_required
def home_view(request):
    # Simple dashboard based on role
    if request.user.role == 'CUSTOMER':
        return redirect('appointments:my_bookings')
    elif request.user.role in ['ADMIN', 'MANAGER', 'ADMIN_OFFICER']:
         # Show links relevant to staff roles
        return render(request, 'appointments/staff_dashboard.html')
    elif request.user.role == 'DOCTOR':
         # Show doctor's schedule
        today = timezone.now().date()
        roster_entries = DutyRoster.objects.filter(doctor=request.user, date__gte=today).order_by('date', 'shift')
        appointments = Appointment.objects.filter(doctor=request.user, appointment_date__gte=today, status='SCHEDULED').order_by('appointment_date', 'shift')
        return render(request, 'appointments/doctor_dashboard.html', {'roster': roster_entries, 'appointments': appointments})
    else:
         return render(request, 'appointments/home.html') # Fallback

@login_required
def book_appointment_view(request):
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            # Logic to create appointment
            # 1. Get data: clinic, service, date, shift
            clinic = form.cleaned_data['clinic']
            service = form.cleaned_data['service']
            date = form.cleaned_data['appointment_date']
            shift = form.cleaned_data['shift']

            # 2. Re-verify availability (doctor & room) - crucial!
            # Get available doctors on duty for this slot
            available_doctors = DutyRoster.objects.filter(
                clinic=clinic, date=date, shift=shift
            ).values_list('doctor', flat=True)

            if not available_doctors:
                form.add_error(None, "No doctors available for the selected slot.")
                return render(request, 'appointments/booking_form.html', {'form': form})

            # Determine required room type
            room_type_needed = Room.RoomType.SURGERY if service.requires_surgery_room else Room.RoomType.NORMAL

            # Find available room and doctor (simplistic: assign first available)
            assigned_doctor_id = None
            assigned_room = None

            # Count existing appointments for each room of the required type in this slot
            booked_rooms = Appointment.objects.filter(
                clinic=clinic, appointment_date=date, shift=shift, status='SCHEDULED'
            ).values_list('room_id', flat=True)

            # Find rooms of the required type in the clinic
            potential_rooms = Room.objects.filter(clinic=clinic, room_type=room_type_needed)

            for room in potential_rooms:
                if room.id not in booked_rooms:
                    # Check capacity constraints
                    if room.room_type == Room.RoomType.NORMAL:
                        appointments_in_room = Appointment.objects.filter(room=room, appointment_date=date, shift=shift, status='SCHEDULED').count()
                        if appointments_in_room < 10: # Capacity per shift/room
                            assigned_room = room
                            break
                    else: # Surgery room (assuming 1 surgery per slot)
                        assigned_room = room
                        break
                # else: If room is booked, check capacity for normal rooms
                elif room.room_type == Room.RoomType.NORMAL:
                     appointments_in_room = Appointment.objects.filter(room=room, appointment_date=date, shift=shift, status='SCHEDULED').count()
                     if appointments_in_room < 10:
                         assigned_room = room
                         break


            if not assigned_room:
                 form.add_error(None, f"No {room_type_needed.label} rooms available for the selected slot.")
                 return render(request, 'appointments/booking_form.html', {'form': form})

            # Find a doctor who isn't already booked in this exact slot/room (though usually 1 doc per room/shift)
            # Simplistic: Assign the first available doctor from the roster for this slot
            # A more complex system might distribute load or allow patient preference
            booked_doctors_in_slot = Appointment.objects.filter(
                clinic=clinic, appointment_date=date, shift=shift, status='SCHEDULED'
            ).values_list('doctor_id', flat=True)

            for doc_id in available_doctors:
                if doc_id not in booked_doctors_in_slot:
                     assigned_doctor_id = doc_id
                     break # Assign first available doctor

            if not assigned_doctor_id:
                # This case implies all rostered doctors are somehow booked, maybe capacity issue
                 form.add_error(None, "Could not assign a doctor. Please try another slot.")
                 return render(request, 'appointments/booking_form.html', {'form': form})


            # 3. Calculate Price
            try:
                service_price = ServicePrice.objects.get(service=service, shift=shift)
                price = service_price.price
            except ServicePrice.DoesNotExist:
                # Handle error - pricing not set up
                 form.add_error(None, "Pricing for this service/shift is not available.")
                 return render(request, 'appointments/booking_form.html', {'form': form})

            # 4. Create Appointment
            appointment = Appointment.objects.create(
                customer=request.user,
                doctor_id=assigned_doctor_id,
                clinic=clinic,
                room=assigned_room,
                service=service,
                appointment_date=date,
                shift=shift,
                price=price,
                status=Appointment.Status.SCHEDULED
            )

            # 5. Redirect to confirmation/receipt page
            return redirect('appointments:booking_detail', booking_reference=appointment.booking_reference)
        else:
             # Form is invalid, render again with errors
            pass
    else: # GET request
        form = BookingForm(user=request.user)

    return render(request, 'appointments/booking_form.html', {'form': form})


# AJAX view to check doctor/room availability
def ajax_check_availability(request):
    clinic_id = request.GET.get('clinic')
    service_id = request.GET.get('service')
    date_str = request.GET.get('date')
    shift_id = request.GET.get('shift')

    if not all([clinic_id, service_id, date_str, shift_id]):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        clinic = Clinic.objects.get(id=clinic_id)
        service = Service.objects.get(id=service_id)
        shift = Shift.objects.get(id=shift_id)

        # --- Availability Logic ---
        # Check if date is Friday
        if date.weekday() == 4: # Friday is 4 (Monday is 0)
           return JsonResponse({'available': False, 'message': 'Clinic closed on Fridays.'})

        # Check doctors on duty
        doctors_on_duty = DutyRoster.objects.filter(
            clinic=clinic, date=date, shift=shift
        ).count()

        if doctors_on_duty == 0:
            return JsonResponse({'available': False, 'message': 'No doctors scheduled for this slot.'})

        # Check room availability and capacity
        room_type_needed = Room.RoomType.SURGERY if service.requires_surgery_room else Room.RoomType.NORMAL
        potential_rooms = Room.objects.filter(clinic=clinic, room_type=room_type_needed)

        room_available = False
        for room in potential_rooms:
            booked_count = Appointment.objects.filter(
                room=room, appointment_date=date, shift=shift, status='SCHEDULED'
            ).count()

            if room.room_type == Room.RoomType.NORMAL:
                if booked_count < 10: # Normal room capacity
                    room_available = True
                    break
            else: # Surgery room
                 if booked_count < 1: # Assume 1 surgery per room per shift slot
                    room_available = True
                    break

        if not room_available:
             return JsonResponse({'available': False, 'message': f'No {room_type_needed.label} rooms available or room capacity reached.'})

        # Calculate price
        try:
            service_price = ServicePrice.objects.get(service=service, shift=shift)
            price = str(service_price.price) # Convert Decimal to string for JSON
        except ServicePrice.DoesNotExist:
            price = "N/A"
        except Exception as e:
            price = f"Error: {e}"


        # If checks pass, slot is potentially available (final check during POST)
        return JsonResponse({'available': True, 'price': price, 'message': 'Slot appears available.'})

    except (Clinic.DoesNotExist, Service.DoesNotExist, Shift.DoesNotExist):
         return JsonResponse({'error': 'Invalid input data'}, status=400)
    except ValueError:
         return JsonResponse({'error': 'Invalid date format'}, status=400)


@login_required
def my_bookings_view(request):
    if request.user.role != 'CUSTOMER':
        # Maybe redirect staff to a different view or show error
        return HttpResponseForbidden("Access denied.")
    appointments = Appointment.objects.filter(customer=request.user).order_by('-appointment_date', 'shift')
    return render(request, 'appointments/my_bookings.html', {'appointments': appointments})

@login_required
def booking_detail_view(request, booking_reference):
    appointment = get_object_or_404(Appointment, booking_reference=booking_reference)
    # Security check: Only customer or relevant staff can view
    if not (request.user == appointment.customer or request.user.role in ['ADMIN', 'MANAGER', 'ADMIN_OFFICER', 'DOCTOR']):
         return HttpResponseForbidden("Access denied.")
    return render(request, 'appointments/booking_detail.html', {'appointment': appointment})

@login_required
@require_POST # Ensure cancellation happens via POST to prevent accidental GET requests
def cancel_booking_view(request, booking_reference):
    appointment = get_object_or_404(Appointment, booking_reference=booking_reference)
    # Only customer or specific staff can cancel
    can_cancel = (request.user == appointment.customer) or \
                 (request.user.role in ['ADMIN', 'MANAGER', 'ADMIN_OFFICER'] and service.requires_surgery_room) # Staff cancel surgery only

    if not can_cancel:
        return HttpResponseForbidden("You do not have permission to cancel this booking.")

    # Check if appointment is already past or cancelled
    if appointment.status != Appointment.Status.SCHEDULED:
         # Add message: Already cancelled or completed/missed
         pass # Redirect back or show message
    elif appointment.appointment_date < timezone.now().date():
         # Add message: Cannot cancel past appointments
         pass # Redirect back or show message
    else:
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        # Add success message (using Django messages framework)
        messages.success(request, f"Booking {booking_reference} has been cancelled.")

    # Redirect based on user role
    if request.user.role == 'CUSTOMER':
        return redirect('appointments:my_bookings')
    else:
        # Redirect staff back to a management view or dashboard
         return redirect('appointments:home') # Placeholder

# --- Staff/Admin Views ---
@login_required
@role_required(['ADMIN_OFFICER', 'MANAGER', 'ADMIN']) # Use custom decorator
def book_surgery_view(request):
    # Similar to book_appointment_view but:
    # - Form might allow selecting a customer
    # - Filter services to only show those requiring surgery room
    # - Permissions strictly enforced
    # Need a SurgeryBookingForm
    if request.method == 'POST':
         # ... handle form submission ...
         pass
    else:
         # form = SurgeryBookingForm()
         pass
    # return render(request, 'appointments/surgery_booking_form.html', {'form': form})
    return render(request, 'appointments/placeholder.html', {'title': 'Book Surgery (Staff)'})


@login_required
@role_required(['ADMIN', 'MANAGER'])
def report_utilization_view(request):
    # Example: Room utilization per clinic/shift
    # Query appointments, group by clinic, room, date, shift, count
    # Use Django ORM aggregation (Count)
    # Pass data to template for display (table or chart)
    report_data = Appointment.objects.filter(status='SCHEDULED') # Or COMPLETED?
    # Filter by date range from request.GET if needed
    report_data = report_data.values('clinic__name', 'room__room_number', 'appointment_date', 'shift__name')\
                             .annotate(count=Count('booking_reference'))\
                             .order_by('clinic__name', 'appointment_date', 'shift__name', 'room__room_number')

    return render(request, 'appointments/report_utilization.html', {'report_data': report_data})

# Other report views (revenue, customer visits, popular doctor/service) follow similar patterns:
# - Use @role_required decorator
# - Filter Appointment data (e.g., by date range, status='COMPLETED')
# - Use Django ORM aggregation (Sum for revenue, Count for visits/popularity)
# - Group by relevant fields (shift, doctor, service)
# - Pass aggregated data to a template

@login_required
@role_required(['ADMIN', 'MANAGER'])
def report_revenue_view(request):
    # Sum price for completed appointments, group by shift, maybe date range
    report_data = Appointment.objects.filter(status='COMPLETED') \
                                     .values('shift__name') \
                                     .annotate(total_revenue=Sum('price')) \
                                     .order_by('shift__name')
    return render(request, 'appointments/report_revenue.html', {'report_data': report_data})

@login_required
@role_required(['ADMIN', 'MANAGER'])
def report_customer_visits_view(request):
    # Count appointments per customer
    # Might need to select a specific customer or show top customers
    report_data = Appointment.objects.values('customer__email', 'customer__first_name', 'customer__last_name') \
                                     .annotate(visit_count=Count('booking_reference')) \
                                     .order_by('-visit_count')
    return render(request, 'appointments/report_customer_visits.html', {'report_data': report_data})

@login_required
@role_required(['ADMIN', 'MANAGER'])
def report_popularity_view(request):
    # Count appointments per doctor and service
    popular_doctors = Appointment.objects.values('doctor__first_name', 'doctor__last_name') \
                                        .annotate(appointment_count=Count('booking_reference')) \
                                        .order_by('-appointment_count')

    popular_services = Appointment.objects.values('service__name') \
                                          .annotate(appointment_count=Count('booking_reference')) \
                                          .order_by('-appointment_count')
    return render(request, 'appointments/report_popularity.html', {
        'popular_doctors': popular_doctors,
        'popular_services': popular_services,
    })