#!/usr/bin/env python3
"""
download_build.py — download a specific build from Firebase App Distribution.
Usage:
  python download_build.py \
    --project RealGreen \
    --os android \
    --release-id <id> \
    --key /path/to/realgreen.json \
    --out ../projects/RealGreen/builds/
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)


def load_config(project: str, config_dir: str) -> dict:
    path = Path(config_dir) / project / "config.json"
    if not path.exists():
        print(f"{Fore.RED}❌ Config not found: {path}")
        sys.exit(1)
    return json.loads(path.read_text())


def download(app_id: str, release_id: str, key_path: str, out_dir: str) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    cmd = [
        "firebase", "appdistribution:releases:download",
        "--app", app_id,
        "--release-id", release_id,
        "--destination", out_dir,
        "--service-account", key_path,
    ]
    print(f"  Downloading release {release_id}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"{Fore.RED}❌ Download failed:\n{result.stderr}")
        sys.exit(1)
    output = result.stdout.strip()
    print(f"{Fore.GREEN}✅ Downloaded: {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Download a Firebase App Distribution build")
    parser.add_argument("--project", required=True, choices=["PestPac", "RealGreen", "WinTeam", "RouteManager"])
    parser.add_argument("--os", required=True, choices=["android", "ios"])
    parser.add_argument("--release-id", required=True, help="Firebase release ID")
    parser.add_argument("--key", required=True, help="Path to Firebase service account JSON")
    parser.add_argument("--out", required=True, help="Output directory for the downloaded build")
    parser.add_argument("--config-dir", default="../projects")
    args = parser.parse_args()

    config = load_config(args.project, args.config_dir)
    app_id = config.get("firebaseAppId", {}).get(args.os, "")
    if not app_id:
        print(f"{Fore.RED}❌ firebaseAppId.{args.os} not set in config.json")
        sys.exit(1)

    print(f"\n{Style.BRIGHT}Downloading {args.project} ({args.os.upper()}) — release {args.release_id}")
    download(app_id, args.release_id, args.key, args.out)


if __name__ == "__main__":
    main()
