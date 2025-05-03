from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.registerPage, name='register'),
    path('login/', views.loginPage, name='login'),
    path('', views.homePage, name='home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('booking/', views.bookingPage, name='booking'),
    path('client/', views.clientPage, name='client'),
    path('booking/<int:court_id>/', views.bookingPage, name='booking_with_id'),  # new
    path('coach/', views.coach_dashboard, name='coachdashboard'),
    path('coach/sessions/', views.coach_sessions, name='coachsessions'),
    path('coach/sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('coach/sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    path('coach/students/', views.coach_students, name='coach_students'),



]