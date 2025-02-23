from machine import Pin, ADC
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

# Konfigurasi Hardware
led = Pin(4, Pin.OUT)
led_red = Pin(2, Pin.OUT)  # LED merah di GPIO2
sensor = dht.DHT11(Pin(5))
pir = Pin(19, Pin.IN)
ldr = ADC(Pin(34))         # GPIO34 (ADC1 CH6)
ldr.atten(ADC.ATTN_11DB)   # Rentang 0-3.3V
ldr.width(ADC.WIDTH_12BIT) # Resolusi 12-bit (0-4095)

# Kalibrasi LDR
LDR_DARK_THRESHOLD = 2500  # Nilai saat kondisi redup (sesuaikan!)
LDR_SAMPLES = 10           # Jumlah sample untuk rata-rata

def read_ldr():
    """Baca nilai LDR dengan rata-rata beberapa sample"""
    total = 0
    for _ in range(LDR_SAMPLES):
        total += ldr.read()
        time.sleep_ms(10)
    return total // LDR_SAMPLES

# Fungsi Koneksi WiFi
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Menghubungkan ke WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        timeout = 10
        while not sta_if.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1

    if sta_if.isconnected():
        print('IP:', sta_if.ifconfig()[0])
    else:
        print('Gagal konek WiFi!')
        raise SystemExit()

# Fungsi MQTT
def connect_mqtt():
    try:
        print("Koneksi ke Ubidots...")
        client = MQTTClient(DEVICE_LABEL, MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD, 60)
        client.connect()
        return client
    except Exception as e:
        print("Gagal MQTT:", e)
        return None

# Main Program
do_connect()
time.sleep(2)
mqtt_client = connect_mqtt()

if not mqtt_client:
    print("MQTT gagal!")
    raise SystemExit()

while True:
    try:
        # Baca semua sensor
        sensor.measure()
        ldr_value = read_ldr()
        suhu = sensor.temperature()
        kelembaban = sensor.humidity()
        gerakan = pir.value()

        # Kontrol LED berdasarkan suhu
        if suhu > 31:
            led.on()
            led_status = 1
            print("🔥 Suhu tinggi! LED menyala.")
        else:
            led.off()
            led_status = 0
            print("✅ Suhu normal. LED mati.")

        # Kontrol LED merah berdasarkan LDR
        if ldr_value > LDR_DARK_THRESHOLD:
            led_red.on()
            led_red_status = 1
            print("🌑 Cahaya redup! LED merah menyala.")
        else:
            led_red.off()
            led_red_status = 0
            print("🌞 Cahaya terang. LED merah mati.")

        # Kirim ke Ubidots
        payload = ujson.dumps({
            "temperature": suhu,  # Diperbaiki dari ldr_value ke suhu
            "humidity": kelembaban,
            "led": led_status,
            "motion": gerakan,
            "ldr": ldr_value
        })
        mqtt_client.publish(MQTT_PUBLISH_TOPIC, payload)
        
        print(f"📡 Data: Temp={suhu}C, Hum={kelembaban}%, LDR={ldr_value}")
        
        time.sleep(0.5)  # Delay diubah menjadi 0.5 detik

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
        mqtt_client = connect_mqtt()
