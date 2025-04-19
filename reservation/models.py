from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    isCoach = models.BooleanField(default=False)

class Moderator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class Court(models.Model):
    id = models.IntegerField(primary_key=True)
    inDoor = models.BooleanField(default=True)
    isAvailable = models.BooleanField(default=True)
    description = models.TextField(blank=True)

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coach = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coach', null=True, blank=True)
    date = models.DateField()
    startTime = models.TimeField()
    endTime = models.TimeField()
    createdAt = models.DateTimeField(auto_now_add=True)
    isPaid = models.BooleanField(default=False)
    court = models.ForeignKey(Court, on_delete=models.CASCADE)

class Payment(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    paymentDate = models.DateTimeField(auto_now_add=True)
    paymentMethod = models.CharField(max_length=50)