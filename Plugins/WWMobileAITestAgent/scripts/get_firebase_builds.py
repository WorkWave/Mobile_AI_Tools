#!/usr/bin/env python3
"""
get_firebase_builds.py — fetch last 10 builds from Firebase App Distribution via REST API.
Usage:
  python get_firebase_builds.py \
    --project RealGreen \
    --os android \
    --key /path/to/realgreen.json \
    --config-dir ../projects
"""
import argparse
import json
import sys
from pathlib import Path

import requests
from colorama import init, Fore, Style
from google.oauth2 import service_account
from google.auth.transport.requests import Request

init(autoreset=True)

FIREBASE_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
RELEASES_URL = "https://firebaseappdistribution.googleapis.com/v1/projects/{project_id}/apps/{app_id}/releases"


def load_config(project: str, config_dir: str) -> dict:
    path = Path(config_dir) / project / "config.json"
    if not path.exists():
        print(f"{Fore.RED}❌ Config not found: {path}")
        sys.exit(1)
    return json.loads(path.read_text())


def get_access_token(key_path: str) -> str:
    creds = service_account.Credentials.from_service_account_file(
        key_path, scopes=FIREBASE_SCOPES
    )
    creds.refresh(Request())
    return creds.token


def get_builds(project_id: str, app_id: str, key_path: str, limit: int = 10) -> list[dict]:
    token = get_access_token(key_path)
    url = RELEASES_URL.format(project_id=project_id, app_id=app_id)
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={"pageSize": limit},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"{Fore.RED}❌ Firebase API error {resp.status_code}:\n{resp.text}")
        sys.exit(1)
    return resp.json().get("releases", [])


def main():
    parser = argparse.ArgumentParser(description="Fetch Firebase App Distribution builds")
    parser.add_argument("--project", required=True, choices=["PestPac", "RealGreen", "WinTeam", "RouteManager"])
    parser.add_argument("--os", required=True, choices=["android", "ios"])
    parser.add_argument("--key", required=True, help="Path to Firebase service account JSON")
    parser.add_argument("--config-dir", default=None, help="Path to OUTPUT_DIR (reads ~/.claude/ww-mobile-ai-test-agent-outputdir.txt if not set)")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    config = load_config(args.project, args.config_dir)
    app_id = config.get("firebaseAppId", {}).get(args.os, "")
    if not app_id:
        print(f"{Fore.RED}❌ firebaseAppId.{args.os} is not set in {args.project}/config.json")
        sys.exit(1)

    project_id = config.get("firebaseProject", "")
    if not project_id:
        print(f"{Fore.RED}❌ firebaseProject is not set in {args.project}/config.json")
        sys.exit(1)

    print(f"\n{Style.BRIGHT}Firebase Builds — {args.project} ({args.os.upper()})")
    print("=" * 60)

    releases = get_builds(project_id, app_id, args.key, args.limit)
    if not releases:
        print(f"{Fore.YELLOW}  No builds found. Upload a build to Firebase App Distribution first.")
        sys.exit(0)

    for i, r in enumerate(releases, 1):
        version = r.get("displayVersion", "?")
        build = r.get("buildVersion", "?")
        date = (r.get("createTime") or "")[:10]
        notes = (r.get("releaseNotes", {}).get("text") or "")[:60]
        print(f"  [{i:2}]  v{version} (build {build})   {date}   {notes}")

    print(f"  [11]  Enter custom release ID or download URL")
    print()


if __name__ == "__main__":
    main()
