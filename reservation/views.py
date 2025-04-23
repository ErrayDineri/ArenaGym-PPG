from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm, BookingForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .models import Court, Reservation, User
from django.utils import timezone

def registerPage(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data.get('isCoach'):
                user.isCoach = True
                user.rate = 120  # Default rate if Coach
            user.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'register.html', {'form': form})

def loginPage(request):
    next_url = request.GET.get('next')  # ?next=/booking/

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Redirect to 'next' if exists, otherwise home
            return redirect(request.POST.get('next') or 'home')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {
        'form': form,
        'next': next_url  # Pass it to the template
    })

def homePage(request):
    return render(request, 'home.html')

def logoutPage(request):
    logout(request)
    return redirect('login')

@login_required
def bookingPage(request, court_id=None):
    total_price = 120  # Default price without coach

    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user

            # Set the reservation times
            reservation.startTime = form.cleaned_data['startTime']
            reservation.endTime = form.cleaned_data['endTime']

            # Calculate total price if a coach is selected
            coach = form.cleaned_data.get('coach')
            booking_duration = form.cleaned_data.get('booking_duration')
            num_people = form.cleaned_data.get('num_people')

            if coach:
                total_price = coach.rate if coach.rate else 120
            if booking_duration == '1h':  # Adjusting price for 1 hour booking
                total_price /= 2
            if num_people == 2:  # Adjusting price if there are 2 people
                total_price *= 2

            reservation.total_price = total_price  # Assuming you have this field in the Reservation model
            reservation.save()

            # Redirect to the home page after saving
            return redirect('home')
    else:
        form = BookingForm(user=request.user)
        if court_id:
            form.fields['court'].initial = court_id

    return render(request, 'booking.html', {'form': form, 'total_price': total_price})


@login_required
def clientPage(request):
    # Get upcoming reservations for the current user
    upcoming_reservations = Reservation.objects.filter(
        user=request.user,
        date__gte=timezone.now().date()
    ).order_by('date', 'startTime')
    
    # Get available courts
    available_courts = Court.objects.all()
    
    context = {
        'upcoming_reservations': upcoming_reservations,
        'available_courts': available_courts,
        'reservation_count': upcoming_reservations.count(),
    }
    return render(request, 'clientdashboard.html', context)
