#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path
import urllib.request

items = json.loads(Path("ingest/urls.json").read_text())
failed = []
for item in items:
    dest = Path(item["dest"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"GET {item['url']} -> {dest}", flush=True)
    req = urllib.request.Request(item["url"], headers={"User-Agent": "caldero-ingest/1"})
    h = hashlib.md5()
    n = 0
    html = False
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as f:
        ctype = resp.headers.get("Content-Type", "")
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            if n == 0 and chunk.lstrip()[:9].lower().startswith(b"<!doctype"):
                html = True
                break
            f.write(chunk)
            h.update(chunk)
            n += len(chunk)
    if html:
        failed.append((item["dest"], f"HTML response type={ctype}"))
        continue
    digest = h.hexdigest()
    if n != item["bytes"] or digest != item["md5"]:
        failed.append((item["dest"], f"mismatch size={n} md5={digest} type={ctype}"))
    else:
        print(f"  OK {n} {digest} {ctype}", flush=True)
if failed:
    for dest, err in failed:
        print(f"FAIL {dest}: {err}", file=sys.stderr)
    sys.exit(1)
