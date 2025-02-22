from machine import Pin, ADC
import ujson
import network
import utime as time
import dht
import urequests as requests

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)
DEVICE_ID = "sic6-esp32ee"
WIFI_SSID = "Wokwi-GUEST"
WIFI_PASSWORD = ""
TOKEN = "BBUS-MClajoBNluAp2Bkkpj1eVLYzrX8LAU"
DHT_PIN = Pin(15)

def did_receive_callback(topic, message):
    print('\n\nData Received! \ntopic = {0}, message = {1}'.format(topic, message))

def create_json_data(temperature, humidity, light):
    data = ujson.dumps({
        "device_id": DEVICE_ID,
        "temp": temperature,
        "humidity": humidity,
        "light": light,
        "type": "sensor"
    })
    return data

def send_data(temperature, humidity, light):
    url = "http://industrial.api.ubidots.com/api/v1.6/devices/" + DEVICE_ID
    headers = {"Content-Type": "application/json", "X-Auth-Token": TOKEN}
    data = {
        "temp": temperature,
        "humidity": humidity,
        "ldr_value": light
    }
    response = requests.post(url, json=data, headers=headers)
    print("Done Sending Data!")
    print("Response:", response.text)

wifi_client = network.WLAN(network.STA_IF)
wifi_client.active(True)
print("Connecting device to WiFi")
wifi_client.connect(WIFI_SSID, WIFI_PASSWORD)

while not wifi_client.isconnected():
    print("Connecting")
    time.sleep(0.1)
print("WiFi Connected!")
print(wifi_client.ifconfig())

dht_sensor = dht.DHT22(DHT_PIN)
telemetry_data_old = ""

while True:
    try:
        dht_sensor.measure()
        ldr_value = ldr.read()
    except:
        pass

    time.sleep(0.5)

    telemetry_data_new = create_json_data(dht_sensor.temperature(), dht_sensor.humidity(), ldr_value)


    send_data(dht_sensor.temperature(), dht_sensor.humidity(), ldr_value)
    
    time.sleep(5)
