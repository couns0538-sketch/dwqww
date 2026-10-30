"""R9 chain: sanity run (to --total-pairs) -> its report -> (only if the sanity result is right) the STC tune -> report.
usage: python -I -B run_pinned.py --mask 0x000F -- r9_chain.py <worktree root> <runs dir> <reports dir> <stc --until HH:MM>
Runs the sanity tuner itself (resuming <runs>/sanity2 if it exists) until 200 pairs in total, reports it and checks
that the deliberately wrong LmrQuietDivisor moved UP toward the lock value 220 with z >= 1 (a sign or attribution
error in the real game pipeline would move it down). Only then the STC run (<runs>/stc1) starts and runs until
--until. The governor inside the tuner waits whenever the load rules say so. Stop the chain with
<runs dir>/CHAIN_STOP (only a file newer than the chain's start counts; checked between the steps), the runs with
their own <run>/STOP."""
import json
import subprocess
import sys
import time
from pathlib import Path

root, runs, reports, until = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
py = sys.executable
tuner, report = root / "opus_r9" / "tuner" / "r9_spsa.py", root / "opus_r9" / "tuner" / "r9_spsa_report.py"
exe = r"F:\opus_scratch\r9\build\forge_r9_c.exe"
t0 = time.time()


def say(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] chain: {msg}", flush=True)


def chain_stop():
    p = runs / "CHAIN_STOP"
    if p.exists() and p.stat().st_mtime >= t0 - 1:
        say("CHAIN_STOP found")
        sys.exit(0)


def tune(config, run, extra):
    args = [py, "-I", "-B", str(tuner), "run", str(root / "opus_r9" / "configs" / config), str(run)] + extra
    if run.exists():
        args.append("--resume")
    rc = subprocess.call(args)
    say(f"{run.name} tuner exit {rc}")
    return rc


def make_report(run, out, title):
    p = subprocess.run([py, "-I", "-B", str(report), str(run), "--out", str(out), "--exe", exe, "--title", title],
                       capture_output=True, text=True)
    say(f"report {out}: exit {p.returncode}")
    return json.loads((out / "r9_params.json").read_text(encoding="ascii")) if p.returncode == 0 else None


sanity = runs / "sanity2"
chain_stop()
tune("sanity.json", sanity, ["--total-pairs", "200"])
chain_stop()
res = make_report(sanity, reports / "sanity2", "R9 sanity run: LmrQuietDivisor started at 120 (lock 220)")
if res is None:
    say("sanity report failed: STC run not started")
    sys.exit(2)
lmr = next(p for p in res["params"] if p["name"] == "LmrQuietDivisor")
say(f"sanity: LmrQuietDivisor {lmr['start']} -> {lmr['end']} (z {lmr['z']}), pairs {res['pairs']}")
if res["pairs"] < 100 or not (lmr["end"] > lmr["start"] and lmr["z"] >= 1):
    say("sanity check NOT passed: the STC run is not started")
    sys.exit(3)
say(f"sanity check passed: starting the STC run until {until}")
chain_stop()
stc = runs / "stc1"
tune("stc_main.json", stc, ["--until", until])
make_report(stc, reports / "stc1", "R9 STC 8+0.08 SPSA run (16 parameters from the lock values)")
say("done")
