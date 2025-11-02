from flask import Flask, request, jsonify
import os
import json

app = Flask(__name__)

FAKE_JSON_FILE = "/app/fake_schedule.json"

@app.route("/schedule-by-queue")
def schedule():
    try:
        if not os.path.exists(FAKE_JSON_FILE):
            return jsonify([])

        with open(FAKE_JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return jsonify(data)
    except Exception as e:
        print("Error reading fake JSON:", e)
        return jsonify([])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
