"""Create the first Django administrator from Container secrets, once."""
from __future__ import annotations

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

import django

django.setup()

from django.contrib.auth import get_user_model


def main() -> None:
    username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "").strip()
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "").strip()
    if not username and not password:
        print("Bootstrap admin not configured; no administrator was created.")
        return
    if not username or not password:
        raise RuntimeError("Set both BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD.")
    user_model = get_user_model()
    if user_model.objects.filter(username=username).exists():
        print(f"Bootstrap administrator {username!r} already exists; leaving it unchanged.")
        return
    user_model.objects.create_superuser(username=username, email=email, password=password)
    print(f"Created initial Django administrator {username!r}.")


if __name__ == "__main__":
    main()
