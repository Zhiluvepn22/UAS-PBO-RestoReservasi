from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

# ===================================================================
# MODEL BARU: Untuk Ruangan (Reguler, VIP, dll.)
# ===================================================================
class Room(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nama Ruangan"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Deskripsi"
    )
    capacity = models.PositiveIntegerField(
        help_text="Kapasitas maksimum tamu untuk ruangan ini",
        verbose_name="Kapasitas"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ruangan"
        verbose_name_plural = "Daftar Ruangan"


# ===================================================================
# MODEL BARU: Untuk Paket Makanan
# ===================================================================
class FoodPackage(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nama Paket"
    )
    description = models.TextField(
        help_text="Isi dari paket makanan, misal: Nasi, Ayam Bakar, Teh",
        verbose_name="Deskripsi Paket"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Harga per paket",
        verbose_name="Harga"
    )

    def __str__(self):
        # Format harga agar lebih mudah dibaca
        return f"{self.name} - Rp{self.price:,.0f}"

    class Meta:
        verbose_name = "Paket Makanan"
        verbose_name_plural = "Daftar Paket Makanan"


# ===================================================================
# MODEL LAMA: RestaurantProfile (Tidak ada perubahan)
# ===================================================================
class RestaurantProfile(models.Model):
    name = models.CharField(max_length=100, default="Nama Restoran Kami")
    address = models.TextField(default="Alamat Lengkap Restoran")
    phone_number = models.CharField(max_length=20, default="08123456789")
    description = models.TextField(blank=True, null=True, help_text="Deskripsi singkat tentang restoran")
    opening_time = models.TimeField(default=datetime.time(10, 0))
    closing_time = models.TimeField(default=datetime.time(22, 0))
    slot_interval_minutes = models.PositiveIntegerField(default=30, help_text="Interval slot waktu dalam menit (misal: 30 menit)")
    # Field ini sekarang kurang relevan karena kapasitas diatur per-ruangan,
    # tapi bisa dipertahankan sebagai referensi atau untuk skenario lain.
    max_guests_per_slot = models.PositiveIntegerField(default=20, help_text="Total maksimum tamu yang bisa dilayani dalam satu slot waktu (sekarang digantikan oleh kapasitas per ruangan)")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and RestaurantProfile.objects.exists():
            raise ValueError("Hanya boleh ada satu RestaurantProfile.")
        return super(RestaurantProfile, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Profil Restoran"
        verbose_name_plural = "Profil Restoran"


# ===================================================================
# MODEL LAMA YANG DIMODIFIKASI: Reservation
# ===================================================================
class Reservation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('WAITLISTED', 'Waitlisted'),
    ]

    # --- Detail Pemesan ---
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Akun Pengguna")
    guest_name = models.CharField(max_length=100, verbose_name="Nama Tamu")
    guest_email = models.EmailField(verbose_name="Email Tamu")
    guest_phone = models.CharField(max_length=20, verbose_name="Telepon Tamu")

    # --- Detail Waktu dan Jumlah ---
    reservation_date = models.DateField(verbose_name="Tanggal Reservasi")
    reservation_time = models.TimeField(verbose_name="Waktu Reservasi")
    number_of_guests = models.PositiveIntegerField(verbose_name="Jumlah Tamu")

    # --- PERUBAHAN BARU: Menghubungkan ke Room dan FoodPackage ---
    room_type = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL, # Jika ruangan dihapus, reservasi tidak ikut terhapus
        null=True,                # Harus bisa null sementara
        blank=False,              # Wajib diisi di form
        related_name="reservations",
        verbose_name="Tipe Ruangan"
    )
    food_package = models.ForeignKey(
        FoodPackage,
        on_delete=models.SET_NULL, # Jika paket dihapus, reservasi tidak ikut terhapus
        null=True,
        blank=True,               # Opsional, tidak wajib diisi
        related_name="reservations",
        verbose_name="Paket Makanan"
    )
    # --- AKHIR PERUBAHAN BARU ---

    # --- Detail Tambahan dan Status ---
    special_requests = models.TextField(blank=True, null=True, help_text="Preferensi meja, alergi, perayaan, dll.", verbose_name="Permintaan Khusus")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Dibuat Pada")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Diperbarui Pada")

    def __str__(self):
        # Tampilkan nama ruangan di string representasi
        room_name = self.room_type.name if self.room_type else "Ruangan tidak spesifik"
        if self.user:
            return f"Reservasi {self.user.username} di {room_name} pada {self.reservation_date} @ {self.reservation_time}"
        return f"Reservasi {self.guest_name} di {room_name} pada {self.reservation_date} @ {self.reservation_time}"

    class Meta:
        ordering = ['reservation_date', 'reservation_time']
        verbose_name = "Reservasi"
        verbose_name_plural = "Semua Reservasi"