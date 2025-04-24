from django.urls import path
from . import views

app_name = 'appointments' # Namespace for URLs

urlpatterns = [
    path('', views.home_view, name='home'), # Homepage / Dashboard
    path('book/', views.book_appointment_view, name='book_appointment'),
    path('ajax/check_availability/', views.ajax_check_availability, name='ajax_check_availability'), # AJAX endpoint
    path('my_bookings/', views.my_bookings_view, name='my_bookings'),
    path('booking/<uuid:booking_reference>/', views.booking_detail_view, name='booking_detail'), # Receipt view
    path('booking/<uuid:booking_reference>/cancel/', views.cancel_booking_view, name='cancel_booking'),

    # Specific routes for surgery booking (maybe admin/manager only)
    path('book_surgery/', views.book_surgery_view, name='book_surgery'),

    # Reporting URLs (Admin/Manager only)
    path('reports/utilization/', views.report_utilization_view, name='report_utilization'),
    path('reports/revenue/', views.report_revenue_view, name='report_revenue'),
    path('reports/customer_visits/', views.report_customer_visits_view, name='report_customer_visits'),
    path('reports/popular/', views.report_popularity_view, name='report_popularity'),
]