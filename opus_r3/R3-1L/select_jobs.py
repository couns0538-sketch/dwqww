#!/usr/bin/env python3
"""R3-1L: picks the jobs of one workflow run from jobs.json.

usage: select_jobs.py <jobs.json> <selection> <out selected.json>
selection: "push" (or empty) = the "push_jobs" list of jobs.json (what a push runs); "all" = every job; otherwise a
comma-separated list of job ids, or id prefixes ending in '*' (e.g. "fin-*,rel-all_on").
Writes {"jobs": [...]} (one line) to <out> for the summary job and prints the matrix {"include": [...]} (one line).
"""
import json
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    src, sel, out = sys.argv[1:]
    with open(src, encoding="utf-8") as f:
        spec = json.load(f)
    jobs = spec["jobs"]
    sel = sel.strip()
    pats = spec.get("push_jobs", ["all"]) if sel in ("", "push") else [p.strip() for p in sel.split(",") if p.strip()]

    def match(job):
        return any(p == "all" or p == job["id"] or (p.endswith("*") and job["id"].startswith(p[:-1])) for p in pats)

    chosen = [j for j in jobs if match(j)]
    if not chosen:
        raise SystemExit(f"no job of {src} matches {pats}")
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        f.write(json.dumps({"jobs": chosen}) + "\n")
    print(json.dumps({"include": chosen}))
    print(f"{len(chosen)} of {len(jobs)} jobs selected by {pats}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
