#!/usr/bin/env python3
"""Offline review of normalized, synthetic Nexus pair change evidence. Python 3.10+."""

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import sys

COLLECTIONS = ("interfaces", "port_channels", "vlans", "neighbors")
VPC_HEALTH = {"peer_link": "up", "peer_keepalive": "alive", "consistency": "success"}
STATES = {"up", "down", "suspended", "unknown"}
MISSING = object()


class InputError(ValueError):
    """Malformed JSON shape or policy; missing observation fields remain evidence gaps."""


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise InputError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=unique)


def validate(before, after, plan):
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise InputError("Plan must be an object with schema_version 1")
    names = plan.get("devices")
    if (not isinstance(names, list) or len(names) != 2 or
            not all(isinstance(n, str) and n.strip() for n in names) or len(set(names)) != 2):
        raise InputError("Plan must name exactly two different devices")
    targets = plan.get("target_versions")
    if not isinstance(targets, dict) or set(targets) != set(names) or not all(
            isinstance(v, str) and v.strip() and v != "unknown" for v in targets.values()):
        raise InputError("target_versions must contain an explicit version for each device")
    seen = set()
    for rule in plan.get("allowed_changes", []):
        if not isinstance(rule, dict) or set(rule) != {"device", "collection", "item", "before", "after", "reason"}:
            raise InputError("Each allowed change needs device, collection, item, before, after, reason")
        if rule["device"] not in names or rule["collection"] not in COLLECTIONS:
            raise InputError("Allowed changes can only affect a planned device's state collection")
        if not isinstance(rule["item"], str) or not rule["item"].strip() or not isinstance(rule["reason"], str) or not rule["reason"].strip():
            raise InputError("Allowed change item and reason must be nonempty strings")
        for key in ("before", "after"):
            if rule[key] is not None and (not isinstance(rule[key], str) or rule[key] not in STATES - {"unknown"}):
                raise InputError("Allowed change values must be known states or null for an absent item")
        if rule["before"] == rule["after"]:
            raise InputError("An allowed change must actually change an item")
        signature = (rule["device"], rule["collection"], rule["item"])
        if signature in seen:
            raise InputError("Duplicate allowed change")
        seen.add(signature)
    for label, snapshot in (("before", before), ("after", after)):
        if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
            raise InputError(f"{label}: snapshot must have schema_version 1")
        devices = snapshot.get("devices", {})
        if not isinstance(devices, dict):
            raise InputError(f"{label}: devices must be an object")
        for name, device in devices.items():
            if not isinstance(device, dict):
                raise InputError(f"{label}/{name}: device must be an object")
            for key in ("model", "version"):
                if key in device and device[key] is not None and not isinstance(device[key], str):
                    raise InputError(f"{label}/{name}/{key}: expected string or null")
            for key in (*COLLECTIONS, "vpc"):
                if key not in device or device[key] is None:
                    continue
                if not isinstance(device[key], dict):
                    raise InputError(f"{label}/{name}/{key}: expected object or null")
                for item, value in device[key].items():
                    if value is not None and not isinstance(value, str):
                        raise InputError(f"{label}/{name}/{key}/{item}: expected string or null")
                    if key in COLLECTIONS and value is not None and value not in STATES:
                        raise InputError(f"{label}/{name}/{key}/{item}: normalize to up/down/suspended/unknown")


def is_unknown(value):
    return value is MISSING or value is None or value == "" or value == "unknown"


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp if stamp.tzinfo is not None else None
    except ValueError:
        return None


def compare(before, after, plan):
    validate(before, after, plan)
    findings = []
    def add(level, path, message):
        findings.append({"level": level, "path": path, "message": message})
    times = [parse_time(s.get("captured_at")) for s in (before, after)]
    if any(t is None for t in times):
        add("INCOMPLETE", "captured_at", "Both snapshots need ISO 8601 timestamps with timezone.")
    elif times[1] <= times[0]:
        add("FAIL", "captured_at", "After evidence must be later than before evidence.")
    else:
        add("PASS", "captured_at", "Evidence is in chronological order.")
    rules = {(r["device"], r["collection"], r["item"]): r for r in plan.get("allowed_changes", [])}
    used = set()
    for label, snapshot in (("before", before), ("after", after)):
        extras = set(snapshot.get("devices", {})) - set(plan["devices"])
        if extras:
            add("FAIL", f"{label}/devices", f"Unplanned devices: {', '.join(sorted(extras))}.")
    for name in plan["devices"]:
        pair = [s.get("devices", {}).get(name) for s in (before, after)]
        if any(d is None for d in pair):
            add("INCOMPLETE", name, "Device missing from before or after snapshot; cannot compare it.")
            continue
        old, new = pair
        for key in ("model", "version"):
            a, b = old.get(key), new.get(key)
            if is_unknown(a) or is_unknown(b):
                add("INCOMPLETE", f"{name}/{key}", "Missing or unknown before/after evidence.")
            elif key == "model":
                add("PASS" if a == b else "FAIL", f"{name}/{key}", f"{a} -> {b}; hardware identity must remain unchanged.")
            else:
                target = plan["target_versions"][name]
                add("PASS" if b == target else "FAIL", f"{name}/{key}", f"{a} -> {b}; expected target {target}.")
        for key, healthy in VPC_HEALTH.items():
            for label, device in (("before", old), ("after", new)):
                vpc = device.get("vpc") or {}
                value = vpc.get(key)
                path = f"{name}/{label}/vpc/{key}"
                if is_unknown(value):
                    add("INCOMPLETE", path, "Missing or unknown vPC evidence; never waived by the plan.")
                elif value != healthy:
                    add("FAIL", path, f"Observed {value}; expected {healthy}.")
                else:
                    add("PASS", path, f"Observed {healthy}.")
        for collection in COLLECTIONS:
            a, b = old.get(collection), new.get(collection)
            if a is None or b is None:
                add("INCOMPLETE", f"{name}/{collection}", "Collection not captured on both sides; an omitted collection is not an empty collection.")
                continue
            for item in sorted(a.keys() | b.keys()):
                previous, current = a.get(item, MISSING), b.get(item, MISSING)
                path = f"{name}/{collection}/{item}"
                # Explicit null/unknown is missing evidence, while absence from an
                # explicitly captured collection represents an absent object.
                if ((previous is not MISSING and is_unknown(previous)) or
                        (current is not MISSING and is_unknown(current))):
                    add("INCOMPLETE", path, "Explicit unknown state; do not infer up or down.")
                    continue
                prev = None if previous is MISSING else previous
                curr = None if current is MISSING else current
                signature = (name, collection, item)
                rule = rules.get(signature)
                if rule and (prev, curr) == (rule["before"], rule["after"]):
                    used.add(signature)
                    add("ACCEPTED", path, f"{prev} -> {curr}; planned: {rule['reason']}")
                elif prev == "up" and curr == "up":
                    add("PASS", path, "Remained up.")
                else:
                    add("FAIL", path, f"{prev} -> {curr}; state is degraded or changed without an exact approved transition.")
            if not a and not b:
                add("PASS", f"{name}/{collection}", "Both collections explicitly empty; validate intended scope with the change owner.")
    for key in rules.keys() - used:
        add("INCOMPLETE", "/".join(key), "Planned transition not observed exactly; reconcile plan and evidence.")
    levels = Counter(item["level"] for item in findings)
    status = "FAIL" if levels["FAIL"] else "INCOMPLETE" if levels["INCOMPLETE"] else "PASS"
    return {"schema_version": 1, "status": status,
            "exit_code": {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2}[status],
            "before_captured_at": before.get("captured_at"), "after_captured_at": after.get("captured_at"),
            "counts": dict(sorted(levels.items())), "findings": findings,
            "limitation": "Offline evidence review only. PASS is not authorization or proof of traffic health or upgrade compatibility."}


def markdown(report):
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    lines = ["# Nexus change evidence review", "", f"**Result: {report['status']}**", "",
             f"Before: {report['before_captured_at']}", f"After: {report['after_captured_at']}", "",
             report["limitation"], "", "| Result | Evidence | Finding |", "| --- | --- | --- |"]
    lines.extend("| " + " | ".join(escape(item[k]) for k in ("level", "path", "message")) + " |" for item in report["findings"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--json", dest="json_path", type=Path, help="Optional report file")
    parser.add_argument("--markdown", dest="md_path", type=Path, help="Optional report file")
    args = parser.parse_args(argv)
    try:
        report = compare(load_json(args.before), load_json(args.after), load_json(args.plan))
        for path, contents in ((args.json_path, json.dumps(report, indent=2) + "\n"),
                               (args.md_path, markdown(report))):
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")
    except (OSError, ValueError, TypeError) as exc:
        print(f"Input/output error: {exc}", file=sys.stderr)
        return 3
    print(f"{report['status']}: " + ", ".join(f"{n} {level.lower()}" for level, n in report["counts"].items()))
    if args.json_path is None and args.md_path is None:
        print(markdown(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
