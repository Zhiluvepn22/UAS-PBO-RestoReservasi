# Proyek Reservasi Restoran (ResResto)

## Deskripsi Singkat

ResResto adalah aplikasi web yang dibangun menggunakan Django untuk mengelola reservasi di sebuah restoran. Aplikasi ini memungkinkan pengguna untuk membuat, melihat, dan membatalkan reservasi mereka, sementara admin dapat mengelola detail restoran, ketersediaan, dan semua data reservasi.

## Fitur Utama

- **Reservasi Online**: Pengguna dapat dengan mudah membuat reservasi dengan memilih tanggal, waktu, jumlah tamu, tipe ruangan, dan paket makanan.
- **Manajemen Pengguna**: Sistem registrasi dan otentikasi pengguna (Login/Logout).
- **Reservasi Saya**: Halaman khusus bagi pengguna untuk melihat riwayat dan status reservasi mereka.
- **Pembatalan Reservasi**: Pengguna dapat membatalkan reservasi yang akan datang.
- **Ketersediaan Real-time**: Slot waktu yang tersedia ditampilkan secara dinamis berdasarkan reservasi yang sudah ada.
- **Sistem Waitlist**: Jika slot waktu yang diinginkan penuh, pengguna dapat memilih untuk masuk ke dalam daftar tunggu.
- **Admin Panel**: Panel admin Django yang sudah disesuaikan untuk mengelola profil restoran, ruangan, paket makanan, dan semua reservasi.

## Teknologi yang Digunakan

- **Backend**: Django
- **Database**: SQLite3 (untuk pengembangan)
- **Frontend**: Django Templates, HTML, CSS (dan sedikit JavaScript untuk AJAX)
- **Styling**: `widget_tweaks` untuk mempermudah rendering form Django.

## Panduan Instalasi dan Setup

1.  **Clone repository ini:**
    ```bash
    git clone <URL_REPOSITORY_ANDA>
    cd <NAMA_DIREKTORI_PROYEK>
    ```

2.  **Buat dan aktifkan virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\\Scripts\\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Lakukan migrasi database:**
    ```bash
    python ResResto/manage.py migrate
    ```

5.  **Buat superuser untuk mengakses admin panel:**
    ```bash
    python ResResto/manage.py createsuperuser
    ```

## Cara Menjalankan Proyek

1.  **Jalankan development server:**
    ```bash
    python ResResto/manage.py runserver
    ```

2.  Buka browser Anda dan akses alamat `http://127.0.0.1:8000/`.

3.  Untuk mengakses admin panel, buka `http://127.0.0.1:8000/admin/` dan login menggunakan akun superuser yang telah Anda buat.

## Struktur Proyek

```
.
├── ResResto/                # Direktori utama proyek Django
│   ├── ResResto/            # Direktori konfigurasi proyek
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── ...
│   ├── reservasi/           # Aplikasi 'reservasi'
│   │   ├── models.py        # Model data (Reservation, Room, FoodPackage, dll.)
│   │   ├── views.py         # Logika dan views
│   │   ├── forms.py         # Form untuk reservasi
│   │   ├── urls.py          # URL-routing untuk aplikasi reservasi
│   │   ├── admin.py         # Konfigurasi admin panel
│   │   └── ...
│   ├── static/              # File statis (CSS, JS, gambar)
│   ├── templates/           # Template HTML
│   │   ├── base.html
│   │   ├── reservasi/
│   │   └── registration/
│   └── manage.py            # Utilitas command-line Django
├── requirements.txt         # Daftar dependensi Python
└── README.md                # File ini
```
