from django import forms
from .models import Reservation, RestaurantProfile, Room, FoodPackage # TAMBAHKAN Room & FoodPackage
from django.utils import timezone
import datetime
from django.db.models import Sum

class ReservationForm(forms.ModelForm):
    # ===================================================================
    # FIELD FORM BARU DIDEFINISIKAN DI SINI
    # ===================================================================
    room_type = forms.ModelChoiceField(
        queryset=Room.objects.all().order_by('name'), # Ambil semua objek Room
        label="Tipe Ruangan",
        empty_label="-- Pilih Ruangan --", # Teks untuk pilihan kosong
        widget=forms.Select() # Nanti di-style di template dengan widget_tweaks
    )
    
    food_package = forms.ModelChoiceField(
        queryset=FoodPackage.objects.all().order_by('name'), # Ambil semua objek FoodPackage
        label="Paket Makanan (Opsional)",
        required=False, # Penting! Membuat field ini tidak wajib diisi
        empty_label="-- Tanpa Paket Makanan --",
        widget=forms.Select()
    )

    # --- Field lama ---
    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Reservation
        # ===================================================================
        # MENAMBAHKAN FIELD BARU KE DAFTAR & MENGATUR URUTAN
        # ===================================================================
        fields = [
            'room_type',  # <-- Field baru
            'reservation_date', 
            'reservation_time', 
            'number_of_guests',
            'food_package', # <-- Field baru
            'guest_name', 
            'guest_email', 
            'guest_phone',
            'special_requests', 
        ]
        
        widgets = {
            'guest_name': forms.TextInput(attrs={'placeholder': 'Nama Anda'}),
            'guest_email': forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'guest_phone': forms.TextInput(attrs={'placeholder': 'Nomor Telepon'}),
            'number_of_guests': forms.NumberInput(attrs={'min': '1'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Preferensi meja, alergi, perayaan ulang tahun, dll.'}),
            'reservation_time': forms.Select(),
        }
        
        # ===================================================================
        # MENAMBAHKAN LABEL UNTUK FIELD BARU
        # ===================================================================
        labels = {
            'room_type': 'Tipe Ruangan', # <-- Label baru
            'food_package': 'Paket Makanan (Opsional)', # <-- Label baru
            'guest_name': 'Nama Lengkap',
            'guest_email': 'Alamat Email',
            'guest_phone': 'Nomor Telepon',
            'reservation_date': 'Tanggal Reservasi',
            'reservation_time': 'Waktu Reservasi',
            'number_of_guests': 'Jumlah Tamu',
            'special_requests': 'Permintaan Khusus (Opsional)',
        }

    # __init__ dan clean_* methods tetap sama seperti sebelumnya, tidak perlu diubah untuk penambahan field ini
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if self.user and self.user.is_authenticated:
            if not self.initial.get('guest_name') and (self.user.get_full_name() or self.user.username):
                 self.initial['guest_name'] = self.user.get_full_name() or self.user.username
            if not self.initial.get('guest_email') and self.user.email: 
                 self.initial['guest_email'] = self.user.email
            
        profile = RestaurantProfile.objects.first()
        time_choices = [('', 'Pilih Waktu')]
        if profile and profile.opening_time and profile.closing_time and profile.slot_interval_minutes and profile.slot_interval_minutes > 0:
            try:
                current_time_dt = datetime.datetime.combine(datetime.date.today(), profile.opening_time)
                closing_time_dt = datetime.datetime.combine(datetime.date.today(), profile.closing_time)
                max_loops = (24 * 60) // profile.slot_interval_minutes
                loop_count = 0
                while current_time_dt < closing_time_dt and loop_count < max_loops:
                    loop_count += 1
                    time_choices.append((current_time_dt.time().strftime('%H:%M:%S'), current_time_dt.time().strftime('%H:%M %p')))
                    current_time_dt += datetime.timedelta(minutes=profile.slot_interval_minutes)
            except Exception as e:
                print(f"[ERROR Form Init] Generating time choices: {e}")
        self.fields['reservation_time'].widget.choices = time_choices

    def clean_reservation_date(self):
        date = self.cleaned_data.get('reservation_date')
        if date and date < timezone.now().date():
            raise forms.ValidationError("Tanggal reservasi tidak boleh di masa lalu.")
        return date

    def clean_number_of_guests(self):
        guests = self.cleaned_data.get('number_of_guests')
        if guests is not None and guests <= 0:
            raise forms.ValidationError("Jumlah tamu harus lebih dari 0.")
        return guests
        
    def clean(self):
        # ===================================================================
        # PERUBAHAN TOTAL PADA LOGIKA VALIDASI KAPASITAS
        # ===================================================================
        cleaned_data = super().clean()
        
        # Ambil data yang relevan dari form
        room = cleaned_data.get('room_type')
        date = cleaned_data.get('reservation_date')
        time_str = cleaned_data.get('reservation_time')
        num_guests = cleaned_data.get('number_of_guests')

        # Validasi field guest jika user tidak login atau tidak punya email
        if not (self.user and self.user.is_authenticated):
            if not cleaned_data.get('guest_name'): self.add_error('guest_name', 'Nama tidak boleh kosong.')
            if not cleaned_data.get('guest_email'): self.add_error('guest_email', 'Email tidak boleh kosong.')
            if not cleaned_data.get('guest_phone'): self.add_error('guest_phone', 'Nomor telepon tidak boleh kosong.')
        elif self.user and self.user.is_authenticated:
            if not self.user.email and not cleaned_data.get('guest_email'): self.add_error('guest_email', 'Email tidak boleh kosong untuk reservasi ini.')
            if not cleaned_data.get('guest_phone'): self.add_error('guest_phone', 'Nomor telepon tidak boleh kosong.')

        # Hentikan validasi lebih lanjut jika sudah ada error atau data inti belum ada
        if self.errors or not all([room, date, time_str, num_guests]):
            return cleaned_data
        
        # Validasi 1: Cek apakah jumlah tamu melebihi kapasitas ruangan yang dipilih
        if num_guests > room.capacity:
            self.add_error('number_of_guests', f"Jumlah tamu ({num_guests}) melebihi kapasitas {room.name} ({room.capacity} orang).")
            # Langsung hentikan validasi lebih lanjut jika sudah error di sini
            return cleaned_data

        # --- Validasi waktu (tetap sama) ---
        try:
            if isinstance(time_str, str): time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
            elif isinstance(time_str, datetime.time): time_obj = time_str
            else: raise ValueError("Format waktu tidak dikenal")
        except ValueError:
            self.add_error('reservation_time', "Waktu reservasi tidak valid.")
            return cleaned_data

        profile = RestaurantProfile.objects.first()
        if not profile or not isinstance(profile.opening_time, datetime.time) or not isinstance(profile.closing_time, datetime.time):
            raise forms.ValidationError("Pengaturan jam operasional restoran tidak valid.")
        
        if not (profile.opening_time <= time_obj < profile.closing_time):
            self.add_error('reservation_time', f"Restoran hanya buka dari {profile.opening_time.strftime('%H:%M')} sampai {profile.closing_time.strftime('%H:%M')}.")
            return cleaned_data

        # Validasi 2: Cek ketersediaan slot untuk RUANGAN SPESIFIK tersebut
        existing_reservations_in_room = Reservation.objects.filter(
            room_type=room,  # <-- Filter berdasarkan ruangan yang dipilih
            reservation_date=date,
            reservation_time=time_obj,
            status__in=['CONFIRMED', 'PENDING']
        )
        
        total_guests_in_room = existing_reservations_in_room.aggregate(
            total=Sum('number_of_guests')
        )['total'] or 0

        # Cek apakah penambahan tamu baru akan melebihi kapasitas ruangan
        if (total_guests_in_room + num_guests) > room.capacity:
            self.add_error(None, f"Maaf, slot di {room.name} pada jam {time_obj.strftime('%H:%M')} sudah penuh atau tidak cukup untuk {num_guests} orang.")
            self.is_waitlist_candidate = True 
        else:
            self.is_waitlist_candidate = False
            
        return cleaned_data