from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import CustomUserCreationForm # Need to create this form

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Set role based on form input if needed, or default to Customer
            user.role = 'CUSTOMER' # Or get from form
            user.save()
            login(request, user) # Log the user in
            return redirect('appointments:home') # Redirect to home/dashboard
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})