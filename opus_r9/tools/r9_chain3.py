"""R9 chain 3 (after sanity2 had too little signal): sanity3 -> report -> STC tune -> report.
usage: python -I -B run_pinned.py --mask 0x000F -- r9_chain3.py <worktree root> <runs dir> <reports dir> <stc --until HH:MM>
sanity3 = LmrQuietBase started at 250 (lock 85), 240 pairs at 4+0.04. Gate before the STC run: the wrong parameter
must not move AWAY from its lock value with z <= -2 (that would mean a sign or attribution error; the attribution
of every sanity2 game was re-counted from the PGNs with 0 mismatches). Moving toward it with z >= 1 = passed;
anything else = inconclusive, the STC run starts and the report says so. Stop with <runs dir>/CHAIN_STOP (newer than
the chain's start)."""
import json
import subprocess
import sys
import time
from pathlib import Path

root, runs, reports, until = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
py = sys.executable
tuner, report = root / "opus_r9" / "tuner" / "r9_spsa.py", root / "opus_r9" / "tuner" / "r9_spsa_report.py"
svg = root / "opus_r9" / "tuner" / "r9_spsa_svg.py"
exe = r"F:\opus_scratch\r9\build\forge_r9_c.exe"
t0 = time.time()


def say(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] chain3: {msg}", flush=True)


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
    subprocess.call([py, "-I", "-B", str(svg), str(run), str(out / "trajectories.svg"), "--title", title])
    say(f"report {out}: exit {p.returncode}")
    return json.loads((out / "r9_params.json").read_text(encoding="ascii")) if p.returncode == 0 else None


chain_stop()
s3 = runs / "sanity3"
tune("sanity3.json", s3, ["--total-pairs", "240"])
chain_stop()
res = make_report(s3, reports / "sanity3", "R9 sanity run 3: LmrQuietBase started at 250 (lock 85)")
if res is None:
    say("sanity3 report failed: STC run not started")
    sys.exit(2)
p = next(x for x in res["params"] if x["name"] == "LmrQuietBase")
toward = (85 - p["start"]) * p["move"] > 0
zt = abs(p["z"]) if toward else -abs(p["z"])  # z in the direction of the lock value
say(f"sanity3: LmrQuietBase {p['start']} -> {p['end']} (z toward the lock value {zt:+.2f}), pairs {res['pairs']}")
if zt <= -2:
    say("sanity3 moved AWAY from the lock value beyond 2 sigma: the STC run is not started")
    sys.exit(3)
say(("sanity check passed" if zt >= 1 else "sanity check inconclusive (recorded)") + f": STC run until {until}")
chain_stop()
stc = runs / "stc1"
tune("stc_main.json", stc, ["--until", until])
make_report(stc, reports / "stc1_final", "R9 STC 8+0.08 SPSA run (16 parameters from the lock values)")
say("done")
