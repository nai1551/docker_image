FROM python:3.11-slim

WORKDIR /app

COPY app.py .
COPY test_app.py .

RUN pip install flask mysql-connector-python pytest

CMD ["python3", "app.py"]



