#!/usr/bin/env python3
"""S36: same-diff merge verifier (stdlib only, read-only, deterministic).

Given two merge diffs (for example the in-place base B and the lock-derived tree L', each against its own
pre-merge tree) and the approved change list (patches, and new files given as DEST=SOURCE), report per file whether
both trees got exactly the approved changes and nothing else.

Normalisation, per file (offsets and context ignored):
  net    : added minus removed count of every line text (composition of sequential patches is additive, so the
           approved net is the sum over the approved patches);
  blocks : the multiset of change blocks (removed lines, added lines), one block per run of -/+ lines.
Verdict SAME_CHANGE_SET when, for every file, A's net == B's net == the approved net and no protected path (forge
sources) changed; otherwise DIFFERENT with every reason. Paths outside --allow are flagged. Equal nets with different
blocks (the same lines placed differently, e.g. doc hunks before an extra section of one tree) are a NOTE.

usage: forge_sol_S36_samediff_verify_20261027.py --a NAME=DIFF --b NAME=DIFF [--approved PATCH ...]
           [--approved-new DEST=SOURCE ...] [--allow PREFIX ...] [--protect PREFIX ...] [--json OUT]
Exit 0 = SAME_CHANGE_SET, 1 = DIFFERENT, 2 = usage / parse error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_ALLOW = ["tests/", "tools/", "docs/", "README.md", "IDEA_SOURCE.md", "CHANGELOG.md"]
DEFAULT_PROTECT = ["src/", "include/", "bench/", "CMakeLists.txt"]
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def clean_path(raw: str) -> str | None:
    path = raw.split("\t")[0].strip()
    if path == "/dev/null":
        return None
    if path.startswith(("a/", "b/")):
        path = path[2:]
    return path[2:] if path.startswith("./") else path


def parse_diff(text: str, label: str) -> dict:
    """Unified diff (git or diff -ruN) -> {path: {"net": Counter, "blocks": [(removed, added)], "status": str}}."""
    files: dict = {}
    lines = text.splitlines()
    i = 0
    current = None
    while i < len(lines):
        line = lines[i]
        if line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old, new = clean_path(line[4:]), clean_path(lines[i + 1][4:])
            path = new or old
            if path is None:
                raise ValueError(f"{label}: file header without a path at line {i + 1}")
            status = "added" if old is None else "deleted" if new is None else "modified"
            current = files.setdefault(path, {"net": Counter(), "blocks": [], "status": status})
            i += 2
            continue
        m = HUNK.match(line)
        if m:
            if current is None:
                raise ValueError(f"{label}: hunk before a file header at line {i + 1}")
            old_left = int(m.group(2)) if m.group(2) is not None else 1
            new_left = int(m.group(4)) if m.group(4) is not None else 1
            i += 1
            removed, added = [], []

            def flush():
                if removed or added:
                    current["blocks"].append((tuple(removed), tuple(added)))
                    removed.clear()
                    added.clear()

            while i < len(lines) and (old_left > 0 or new_left > 0):
                body = lines[i]
                if body.startswith("\\"):          # "\ No newline at end of file" belongs to the previous line
                    i += 1
                    continue
                tag, content = (body[:1], body[1:]) if body else (" ", "")
                if tag == " ":
                    flush()
                    old_left -= 1
                    new_left -= 1
                elif tag == "-":
                    removed.append(content)
                    current["net"][content] -= 1
                    old_left -= 1
                elif tag == "+":
                    added.append(content)
                    current["net"][content] += 1
                    new_left -= 1
                else:
                    raise ValueError(f"{label}: unexpected line in hunk at line {i + 1}: {body[:40]!r}")
                i += 1
            flush()
            while i < len(lines) and lines[i].startswith("\\"):
                i += 1
            continue
        i += 1
    for entry in files.values():
        entry["net"] = Counter({k: v for k, v in entry["net"].items() if v != 0})
    return files


def new_file(dest: str, source: Path) -> dict:
    content = source.read_text(encoding="utf-8").splitlines()
    return {dest: {"net": Counter(content), "blocks": [((), tuple(content))], "status": "added"}}


def add_into(total: dict, part: dict) -> None:
    for path, entry in part.items():
        slot = total.setdefault(path, {"net": Counter(), "blocks": [], "status": entry["status"]})
        slot["net"].update(entry["net"])
        slot["net"] = Counter({k: v for k, v in slot["net"].items() if v != 0})
        slot["blocks"].extend(entry["blocks"])


def net_diff(x: Counter, y: Counter, limit: int = 8) -> list:
    keys = sorted(set(x) | set(y))
    out = [{"line": k[:120], "a": x.get(k, 0), "b": y.get(k, 0)} for k in keys if x.get(k, 0) != y.get(k, 0)]
    return out[:limit] + ([{"more": len(out) - limit}] if len(out) > limit else [])


def under(path: str, prefixes: list[str]) -> bool:
    return any(path == p or path.startswith(p) for p in prefixes)


def compare(a: dict, b: dict, approved: dict | None, allow: list[str], protect: list[str], names: tuple[str, str]) -> dict:
    rows, reasons, notes = [], [], []
    for path in sorted(set(a) | set(b) | set(approved or {})):
        ea = a.get(path, {"net": Counter(), "blocks": []})
        eb = b.get(path, {"net": Counter(), "blocks": []})
        row = {"file": path, "a_lines": sum(abs(v) for v in ea["net"].values()),
               "b_lines": sum(abs(v) for v in eb["net"].values()),
               "a_equals_b_net": ea["net"] == eb["net"],
               "a_equals_b_blocks": sorted(ea["blocks"]) == sorted(eb["blocks"])}
        if approved is not None:
            ep = approved.get(path, {"net": Counter()})
            row["a_equals_approved"] = ea["net"] == ep["net"]
            row["b_equals_approved"] = eb["net"] == ep["net"]
            if not row["a_equals_approved"]:
                reasons.append(f"{path}: {names[0]} differs from the approved changes")
                row["a_vs_approved"] = net_diff(ea["net"], ep["net"])
            if not row["b_equals_approved"]:
                reasons.append(f"{path}: {names[1]} differs from the approved changes")
                row["b_vs_approved"] = net_diff(eb["net"], ep["net"])
        if not row["a_equals_b_net"]:
            reasons.append(f"{path}: {names[0]} and {names[1]} differ")
            row["a_vs_b"] = net_diff(ea["net"], eb["net"])
        elif not row["a_equals_b_blocks"]:
            # Same added/removed lines, split into different blocks: the change landed at another place or the diff
            # aligned blank lines differently. Not a different change set; reported for the reviewer.
            notes.append(f"{path}: same lines, different change blocks in {names[0]} and {names[1]} (placement differs)")
        changed = bool(ea["net"]) or bool(eb["net"])
        if changed and under(path, protect):
            reasons.append(f"{path}: protected forge source changed")
            row["protected"] = True
        if changed and not under(path, allow):
            reasons.append(f"{path}: outside the allowed paths")
            row["outside_allow"] = True
        rows.append(row)
    return {"files": rows, "reasons": reasons, "notes": notes,
            "verdict": "SAME_CHANGE_SET" if not reasons else "DIFFERENT"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="NAME=DIFF (first tree's merge diff)")
    ap.add_argument("--b", required=True, help="NAME=DIFF (second tree's merge diff)")
    ap.add_argument("--approved", nargs="*", default=[], type=Path, help="approved patches (unified diffs)")
    ap.add_argument("--approved-new", nargs="*", default=[], help="approved new files DEST=SOURCE")
    ap.add_argument("--allow", nargs="*", default=DEFAULT_ALLOW)
    ap.add_argument("--protect", nargs="*", default=DEFAULT_PROTECT)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)
    try:
        (na, pa), (nb, pb) = (s.split("=", 1) for s in (args.a, args.b))
        a = parse_diff(Path(pa).read_text(encoding="utf-8"), na)
        b = parse_diff(Path(pb).read_text(encoding="utf-8"), nb)
        approved = None
        if args.approved or args.approved_new:
            approved = {}
            for p in args.approved:
                add_into(approved, parse_diff(p.read_text(encoding="utf-8"), str(p)))
            for spec in args.approved_new:
                dest, source = spec.split("=", 1)
                add_into(approved, new_file(dest, Path(source)))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    result = compare(a, b, approved, args.allow, args.protect, (na, nb))
    result["inputs"] = {
        na: {"path": pa, "sha256": hashlib.sha256(Path(pa).read_bytes()).hexdigest()},
        nb: {"path": pb, "sha256": hashlib.sha256(Path(pb).read_bytes()).hexdigest()},
        "approved": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in args.approved],
        "approved_new": args.approved_new,
    }
    print(f"{'file':40s} {na + ' lines':>12s} {nb + ' lines':>12s}  same net  same blocks  approved")
    for r in result["files"]:
        appr = "-" if approved is None else ("yes" if r["a_equals_approved"] and r["b_equals_approved"] else "NO")
        print(f"{r['file']:40s} {r['a_lines']:12d} {r['b_lines']:12d}  {str(r['a_equals_b_net']):8s}  "
              f"{str(r['a_equals_b_blocks']):11s}  {appr}")
    for note in result["notes"]:
        print("NOTE:", note)
    for reason in result["reasons"]:
        print("REASON:", reason)
    print("VERDICT:", result["verdict"])
    if args.json:
        args.json.write_text(json.dumps(result, indent=1, sort_keys=True, default=list) + "\n", encoding="utf-8")
    return 0 if result["verdict"] == "SAME_CHANGE_SET" else 1


if __name__ == "__main__":
    sys.exit(main())
