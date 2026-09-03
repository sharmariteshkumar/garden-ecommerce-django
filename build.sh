#!/usr/bin/env bash
set -o errexit

python manage.py migrate
python manage.py collectstatic --no-input

python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("ADMIN_USERNAME")
email = os.environ.get("ADMIN_EMAIL")
password = os.environ.get("ADMIN_PASSWORD")

if not username or not email or not password:
    raise RuntimeError(
        "ADMIN_USERNAME, ADMIN_EMAIL and ADMIN_PASSWORD must be set in Render Environment."
    )

user, created = User.objects.get_or_create(
    username=username,
    defaults={
        "email": email,
        "is_staff": True,
        "is_superuser": True,
    },
)

user.email = email
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

print(f"Admin user ready: {username}")
PY