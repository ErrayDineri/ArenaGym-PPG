from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegistrationForm, BookingForm
from .coach_forms import CoachAvailabilityForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from .models import Court, Reservation, User, CoachAvailability
from django.utils import timezone
from datetime import timedelta, datetime, time
from django.http import JsonResponse
from django.contrib import messages
from decimal import Decimal

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
    
    # Get session counts for each student
    student_data = []
    for student in students:
        sessions = Reservation.objects.filter(coach=request.user, user=student)
        student_data.append({
            'student': student,
            'session_count': sessions.count(),
            'last_session': sessions.order_by('-date').first() if sessions.exists() else None,
            'total_spent': sum(session.total_price for session in sessions)
        })
    
    return render(request, 'coach_students.html', {
        'students': student_data,
        'total_students': len(student_data)
    })

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
        # Handle the booking submission directly without using the form class
        try:
            # Get form data
            date_str = request.POST.get('date')
            start_time_str = request.POST.get('startTime')
            end_time_str = request.POST.get('endTime')
            court_id = request.POST.get('court')
            coach_id = request.POST.get('coach')
            payment_method = request.POST.get('payment_method', 'Cash')
            
            # Parse and validate the data
            if not all([date_str, start_time_str, end_time_str, court_id]):
                messages.error(request, "Please fill in all required fields.")
                return redirect('booking')
                
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            court = get_object_or_404(Court, id=court_id)
            coach = None
            if coach_id:
                coach = get_object_or_404(User, id=coach_id, isCoach=True)
              # Check for conflicts
            print(f"DEBUG VIEW: Checking court {court} for date {date}, time {start_time}-{end_time}")
            conflicts = Reservation.objects.filter(
                court=court,
                date=date,
                startTime__lt=end_time,
                endTime__gt=start_time
            )
            
            print(f"DEBUG VIEW: Found {conflicts.count()} conflicts")
            for conflict in conflicts:
                print(f"DEBUG VIEW: Conflict - Date: {conflict.date}, Time: {conflict.startTime}-{conflict.endTime}, User: {conflict.user.username}")
            
            if conflicts.exists():
                messages.error(request, "This court is already booked during the selected time.")
                return redirect('booking')
            
            # Check coach availability if coach is selected
            if coach:
                # Verify coach set availability rules
                availabilities = CoachAvailability.objects.filter(coach=coach)
                has_slot = any(slot.is_available(date, start_time, end_time) for slot in availabilities)
                if not has_slot:
                    messages.error(request, "The selected coach has not set availability for this time. Please choose another time or coach.")
                    return redirect('booking')

                coach_conflicts = Reservation.objects.filter(
                    coach=coach,
                    date=date,
                    startTime__lt=end_time,
                    endTime__gt=start_time
                )
                
                if coach_conflicts.exists():
                    messages.error(request, f"{coach.get_full_name()} is already booked during this time.")
                    return redirect('booking')
            
            # Calculate duration and price
            duration_timedelta = datetime.combine(date, end_time) - datetime.combine(date, start_time)
            duration_hours = duration_timedelta.total_seconds() / 3600
              # Calculate total price
            court_rate = Decimal('60.00')  # Default court rate per hour
            if coach:
                coach_rate = Decimal(str(coach.rate))
                total_price = Decimal(str(duration_hours)) * (court_rate + coach_rate)
            else:
                # Set price to 100 when no coach is selected
                total_price = Decimal('100.00')
            
            # Create the reservation
            reservation = Reservation.objects.create(
                user=request.user,
                date=date,
                startTime=start_time,
                endTime=end_time,
                court=court,
                coach=coach,
                total_price=total_price,
                isPaid=False
            )
            
            coach_msg = f" with {coach.get_full_name()}" if coach else ""
            messages.success(request, f"Court {court.id} booked successfully for {date.strftime('%B %d, %Y')} from {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}{coach_msg}!")
            return redirect('client')
            
        except Exception as e:
            messages.error(request, f"Error creating reservation: {str(e)}")
            return redirect('booking')
    
    # GET request - show the booking form
    form = BookingForm(user=request.user)
    if court_id:
        form.fields['court'].initial = court_id
    
    # Get available courts and coaches (excluding current user if they're a coach)
    courts = Court.objects.all()
    coaches = User.objects.filter(isCoach=True).exclude(id=request.user.id)
    
    return render(request, 'booking.html', {
        'form': form,
        'courts': courts,
        'coaches': coaches
    })

def availability_api(request):
    """API endpoint for checking court and coach availability"""
    coach_id = request.GET.get('coach_id')
    court_id = request.GET.get('court_id')
    date_str = request.GET.get('date')
    start_time_str = request.GET.get('start')
    end_time_str = request.GET.get('end')
    
    events = []
    
    # If we have specific date and times, we're checking a specific slot's availability
    specific_check = date_str and start_time_str and end_time_str
    
    if coach_id:
        try:
            coach = User.objects.get(id=coach_id, isCoach=True)
            
            if specific_check:
                # Convert strings to date/time objects
                check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                check_start = datetime.strptime(start_time_str, '%H:%M').time()
                check_end = datetime.strptime(end_time_str, '%H:%M').time()                # Get all availability slots that overlap with this timeframe
                availabilities = coach.coachavailability_set.all()
                
                # Check if coach is available during this slot
                is_available = False
                
                # If coach has no availability set at all, they're not available
                if not availabilities.exists():
                    events.append({
                        'title': 'Coach Not Available',
                        'start': f"{date_str}T{start_time_str}:00",
                        'end': f"{date_str}T{end_time_str}:00",
                        'color': '#dc3545',  # Red
                        'extendedProps': {
                            'type': 'booking',  # Mark as conflict
                            'conflict': 'coach_not_available'
                        }
                    })
                else:
                    for avail in availabilities:
                        if avail.is_available(check_date, check_start, check_end):
                            is_available = True
                            break
                    
                    # If coach isn't available and has availability set, return conflict events
                    if not is_available:
                        # Create a conflict event
                        events.append({
                            'title': 'Coach Not Available',
                            'start': f"{date_str}T{start_time_str}:00",
                            'end': f"{date_str}T{end_time_str}:00",
                            'color': '#dc3545',  # Red
                            'extendedProps': {
                                'type': 'booking',  # Mark as conflict
                                'conflict': 'coach_not_available'
                            }
                        })
            else:
                # Get full availability schedule (for calendar display)
                events.extend(coach.get_availability_schedule())
        except User.DoesNotExist:
            pass
    
    if court_id:
        try:
            court = Court.objects.get(id=court_id)
            events.extend(court.get_booked_slots())
        except Court.DoesNotExist:
            pass
    
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

@login_required
def coach_availability(request):
    """View for coaches to manage their availability schedule"""
    if not request.user.isCoach:
        return redirect('client')
        
    if request.method == 'POST':
        form = CoachAvailabilityForm(request.POST)
        if form.is_valid():
            availability = form.save(commit=False)
            availability.coach = request.user
            
            # For recurring slots, we need to set a date value (required by the model)
            # We'll use today's date as a placeholder since it's the day_of_week that matters
            if availability.is_recurring and not availability.date:
                availability.date = timezone.now().date()
                
            availability.save()
            messages.success(request, "Availability slot added successfully!")
            return redirect('coach_availability')
    
    # Get all existing availability slots for this coach
    availability_slots = CoachAvailability.objects.filter(coach=request.user)
    
    # Prepare hours for the template
    hours = range(6, 22)  # 6 AM to 9 PM
    
    context = {
        'availability_slots': availability_slots,
        'hours': hours,
        'today': timezone.now().date(),
    }
    
    return render(request, 'coach_availability.html', context)

@login_required
def delete_availability(request, availability_id):
    """Delete a coach's availability slot"""
    if not request.user.isCoach:
        return redirect('client')
        
    availability = get_object_or_404(CoachAvailability, id=availability_id, coach=request.user)
    availability.delete()
    messages.success(request, "Availability slot removed successfully!")
    return redirect('coach_availability')

@login_required
def coach_availability_api(request):
    """API endpoint to get coach availability for calendar display"""
    if not request.user.isCoach:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Get the coach's availability schedule and booked sessions
    events = request.user.get_availability_schedule()
    return JsonResponse(events, safe=False)

def coach_details_api(request, coach_id):
    """API endpoint to get coach details for the booking page"""
    try:
        coach = User.objects.get(id=coach_id, isCoach=True)
        
        # Count available slots in the next 7 days
        today = timezone.now().date()
        week_ahead = today + timedelta(days=7)
        
        # For recurring availabilities, count days that match in the next week
        recurring_count = 0
        for avail in CoachAvailability.objects.filter(coach=coach, is_recurring=True):
            for day in range(7):
                check_date = today + timedelta(days=day)
                if check_date.weekday() == avail.day_of_week:
                    recurring_count += 1
        
        # One-time availabilities
        onetime_count = CoachAvailability.objects.filter(
            coach=coach, 
            is_recurring=False,
            date__range=[today, week_ahead]
        ).count()
        
        total_availability = recurring_count + onetime_count
        
        # Check if coach has any booked sessions
        booked_count = Reservation.objects.filter(
            coach=coach,
            date__range=[today, week_ahead]
        ).count()
        
        # Prepare an appropriate message based on availability
        if total_availability > 5:
            availability_message = "Very available this week!"
        elif total_availability > 2:
            availability_message = "Has some availability this week."
        elif total_availability > 0:
            availability_message = "Limited availability this week."
        else:
            availability_message = "No availability set for this week."
            
        # Get daily availability breakdown
        daily_availability = []
        for day_offset in range(7):
            check_date = today + timedelta(days=day_offset)
            day_name = check_date.strftime('%a')  # Mon, Tue, Wed, etc.
            
            # Check recurring slots for this weekday
            recurring_slots = CoachAvailability.objects.filter(
                coach=coach, 
                is_recurring=True,
                day_of_week=check_date.weekday()
            )
            
            # Check one-time slots for this date
            onetime_slots = CoachAvailability.objects.filter(
                coach=coach,
                is_recurring=False,
                date=check_date
            )
            
            # Total available hours for this day
            total_hours = 0
            for slot in list(recurring_slots) + list(onetime_slots):
                slot_duration = (
                    datetime.combine(check_date, slot.end_time) - 
                    datetime.combine(check_date, slot.start_time)
                ).total_seconds() / 3600
                total_hours += slot_duration
                
            daily_availability.append({
                'day': day_name,
                'date': check_date.strftime('%Y-%m-%d'),
                'available_hours': round(total_hours, 1),
                'has_availability': total_hours > 0
            })
        
        # Mock expertise fields (in a real app, you'd store these in the database)
        expertise = ['Tennis', 'Fitness', 'Training']
        experience = "Professional tennis player with 5+ years of coaching experience."
            
        response_data = {
            'id': coach.id,
            'name': coach.get_full_name() or coach.username,
            'rate': float(coach.rate),
            'available_slots': total_availability,
            'booked_slots': booked_count,
            'availability_message': availability_message,
            'daily_availability': daily_availability,
            'expertise': expertise,
            'experience': experience
        }
        
        return JsonResponse(response_data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Coach not found'}, status=404)
