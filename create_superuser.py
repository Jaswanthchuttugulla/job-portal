"""
Automatic superuser creation script.

Run with: python create_superuser.py

Reads ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD from environment
variables. Creates the superuser only if a user with that username does
not already exist. Never overwrites an existing user's password and
never prints the password to the console or logs.
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jobboard_ats.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402


def main():
    username = os.environ.get("ADMIN_USERNAME")
    email = os.environ.get("ADMIN_EMAIL", "")
    password = os.environ.get("ADMIN_PASSWORD")

    if not username or not password:
        print(
            "ADMIN_USERNAME and ADMIN_PASSWORD environment variables are not "
            "both set - skipping automatic superuser creation."
        )
        return

    User = get_user_model()

    try:
        if User.objects.filter(username=username).exists():
            print(f"Superuser '{username}' already exists - skipping creation.")
            return

        User.objects.create_superuser(
            username=username, email=email, password=password
        )
        print(f"Superuser '{username}' created successfully.")
    except Exception as exc:  # noqa: BLE001 - report safely, never re-raise secrets
        print(f"Could not create superuser due to an error: {exc.__class__.__name__}")
        sys.exit(0)


if __name__ == "__main__":
    main()
