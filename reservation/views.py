from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm, BookingForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .models import Court, Reservation, User
from django.utils import timezone
from datetime import timedelta

@login_required
def coach_dashboard(request):
    if not request.user.isCoach:
        return redirect('client')
    
    # Today's sessions
    today = timezone.now().date()
    todays_sessions = Reservation.objects.filter(
        coach=request.user,
        date=today
    ).order_by('startTime')
    
    # Upcoming sessions (next 7 days)
    upcoming_sessions = Reservation.objects.filter(
        coach=request.user,
        date__range=[today, today + timedelta(days=7)]
    ).exclude(date=today).order_by('date', 'startTime')
    
    # Calculate earnings (assuming you have a price field in Reservation)
    total_earnings = sum(
        session.total_price for session in 
        Reservation.objects.filter(
            coach=request.user,
            date__month=timezone.now().month,
            isPaid=True
        )
    )
    
    # Get unique students
    student_ids = Reservation.objects.filter(
        coach=request.user
    ).values_list('user', flat=True).distinct()
    students = User.objects.filter(id__in=student_ids)
    
    context = {
        'todays_sessions': todays_sessions,
        'upcoming_sessions': upcoming_sessions,
        'total_earnings': total_earnings,
        'student_count': students.count(),
        'session_count': todays_sessions.count() + upcoming_sessions.count(),
    }
    return render(request, 'coachdashboard.html', context)

@login_required
def coach_sessions(request):
    if not request.user.isCoach:
        return redirect('client')
    
    sessions = Reservation.objects.filter(
        coach=request.user,
        date__gte=timezone.now().date()
    ).order_by('date', 'startTime')
    
    return render(request, 'coachsessions.html', {'sessions': sessions})

@login_required
def coach_students(request):
    if not request.user.isCoach:
        return redirect('client')
    
    # Get unique students who have booked with this coach
    student_ids = Reservation.objects.filter(
        coach=request.user
    ).values_list('user', flat=True).distinct()
    students = User.objects.filter(id__in=student_ids)
    
    return render(request, 'coach_students.html', {'students': students})

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Reservation, id=session_id, coach=request.user)
    return render(request, 'session_detail.html', {'session': session})

@login_required
def cancel_session(request, session_id):
    session = get_object_or_404(Reservation, id=session_id, coach=request.user)
    if request.method == 'POST':
        session.delete()
        return redirect('coach_dashboard')
    return render(request, 'confirm_cancel.html', {'session': session})


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
