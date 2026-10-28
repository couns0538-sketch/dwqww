#!/usr/bin/env python3
"""R3-1L: table of the Linux self-play double-check (one row per job x config).

usage: summarize.py --single <job out dir>                       (one job; printed by run_job.sh)
       summarize.py --jobs jobs.json --arts <dir> [--out <dir>]   (all jobs; <dir> holds the downloaded
                                                                   sp-<job id> artifacts)
Pass rule (the PC's): every config ran all requested games (500 for release jobs) with 0 errors and a clean
preflight; every build of the job passed the identity check (bench/perft pins; FMA 0 for release); sanitizer
jobs wrote 0 sanitizer reports. Exit 1 if any row fails or a job left no artifact.
"""
import argparse
import glob
import json
import os
import sys

COLS = ("| job | mode | config | exe (sha256) | identity | games | plies | errors | errors by kind | crashes | "
        "illegal moves | double bestmoves | timeouts | malformed | watchdog answers | HardDeadline fired | "
        "late after watchdog | sanitizer reports | wall s | status |")
SEP = "|" + "---|" * (COLS.count("|") - 1)


def read_tsv(path):
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 2:
                    out[parts[0]] = parts[1]
    return out


def read_builds(path):
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 5:
                    out[p[0]] = dict(sha256=p[1], mode=p[2], fma=p[3], identity=p[4])
    return out


def job_rows(job_dir, job_id=None, want_games=None):
    """Rows (dicts) of one job out dir."""
    jt = read_tsv(os.path.join(job_dir, "job.tsv"))
    builds = read_builds(os.path.join(job_dir, "builds.tsv"))
    jid = job_id or jt.get("job", os.path.basename(job_dir))
    mode = jt.get("mode", "?")
    games_req = int(want_games or jt.get("games", 0) or 0)
    san = jt.get("sanitizer_reports", "?")
    cfgs = []
    try:
        with open(os.path.join(job_dir, "job_configs.json"), encoding="utf-8") as f:
            cfgs = json.load(f)["configs"]
    except (OSError, ValueError, KeyError):
        pass
    names = [c["name"] for c in cfgs] or [n for n in jt.get("configs", "").split(",") if n]
    exe_of = {c["name"]: c.get("exe", "?") for c in cfgs}
    rows = []
    for name in names:
        r = dict(job=jid, mode=mode, config=name, sanitizer=san)
        b = builds.get(exe_of.get(name, "?"), {})
        ident_ok = b.get("identity") == "ALL OK" and (mode != "release" or b.get("fma") == "0")
        r["exe"] = f"{exe_of.get(name, '?')} `{b.get('sha256', '?')[:12]}`"
        r["identity"] = (b.get("identity", "no build") + ("" if mode != "release" else f", FMA {b.get('fma', '?')}"))
        sp = os.path.join(job_dir, "runs", name + ".summary.json")
        if not os.path.exists(sp):
            r.update(status="FAIL (no summary)", ok=False)
            rows.append(r)
            continue
        with open(sp, encoding="utf-8") as f:
            s = json.load(f)
        kinds = s.get("errors_by_type") or {}
        r.update(games=f"{s.get('games')}/{s.get('games_requested')}", plies=s.get("plies"), errors=s.get("errors"),
                 kinds=", ".join(f"{k} {v}" for k, v in sorted(kinds.items())) or "-",
                 crashes=s.get("crashes"), illegal=s.get("illegal_moves"), double=s.get("double_bestmoves"),
                 timeouts=s.get("timeouts"), malformed=s.get("malformed_output"),
                 watchdog=s.get("watchdog_answers", "-"), fired=s.get("hard_deadline_fired", "-"),
                 late=s.get("late_after_watchdog", "-"), wall=s.get("wall_s"))
        why = []
        if not s.get("preflight_ok"):
            why.append(f"preflight: {s.get('preflight_errors')}")
        if s.get("errors") != 0:
            why.append("errors")
        if s.get("games") != s.get("games_requested") or (games_req and s.get("games_requested") != games_req):
            why.append("games short")
        if mode == "release" and s.get("games_requested") != 500:
            why.append("not 500 games")
        if not ident_ok:
            why.append("identity")
        if mode != "release" and str(san) != "0":
            why.append("sanitizer report")
        r.update(status="PASS" if not why else "FAIL (" + "; ".join(why) + ")", ok=not why)
        rows.append(r)
    return rows


def fmt(r):
    g = lambda k: r.get(k, "-")
    return (f"| {g('job')} | {g('mode')} | {g('config')} | {g('exe')} | {g('identity')} | {g('games')} | {g('plies')} | "
            f"{g('errors')} | {g('kinds')} | {g('crashes')} | {g('illegal')} | {g('double')} | {g('timeouts')} | "
            f"{g('malformed')} | {g('watchdog')} | {g('fired')} | {g('late')} | {g('sanitizer')} | {g('wall')} | "
            f"**{g('status')}** |")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--single")
    ap.add_argument("--jobs")
    ap.add_argument("--arts")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.single:
        rows = job_rows(a.single)
        print("\n" + COLS + "\n" + SEP + "\n" + "\n".join(fmt(r) for r in rows) + "\n")
        return 0 if rows and all(r["ok"] for r in rows) else 1
    with open(a.jobs, encoding="utf-8") as f:
        jobs = json.load(f)["jobs"]
    rows, missing = [], []
    for j in jobs:
        hits = glob.glob(os.path.join(a.arts, "sp-" + j["id"], "**", "job.tsv"), recursive=True)
        if not hits:
            missing.append(j["id"])
            for n in j["configs"].split(","):
                rows.append(dict(job=j["id"], mode=j["mode"], config=n, status="FAIL (no artifact)", ok=False))
            continue
        rows += job_rows(os.path.dirname(hits[0]), j["id"], j["games"])
    rel = [r for r in rows if r["mode"] == "release"]
    san = [r for r in rows if r["mode"] != "release"]
    games = lambda rs: sum(int(str(r.get("games", "0/0")).split("/")[0] or 0) for r in rs if r.get("games"))
    errs = lambda rs: sum(int(r.get("errors") or 0) for r in rs)
    head = (f"# R3-1L Linux self-play double-check\n\n"
            f"release: {len({r['config'] for r in rel})} configs, {games(rel)} games, {errs(rel)} errors, "
            f"{sum(1 for r in rel if not r['ok'])} failing rows; sanitizer (ASan+UBSan / TSan): {len(san)} rows, "
            f"{games(san)} games, {errs(san)} errors, {sum(1 for r in san if not r['ok'])} failing rows; jobs "
            f"without artifact: {', '.join(missing) or 'none'}.\n\n"
            "Pass rule: all requested games (500 per release config) with 0 errors and a clean preflight, identity "
            "ALL OK (and FMA 0) for every build, 0 sanitizer reports.\n\n")
    md = head + COLS + "\n" + SEP + "\n" + "\n".join(fmt(r) for r in rows) + "\n"
    print(md)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with open(os.path.join(a.out, "SUMMARY.md"), "w", newline="\n", encoding="utf-8") as f:
            f.write(md)
        with open(os.path.join(a.out, "summary.json"), "w", newline="\n", encoding="utf-8") as f:
            json.dump(dict(rows=rows, missing=missing), f, indent=1)
    return 0 if rows and all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
