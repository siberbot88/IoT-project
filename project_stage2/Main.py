from machine import Pin
import time
import dht
import ujson
import network
from umqtt.simple import MQTTClient

# Konfigurasi WiFi
WIFI_SSID = "esp32"
WIFI_PASS = "none1234"

# Konfigurasi MQTT Ubidots
UBIDOTS_TOKEN = "BBUS-MClajoBNluAp2Bkkpj1eVLYzrX8LAU"
DEVICE_LABEL = "sic6-esp32ee"
MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883
MQTT_USER = UBIDOTS_TOKEN
MQTT_PASSWORD = ""
MQTT_PUBLISH_TOPIC = f"/v1.6/devices/{DEVICE_LABEL}"

# Konfigurasi LED & Sensor
led = Pin(4, Pin.OUT)
sensor = dht.DHT11(Pin(5))
pir = Pin(19, Pin.IN)  # Tambah konfigurasi PIR

# Fungsi Koneksi WiFi
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Menghubungkan ke jaringan WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        timeout = 10
        while not sta_if.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

    if sta_if.isconnected():
        print('Terhubung ke WiFi dengan IP:', sta_if.ifconfig()[0])
    else:
        print('Gagal terhubung ke WiFi!')
        raise SystemExit()

# Fungsi Koneksi ke MQTT
def connect_mqtt():
    try:
        print("Menghubungkan ke Ubidots MQTT... ", end="")
        client = MQTTClient(DEVICE_LABEL, MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD, keepalive=60)
        client.connect()
        print("Terhubung ke Ubidots!")
        return client
    except Exception as e:
        print("Gagal terhubung ke MQTT:", e)
        return None

# Mulai Program
do_connect()
time.sleep(2)
mqtt_client = connect_mqtt()

if mqtt_client is None:
    print("Koneksi MQTT gagal, cek kembali pengaturan!")
    raise SystemExit()

# Loop utama
while True:
    try:
        # Baca Sensor
        sensor.measure()
        suhu = sensor.temperature()
        kelembaban = sensor.humidity()
        gerakan = pir.value()  # Baca nilai PIR

        # Kontrol LED berdasarkan suhu
        if suhu > 30:
            led.on()
            led_status = 1
            print("🔥 Suhu tinggi! LED menyala.")
        else:
            led.off()
            led_status = 0
            print("✅ Suhu normal. LED mati.")

        # Kirim Data ke Ubidots
        message = ujson.dumps({
            "temperature": {"value": suhu},
            "humidity": {"value": kelembaban},
            "led": {"value": led_status},
            "motion": {"value": gerakan}  # Tambah data PIR
        })
        mqtt_client.publish(MQTT_PUBLISH_TOPIC, message)
        print(f"📡 Data dikirim ke Ubidots: {message}")
        print(f"🚨 Status Gerakan: {'Terdeteksi' if gerakan else 'Tidak Ada'}")
        
        time.sleep(0.2)  # Kirim data setiap 5 detik

    except Exception as e:
        print("Error:", e)
        print("Mencoba reconnect dalam 5 detik...")
        time.sleep(1)
        mqtt_client = connect_mqtt()
