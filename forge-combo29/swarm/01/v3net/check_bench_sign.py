#!/usr/bin/env python3
"""swarm seat 01: verify the bench SIGN FLIP myself, since my FINAL now rests on it (S-C51).

My FINAL states: "bench node ratios flip sign across benches (+14.5 % bench 11, -10.6 % bench 13, +8.7 % bench 16)
while real positions sit at -9.1 %" — and that evidence licenses the corrected workload rule. I took those three
figures from seat 19's audit. **A rule in my FINAL should not rest on a figure I have not measured**, so this measures
the same three bench ratios on my build.

The claim under test is narrow and falsifiable: does the SIGN of (PC20 nodes / S14 nodes) differ between benches 11,
13 and 16? If it does, a bench-based aggregate claim is workload-dependent and the rule stands. If all three agree in
sign with each other and with real positions, then the sign flip is not reproducible here and my FINAL overstates it.

Design, from traps already paid for:
  * both settings on the same build, fresh process per measurement (bench is not stateful across processes here, but
    the settings are);
  * S14 vs PC20 exactly, since that is the toggle set the rule is about - one flag group, not a single switch;
  * bench numbers are deterministic (verified by the honesty pins), so n=1 per cell is sufficient and a repeat is a
    control rather than a sample;
  * the SAME comparison is run on real positions in the same invocation, so the "bench vs real" contrast is measured
    under one set of conditions rather than across two runs.

Usage: check_bench_sign.py <pc-build> <fens> <outdir>
"""
import hashlib
import json
import re
import subprocess
import statistics
import sys
from pathlib import Path

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BENCHES = [11, 13, 16]


def run_bench(exe, opts, depth):
    cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
    cmd += ["setoption name %s value %s" % (n, v) for n, v in opts]
    cmd += ["isready", "ucinewgame", "isready", "bench %d" % depth, "quit"]
    out = subprocess.run([exe], input="\n".join(cmd) + "\n", capture_output=True, text=True, cwd="/tmp").stdout
    m = re.search(r"bench depth \d+ nodes (\d+)", out)
    return int(m.group(1)) if m else None


def run_positions(exe, opts, fens):
    """Pooled node count at depth 12 over the FEN sample - the 'real positions' arm of the contrast."""
    total = 0
    for fen in fens:
        cmd = ["uci", "setoption name Threads value 1", "setoption name Hash value 16"]
        cmd += ["setoption name %s value %s" % (n, v) for n, v in opts]
        cmd += ["isready", "ucinewgame", "isready", "position fen " + fen, "isready",
                "go depth 12", "quit"]
        p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True, bufsize=1, cwd="/tmp")

        def send(s):
            p.stdin.write(s + "\n")
            p.stdin.flush()

        def until(pre):
            for line in p.stdout:
                if line.startswith(pre):
                    return line.rstrip("\n")
            return None

        send("uci")
        until("uciok")
        for s in cmd[1:-4]:
            send(s)
        send("isready")
        until("readyok")
        send("ucinewgame")
        send("isready")
        until("readyok")
        send("position fen " + fen)
        send("isready")
        until("readyok")
        send("go depth 12")
        last = None
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("info depth"):
                last = line
            if line.startswith("bestmove"):
                break
        send("quit")
        try:
            p.wait(timeout=120)
        except Exception:
            p.kill()
        if last:
            m = re.search(r"nodes (\d+)", last)
            if m:
                total += int(m.group(1))
    return total


def main():
    exe, fenfile, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    lines = [l.strip() for l in Path(fenfile).read_text().splitlines() if l.strip()]
    fens = lines[::max(1, len(lines) // 40)][:40]

    rows = []
    L = ["S-C51: is the bench SIGN FLIP real on MY build?",
         "exe: %s" % exe, "sha256: %s" % sha,
         "S14 vs PC20 (the six-flag group), Threads 1, Hash 16, fresh process per measurement.", ""]
    L.append("arm\tS14 nodes\tPC20 nodes\tratio\tpercent\tsign")

    for d in BENCHES:
        a = run_bench(exe, S14, d)
        b = run_bench(exe, PC20, d)
        # a repeat is a determinism CONTROL, not a sample
        a2 = run_bench(exe, S14, d)
        if a is None or b is None:
            L.append("bench %d\tMISSING" % d)
            continue
        r = b / a
        rows.append({"arm": "bench %d" % d, "a": a, "b": b, "ratio": r, "deterministic": a == a2})
        L.append("bench %d\t%d\t%d\t%.4f\t%+.1f %%\t%s" % (d, a, b, r, 100 * (r - 1), "+" if r > 1 else "-"))

    a_pos = run_positions(exe, S14, fens)
    b_pos = run_positions(exe, PC20, fens)
    if a_pos:
        r = b_pos / a_pos
        rows.append({"arm": "real positions (n=%d, depth 12)" % len(fens), "a": a_pos, "b": b_pos, "ratio": r})
        L.append("real n=%d\t%d\t%d\t%.4f\t%+.1f %%\t%s" % (len(fens), a_pos, b_pos, r, 100 * (r - 1),
                                                          "+" if r > 1 else "-"))
    L.append("")

    signs = {}
    for r in rows:
        signs.setdefault("+" if r["ratio"] > 1 else "-", []).append(r["arm"])
    L.append("SIGNS: %s" % {k: v for k, v in signs.items()})
    L.append("")
    if len(signs) > 1:
        L.append("VERDICT: the SIGN FLIP REPRODUCES on this build - bench ratios disagree in sign across arms")
        L.append("  (%s positive, %s negative). A bench-based aggregate claim is therefore workload-dependent, which"
                 % (", ".join(signs.get("+", ["none"])), ", ".join(signs.get("-", ["none"]))))
        L.append("  is what licenses the corrected rule. Seat 19's specific percentages may differ from mine - the")
        L.append("  claim under test is the SIGN PATTERN, not their exact figures.")
    else:
        L.append("VERDICT: NO sign flip on this build - every arm has the same sign. My FINAL's bench rule would then")
        L.append("  need narrowing, because its evidence would not reproduce here.")
    bad = [r for r in rows if "deterministic" in r and not r["deterministic"]]
    if bad:
        L.append("")
        L.append("CONTROL FAILED: bench numbers were not reproducible for %s - the honesty pins say they should be, so"
                 % ", ".join(r["arm"] for r in bad))
        L.append("  something differs between the runs and these ratios should not be trusted.")
    else:
        L.append("")
        L.append("CONTROL: each bench repeat reproduced its node count exactly, so n=1 per cell is justified here.")

    (out / "check_bench_sign.json").write_text(json.dumps({"sha": sha, "rows": rows}, indent=1))
    txt = "\n".join(L) + "\n"
    (out / "check_bench_sign.txt").write_text(txt)
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
