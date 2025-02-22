from machine import Pin, unique_id
import time
import dht
import ujson
import network
from umqtt.simple import MQTTClient
import ubinascii

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
pir = Pin(19, Pin.IN)

# Hasilkan Client ID unik
CLIENT_ID = f"{DEVICE_LABEL}-{ubinascii.hexlify(unique_id()).decode()}"

# Variabel global untuk koneksi
sta_if = network.WLAN(network.STA_IF)
mqtt_client = None

def do_connect():
    if not sta_if.isconnected():
        print('Menghubungkan ke WiFi...')
        sta_if.active(True)
        sta_if.connect(WIFI_SSID, WIFI_PASS)
        
        timeout = 20  # Tambah timeout
        while not sta_if.isconnected() and timeout > 0:
            print('.', end='')
            time.sleep(1)
            timeout -= 1
            
    if sta_if.isconnected():
        print('\nIP:', sta_if.ifconfig()[0])
        return True
    else:
        print('\nGagal terhubung WiFi!')
        return False

def connect_mqtt():
    global mqtt_client
    try:
        if mqtt_client:
            mqtt_client.disconnect()
            
        print("Connecting MQTT...")
        mqtt_client = MQTTClient(
            CLIENT_ID,
            MQTT_BROKER,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASSWORD,
            keepalive=120  # Tambah keepalive
        )
        mqtt_client.connect()
        print("MQTT Connected!")
        return True
    except Exception as e:
        print("MQTT Error:", e)
        mqtt_client = None
        return False

def reconnect():
    print("\nAttempting reconnect...")
    if do_connect() and connect_mqtt():
        return True
    return False

def read_sensor():
    try:
        sensor.measure()
        return {
            'temperature': sensor.temperature(),
            'humidity': sensor.humidity(),
            'motion': pir.value()
        }
    except Exception as e:
        print("Sensor Error:", e)
        return None

# Main Program
if not do_connect():
    raise SystemExit()

if not connect_mqtt():
    raise SystemExit()

last_publish = time.time()
publish_interval = 5  # 5 detik

while True:
    try:
        # Cek koneksi WiFi
        if not sta_if.isconnected():
            reconnect()
            continue
            
        # Cek koneksi MQTT
        if not mqtt_client:
            connect_mqtt()
            time.sleep(2)
            continue
            
        # Baca sensor setiap interval
        if time.time() - last_publish >= publish_interval:
            data = read_sensor()
            if not data:
                continue
                
            # Kontrol LED
            led_status = 1 if data['temperature'] > 30 else 0
            led.value(led_status)
            
            # Format payload
            payload = ujson.dumps({
                "temperature": data['temperature'],
                "humidity": data['humidity'],
                "led": led_status,
                "motion": data['motion']
            })
            
            # Publish data
            mqtt_client.publish(MQTT_PUBLISH_TOPIC, payload)
            print(f"Data terkirim: {payload}")
            last_publish = time.time()
            
        # Maintenance connection
        mqtt_client.check_msg()
        time.sleep(0.5)
        
    except Exception as e:
        print("Main Error:", e)
        print("Reconnecting in 5s...")
        time.sleep(5)
        reconnect()