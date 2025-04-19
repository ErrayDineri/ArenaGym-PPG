from django.contrib import admin
from .models import User, Court, Reservation, Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Court)
admin.site.register(Reservation)
admin.site.register(Payment)