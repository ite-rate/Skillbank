#!/usr/bin/env python3
"""
List available printers and show system printing information.
"""

import sys
import json
from pathlib import Path

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from utils import detect_platform, get_default_printer, get_available_printers, check_dependencies

def main():
    json_mode = len(sys.argv) > 1 and sys.argv[1] == "--json"

    platform = detect_platform()
    deps = check_dependencies()
    default = get_default_printer()
    printers = get_available_printers()

    if json_mode:
        output = {
            "platform": platform,
            "dependencies": deps,
            "default_printer": default,
            "available_printers": printers
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print("PRINT SYSTEM INFORMATION")
    print("=" * 60)

    # Platform
    print(f"\nPlatform: {platform}")

    # Dependencies
    print("\nDependencies:")
    for name, available in deps.items():
        status = "✓" if available else "✗"
        print(f"  {status} {name}")

    # Default printer
    print("\nDefault Printer:")
    if default:
        print(f"  {default}")
    else:
        print("  (none)")

    # Available printers
    print("\nAvailable Printers:")
    if printers:
        for p in printers:
            marker = " [DEFAULT]" if p.get("default") else ""
            status = f" - {p.get('status', 'unknown')}" if p.get("status") else ""
            print(f"  • {p['name']}{marker}{status}")
    else:
        print("  (none found)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
