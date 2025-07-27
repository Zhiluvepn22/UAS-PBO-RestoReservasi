from django.contrib import admin
from .models import RestaurantProfile, Reservation, Room, FoodPackage # TAMBAHKAN Room & FoodPackage

# ===================================================================
# ADMIN UNTUK MODEL LAMA: RestaurantProfile (Tidak ada perubahan)
# ===================================================================
@admin.register(RestaurantProfile)
class RestaurantProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'opening_time', 'closing_time', 'max_guests_per_slot')
    
    # Mencegah penambahan lebih dari satu profil restoran
    def has_add_permission(self, request):
        return not RestaurantProfile.objects.exists()

# ===================================================================
# ADMIN UNTUK MODEL BARU: Room
# ===================================================================
@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """
    Konfigurasi panel admin untuk mengelola Ruangan.
    Memungkinkan admin untuk menambah, mengubah, dan menghapus ruangan.
    """
    list_display = ('name', 'capacity', 'description')
    search_fields = ('name',)
    ordering = ('name',)

# ===================================================================
# ADMIN UNTUK MODEL BARU: FoodPackage
# ===================================================================
@admin.register(FoodPackage)
class FoodPackageAdmin(admin.ModelAdmin):
    """
    Konfigurasi panel admin untuk mengelola Paket Makanan.
    Memungkinkan admin untuk menambah, mengubah, dan menghapus paket.
    """
    list_display = ('name', 'price', 'description')
    search_fields = ('name',)
    ordering = ('price',)
    
    # Format kolom harga agar lebih rapi
    def price_formatted(self, obj):
        return f"Rp {obj.price:,.0f}"
    price_formatted.short_description = 'Harga'
    price_formatted.admin_order_field = 'price'

    # Ganti 'price' dengan 'price_formatted' di list_display jika ingin formatnya tampil
    # Contoh: list_display = ('name', 'price_formatted', 'description')


# ===================================================================
# ADMIN UNTUK MODEL LAMA YANG DIMODIFIKASI: Reservation
# ===================================================================
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """
    Konfigurasi panel admin untuk mengelola Reservasi.
    Tampilan diperbarui untuk menyertakan informasi ruangan dan paket makanan.
    """
    # Menambahkan 'room_type' dan 'food_package' ke list_display agar terlihat di tabel
    list_display = (
        'guest_name', 
        'reservation_date', 
        'reservation_time', 
        'room_type',  # <-- Ditambahkan
        'number_of_guests',
        'food_package',  # <-- Ditambahkan
        'status', 
        'created_at'
    )
    
    # Menambahkan 'room_type' ke filter agar bisa menyaring reservasi per ruangan
    list_filter = ('status', 'reservation_date', 'room_type')
    
    # Search fields tidak perlu diubah, tapi bisa ditambahkan jika ingin mencari berdasarkan nama ruangan
    search_fields = ('guest_name', 'guest_email', 'guest_phone', 'room_type__name')
    
    # Actions tetap sama
    actions = ['confirm_reservations', 'cancel_reservations', 'mark_as_waitlisted']

    # Membuat field-field tertentu read-only di halaman detail admin untuk mencegah perubahan tidak sengaja
    readonly_fields = ('created_at', 'updated_at')

    # Mengelompokkan field di halaman edit/tambah agar lebih rapi
    fieldsets = (
        ('Detail Pemesan', {
            'fields': ('user', ('guest_name', 'guest_email', 'guest_phone'))
        }),
        ('Detail Reservasi', {
            'fields': (('reservation_date', 'reservation_time'), ('room_type', 'number_of_guests'), 'food_package', 'special_requests')
        }),
        ('Status', {
            'fields': ('status', ('created_at', 'updated_at'))
        }),
    )

    def confirm_reservations(self, request, queryset):
        queryset.update(status='CONFIRMED')
    confirm_reservations.short_description = "Tandai sebagai Dikonfirmasi"

    def cancel_reservations(self, request, queryset):
        queryset.update(status='CANCELLED')
    cancel_reservations.short_description = "Tandai sebagai Dibatalkan"

    def mark_as_waitlisted(self, request, queryset):
        queryset.update(status='WAITLISTED')
    mark_as_waitlisted.short_description = "Masukkan ke Waiting List"