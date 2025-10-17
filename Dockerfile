FROM python:3.13-slim

WORKDIR /app

COPY svitlo_monitor.py .

RUN pip install --no-cache-dir requests

CMD ["python", "svitlo_monitor.py"]