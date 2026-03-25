#!/usr/bin/env python3
"""
install_build.py — install a .apk or .ipa on a connected device or simulator.
Usage:
  python install_build.py --platform android --udid emulator-5554 --file builds/app.apk
  python install_build.py --platform ios --udid <sim-udid> --file builds/app.ipa
  python install_build.py --platform ios --udid <physical-udid> --file builds/app.ipa --physical
"""
import argparse
import subprocess
import sys
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)


def install_android(udid: str, apk_path: str):
    print(f"  Installing {Path(apk_path).name} on {udid}...")
    cmd = ["adb", "-s", udid, "install", "-r", apk_path]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or "Failure" in result.stdout:
        print(f"{Fore.RED}❌ Install failed:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)
    print(f"{Fore.GREEN}✅ Installed successfully on {udid}")


def install_ios_simulator(udid: str, ipa_path: str):
    subprocess.run(["xcrun", "simctl", "boot", udid], capture_output=True, text=True)
    print(f"  Installing {Path(ipa_path).name} on simulator {udid}...")
    result = subprocess.run(
        ["xcrun", "simctl", "install", udid, ipa_path],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        print(f"{Fore.RED}❌ Install failed:\n{result.stderr}")
        sys.exit(1)
    print(f"{Fore.GREEN}✅ Installed on simulator {udid}")


def install_ios_physical(udid: str, ipa_path: str):
    print(f"  Installing {Path(ipa_path).name} on physical device {udid}...")
    result = subprocess.run(
        ["ios-deploy", "--id", udid, "--bundle", ipa_path, "--no-wifi"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"{Fore.RED}❌ Install failed:\n{result.stderr}")
        sys.exit(1)
    print(f"{Fore.GREEN}✅ Installed on device {udid}")


def main():
    parser = argparse.ArgumentParser(description="Install a build on a device or simulator")
    parser.add_argument("--platform", required=True, choices=["android", "ios"])
    parser.add_argument("--udid", required=True, help="Device UDID or ADB serial")
    parser.add_argument("--file", required=True, help="Path to .apk or .ipa")
    parser.add_argument("--physical", action="store_true", help="iOS physical device (use ios-deploy)")
    args = parser.parse_args()

    if not Path(args.file).exists():
        print(f"{Fore.RED}❌ File not found: {args.file}")
        sys.exit(1)

    print(f"\n{Style.BRIGHT}Installing build — {args.platform.upper()}")
    if args.platform == "android":
        install_android(args.udid, args.file)
    elif args.physical:
        install_ios_physical(args.udid, args.file)
    else:
        install_ios_simulator(args.udid, args.file)


if __name__ == "__main__":
    main()
