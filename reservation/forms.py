from django.forms import ModelForm
from django import forms
from .models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        help_text=None
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        help_text=None
    )
    isCoach = forms.BooleanField(
        label="Are you registering as a coach?",
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'isCoach']
