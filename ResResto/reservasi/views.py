from django.shortcuts import render, redirect, get_object_or_404 # type: ignore
from django.contrib import messages # type: ignore
from .models import RestaurantProfile, Reservation
from .forms import ReservationForm
from django.utils import timezone # type: ignore
import datetime
from django.http import JsonResponse # type: ignore
from django.contrib.auth.decorators import login_required # type: ignore 
from django.contrib.auth.forms import UserCreationForm # type: ignore
from django.contrib.auth import login, authenticate, logout # type: ignore
from django.db.models import Sum # type: ignore 

def get_restaurant_profile():
    profile = RestaurantProfile.objects.first()
    if not profile:
        profile = RestaurantProfile.objects.create() 
        messages.warning(None, "Profil restoran default telah dibuat. Harap konfigurasikan di halaman admin.")
    return profile

def home_view(request):
    profile = get_restaurant_profile()
    return render(request, 'reservasi/home.html', {'profile': profile})

def create_reservation_view(request):
    profile = get_restaurant_profile()
    initial_data = {}
    if request.user.is_authenticated:
        initial_data['guest_name'] = request.user.get_full_name() or request.user.username
        initial_data['guest_email'] = request.user.email
        # initial_data['guest_phone'] = # ... jika ada
        
    if request.method == 'POST':
        form = ReservationForm(request.POST, user=request.user) 
        if form.is_valid():
            # Semua logika untuk form yang VALID ada di dalam blok if ini
            reservation = form.save(commit=False)
            if request.user.is_authenticated:
                reservation.user = request.user
                if not form.cleaned_data.get('guest_name') and (request.user.get_full_name() or request.user.username):
                    reservation.guest_name = request.user.get_full_name() or request.user.username
                if not form.cleaned_data.get('guest_email') and request.user.email:
                    reservation.guest_email = request.user.email
                # guest_phone akan diambil dari form.cleaned_data.get('guest_phone') yang sudah diisi
            
            # Logika waitlist juga hanya dijalankan jika form.is_valid()
            # Meskipun pengecekan ketersediaan ada di form.clean(),
            # kita tetap butuh akses ke reservation object yang valid.
            if hasattr(form, 'is_waitlist_candidate') and form.is_waitlist_candidate:
                # Periksa apakah pengguna menekan tombol "join_waitlist"
                if 'join_waitlist' in request.POST:
                    reservation.status = 'WAITLISTED'
                    messages.info(request, "Slot penuh. Anda telah dimasukkan ke dalam waiting list.")
                else:
                    pass 
            else: 
                reservation.status = 'PENDING'
                messages.success(request, f"Reservasi Anda untuk {reservation.number_of_guests} orang pada {reservation.reservation_date.strftime('%d %B %Y')} pukul {reservation.reservation_time.strftime('%H:%M')} telah diterima dan sedang diproses.")

            reservation.save()
            return redirect('reservasi:reservation_success', reservation_id=reservation.id)
        
        else: # Blok ini dieksekusi jika form.is_valid() adalah False
            print("-----------------------------------")
            print("Form is NOT valid. Errors:")
            for field, errors in form.errors.items():
                print(f"Field: {field}")
                for error in errors:
                    print(f"  - Error: {error}")
            if form.non_field_errors():
                print("Non-field errors:")
                for error in form.non_field_errors():
                    print(f"  - Error: {error}")
            
            print("Cleaned data (jika ada sebagian):")
            print(form.cleaned_data)
            print("Data POST:")
            print(request.POST)
            print("-----------------------------------")
            messages.error(request, "Harap perbaiki kesalahan pada form di bawah.")
            
    else: # Jika request.method bukan 'POST' (misalnya 'GET')
        form = ReservationForm(user=request.user, initial=initial_data) 

    # Ini akan merender template dengan form (baik form baru untuk GET, 
    # atau form yang tidak valid dengan error untuk POST)
    return render(request, 'reservasi/create_reservation.html', {'form': form, 'profile': profile})

def reservation_success_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'reservasi/reservation_success.html', {'reservation': reservation})

def ajax_get_time_slots(request):
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Tanggal tidak disediakan'}, status=400)
    
    # Tambahkan try-except di sini untuk menangkap error dari get_available_time_slots
    try:
        slots = get_available_time_slots(date_str) 
        return JsonResponse({'time_slots': slots})
    except Exception as e:
        # Log error ini dengan lebih baik di produksi
        print(f"Error in ajax_get_time_slots calling get_available_time_slots: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': 'Terjadi kesalahan internal saat mengambil slot waktu.', 'details': str(e)}, status=500)


def get_available_time_slots(date_selected_str):
    profile = get_restaurant_profile()
    if not profile: # Tambahkan pengecekan eksplisit jika profile None
        print("[DEBUG] get_available_time_slots: No restaurant profile found.")
        return []
    
    if not date_selected_str: 
        print("[DEBUG] get_available_time_slots: date_selected_str is empty.")
        return []

    try: 
        date_selected = datetime.datetime.strptime(date_selected_str, '%Y-%m-%d').date()
    except ValueError: 
        print(f"[DEBUG] get_available_time_slots: Invalid date format for '{date_selected_str}'.")
        return []
    
    available_slots = []
    
    # Pastikan opening_time dan closing_time adalah objek time
    if not isinstance(profile.opening_time, datetime.time) or \
       not isinstance(profile.closing_time, datetime.time):
        print("[DEBUG] get_available_time_slots: opening_time or closing_time is not a valid time object.")
        # Bisa return error atau default slots
        return []

    current_dt = datetime.datetime.combine(date_selected, profile.opening_time)
    closing_dt = datetime.datetime.combine(date_selected, profile.closing_time)
    
    # Safety break untuk loop
    max_loops = (24 * 60) / profile.slot_interval_minutes if profile.slot_interval_minutes > 0 else 100 
    loop_count = 0

    while current_dt < closing_dt and loop_count < max_loops:
        loop_count += 1
        time_slot = current_dt.time()
        
        # aggregate menggunakan 'Sum' yang sudah diimpor
        existing_reservations = Reservation.objects.filter(
            reservation_date=date_selected, 
            reservation_time=time_slot, 
            status__in=['CONFIRMED', 'PENDING'] # Mungkin Anda juga ingin menghitung PENDING
        ).aggregate(total_guests=Sum('number_of_guests')) # Menggunakan Sum
        
        reserved_guests = existing_reservations['total_guests'] or 0
        
        if reserved_guests < profile.max_guests_per_slot:
            remaining_capacity = profile.max_guests_per_slot - reserved_guests
            available_slots.append({
                'time_value': time_slot.strftime('%H:%M:%S'),
                'time_display': time_slot.strftime('%H:%M %p'),
                'remaining_capacity': remaining_capacity
            })
        current_dt += datetime.timedelta(minutes=profile.slot_interval_minutes)
    
    if loop_count >= max_loops:
        print(f"[DEBUG] get_available_time_slots: Max loop count reached for date {date_selected_str}.")

    return available_slots


@login_required
def my_reservations_view(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date', '-reservation_time')
    return render(request, 'reservasi/my_reservations.html', {'reservations': reservations})

@login_required
def cancel_reservation_view(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user) 
    
    # Logika can_cancel dipindahkan ke model atau bisa tetap di sini
    # Untuk konsistensi, jika Anda menggunakan @property di model, gunakan itu.
    # Jika tidak, logika ini oke.
    reservation_datetime_naive = datetime.datetime.combine(reservation.reservation_date, reservation.reservation_time)
    # Membuat datetime aware jika USE_TZ=True. Jika tidak, bisa langsung bandingkan dengan naive now.
    if timezone.is_aware(timezone.now()):
        reservation_datetime_aware = timezone.make_aware(reservation_datetime_naive, timezone.get_current_timezone())
        can_cancel = reservation.status in ['PENDING', 'CONFIRMED', 'WAITLISTED'] and reservation_datetime_aware > timezone.now()
    else: # Jika sistem menggunakan naive datetime (USE_TZ=False)
        can_cancel = reservation.status in ['PENDING', 'CONFIRMED', 'WAITLISTED'] and reservation_datetime_naive > datetime.datetime.now()


    if request.method == 'POST':
        if can_cancel:
            reservation.status = 'CANCELLED'
            reservation.save()
            messages.success(request, "Reservasi Anda telah berhasil dibatalkan.")
        else:
            messages.error(request, "Reservasi ini tidak dapat dibatalkan saat ini.")
        return redirect('reservasi:my_reservations')
    
    return render(request, 'reservasi/confirm_cancel_reservation.html', {'reservation': reservation, 'can_cancel': can_cancel})


# VIEWS UNTUK AUTENTIKASI
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registrasi berhasil! Anda sekarang sudah login.")
            return redirect('reservasi:home')
        else:
            # Mengambil error spesifik dari form jika ada
            error_message = "Registrasi gagal. Harap perbaiki kesalahan di bawah."
            if form.errors:
                # Ambil error pertama untuk ditampilkan (atau gabungkan semua)
                first_field_with_error = next(iter(form.errors))
                error_message += f" ({first_field_with_error.capitalize()}: {form.errors[first_field_with_error][0]})"
            messages.error(request, error_message)
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah berhasil logout.")
    return redirect('reservasi:home')