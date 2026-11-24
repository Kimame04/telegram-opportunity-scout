#!/usr/bin/env python3
"""
Helper utility to generate a macOS launchd plist or cron entry for daily execution.
"""

import sys
from pathlib import Path

PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.telegram.opportunityscout</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_bin}</string>
        <string>-m</string>
        <string>src.cli</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{working_dir}/output/scout.log</string>
    <key>StandardErrorPath</key>
    <string>{working_dir}/output/scout_error.log</string>
</dict>
</plist>
"""


def main():
    root = Path(__file__).resolve().parent.parent
    python_bin = sys.executable

    print("============================================================")
    print("🤖 Telegram Opportunity Scout — Daily Automation Setup")
    print("============================================================")
    print(f"Working Directory: {root}")
    print(f"Python Executable: {python_bin}")
    print()

    # Option A: launchd (macOS recommended)
    plist_content = PLIST_TEMPLATE.format(
        python_bin=python_bin,
        working_dir=str(root),
    )
    launchd_dir = Path.home() / "Library" / "LaunchAgents"
    plist_file = launchd_dir / "com.telegram.opportunityscout.plist"

    print("Option A (macOS LaunchAgent - runs daily at 08:30):")
    print(f"1. Save plist to: {plist_file}")
    print(f"2. Load via: launchctl load -w {plist_file}")
    print()
    print("Option B (Standard Cron):")
    print(f"30 8 * * * cd {root} && {python_bin} -m src.cli >> output/scout.log 2>&1")
    print("============================================================")


if __name__ == "__main__":
    main()
