FROM python:3.13-slim

WORKDIR /app

COPY app.py .

RUN pip install --no-cache-dir flask

CMD ["python", "app.py"]