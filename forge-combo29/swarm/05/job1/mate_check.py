#!/usr/bin/env python3
"""mate_check.py ROWS.jsonl OUTFILE -- for every position whose LAST pv line carries `score mate N`,
run dtm2.py independently and compare with the engine's N.
Writes one line per position: ok/mismatch, engine N, dtm2 verdict.
"""
import json
import re
import subprocess
import sys

rows_file, out_file = sys.argv[1], sys.argv[2]
MAXPLY = sys.argv[3] if len(sys.argv) > 3 else "24"
CAP = sys.argv[4] if len(sys.argv) > 4 else "120"

lines = []
n_ok = n_bad = n_unk = 0
for line in open(rows_file):
    r = json.loads(line)
    lp = r.get("last_pv")
    if not lp or lp.get("score", ("",))[0] != "mate":
        continue
    n = lp["score"][1]
    p = subprocess.run([sys.executable, "dtm2.py", r["fen"], MAXPLY, CAP],
                       capture_output=True, text=True, timeout=float(CAP) * 3 + 60)
    verdict = next((l for l in p.stdout.splitlines() if l.startswith("verdict")), None)
    if verdict is None:
        # A MISSING verdict must never be scored as a measurement. Fixing this after seat 19's
        # measurement-integrity warning: the old code fell through to "MISMATCH", i.e. it would have
        # invented a REFUTES from an empty parse.
        tag = "NO_VERDICT"
        n_bad += 0
        n_unk += 1
        lines.append(f"{tag:10s} {r['set']} pos {r['pos']:3d} engine_mate={n:+3d}  dtm2 printed NO verdict "
                     f"line (stdout was {len(p.stdout)} chars) -- counted as UNKNOWN, never as a mismatch")
        continue
    vpl = ""
    m = re.search(r"(MATES|IS MATED) in (\d+) plies", verdict)
    if m:
        vpl = m.group(2)
    if "unknown" in verdict or m is None:
        tag = "UNKNOWN"          # no parsed number => not a measurement, in EITHER direction
        n_unk += 1
    elif n > 0:
        want = 2 * n - 1
        tag = "OK" if (m and m.group(1) == "MATES" and int(vpl) == want) else "MISMATCH"
    else:
        want = 2 * (-n)
        tag = "OK" if (m and m.group(1) == "IS MATED" and int(vpl) == want) else "MISMATCH"
    if tag == "OK":
        n_ok += 1
    elif tag == "MISMATCH":
        n_bad += 1
    # also record the pv's own claim (from check_pv data)
    pv_ok = lp.get("mate_ok")
    pv_plies = lp.get("plies")
    lines.append(f"{tag:9s} {r['set']} pos {r['pos']:3d} engine_mate={n:+3d} want_plies={want:2d} "
                 f"dtm2=[{verdict}]  pv_plies={pv_plies} pv_ends_mate={lp.get('ends_checkmate')} "
                 f"pv_ok={pv_ok}  fen={r['fen']}")

with open(out_file, "w") as f:
    f.write("\n".join(lines) + "\n")
    f.write(f"\nSUMMARY ok={n_ok} mismatch={n_bad} unknown={n_unk}\n")
print("\n".join(lines))
print(f"SUMMARY ok={n_ok} mismatch={n_bad} unknown={n_unk}")
