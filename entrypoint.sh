#!/usr/bin/env bash
set -e

echo "Esperando a MySQL..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done
echo "MySQL disponible."

echo "Migrando base de datos..."
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000
