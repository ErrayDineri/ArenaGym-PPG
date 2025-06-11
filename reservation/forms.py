from .utils import generate_time_slots
from .models import User, Reservation, Court, CoachAvailability
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone
from django.forms.widgets import MultiWidget, Select
import datetime
from decimal import Decimal

class TimeSelectWidget(MultiWidget):
    def __init__(self, attrs=None):
        hours = [(str(i), f"{i:02}") for i in range(1, 13)]
        minutes = [(str(i), f"{i:02}") for i in [0, 15, 30, 45]]
        meridian = [('AM', 'AM'), ('PM', 'PM')]

        widgets = [
            Select(attrs=attrs, choices=hours),
            Select(attrs=attrs, choices=minutes),
            Select(attrs=attrs, choices=meridian),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value is None:
            return [None, None, None]
        if isinstance(value, str):
            value = datetime.datetime.strptime(value, '%H:%M:%S').time()
        hour = value.hour
        meridian = 'AM'
        if hour >= 12:
            meridian = 'PM'
        if hour > 12:
            hour -= 12
        elif hour == 0:
            hour = 12
        return [str(hour), f"{value.minute:02}", meridian]

    def format_output(self, rendered_widgets):
        return ''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        hour = int(data.get(f'{name}_0', 0))
        minute = int(data.get(f'{name}_1', 0))
        meridian = data.get(f'{name}_2', 'AM')

        if meridian == 'PM' and hour != 12:
            hour += 12
        elif meridian == 'AM' and hour == 12:
            hour = 0

        return f"{hour:02}:{minute:02}"

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'example@example.org'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        help_text=None
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password Again'}),
        help_text=None
    )
    isCoach = forms.BooleanField(
        label="Are you registering as a coach?",
        required=False
    )
    rate = forms.DecimalField(
        label="How much do you charge per hour?",
        required=False,
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'isCoach', 'rate']

    def clean(self):
        cleaned_data = super().clean()
        is_coach = cleaned_data.get('isCoach')
        rate = cleaned_data.get('rate')

        if is_coach and rate in [None, '']:
            self.add_error('rate', 'Rate is required if registering as a coach.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.isCoach = self.cleaned_data.get('isCoach', False)
        user.rate = self.cleaned_data.get('rate') if user.isCoach else 0.00
        if commit:
            user.save()
        return user


class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )
    time_slot = forms.ChoiceField(
        choices=[(slot[0].strftime('%H:%M'), f"{slot[0].strftime('%H:%M')} - {slot[1].strftime('%H:%M')}") for slot in generate_time_slots()],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    court = forms.ModelChoiceField(
        queryset=Court.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    payment_method = forms.ChoiceField(
        choices=[('Cash', 'Cash'), ('Online', 'Online')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    coach = forms.ModelChoiceField(
        queryset=User.objects.filter(isCoach=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    booking_duration = forms.ChoiceField(
        choices=[('full', 'Full time slot'), ('1h', '1 hour')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    num_people = forms.ChoiceField(
        choices=[(1, '1 person'), (2, '2 people')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Reservation
        fields = ['date', 'court', 'coach', 'payment_method']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BookingForm, self).__init__(*args, **kwargs)

        if user and hasattr(user, 'isCoach') and user.isCoach:
            self.fields.pop('coach')

        if 'coach' in self.fields:
            if self.fields['coach'].queryset.exists():
                self.fields['booking_duration'].required = True
                self.fields['num_people'].required = True

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        court = cleaned_data.get('court')
        coach = cleaned_data.get('coach')
        time_slot_str = cleaned_data.get('time_slot')

        if not time_slot_str:
            raise forms.ValidationError("Time slot selection is required.")

        if not court:
            raise forms.ValidationError("Court selection is required.")

        start_time = datetime.datetime.strptime(time_slot_str, '%H:%M').time()
        end_time = None
        for slot_start, slot_end in generate_time_slots():
            if slot_start == start_time:
                end_time = slot_end
                break
        else:
            raise forms.ValidationError("Invalid time slot selected.")        # Add the times to cleaned_data
        cleaned_data['startTime'] = start_time
        cleaned_data['endTime'] = end_time
        
        # Debug information - you can remove this later
        print(f"DEBUG: Checking court {court} for date {date}, time {start_time}-{end_time}")
        
        # Check if the court is already reserved during the chosen time (with both date and time)
        conflicting_reservations = Reservation.objects.filter(
            court=court,
            date=date,
            startTime__lt=end_time,
            endTime__gt=start_time
        )
        
        if conflicting_reservations.exists():
            # Add detailed debugging information
            conflict_details = []
            for reservation in conflicting_reservations:
                conflict_details.append(
                    f"Date: {reservation.date}, Time: {reservation.startTime}-{reservation.endTime}, User: {reservation.user.username}"
                )
            
            error_message = f'The selected court is already reserved during this time. Conflicts found: {"; ".join(conflict_details)}'
            self.add_error('court', error_message)
            
        # Check if the coach is available during the chosen time
        if coach:
            # First check if coach has any availability for this time slot
            coach_is_available = False
            if CoachAvailability.objects.filter(coach=coach).exists():
                for availability in CoachAvailability.objects.filter(coach=coach):
                    if availability.is_available(date, start_time, end_time):
                        coach_is_available = True
                        break
                
                if not coach_is_available:
                    self.add_error('coach', 'The selected coach is not available during this time.')
            else:
                self.add_error('coach', 'The selected coach has not set their availability yet.')
            
            # Then check for booking conflicts
            if Reservation.objects.filter(
                coach=coach,
                date=date,
                startTime__lt=end_time,
                endTime__gt=start_time            ).exists():
                self.add_error('coach', 'The selected coach is already booked during this time.')

        return cleaned_data
        
    def save(self, commit=True):
        reservation = super().save(commit=False)
        reservation.startTime = self.cleaned_data.get('startTime')
        reservation.endTime = self.cleaned_data.get('endTime')

        coach = self.cleaned_data.get('coach')
        if coach:
            duration = (datetime.datetime.combine(datetime.date.min, reservation.endTime) -
                        datetime.datetime.combine(datetime.date.min, reservation.startTime)).total_seconds() / 3600
            # Always convert both to Decimal explicitly
            try:
                duration_decimal = Decimal(str(duration))
                # Court rate per hour (should match views.py)
                court_rate = Decimal('60.00')
                # Coach rate
                coach_rate = coach.rate
                if not isinstance(coach_rate, Decimal):
                    coach_rate = Decimal(str(coach_rate))
                # Total = (court_rate + coach_rate) * duration
                reservation.total_price = duration_decimal * (court_rate + coach_rate)
            except Exception as e:
                reservation.total_price = Decimal('0.00')
        else:
            # Set price to 100 when no coach is selected (should match views.py)
            reservation.total_price = Decimal('100.00')

        if commit:
            reservation.save()
        return reservation
