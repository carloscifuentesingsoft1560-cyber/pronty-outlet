FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SECRET_KEY=build-only-secret \
    DEBUG=True \
    python manage.py collectstatic --noinput

CMD exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --threads 4 \
    --timeout 120
