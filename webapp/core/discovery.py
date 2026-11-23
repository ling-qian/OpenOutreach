"""Workspace-isolated adapter for the OpenOutFind CLI.

OpenOutFind owns its discovery/ICP pipeline. Each workspace gets a separate SQLite
store, avoiding cross-workspace leakage from its install-level lead tables.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings


def discover(workspace, profile, count: int = 5) -> list[dict]:
    if not 1 <= count <= 25:
        raise ValueError("Discovery count must be between 1 and 25.")
    required = ("OPENOUTFIND_BETTERCONTACT_API_KEY", "OPENOUTFIND_AI_MODEL", "OPENOUTFIND_LLM_API_KEY")
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise ValueError("Server discovery configuration is missing: " + ", ".join(missing))
    if not profile or not profile.ideal_customer_description.strip():
        raise ValueError("Complete the Ideal Customer Description in Service Profile first.")
    state_dir = Path(settings.BASE_DIR) / "var" / "openoutfind" / f"workspace-{workspace.pk}"
    state_dir.mkdir(parents=True, exist_ok=True)
    database = state_dir / "leads.sqlite3"
    env = os.environ.copy()
    env["OPENOUTFIND_CAMPAIGN_TARGET"] = profile.ideal_customer_description
    env["OPENOUTFIND_PRODUCT_DOCS"] = profile.service_description or profile.service_name or "Professional services"
    command = [sys.executable, "-m", "openoutfind", "--db", str(database), "find", str(count), "--json", "--batch", "--new"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=240, env=env, check=False)
    if result.returncode not in (0,):
        detail = (result.stderr or result.stdout or "OpenOutFind did not complete.")[-2500:]
        raise RuntimeError(detail)
    records = []
    for line in result.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("profile_url"):
            records.append(item)
    return records
