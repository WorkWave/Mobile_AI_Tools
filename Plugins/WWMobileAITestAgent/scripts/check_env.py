#!/usr/bin/env python3
"""
check_env.py — verify all required SDK dependencies for WWMobileAITestAgent.
Usage: python check_env.py
"""
import subprocess
import shutil
import sys
import platform
from colorama import init, Fore, Style

init(autoreset=True)

CHECKS = [
    {
        "name": "Python 3.11+",
        "cmd": [sys.executable, "--version"],
        "critical": True,
        "install": "brew install python",
    },
    {
        "name": "Java 11+",
        "cmd": ["java", "-version"],
        "stderr": True,
        "critical": True,
        "install": "brew install openjdk@17",
    },
    {
        "name": "Node.js 18+",
        "cmd": ["node", "--version"],
        "critical": True,
        "install": "brew install node",
    },
    {
        "name": "Appium 2.x",
        "cmd": ["appium", "--version"],
        "critical": True,
        "install": "npm install -g appium",
    },
    {
        "name": "pytest",
        "cmd": [sys.executable, "-m", "pytest", "--version"],
        "critical": True,
        "install": "pip install pytest",
    },
    {
        "name": "Appium UIAutomator2",
        "cmd": ["appium", "driver", "list", "--installed"],
        "grep": "uiautomator2",
        "critical": False,
        "install": "appium driver install uiautomator2",
    },
    {
        "name": "Appium XCUITest",
        "cmd": ["appium", "driver", "list", "--installed"],
        "grep": "xcuitest",
        "critical": False,
        "install": "appium driver install xcuitest",
    },
    {
        "name": "Firebase CLI",
        "cmd": ["firebase", "--version"],
        "critical": True,
        "install": "npm install -g firebase-tools",
    },
    {
        "name": "Xcode",
        "cmd": ["xcode-select", "-p"],
        "critical": platform.system() == "Darwin",
        "install": "Install from Mac App Store, then: sudo xcode-select --switch /Applications/Xcode.app",
        "darwin_only": True,
    },
    {
        "name": "Android SDK (adb)",
        "cmd": ["adb", "--version"],
        "critical": False,
        "install": "Install Android Studio → set ANDROID_HOME in your shell profile",
    },
    {
        "name": "ios-deploy",
        "cmd": ["ios-deploy", "--version"],
        "critical": False,
        "install": "brew install ios-deploy",
        "darwin_only": True,
    },
]


def run_check(check: dict) -> tuple[bool, str]:
    if check.get("darwin_only") and platform.system() != "Darwin":
        return True, "N/A (non-macOS)"
    if not shutil.which(check["cmd"][0]):
        return False, "NOT FOUND"
    try:
        result = subprocess.run(
            check["cmd"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stderr if check.get("stderr") else result.stdout
        output = output.strip().splitlines()[0] if output.strip() else ""
        if check.get("grep") and check["grep"] not in (result.stdout + result.stderr):
            return False, "NOT INSTALLED"
        return True, output or "ok"
    except Exception as e:
        return False, str(e)


def main():
    print(f"\n{Style.BRIGHT}Environment Check — WWMobileAITestAgent")
    print("=" * 52)

    all_critical_ok = True
    for check in CHECKS:
        ok, version = run_check(check)
        icon = f"{Fore.GREEN}✅" if ok else (
            f"{Fore.RED}❌" if check["critical"] else f"{Fore.YELLOW}⚠️ "
        )
        name = check["name"].ljust(22)
        print(f"  {icon}  {name} {version}")
        if not ok and check["critical"]:
            all_critical_ok = False
            print(f"       {Fore.CYAN}Install: {check['install']}")

    print("=" * 52)
    if all_critical_ok:
        print(f"{Fore.GREEN}✅ All critical dependencies installed. Ready to test.\n")
        sys.exit(0)
    else:
        print(f"{Fore.RED}❌ Missing critical dependencies. Install them before testing.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
