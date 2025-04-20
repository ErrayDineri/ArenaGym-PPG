from django.forms import ModelForm
from .models import User, Reservation, Court
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone
from django.forms.widgets import MultiWidget, Select
from django.forms import TimeField
import datetime

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

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'isCoach']



class BookingForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date()
    )
    startTime = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    endTime = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    court = forms.ModelChoiceField(
        queryset=Court.objects.filter(isAvailable=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    payment_method = forms.ChoiceField(
        choices=[('Cash', 'Cash'), ('Online', 'Online')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Reservation
        fields = ['date', 'startTime', 'endTime', 'court', 'coach', 'payment_method']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(BookingForm, self).__init__(*args, **kwargs)

        # Only show coaches in the coach field
        self.fields['coach'].queryset = User.objects.filter(isCoach=True)
        self.fields['coach'].required = False
        self.fields['coach'].widget.attrs.update({'class': 'form-control'})

        # If the current user is a coach, don't let them assign a coach to the booking
        if user and user.isCoach:
            self.fields.pop('coach')

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('startTime')
        end_time = cleaned_data.get('endTime')
        court = cleaned_data.get('court')
        coach = cleaned_data.get('coach')
        payment_method = cleaned_data.get('payment_method')

        # Check if the court is available for the selected date and time
        if Reservation.objects.filter(court=court, date=date, startTime__lt=end_time, endTime__gt=start_time).exists():
            self.add_error('court', 'The selected court is already reserved during this time.')

        # If a coach is selected, check if the coach is available
        if coach and Reservation.objects.filter(coach=coach, date=date, startTime__lt=end_time, endTime__gt=start_time).exists():
            self.add_error('coach', 'The selected coach is already booked during this time.')

        # If online payment is selected, ensure it's handled later (integration with payment provider)
        if payment_method == 'Online':
            pass  # Add payment gateway logic here

        return cleaned_data
