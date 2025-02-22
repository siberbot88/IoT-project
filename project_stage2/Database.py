from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from bson import json_util
import json

app = Flask(__name__)

# MongoDB Configuration
uri = "mongodb+srv://siberbot88:xXQ9H3uDpZkwIMPR@cluster-siberbot88.sw4in.mongodb.net/?retryWrites=true&w=majority&appName=Cluster-Siberbot88"
client = MongoClient(uri)
db = client['MyDatabase']
collection = db['SensorData']

def parse_json(data):
    return json.loads(json_util.dumps(data))

@app.route('/api/data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()
        
        # Validasi data
        required_fields = ['temperature', 'humidity', 'motion']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Hitung average dan tambahkan timestamp
        timestamp = data.get('timestamp', datetime.utcnow())
        avg = (data['temperature'] + data['humidity']) / 2
        
        document = {
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'motion': data['motion'],
            'timestamp': timestamp,
            'average': avg
        }

        # Simpan ke MongoDB
        result = collection.insert_one(document)
        return jsonify({"message": "Data saved successfully", "id": str(result.inserted_id)}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_all_data():
    try:
        # Ambil semua data dari database
        data = list(collection.find({}, {'_id': 0}))
        
        # Hitung rata-rata keseluruhan
        total_docs = len(data)
        if total_docs == 0:
            return jsonify({"data": [], "averages": {}}), 200

        totals = {
            'temperature': 0,
            'humidity': 0,
            'motion': 0,
            'average': 0
        }

        for doc in data:
            totals['temperature'] += doc['temperature']
            totals['humidity'] += doc['humidity']
            totals['motion'] += doc['motion']
            totals['average'] += doc['average']

        averages = {k: v/total_docs for k, v in totals.items()}

        return jsonify({
            "data": parse_json(data),
            "averages": averages
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)