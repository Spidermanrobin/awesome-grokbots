#!/usr/bin/env python3
"""GET every active URL. Dry by default. Exit: 0 clean/applied, 1 gone, 2 breaker.

Only 404/410 retire entries. All other failures count toward a >25% breaker.
The entire sweep completes before any write, including report output.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import time
import requests
import yaml
from common import ROOT, load_catalog, read_yaml

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"


def classify(status):
    if status in (404, 410):
        return "gone"
    if status is not None and 200 <= status < 400:
        return "alive"
    return "blocked" if status in (401, 403, 429) else "error"


def probe(entry, timeout=25):
    result = {"id": entry["id"], "url": entry["url"], "status": None}
    for attempt in range(2):
        try:
            with requests.get(entry["url"], headers={"User-Agent": UA}, timeout=timeout, stream=True, allow_redirects=True) as response:
                result.update(status=response.status_code, final_url=response.url)
                # A challenge can be returned with HTTP 200; don't stamp it alive.
                challenged = "challenge" in response.headers.get("cf-mitigated", "").lower()
                result["bucket"] = "blocked" if challenged else classify(response.status_code)
            if result["bucket"] != "error" or attempt:
                break
        except requests.RequestException as ex:
            result.update(bucket="error", detail=type(ex).__name__)
        if not attempt:
            time.sleep(0.5)
    time.sleep(0.1)
    return result


def tripped(results):
    return bool(results) and sum(r["bucket"] in ("blocked", "error") for r in results) / len(results) > 0.25


def apply_results(root, data, results, checked):
    """No writes at all when the breaker trips, even if another URL is gone."""
    if tripped(results):
        return False
    by_id = {r["id"]: r for r in results}
    retired = read_yaml(root / "data/retired.yaml")
    removed = set()
    pending = {}
    for kind, entries in data.items():
        kept = []
        for entry in entries:
            e = dict(entry)
            result = by_id.get(e["id"], {})
            bucket = result.get("bucket")
            if bucket == "gone":
                e.update(status="retired", last_checked=checked)
                retired.append(e)
                removed.add(e["id"])
            else:
                if bucket == "alive":
                    e["last_checked"] = checked
                kept.append(e)
        pending[root / "data" / f"{kind}.yaml"] = kept
    if removed:
        pending[root / "data/retired.yaml"] = retired
        picks = read_yaml(root / "data/picks.yaml")
        picks = [{**p, "entries": [i for i in p["entries"] if i not in removed]} for p in picks]
        pending[root / "data/picks.yaml"] = [p for p in picks if p["entries"]]
    # Prepare all serialization before replacing any source file.
    rendered = {p: yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=110) for p, value in pending.items()}
    for path, content in rendered.items():
        if path.read_text(encoding="utf-8") != content:
            tmp = path.with_suffix(".yaml.tmp")
            tmp.write_text(content, encoding="utf-8")
            os.replace(tmp, path)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--dry-run", action="store_true", help="default; no files written")
    parser.add_argument("--workers", type=int, default=6, choices=range(1, 13))
    parser.add_argument("--timeout", type=float, default=25)
    parser.add_argument("--report", type=str, help="JSON report path; only written with --write and a healthy sweep")
    args = parser.parse_args()
    from validate import validate
    validate()
    data = load_catalog()
    entries = [e for group in data.values() for e in group]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda e: probe(e, args.timeout), entries))
    for r in results:
        print(f"{r['bucket']:7} {str(r['status']):4} {r['id']}")
    print(json.dumps(dict(Counter(r["bucket"] for r in results)), sort_keys=True))
    if tripped(results):
        print("Circuit breaker: >25% blocked/errors. No files written.")
        return 2
    if args.write:
        now = datetime.now(timezone.utc)
        apply_results(ROOT, data, results, now.date().isoformat())
        if args.report:
            (ROOT / args.report).write_text(json.dumps({"checked_at": now.isoformat(), "results": results}, indent=2) + "\n")
        return 0
    print("Dry run: no files written.")
    return 1 if any(r["bucket"] == "gone" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
