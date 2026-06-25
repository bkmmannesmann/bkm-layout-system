#!/usr/bin/env python3
import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "content/prospekt-fachbetrieb/content.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"JSON valid! ({len(data)} top-level keys)")
except json.JSONDecodeError as e:
    print(f"JSON ERROR: {e}")
    sys.exit(1)
