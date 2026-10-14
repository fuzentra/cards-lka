#!/usr/bin/env python3
"""
inject_offers.py
================
Reads offers.json produced by crawler.py and patches the EMBEDDED object
(offers array + updated timestamp) inside index.html in-place.

Usage:
    python scripts/inject_offers.py               # uses default paths
    python scripts/inject_offers.py offers.json index.html
"""

import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

COLOMBO = ZoneInfo("Asia/Colombo")

MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

def load_offers(offers_path: Path) -> list:
    with open(offers_path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("offers", [])

def offers_to_js(offers: list) -> str:
    lines = []
    for i, o in enumerate(offers):
        comma = "," if i < len(offers) - 1 else ""
        lines.append("  " + json.dumps(o, ensure_ascii=False) + comma)
    return "\n".join(lines)

def fmt_colombo() -> str:
    now = datetime.now(COLOMBO)
    return f"{now.day} {MONTHS_SHORT[now.month-1]} {now.year}, {now.hour:02d}:{now.minute:02d}"

def inject(offers_path: Path, html_path: Path) -> None:
    offers = load_offers(offers_path)
    html   = html_path.read_text(encoding="utf-8")
    updated = fmt_colombo()

    # ── 1. Replace the offers array inside EMBEDDED ──────────────────────────
    # Matches: const EMBEDDED={"updated":...,"offers":[...]}
    # Strategy: replace everything between "offers":[ and the closing ]}
    pattern = re.compile(
        r'(const EMBEDDED=\{"updated":)("[^"]*"|null)(,"offers":\[)(.*?)(\]\};)',
        re.DOTALL,
    )
    if not pattern.search(html):
        print("ERROR: could not find 'const EMBEDDED' block in index.html")
        sys.exit(1)

    new_offers_js = offers_to_js(offers)
    html = pattern.sub(
        lambda m: (
            m.group(1)
            + json.dumps(updated)          # "updated" value
            + m.group(3)                   # ,"offers":[
            + "\n" + new_offers_js + "\n"  # offer lines
            + m.group(5)                   # ]};
        ),
        html,
    )

    html_path.write_text(html, encoding="utf-8")
    print(f"✓ Injected {len(offers)} offers into {html_path}")
    print(f"  Updated timestamp: {updated}")

if __name__ == "__main__":
    args = sys.argv[1:]
    offers_path = Path(args[0]) if len(args) > 0 else Path("offers.json")
    html_path   = Path(args[1]) if len(args) > 1 else Path("index.html")
    inject(offers_path, html_path)
