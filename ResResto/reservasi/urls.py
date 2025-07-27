from django.urls import path # type: ignore
from . import views
from django.contrib.auth import views as auth_views # type: ignore

app_name = 'reservasi'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('buat-reservasi/', views.create_reservation_view, name='create_reservation'),
    path('reservasi-sukses/<int:reservation_id>/', views.reservation_success_view, name='reservation_success'),
    path('ajax/get-time-slots/', views.ajax_get_time_slots, name='ajax_get_time_slots'),
    
    # URL untuk pengguna terdaftar
    path('reservasi-saya/', views.my_reservations_view, name='my_reservations'),
    path('batalkan-reservasi/<int:reservation_id>/', views.cancel_reservation_view, name='cancel_reservation'),
    
    # URL Autentikasi
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'), 
    path('logout/', views.logout_view, name='logout'), 
    
]