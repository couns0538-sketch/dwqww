"""R9 chain: sanity run -> its report -> (only if the sanity result is right) the STC tune -> its report.
usage: python -I -B run_pinned.py --mask 0x000F -- r9_chain.py <worktree root> <runs dir> <reports dir> <stc --until HH:MM>
Waits for the sanity run (already started by hand) to write its `end:` line, reports it, and checks that the
deliberately wrong LmrQuietDivisor moved UP toward the lock value 220 with z >= 1 (a sign or attribution error in the
real game pipeline would move it down). Only then the STC run starts (it waits for CPU under the cap by itself) and
runs until --until. Stop the chain with <runs dir>/CHAIN_STOP (checked every 30 s; the runs have their own STOP)."""
import json
import subprocess
import sys
import time
from pathlib import Path

root, runs, reports, until = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
py = sys.executable
tuner, report = root / "opus_r9" / "tuner" / "r9_spsa.py", root / "opus_r9" / "tuner" / "r9_spsa_report.py"
exe = r"F:\opus_scratch\r9\build\forge_r9_c.exe"


def say(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] chain: {msg}", flush=True)


def wait_end(run):
    log = run / "tuner.log"
    while True:
        if (runs / "CHAIN_STOP").exists():
            say("CHAIN_STOP found")
            sys.exit(0)
        if log.exists() and "end: pair count" in log.read_text(encoding="ascii", errors="replace"):
            return
        time.sleep(30)


def make_report(run, out, title):
    p = subprocess.run([py, "-I", "-B", str(report), str(run), "--out", str(out), "--exe", exe, "--title", title],
                       capture_output=True, text=True)
    say(f"report {out}: exit {p.returncode}")
    return json.loads((out / "r9_params.json").read_text(encoding="ascii")) if p.returncode == 0 else None


sanity = runs / "sanity2"
wait_end(sanity)
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
stc = runs / "stc1"
rc = subprocess.call([py, "-I", "-B", str(tuner), "run", str(root / "opus_r9" / "configs" / "stc_main.json"), str(stc),
                      "--until", until] + (["--resume"] if stc.exists() else []))
say(f"STC run ended: exit {rc}")
make_report(stc, reports / "stc1", "R9 STC 8+0.08 SPSA run (16 parameters from the lock values)")
say("done")
