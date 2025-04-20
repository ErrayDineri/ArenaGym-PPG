from django.shortcuts import render, redirect
from .forms import UserRegistrationForm,  BookingForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

def registerPage(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
        
    return render(request, 'register.html', {'form': form})

def loginPage(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # or wherever you want to redirect
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

def homePage(request):
    return render(request, 'home.html')

def logoutPage(request):
    logout(request)
    return redirect('login')

@login_required
def bookingPage(request):
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.user = request.user
            reservation.save()
            return redirect('home')
    else:
        form = BookingForm(user=request.user)

    return render(request, 'booking.html', {'form': form})