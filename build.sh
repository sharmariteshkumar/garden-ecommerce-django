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

if username and email and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        }
    )

    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.set_password(password)
    user.save()

    print("Admin user ready:", username)
else:
    print("ERROR: ADMIN_USERNAME, ADMIN_EMAIL or ADMIN_PASSWORD is missing.")
PY