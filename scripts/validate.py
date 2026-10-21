#!/usr/bin/env python3
"""Validate schema, uniqueness, date ordering, locales and weekly references."""
import json
import re
import sys
from datetime import date
from jsonschema import Draft202012Validator, FormatChecker
from common import ROOT, KINDS, CATEGORIES, load_catalog, read_yaml, locales


def validate(root=ROOT):
    errors = []
    schema = json.loads((root / "schema/entry.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    data = load_catalog(root)
    data["retired"] = read_yaml(root / "data/retired.yaml")
    ids, urls, active = set(), set(), set()
    for kind, entries in data.items():
        if not isinstance(entries, list):
            errors.append(f"{kind}: expected an array")
            continue
        for i, e in enumerate(entries):
            label = f"{kind}[{i}]"
            issues = list(validator.iter_errors(e))
            errors.extend(f"{label} {'.'.join(map(str, x.path))}: {x.message}" for x in issues)
            if issues:
                continue
            for key, seen in (("id", ids), ("url", urls)):
                value = e[key].rstrip("/") if key == "url" else e[key]
                if value in seen:
                    errors.append(f"{label}: duplicate {key} {value}")
                seen.add(value)
            if kind != "retired":
                active.add(e["id"])
            expected = "retired" if kind == "retired" else "active"
            if e["status"] != expected:
                errors.append(f"{label}: expected status {expected}")
            if kind == "bots" and not re.fullmatch(r"https://x\.ai/bot/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)?", e["url"]):
                errors.append(f"{label}: bots require an x.ai/bot share URL")
            if kind in ("skills", "guides") and e["category"] != kind:
                errors.append(f"{label}: category must be {kind}")
            if kind == "bots" and e["category"] in ("skills", "guides"):
                errors.append(f"{label}: invalid bot category")
            if not e["added"] <= e["last_checked"] <= date.today().isoformat():
                errors.append(f"{label}: dates must satisfy added <= last_checked <= today")
    picks = read_yaml(root / "data/picks.yaml")
    weeks = set()
    if not isinstance(picks, list):
        errors.append("picks: expected an array")
    else:
        for pick in picks:
            if not isinstance(pick, dict) or set(pick) != {"week", "entries"}:
                errors.append("picks: each selection needs exactly week and entries")
                continue
            try:
                day = date.fromisoformat(pick["week"])
                if day.weekday() != 0 or day.isoformat() in weeks:
                    raise ValueError("week must be a unique Monday")
                weeks.add(day.isoformat())
            except (TypeError, ValueError) as ex:
                errors.append(f"picks: invalid week: {ex}")
            selected = pick["entries"]
            if not isinstance(selected, list) or not 1 <= len(selected) <= 6 or not all(isinstance(x, str) for x in selected):
                errors.append("picks: entries must contain 1–6 IDs")
            elif len(set(selected)) != len(selected) or any(x not in active for x in selected):
                errors.append("picks: IDs must be unique active entries")
    ui = locales(root)
    def shape(value, prefix=""):
        if isinstance(value, dict):
            return {p for key, item in value.items() for p in shape(item, prefix + "." + key)}
        return {prefix}
    if "en" not in ui:
        errors.append("i18n: en.yaml is required")
    else:
        for lang, strings in ui.items():
            if shape(strings) != shape(ui["en"]):
                errors.append(f"i18n/{lang}: keys must match en.yaml")
            if set(strings.get("categories", {})) != set(CATEGORIES):
                errors.append(f"i18n/{lang}: category translations missing")
    if errors:
        raise ValueError("\n".join(errors))
    return {kind: len(data[kind]) for kind in KINDS}


if __name__ == "__main__":
    try:
        print("Valid catalog:", validate())
    except (ValueError, KeyError, TypeError) as ex:
        print(ex, file=sys.stderr)
        sys.exit(1)
