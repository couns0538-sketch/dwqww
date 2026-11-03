#!/usr/bin/env python3
"""job_damage.py OUT_DIR [--only CASE,...] - Opus R14-B item 2: damaged JOB state against relabel2.py run / assemble /
status (published shards, manifests, rows.tsv, prepare.json, run_config.json, status files, stray names).

A small base job is made first (OUT_DIR/base: prepare 1,500 rows, run at 2,000 nodes in 500-row shards, all shards
published, not assembled) with the relabel2.py next to this file (or $R2). Every (case, command) then gets a fresh copy
of it; the damage is made by renaming aside (nothing is deleted) or by editing the copy. Verdict "ok" = the exit code the
case should give (0, or 2 / 3 / 4 with relabel2's own "BAD INPUT:" / "CONFIG MISMATCH:" / "INTEGRITY:" line) and
nothing new published on a refusal; anything else (a traceback = exit 1, a silent exit 0 on damaged state, a refusal
after publishing) is a FINDING. Exit 0 = no finding. Bug hunt of 2026-11-02 22:11: 29 findings on 0a81dd5f, 0 after
the fix. 22:37: a run_config.json edited to other settings is caught with a matching command line too (shards record
their node limit / hash / probe sha256): 3 more runs that 56eef0a6 passes silently.
Environment: PY (python with python-chess), PROBE (R13 probe), SRC (self-play text), R2 (relabel2.py).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.environ.get("R2", os.path.join(HERE, "relabel2.py"))
PY = os.environ.get("PY", "C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe")
PROBE = os.environ.get("PROBE", "C:/o13/p5/forge_data_probe.exe")
SRC = os.environ.get("SRC", "D:/grok-pc-data/selfplay_out/forge_selfplay_001.txt")
RUN_ARGS = ["--probe", PROBE, "--nodes", "2000", "--shard-size", "500", "--workers", "1", "--mask", "0xC"]


def sh(args, timeout=300):
    p = subprocess.run([PY, "-I", "-B", R] + args, capture_output=True, timeout=timeout)
    err = p.stderr.decode("utf-8", "replace").strip().splitlines()
    return p.returncode, (err[-1] if err else "")[:200]


def build_base(base):
    job = os.path.join(base, "job")
    os.makedirs(base)
    for args in (["prepare", "--job", job, "--run-id", "jd", "--rows", "1500", "--selfplay", SRC],
                 ["run", "--job", job, "--run-id", "jd"] + RUN_ARGS):
        rc, msg = sh(args)
        if rc != 0:
            sys.exit(f"base job: {args[0]} failed with exit {rc}: {msg}")
    return job


def aside(p):
    os.rename(p, p + ".aside")


def flip(p, at=200):
    with open(p, "r+b") as fh:
        fh.seek(at)
        b = fh.read(1)
        fh.seek(at)
        fh.write(bytes([b[0] ^ 0x01]))


def trunc(p):
    with open(p, "r+b") as fh:
        fh.truncate(os.path.getsize(p) // 2)


def put(p, text):
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def S(j, k, name=""):
    d = os.path.join(j, "shards", f"shard_{k:05d}")
    return os.path.join(d, name) if name else d


def swap(j):
    a, b = S(j, 0), S(j, 1)
    os.rename(a, a + ".tmp")
    os.rename(b, a)
    os.rename(a + ".tmp", b)


def copy_over(j):
    aside(S(j, 1))
    shutil.copytree(S(j, 0), S(j, 1))


def dir_to_file(j):
    aside(S(j, 2))
    put(S(j, 2), "not a dir\n")


def edit_json(p, **kw):
    with open(p, encoding="utf-8") as fh:
        d = json.load(fh)
    d.update(kw)
    put(p, json.dumps(d, indent=1) + "\n")


def extra_shard(j):
    shutil.copytree(S(j, 0), os.path.join(j, "shards", "shard_00099"))


def shards_to_file(j):
    aside(os.path.join(j, "shards"))
    put(os.path.join(j, "shards"), "x\n")


def J(*parts):
    return lambda j: os.path.join(j, *parts)


# case -> (damage, {command: expected exit}[, --nodes for run]); expected = what a careful tool does, decided before the first run
CASES = {
    "labels_flip": (lambda j: flip(S(j, 1, "labels.tsv")), {"run": 4, "assemble": 4, "status": 0}),
    "labels_trunc": (lambda j: trunc(S(j, 1, "labels.tsv")), {"run": 4, "assemble": 4, "status": 0}),
    "labels_missing": (lambda j: aside(S(j, 1, "labels.tsv")), {"run": 4, "assemble": 4, "status": 0}),
    "manifest_missing": (lambda j: aside(S(j, 1, "manifest.json")), {"run": 4, "assemble": 4, "status": 0}),
    "manifest_empty_obj": (lambda j: put(S(j, 1, "manifest.json"), "{}\n"), {"run": 4, "assemble": 4, "status": 0}),
    "manifest_list": (lambda j: put(S(j, 1, "manifest.json"), "[]\n"), {"run": 4, "assemble": 4, "status": 0}),
    "manifest_garbage": (lambda j: put(S(j, 1, "manifest.json"), "{\"labels.tsv\": \n"), {"run": 4, "assemble": 4, "status": 0}),
    "summary_missing": (lambda j: aside(S(j, 1, "summary.json")), {"run": 4, "assemble": 4, "status": 0}),
    "summary_edit": (lambda j: edit_json(S(j, 1, "summary.json"), seconds=0.5), {"run": 4, "assemble": 4, "status": 0}),
    "shard_swap": (swap, {"run": 4, "assemble": 4, "status": 0}),
    "shard_copy": (copy_over, {"run": 4, "assemble": 4, "status": 0}),
    "shard_dir_missing": (lambda j: aside(S(j, 2)), {"run": 0, "assemble": 4, "status": 0}),
    "shard_dir_is_file": (dir_to_file, {"run": 4, "assemble": 4, "status": 0}),
    "rows_flip": (lambda j: flip(J("rows.tsv")(j), 5000), {"run": 4, "assemble": 4, "status": 0}),
    "rows_missing": (lambda j: aside(J("rows.tsv")(j)), {"run": 4, "assemble": 4, "status": 0}),
    "prepare_missing": (lambda j: aside(J("prepare.json")(j)), {"run": 2, "assemble": 2, "status": 2}),
    "prepare_garbage": (lambda j: put(J("prepare.json")(j), "{\"rows\": \n"), {"run": 4, "assemble": 4, "status": 4}),
    "prepare_empty_obj": (lambda j: put(J("prepare.json")(j), "{}\n"), {"run": 4, "assemble": 4, "status": 4}),
    "run_config_missing": (lambda j: aside(J("run_config.json")(j)), {"run": 4, "assemble": 4, "status": 0}),
    "run_config_garbage": (lambda j: put(J("run_config.json")(j), "{\"run_id\": \n"), {"run": 4, "assemble": 4, "status": 0}),
    "run_config_empty_obj": (lambda j: put(J("run_config.json")(j), "{}\n"), {"run": 4, "assemble": 4, "status": 0}),
    "run_config_other_nodes": (lambda j: edit_json(J("run_config.json")(j), nodes=3000), {"run": 3, "assemble": 4, "status": 0}),
    # the same edit with a command line that matches it (run --nodes 3000): the shards were labelled at 2,000
    "run_config_other_nodes_matching_command": (lambda j: edit_json(J("run_config.json")(j), nodes=3000),
                                                {"run": 4, "assemble": 4, "status": 0}, "3000"),
    "status_garbage": (lambda j: put(J("status.json")(j), "{\"run_id\": \n"), {"run": 0, "assemble": 0, "status": 0}),
    "status_list": (lambda j: put(J("status.json")(j), "[1, 2]\n"), {"run": 0, "assemble": 0, "status": 0}),
    "stale_lock_file": (lambda j: put(J("job.lock")(j), "old\n"), {"run": 0, "assemble": 0, "status": 0}),
    "final_exists": (lambda j: os.mkdir(J("final")(j)), {"run": 0, "assemble": 3, "status": 0}),
    "final_part_junk": (lambda j: os.mkdir(J("final.part.1")(j)), {"run": 0, "assemble": 0, "status": 0}),
    "final_part_bad_name": (lambda j: os.mkdir(J("final.part.x")(j)), {"run": 0, "assemble": 0, "status": 0}),
    "part_dir_junk": (lambda j: os.mkdir(S(j, 1) + ".part.7"), {"run": 0, "assemble": 0, "status": 0}),
    "part_bad_name_unpublished": (lambda j: (aside(S(j, 2)), os.mkdir(S(j, 2) + ".part.x")), {"run": 0, "assemble": 4, "status": 0}),
    "extra_shard_out_of_range": (extra_shard, {"run": 0, "assemble": 0, "status": 0}),
    "foreign_name_in_shards": (lambda j: os.mkdir(J("shards", "shard_abcde")(j)), {"run": 0, "assemble": 0, "status": 0}),
    "sessions_log_missing": (lambda j: aside(J("sessions.log")(j)), {"run": 0, "assemble": 0, "status": 0}),
    "shards_is_file": (shards_to_file, {"run": 4, "assemble": 4, "status": 0}),
}

PREFIX = {2: "BAD INPUT: ", 3: "CONFIG MISMATCH: ", 4: "INTEGRITY: "}


def published(j):
    sd = os.path.join(j, "shards")
    names = sorted(n for n in os.listdir(sd) if re.fullmatch(r"shard_\d{5}", n)) if os.path.isdir(sd) else []
    return names, os.path.isdir(os.path.join(j, "final"))


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    out = sys.argv[1]
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    for f in (R, PY, PROBE, SRC):
        if not os.path.isfile(f):
            print(f"not found: {f} (set PY / PROBE / SRC / R2)", file=sys.stderr)
            return 2
    if os.path.exists(out):
        print(f"refusing existing {out}", file=sys.stderr)
        return 2
    try:  # Idle on CPUs 2-3 (the children inherit both); without psutil the caller pins the process
        import psutil
        me = psutil.Process()
        me.nice(psutil.IDLE_PRIORITY_CLASS if os.name == "nt" else 19)
        me.cpu_affinity([2, 3])
    except ImportError:
        pass
    job0 = build_base(os.path.join(out, "base"))
    bad = n = 0
    with open(os.path.join(out, "cases.tsv"), "x", encoding="utf-8", newline="\n") as log:
        log.write("case\tcommand\texpected\texit\tverdict\tseconds\tmessage\n")
        for case, (damage, exp, *nodes) in CASES.items():
            if only and case not in only:
                continue
            for cmd in ("run", "assemble", "status"):
                j = os.path.join(out, f"{case}.{cmd}", "job")
                shutil.copytree(job0, j, ignore=shutil.ignore_patterns("job.lock"))
                damage(j)
                before = published(j)
                run_args = [nodes[0] if nodes and x == "2000" else x for x in RUN_ARGS]  # a case's own --nodes
                args = {"run": ["run", "--job", j, "--run-id", "jd"] + run_args,
                        "assemble": ["assemble", "--job", j, "--run-id", "jd", "--mask", "0xC"],
                        "status": ["status", "--job", j]}[cmd]
                t0 = time.monotonic()
                try:
                    rc, msg = sh(args, timeout=120)
                except subprocess.TimeoutExpired:
                    rc, msg = "HANG", ""
                after = published(j)
                want = exp[cmd]
                why = ""
                if rc != want:
                    why = f"exit {rc}, want {want}"
                elif rc in PREFIX and not msg.startswith(PREFIX[rc]):
                    why = "no relabel2 reason line"
                elif rc != 0 and after != before:
                    why = f"refused after publishing {before} -> {after}"
                n += 1
                bad += bool(why)
                verdict = "FINDING" if why else "ok"
                log.write(f"{case}\t{cmd}\t{want}\t{rc}\t{verdict}\t{time.monotonic() - t0:.1f}\t"
                          f"{why + ' | ' if why else ''}{msg}\n")
                log.flush()
                print(f"{case:28s} {cmd:8s} want {want} got {rc!s:4s} {verdict:7s} {why} | {msg[:110]}")
    print(f"job_damage: {n} runs, findings {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
