#!/usr/bin/env python3
"""
list_devices.py — list connected Android/iOS devices and simulators.
Usage:
  python list_devices.py                    # both platforms
  python list_devices.py --platform android
  python list_devices.py --platform ios
"""
import argparse
import subprocess
import re
import json
import sys
from colorama import init, Fore, Style

init(autoreset=True)


def list_android() -> list[dict]:
    devices = []
    try:
        result = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, timeout=10)
        for line in result.stdout.splitlines()[1:]:
            line = line.strip()
            if not line or "offline" in line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial = parts[0]
            state = parts[1]
            model = next((p.split(":")[1] for p in parts if p.startswith("model:")), serial)
            devices.append({"serial": serial, "name": model, "type": "physical", "state": state})
    except FileNotFoundError:
        print(f"{Fore.YELLOW}⚠️  adb not found. Install Android SDK and set ANDROID_HOME.")
        return []

    try:
        result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True, timeout=10)
        running_result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
        running_serials = [l.split()[0] for l in running_result.stdout.splitlines()[1:] if l.strip()]
        for avd in result.stdout.strip().splitlines():
            if not avd.strip():
                continue
            state = "running" if any(avd in s for s in running_serials) else "stopped"
            devices.append({"serial": avd, "name": avd, "type": "emulator", "state": state})
    except FileNotFoundError:
        pass

    return devices


def list_ios() -> list[dict]:
    devices = []
    try:
        result = subprocess.run(
            ["xcrun", "xctrace", "list", "devices"],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.splitlines():
            match = re.match(r"^(.+?)\s+\((\d+[\.\d]*)\)\s+\(([0-9A-F\-]+)\)$", line.strip())
            if match and "Simulator" not in line:
                devices.append({
                    "name": match.group(1).strip(),
                    "os_version": match.group(2),
                    "udid": match.group(3),
                    "type": "physical",
                    "state": "connected",
                })
    except FileNotFoundError:
        print(f"{Fore.YELLOW}⚠️  xcrun not found. Install Xcode.")
        return []

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "available", "--json"],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        for runtime, sims in data.get("devices", {}).items():
            os_version = re.search(r"(\d+\.\d+)", runtime)
            os_str = os_version.group(1) if os_version else runtime
            for sim in sims:
                devices.append({
                    "name": sim["name"],
                    "os_version": os_str,
                    "udid": sim["udid"],
                    "type": "simulator",
                    "state": sim.get("state", "Shutdown"),
                })
    except Exception:
        pass

    return devices


def print_android(devices: list[dict]):
    print(f"\n{Style.BRIGHT}Android Devices & Emulators")
    print("=" * 55)
    if not devices:
        print(f"  {Fore.YELLOW}No Android devices found.")
        return
    physical = [d for d in devices if d["type"] == "physical"]
    emulators = [d for d in devices if d["type"] == "emulator"]
    idx = 1
    if physical:
        print(f"  {Style.BRIGHT}Physical Devices:")
        for d in physical:
            print(f"    [{idx}] {d['name']}  ({d['serial']})  {d['state']}")
            idx += 1
    if emulators:
        print(f"  {Style.BRIGHT}Emulators (AVDs):")
        for d in emulators:
            state_str = f"{Fore.GREEN}running" if d["state"] == "running" else f"{Fore.WHITE}stopped"
            print(f"    [{idx}] {d['name']}  {state_str}")
            idx += 1


def print_ios(devices: list[dict]):
    print(f"\n{Style.BRIGHT}iOS Devices & Simulators")
    print("=" * 55)
    if not devices:
        print(f"  {Fore.YELLOW}No iOS devices found.")
        return
    physical = [d for d in devices if d["type"] == "physical"]
    sims = [d for d in devices if d["type"] == "simulator"]
    idx = 1
    if physical:
        print(f"  {Style.BRIGHT}Physical Devices:")
        for d in physical:
            print(f"    [{idx}] {d['name']}  iOS {d['os_version']}  ({d['udid']})")
            idx += 1
    if sims:
        print(f"  {Style.BRIGHT}Simulators:")
        for d in sims:
            state_str = f"{Fore.GREEN}[Booted]" if d["state"] == "Booted" else f"{Fore.WHITE}[Shutdown]"
            print(f"    [{idx}] {d['name']}  iOS {d['os_version']}  {state_str}")
            idx += 1


def main():
    parser = argparse.ArgumentParser(description="List connected mobile devices and simulators")
    parser.add_argument("--platform", choices=["android", "ios", "all"], default="all")
    args = parser.parse_args()

    if args.platform in ("android", "all"):
        print_android(list_android())
    if args.platform in ("ios", "all"):
        print_ios(list_ios())
    print()


if __name__ == "__main__":
    main()
