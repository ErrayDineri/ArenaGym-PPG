from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    isCoach = models.BooleanField(default=False)
    isModerator = models.BooleanField(default=False)
    rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, null=True, blank=True)

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
