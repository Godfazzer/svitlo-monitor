FROM python:3.13-slim

WORKDIR /app

COPY app.py .
COPY fake_schedule.json .

RUN pip install --no-cache-dir flask

CMD ["python", "app.py"]