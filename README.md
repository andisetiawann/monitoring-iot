🌊 River Monitoring System
Django + IoT (Flow & SRF Sensor) + Chart.js + Leaflet + Telegram Alert

Sistem ini dibuat untuk melakukan monitoring kondisi sungai secara real-time menggunakan sensor flow (kecepatan aliran) dan SRF (ketinggian air). Data dikirim dari perangkat IoT (ESP32/ESP8266/Arduino) menuju server Django melalui endpoint API.

Fiturnya meliputi:

Dashboard monitoring dengan grafik riwayat (Chart.js)

Peta lokasi sensor (Leaflet)

API ingest data untuk IoT

Threshold (Warning & Danger)

Notifikasi Telegram otomatis

Export data CSV

Sistem login (Auth Django)

🚀 Tech Stack

Backend: Django 6

Frontend: Chart.js, jQuery, Leaflet

Database: SQLite / PostgreSQL

IoT: ESP32/ESP8266/Arduino

Integrasi Notifikasi: Telegram Bot API

📦 Instalasi & Setup
1️⃣ Clone Repository
git clone https://github.com/username/river-monitoring.git
cd river-monitoring

2️⃣ Buat Virtual Environment
python -m venv venv
source venv/bin/activate     # Mac/Linux
venv\Scripts\activate        # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Migrasi Database
python manage.py makemigrations
python manage.py migrate

5️⃣ Buat Superuser
python manage.py createsuperuser

6️⃣ Jalankan Server
python manage.py runserver


Buka di browser:
👉 http://127.0.0.1:8000/

🗂 Struktur Project
sungai_monitor/
│
├── monitor/
│   ├── models.py       # Sensor, Reading, Threshold
│   ├── views.py        # Dashboard + API Ingest + CSV Export
│   ├── urls.py
│   └── templates/monitor/dashboard.html
│
├── sungai_monitor/
│   ├── settings.py
│   ├── urls.py
│
├── README.md
└── manage.py

📡 API Dokumentasi (untuk IoT)
1️⃣ Kirim Data Sensor (IoT → Server)
Endpoint
POST /api/ingest/

JSON Body:
{
  "identifier": "sensor-flow-1",
  "timestamp": "2025-12-11T12:30:00Z",
  "value": 20.5,
  "raw": {
    "detail": "original sensor data"
  }
}

Response:
{
  "status": "ok",
  "id": 55
}

Sample ESP32 Code:
HTTPClient http;
http.begin("http://your-ip/api/ingest/");
http.addHeader("Content-Type", "application/json");

String payload = "{\"identifier\":\"flow-1\",\"value\":23.5}";
http.POST(payload);
http.end();

📊 Dashboard & Fitur
✔ Grafik Riwayat Sensor

Chart.js menampilkan data terakhir (default 50 data):

Endpoint digunakan oleh AJAX:

GET /api/latest/<sensor_id>/?limit=50

✔ Peta Lokasi Sensor

Menggunakan Leaflet:

Menampilkan marker lokasi sensor (lat/lon)

Auto-fit map ke lokasi semua sensor

✔ Export CSV
/export/csv/<sensor_id>/


File berisi:

timestamp,value
2025-12-11T12:00:00Z,10.5
2025-12-11T12:05:00Z,11.2
...

⚠️ Threshold & Notifikasi Telegram

Setiap sensor bisa memiliki:

warn_value

danger_value

notify_telegram (on/off)

telegram_chat_id

Jika data baru melebihi ambang:

Bot Telegram akan mengirimkan notifikasi otomatis:

Contoh:

⚠️ DANGER: Sensor Sungai A value 180 >= 150

Setup Telegram Bot

Buka @BotFather

Buat bot → ambil TOKEN

Tambah ke settings.py:

TELEGRAM_BOT_TOKEN = "123456:ABC-xyz"


Ambil chat_id via:

https://api.telegram.org/bot<token>/getUpdates


Isi pada menu Threshold di Django Admin.

🔐 Login, Role & Permission

Menggunakan auth Django default.
Role disarankan:

Admin → mengelola sensor, threshold, user

Operator → hanya melihat dashboard

🧪 Data Dummy (Optional)

Masukkan lewat Django shell:

python manage.py shell

from monitor.models import Sensor, Reading
from django.utils import timezone
import random

s = Sensor.objects.create(name="Flow Sungai A", sensor_type="flow", latitude=-5.123, longitude=105.12)

for i in range(50):
    Reading.objects.create(
        sensor=s,
        timestamp=timezone.now(),
        value=random.uniform(10,40)
    )

📜 Lisensi

MIT License — bebas dipakai untuk project kampus maupun produk IoT.

📞 Kontak & Kontribusi

Jika ingin menambah fitur:

Websocket real-time (tanpa polling)

Mobile-friendly UI (Bootstrap/Tailwind)

Multi-sensor analytics

AI anomaly detection

Cukup buat issue atau hubungi developer.

🎉 Selesai!

README ini sudah lengkap untuk GitHub dan mudah digunakan oleh siapa pun yang ingin menjalankan project monitoring sungai.
