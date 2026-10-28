#!/usr/bin/env python3
"""R3-1 self-play matrix: runs opus_selfplay_check.py once per config of configs.json (one config at a time),
then writes MATRIX.md and matrix_summary.json (per config: games, plies, errors, crashes, illegal moves, double
bestmoves, timeouts, exe sha256, git head, sha256 of every log file).

usage: run_matrix.py --engines DIR --nets DIR --out DIR --git-head SHA [--configs configs.json] [--games 500]
                     [--parallel 3] [--parallel-smp 2] [--only a,b] [--skip a,b] [--no-optional]
                     [--preflight-only] [--resume] [--report-only] [--seed 1] [--harness PATH] [--epd PATH]
                     [--harness-arg=ARG ...] [--log-name matrix.log] [--runner NAME]
Engines are DIR/opus_r3sp_<exe key>.exe. --resume skips configs whose summary shows all games played.
--runner NAME runs only the configs with "runner": NAME (two runners can share one configs file and --out).
The configs file is read again before every config (a broken file keeps the previous list): configs can be
added, removed or reordered while a matrix runs, and optional top-level "parallel" / "parallel_smp" keys
override the command-line parallelism from the next config on. Extra checker arguments (e.g. lower per-move
budgets: --nodes-min/--nodes-max/--mix) come from --harness-arg, a top-level "harness_args" list and a
per-config "harness_args" list, in that order.
Exit status 0 when every config ran all its games with 0 errors.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "opus_selfplay_check.py")
LOG_SUFFIXES = (".summary.json", ".games.jsonl", ".pgn", ".events.log", ".preflight.json", ".preflight.log",
                ".stdout.log")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def subst(text, a, syzygy):
    return text.replace("{nets}", a.nets.replace("\\", "/")).replace("{syzygy}", syzygy)


def report(a, configs):
    rows, total_bad = [], 0
    out = dict(git_head=a.git_head, out_dir=a.out, configs=[])
    for c in configs:
        path = os.path.join(a.out, c["name"] + ".summary.json")
        if not os.path.exists(path):
            out["configs"].append(dict(config=c["name"], status="not run"))
            rows.append(f"| {c['name']} | not run | | | | | | | | | | | | | | |")
            continue
        s = load(path)
        logs = {}
        for suf in LOG_SUFFIXES:
            p = os.path.join(a.out, c["name"] + suf)
            if os.path.exists(p):
                logs[os.path.basename(p)] = dict(bytes=os.path.getsize(p), sha256=sha256(p))
        errgames = os.path.join(a.out, "errgames")
        if os.path.isdir(errgames):
            for fn in sorted(os.listdir(errgames)):
                if fn.startswith(c["name"] + "_g") or fn.startswith(c["name"] + "_w"):
                    p = os.path.join(errgames, fn)
                    logs["errgames/" + fn] = dict(bytes=os.path.getsize(p), sha256=sha256(p))
        ok = s.get("preflight_ok") and s.get("errors") == 0 and s.get("games") == s.get("games_requested")
        total_bad += 0 if ok else 1
        out["configs"].append(dict(s, status="clean" if ok else "FAIL", logs=logs))
        if not s.get("preflight_ok"):
            rows.append(f"| {c['name']} | preflight FAILED: {s.get('preflight_errors')} | | | | | | | | | | | | | | |")
            continue
        opts = ", ".join(o for o in s["options"][4:]) or "(none)"
        rows.append(
            f"| {c['name']} | {os.path.basename(s['exe'])} `{s['exe_sha256'][:12]}` | {s['threads']} | {opts} | "
            f"{s['games']}/{s['games_requested']} | {s['plies']} | **{s['errors']}** | {s['crashes']} | "
            f"{s['illegal_moves']} | {s['double_bestmoves']} | {s['timeouts']} | {s['malformed_output']} | "
            f"{s['errors_by_type'].get('late_search_output', 0)}"
            f"{'' if s.get('late_after_watchdog') is None else ' (' + str(s['late_after_watchdog']) + ' after watchdog)'} | "
            f"{s['hard_deadline_fired']} | {s['games_with_tbhits']} | {s['bench11_nodes']} | {s['wall_s']} |")
    head = ("| config | exe (sha256) | thr | options | games | plies | errors | crashes | illegal moves | "
            "double bestmoves | timeouts | malformed | of which late info after bestmove | HardDeadline fired | "
            "games w/ tbhits | bench11 | wall s |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    md = (f"# R3-1 self-play matrix, git head {a.git_head}\n\n"
          f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} by run_matrix.py from {a.out}; every engine also runs with "
          f"Hash 16, Ponder true, OwnBook false. Configs with errors or missing games: {total_bad}.\n\n"
          + head + "\n" + "\n".join(rows) + "\n")
    with open(os.path.join(a.out, "MATRIX.md"), "w", newline="\n", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(a.out, "matrix_summary.json"), "w", newline="\n", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    return total_bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engines", required=True)
    ap.add_argument("--nets", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--git-head", required=True)
    ap.add_argument("--configs", default=os.path.join(HERE, "configs.json"))
    ap.add_argument("--games", type=int, default=500)
    ap.add_argument("--parallel", type=int, default=3)
    ap.add_argument("--parallel-smp", type=int, default=2)
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--no-optional", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--seed", default="1")
    ap.add_argument("--epd", default=None)
    ap.add_argument("--harness", default=CHECK, help="checker script (default: the one next to this file)")
    ap.add_argument("--harness-arg", action="append", default=[], help="extra checker argument (repeatable)")
    ap.add_argument("--log-name", default="matrix.log",
                    help="runner log in --out (one per runner when several share --out)")
    ap.add_argument("--runner", default="",
                    help="run only the configs whose \"runner\" field is this (several runners, one configs file); "
                         "configs that already have a complete summary in --out are skipped")
    a = ap.parse_args()
    only = [x for x in a.only.split(",") if x]
    skip = set(x for x in a.skip.split(",") if x)
    state = {}

    def pick():
        """(spec, configs) from the configs file, read again each time; the last good read if it is broken."""
        try:
            spec = load(a.configs)
            cfgs = [c for c in spec["configs"] if (not only or c["name"] in only) and c["name"] not in skip
                    and not (a.no_optional and c.get("optional")) and (not a.runner or c.get("runner") == a.runner)]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            if not state:
                raise
            print(f"configs file unreadable ({exc}); keeping the previous list", flush=True)
            return state["spec"], state["configs"]
        if only:
            cfgs.sort(key=lambda c: only.index(c["name"]))
        state.update(spec=spec, configs=cfgs)
        return spec, cfgs

    spec, configs = pick()
    os.makedirs(a.out, exist_ok=True)
    if a.report_only:
        return 1 if report(a, configs) else 0
    mlog = open(os.path.join(a.out, a.log_name), "a", newline="\n", encoding="utf-8")

    def log(text):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {text}"
        print(line, flush=True)
        mlog.write(line + "\n")
        mlog.flush()

    log(f"matrix start: {len(configs)} configs, git head {a.git_head}, engines {a.engines}, games {a.games}, "
        f"harness {a.harness} sha256 {sha256(a.harness)}, configs {a.configs} sha256 {sha256(a.configs)}")
    done = set()
    while True:
        spec, configs = pick()
        todo = [c for c in configs if c["name"] not in done]
        if not todo:
            break
        c = todo[0]
        done.add(c["name"])
        syzygy = spec.get("syzygy", "")
        parallel, parallel_smp = int(spec.get("parallel", a.parallel)), int(spec.get("parallel_smp", a.parallel_smp))
        name = c["name"]
        spath = os.path.join(a.out, name + ".summary.json")
        if (a.resume or a.runner) and os.path.exists(spath):
            s = load(spath)
            if s.get("games") == a.games:
                log(f"{name}: done already ({s.get('errors')} errors), skipped")
                continue
        exe = os.path.join(a.engines, f"opus_r3sp_{c['exe']}.exe").replace("\\", "/")
        threads = c.get("threads", 1)
        cmd = [sys.executable, "-I", "-B", a.harness, "--name", name, "--exe", exe, "--threads", str(threads),
               "--games", str(a.games), "--parallel", str(parallel_smp if threads > 1 else parallel),
               "--out-dir", a.out, "--git-head", a.git_head, "--seed", a.seed]
        if a.epd:
            cmd += ["--epd", a.epd]
        for o in c.get("opts", []):
            cmd += ["--opt", subst(o, a, syzygy)]
        cmd += a.harness_arg + [str(x) for x in spec.get("harness_args", [])] + [str(x) for x in
                                                                                c.get("harness_args", [])]
        if a.preflight_only:
            cmd.append("--preflight-only")
        log(f"{name}: start: {' '.join(cmd[3:])}")
        t0 = time.time()
        with open(os.path.join(a.out, name + ".stdout.log"), "w", newline="\n", encoding="utf-8") as out:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for raw in iter(p.stdout.readline, b""):
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                out.write(line + "\n")
                out.flush()
                if line.startswith(f"[{name}]") or "Traceback" in line or "Error" in line:
                    log("   " + line)
            code = p.wait()
        log(f"{name}: exit status {code} after {time.time() - t0:.0f} s")
    spec, configs = pick()
    bad = report(a, configs)
    log(f"matrix end: {len(configs)} configs, {bad} with errors or missing games; MATRIX.md written")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
