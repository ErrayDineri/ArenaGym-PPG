from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, time, timedelta

class User(AbstractUser):
    isCoach = models.BooleanField(default=False)
    isModerator = models.BooleanField(default=False)
    rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, null=True, blank=True)
    
    def get_availability_schedule(self):
        """Returns coach availability in FullCalendar event format"""
        if not self.isCoach:
            return []
            
        events = []
        
        # Import timezone here to avoid circular imports
        from django.utils import timezone
        from datetime import timedelta
        
        # Define the range for recurring events (e.g., next 8 weeks)
        today = timezone.now().date()
        start_range = today - timedelta(days=7)  # Show past week too
        end_range = today + timedelta(weeks=8)   # Show next 8 weeks
        
        # Get all availability slots for the coach
        for availability in self.coachavailability_set.all():
            if availability.is_recurring:
                # Generate events for all matching weekdays in the range
                current_date = start_range
                while current_date <= end_range:
                    # Check if this date matches the recurring day of week
                    if current_date.weekday() == availability.day_of_week:
                        events.append({
                            'title': f"Available - {self.get_full_name() or self.username}",
                            'start': f"{current_date.isoformat()}T{availability.start_time.strftime('%H:%M:%S')}",
                            'end': f"{current_date.isoformat()}T{availability.end_time.strftime('%H:%M:%S')}",
                            'color': '#28a745',  # Green for available
                            'extendedProps': {
                                'type': 'availability',
                                'availability_id': availability.id,
                                'coach_id': self.id,
                                'coach_name': self.get_full_name() or self.username,
                                'coach_rate': str(self.rate),
                                'is_recurring': True
                            }
                        })
                    current_date += timedelta(days=1)
            else:
                # One-time availability - only show for the specific date
                events.append({
                    'title': f"Available - {self.get_full_name() or self.username}",
                    'start': f"{availability.date.isoformat()}T{availability.start_time.strftime('%H:%M:%S')}",
                    'end': f"{availability.date.isoformat()}T{availability.end_time.strftime('%H:%M:%S')}",
                    'color': '#28a745',  # Green for available
                    'extendedProps': {
                        'type': 'availability',
                        'availability_id': availability.id,
                        'coach_id': self.id,
                        'coach_name': self.get_full_name() or self.username,
                        'coach_rate': str(self.rate),
                        'is_recurring': False
                    }
                })
        
        # Get all booked slots for the coach (to avoid double-booking)
        for reservation in self.coach.all():
            events.append({
                'title': f"Booked - {reservation.user.username}",
                'start': f"{reservation.date.isoformat()}T{reservation.startTime.strftime('%H:%M:%S')}",
                'end': f"{reservation.date.isoformat()}T{reservation.endTime.strftime('%H:%M:%S')}",
                'color': '#dc3545',  # Red for booked
                'extendedProps': {
                    'type': 'booking',
                    'reservation_id': reservation.id,
                }
            })
            
        return events

class Court(models.Model):
    id = models.IntegerField(primary_key=True)
    inDoor = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Court {self.id} - {'Indoor' if self.inDoor else 'Outdoor'}"
        
    def get_booked_slots(self):
        """Returns booked slots in FullCalendar event format"""
        events = []
        for reservation in self.reservation_set.all():
            events.append({
                'title': f"Booked - {reservation.user.username}",
                'start': f"{reservation.date.isoformat()}T{reservation.startTime.strftime('%H:%M:%S')}",
                'end': f"{reservation.date.isoformat()}T{reservation.endTime.strftime('%H:%M:%S')}",
                'color': '#dc3545',
                'extendedProps': {
                    'type': 'booking',
                    'reservation_id': reservation.id
                }
            })
        return events
        
class CoachAvailability(models.Model):
    coach = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=False)
    # For recurring availability - null if not recurring
    day_of_week = models.IntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ], null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Coach Availabilities"
        
    def __str__(self):
        if self.is_recurring:
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][self.day_of_week]
            return f"{self.coach.username} - {day_name} {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
        return f"{self.coach.username} - {self.date} {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')}"
        
    def is_available(self, check_date, check_start_time, check_end_time):
        """Check if a coach is available at the specified date and time range"""
        if self.is_recurring:
            # Check if day of week matches and time range is available
            if check_date.weekday() != self.day_of_week:
                return False
        else:
            # Check if date matches for non-recurring availability
            if check_date != self.date:
                return False
                
        # Check time overlap
        if check_start_time >= self.end_time or check_end_time <= self.start_time:
            return False
            
        # Check for existing reservations
        conflicting_reservations = Reservation.objects.filter(
            coach=self.coach,
            date=check_date
        ).exclude(
            # Exclude reservations that don't overlap
            startTime__gte=check_end_time
        ).exclude(
            endTime__lte=check_start_time
        )
        
        return not conflicting_reservations.exists()
    
class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coach', null=True, blank=True)
    date = models.DateField()
    startTime = models.TimeField()
    endTime = models.TimeField()
    createdAt = models.DateTimeField(auto_now_add=True)
    isPaid = models.BooleanField(default=False)
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=120)
