"""
Import MERA dashboard into SigNoz via API.

Usage:
    python scripts/import_dashboard.py

This script:
    1. Checks if SigNoz is running at http://localhost:8080
    2. Attempts to import the MERA dashboard JSON
    3. If signup is needed, prompts the user to complete it first
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SIGNOZ_URL = "http://localhost:8080"
DASHBOARD_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboards", "mera_dashboard.json")


def check_signoz_running() -> bool:
    import requests
    try:
        r = requests.get(f"{SIGNOZ_URL}/api/v1/version", timeout=5)
        return r.status_code == 200
    except requests.ConnectionError:
        return False


def check_signoz_ready() -> bool:
    import requests
    try:
        r = requests.get(f"{SIGNOZ_URL}/api/v1/login", timeout=5, allow_redirects=False)
        return r.status_code in (200, 302, 401, 403)
    except requests.ConnectionError:
        return False


def import_dashboard() -> bool:
    import requests

    if not os.path.exists(DASHBOARD_FILE):
        print(f" Dashboard file not found: {DASHBOARD_FILE}")
        return False

    with open(DASHBOARD_FILE, "r") as f:
        dashboard_json = json.load(f)

    payload = {
        "title": dashboard_json.get("title", "MERA Dashboard"),
        "data": dashboard_json
    }

    try:
        r = requests.post(
            f"{SIGNOZ_URL}/api/v1/dashboards",
            json=payload,
            timeout=10
        )
        if r.status_code == 200:
            print(f" Dashboard imported: {dashboard_json.get('title', 'MERA')}")
            return True
        elif r.status_code == 401:
            print(" SigNoz needs login first.")
            print(" Open http://localhost:8080 in your browser, complete signup, then re-run this script.")
            return False
        else:
            print(f" Dashboard import failed (HTTP {r.status_code}): {r.text[:200]}")
            return False
    except requests.ConnectionError:
        print(f" Cannot connect to SigNoz at {SIGNOZ_URL}")
        print(" Make sure Foundry deployment is running: foundryctl cast -f casting.yaml")
        return False
    except Exception as e:
        print(f" Error importing dashboard: {e}")
        return False


def main():
    print("=" * 50)
    print("  MERA Dashboard Importer")
    print("=" * 50)
    print()

    if not check_signoz_running():
        print(f" SigNoz is not running at {SIGNOZ_URL}")
        print()
        print(" To deploy SigNoz:")
        print("   foundryctl cast -f casting.yaml")
        print()
        input(" Press Enter after deploying SigNoz...")
        if not check_signoz_running():
            print(" Still can't reach SigNoz. Please deploy it first.")
            return

    print(" SigNoz is running.")
    print()

    if not check_signoz_ready():
        print(" SigNoz UI needs first-time setup.")
        print(" 1. Open http://localhost:8080 in your browser")
        print(" 2. Complete the signup form")
        print(" 3. Return here and press Enter")
        input()
        if not check_signoz_ready():
            print(" Still not ready. Complete signup at http://localhost:8080")
            return

    print(" Importing dashboard...")
    import_dashboard()
    print()
    print(" Done! Go to http://localhost:8080 → Dashboards to see it.")


if __name__ == "__main__":
    main()
