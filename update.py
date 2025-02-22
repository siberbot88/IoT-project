from machine import Pin, Timer
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
sensor = dht.DHT11(Pin(5))
pir = Pin(16, Pin.IN)

# Variabel Global
last_temp = None
last_humidity = None
last_motion = 0
last_publish = 0
publish_interval = 5000  # 5 detik dalam milisekon

# Timer Virtual
tim = Timer(-1)

# Fungsi Koneksi WiFi (Non-Blocking)
def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Menghubungkan WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        tim.init(period=500, mode=Timer.PERIODIC, callback=lambda t: check_wifi(sta_if))

def check_wifi(sta_if):
    if sta_if.isconnected():
        print('\nTerhubung WiFi! IP:', sta_if.ifconfig()[0])
        tim.deinit()
        connect_mqtt()
    else:
        print('.', end='')

# Fungsi MQTT (Asinkron)
def connect_mqtt():
    global mqtt_client
    try:
        mqtt_client = MQTTClient(DEVICE_LABEL, MQTT_BROKER, port=MQTT_PORT, 
                               user=MQTT_USER, password=MQTT_PASSWORD)
        mqtt_client.connect()
        print("MQTT Terhubung!")
        tim.init(period=100, mode=Timer.PERIODIC, callback=main_loop)
    except Exception as e:
        print("MQTT Error:", e)
        tim.init(period=5000, mode=Timer.ONE_SHOT, callback=lambda t: connect_mqtt())

# Main Loop Non-Blocking
def main_loop(t):
    global last_temp, last_humidity, last_motion, last_publish
    
    try:
        # Baca sensor DHT11 setiap 2 detik
        if time.ticks_diff(time.ticks_ms(), last_publish) >= 2000:
            sensor.measure()
            last_temp = sensor.temperature()
            last_humidity = sensor.humidity()
            
            # Kontrol LED
            led.value(1 if last_temp > 30 else 0)
        
        # Baca PIR secara real-time
        current_motion = pir.value()
        motion_changed = current_motion != last_motion
        
        # Kirim data jika ada perubahan atau interval terpenuhi
        if motion_changed or time.ticks_diff(time.ticks_ms(), last_publish) >= publish_interval:
            payload = {
                "temperature": last_temp,
                "humidity": last_humidity,
                "led": led.value(),
                "motion": current_motion
            }
            
            try:
                mqtt_client.publish(MQTT_PUBLISH_TOPIC, ujson.dumps(payload))
                print("📡 Data Terkirim:", payload)
                last_publish = time.ticks_ms()
                last_motion = current_motion
            except Exception as e:
                print("Publish Error:", e)
                connect_mqtt()
                
    except Exception as e:
        print("Sensor Error:", e)

# Inisialisasi Program
do_connect()