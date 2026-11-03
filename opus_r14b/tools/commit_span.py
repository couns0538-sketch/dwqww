#!/usr/bin/env python3
"""commit_span.py - Opus R14-B: what did the hours buy? Time spans from commit times, never from memory (own code).

usage: python -I -B commit_span.py [--repo DIR] [--since "YYYY-MM-DD HH:MM"] [--until ...] [--gap 30] BRANCH...
Per branch (remote refs are fine, e.g. origin/opus-r14b-relabel): commits in the window, first and last commit time,
span. Then all branches merged into one timeline with every pause longer than --gap minutes (no commit on any of the
branches) and the busiest hours. Commit (not author) dates, in the PC's local clock. Read-only (git log only).
Exit 0, or 2 for a bad branch / no commits.
"""
import argparse
import collections
import datetime as dt
import subprocess
import sys


def commits(repo, branch, since, until):
    cmd = ["git", "-C", repo, "log", "--format=%ct%x09%h%x09%s", branch]
    if since:
        cmd.insert(4, f"--since={since}")
    if until:
        cmd.insert(4, f"--until={until}")
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    if r.returncode:
        print(f"commit_span: git log {branch} failed: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    out = []
    for line in r.stdout.splitlines():
        ts, h, subj = line.split("\t", 2)
        out.append((dt.datetime.fromtimestamp(int(ts)), h, subj))
    return sorted(out)


def fmt(t):
    return t.strftime("%m-%d %H:%M")


def dur(d):
    m = int(d.total_seconds() // 60)
    return f"{m // 60}h{m % 60:02d}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("branches", nargs="+")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--gap", type=int, default=30, help="report pauses longer than this many minutes")
    a = ap.parse_args()
    allc = []
    print(f"{'branch':<34} {'commits':>7}  {'first':<11}  {'last':<11}  span")
    for b in a.branches:
        c = commits(a.repo, b, a.since, a.until)
        if not c:
            print(f"{b:<34} {0:>7}  (no commits in the window)")
            continue
        allc += [(t, b, h, s) for t, h, s in c]
        print(f"{b:<34} {len(c):>7}  {fmt(c[0][0]):<11}  {fmt(c[-1][0]):<11}  {dur(c[-1][0] - c[0][0])}")
    if not allc:
        print("commit_span: no commits", file=sys.stderr)
        return 2
    allc.sort()
    seen, uniq = set(), []
    for t, b, h, s in allc:  # a commit reachable from two branches counts once
        if h not in seen:
            seen.add(h)
            uniq.append((t, b, h, s))
    print(f"\nall: {len(uniq)} distinct commits, {fmt(uniq[0][0])} -> {fmt(uniq[-1][0])} "
          f"({dur(uniq[-1][0] - uniq[0][0])})")
    gaps = [(uniq[i][0], uniq[i + 1][0]) for i in range(len(uniq) - 1)
            if (uniq[i + 1][0] - uniq[i][0]).total_seconds() > a.gap * 60]
    print(f"pauses > {a.gap} min with no commit on any branch: {len(gaps)}"
          + (f" (total {dur(sum((y - x for x, y in gaps), dt.timedelta()))})" if gaps else ""))
    for x, y in gaps:
        print(f"  {fmt(x)} -> {fmt(y)}  {dur(y - x)}")
    per_hour = collections.Counter(t.strftime("%m-%d %H:00") for t, _, _, _ in uniq)
    print("commits per hour: " + ", ".join(f"{k[6:]} {v}" for k, v in sorted(per_hour.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
