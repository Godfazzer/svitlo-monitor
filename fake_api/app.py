from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

@app.route("/schedule-by-queue")
def schedule():
    hours = os.getenv("QUEUE_FAKE_HOURS", "08:00-10:00")
    status = os.getenv("QUEUE_FAKE_STATUS", "1")
    empty = os.getenv("QUEUE_FAKE_EMPTY", "0")  # 1 = return []

    if empty == "1":
        return jsonify([])

    from_time, to_time = hours.split("-")
    today = datetime.now().strftime("%d.%m.%Y")
    queue_id = request.args.get("queue", "fake")

    data = [
        {
            "eventDate": today,
            "queues": {
                queue_id: [
                    {
                        "shutdownHours": hours,
                        "from": from_time,
                        "to": to_time,
                        "status": int(status)
                    }
                ]
            },
            "createdAt": f"{today} 07:35",
            "scheduleApprovedSince": f"{today} 07:35"
        }
    ]

    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
