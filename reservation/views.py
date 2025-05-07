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
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            
            # Calculate price
            coach = form.cleaned_data.get('coach')
            duration = (datetime.combine(reservation.date, reservation.endTime) - 
                       datetime.combine(reservation.date, reservation.startTime)).total_seconds() / 3600
            reservation.total_price = duration * (coach.rate if coach else 60)  # Default rate
            
            reservation.save()
            messages.success(request, "Reservation created successfully!")
            return redirect('client_dashboard')
    else:
        form = BookingForm(user=request.user)
        if court_id:
            form.fields['court'].initial = court_id
    
    # Get available courts and coaches
    courts = Court.objects.all()
    coaches = User.objects.filter(isCoach=True)
    
    return render(request, 'booking.html', {
        'form': form,
        'courts': courts,
        'coaches': coaches
    })

def availability_api(request):
    coach_id = request.GET.get('coach_id')
    court_id = request.GET.get('court_id')
    
    events = []
    
    if coach_id:
        coach = User.objects.get(id=coach_id, isCoach=True)
        events.extend(coach.get_availability_schedule())
    
    if court_id:
        court = Court.objects.get(id=court_id)
        events.extend(court.get_booked_slots())
    
    return JsonResponse(events, safe=False)

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
