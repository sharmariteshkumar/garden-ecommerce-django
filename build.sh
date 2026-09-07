#!/usr/bin/env bash
set -o errexit

echo "Installing/migrating database..."
python manage.py migrate --noinput

python manage.py import_plants

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating admin user..."
python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("ADMIN_USERNAME")
email = os.environ.get("ADMIN_EMAIL")
password = os.environ.get("ADMIN_PASSWORD")

if username and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email or "",
            "is_staff": True,
            "is_superuser": True,
        },
    )

    user.email = email or user.email
    user.is_staff = True
    user.is_superuser = True

    if created or not user.check_password(password):
        user.set_password(password)

    user.save()

    print(f"Admin user ready: {username}")
else:
    print("ADMIN_USERNAME or ADMIN_PASSWORD is missing")
PY

echo "Build completed successfully."