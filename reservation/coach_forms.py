from django import forms
from .models import CoachAvailability

class CoachAvailabilityForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    day_of_week = forms.ChoiceField(
        choices=[
            (0, 'Monday'),
            (1, 'Tuesday'),
            (2, 'Wednesday'),
            (3, 'Thursday'),
            (4, 'Friday'),
            (5, 'Saturday'),
            (6, 'Sunday'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    is_recurring = forms.BooleanField(required=False)
    
    class Meta:
        model = CoachAvailability
        fields = ['date', 'start_time', 'end_time', 'is_recurring', 'day_of_week']
        
    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        date = cleaned_data.get('date')
        day_of_week = cleaned_data.get('day_of_week')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Validation based on recurring or one-time
        if is_recurring and not day_of_week:
            self.add_error('day_of_week', 'Day of week is required for recurring availability')
        
        if not is_recurring and not date:
            self.add_error('date', 'Date is required for one-time availability')
            
        # Validate time range
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', 'End time must be after start time')
            
        return cleaned_data
