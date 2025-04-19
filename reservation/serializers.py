from rest_framework import serializers
from .models import User,Moderator, Court,Reservation,Payment
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'isCoach']

class ModeratorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Moderator
        fields = ['user']

class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ['id', 'inDoor', 'isAvailable', 'description']

class ReservationSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    coach = UserSerializer(required=False)
    court = CourtSerializer()

    class Meta:
        model = Reservation
        fields = ['id', 'user', 'coach', 'date', 'startTime', 'endTime', 'createdAt', 'isPaid', 'court']

class PaymentSerializer(serializers.ModelSerializer):
    reservation = ReservationSerializer()

    class Meta:
        model = Payment
        fields = ['id', 'reservation', 'amount', 'paymentDate', 'paymentMethod']