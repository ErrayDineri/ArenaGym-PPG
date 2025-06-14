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
    path('booking/<int:court_id>/', views.bookingPage, name='booking_with_id'),
    path('coach/', views.coach_dashboard, name='coachdashboard'),
    path('coach/sessions/', views.coach_sessions, name='coachsessions'),
    path('coach/sessions/<int:session_id>/', views.session_detail, name='session_detail'),
    path('coach/sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    path('coach/students/', views.coach_students, name='coach_students'),
      # Coach availability management
    path('coach/availability/', views.coach_availability, name='coach_availability'),
    path('coach/availability/<int:availability_id>/delete/', views.delete_availability, name='delete_availability'),
    path('api/coach/availability/', views.coach_availability_api, name='coach_availability_api'),
    path('api/coach/details/<int:coach_id>/', views.coach_details_api, name='coach_details_api'),
    
    # General availability API for booking system
    path('api/availability/', views.availability_api, name='availability_api')

]