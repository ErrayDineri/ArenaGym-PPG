from django.contrib import admin
from .models import User, Court, Reservation, CoachAvailability

class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'isCoach', 'isModerator', 'rate')
    list_filter = ('isCoach', 'isModerator')
    search_fields = ('username', 'email', 'first_name', 'last_name')

class CourtAdmin(admin.ModelAdmin):
    list_display = ('id', 'inDoor', 'description')
    list_filter = ('inDoor',)

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'coach', 'court', 'date', 'startTime', 'endTime', 'isPaid', 'total_price')
    list_filter = ('isPaid', 'date', 'court')
    search_fields = ('user__username', 'coach__username')
    date_hierarchy = 'date'

class CoachAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('coach', 'date', 'start_time', 'end_time', 'is_recurring', 'day_of_week')
    list_filter = ('is_recurring', 'day_of_week', 'coach')
    search_fields = ('coach__username',)
    date_hierarchy = 'date'

admin.site.register(User, UserAdmin)
admin.site.register(Court, CourtAdmin)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(CoachAvailability, CoachAvailabilityAdmin)