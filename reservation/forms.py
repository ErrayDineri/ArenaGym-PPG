from django.forms import ModelForm
from .models import User, Reservation, Court
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone

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

    class Meta:
        model = Reservation
        fields = ['date', 'startTime', 'endTime', 'court', 'coach']

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