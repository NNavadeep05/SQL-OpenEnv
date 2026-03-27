FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p env tasks baseline

EXPOSE 7860

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
