#!/usr/bin/env python3
"""Re-run the engine on every harvested FEN and record `seldepth` beside the label.

WHY THIS IS A SEPARATE PASS. The harvest recorded depth, score, nodes, PV and
the build, but NOT seldepth -- and seldepth is the field that tells a reader
whether the score was backed by a selective search deeper than the nominal
depth. Reporting a label "wrong" without its seldepth invites exactly the
mistake this run already made once: calling an unverifiable claim false.

The pass also re-reads the score, so it doubles as a determinism check: if a
label does not reproduce bit-for-bit at the same build/settings/depth, that row
is flagged rather than silently kept.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paths
import uci_driver as uci

ENGINE = paths.engine_binary()


def parse_seldepth(info_line):
    tok = info_line.split()
    for i, t in enumerate(tok):
        if t == "seldepth" and i + 1 < len(tok):
            return int(tok[i + 1])
    return None


def main():
    src = paths.work_file("harvest.jsonl")
    rows = [json.loads(l) for l in open(src)]
    out = []
    mismatch = 0
    for i, row in enumerate(rows):
        e = uci.Uci(ENGINE, row["options"])
        e.position(row["fen"])
        best, info, elapsed, timed_out = e.search(f"go depth {row['depth']}", timeout=180)
        e.quit()

        seldepth = None
        score = None
        nodes = None
        # Take the last multipv-1 line, the same line the harvest used.
        for line in info:
            p = uci.parse_score(line)
            if p and p["multipv"] == 1 and p["kind"] is not None:
                score = p
                seldepth = parse_seldepth(line)
                nodes = p["nodes"]
        if score is None:
            row["seldepth"] = None
            row["reproduced"] = False
            row["repro_note"] = "no score line on re-run"
            mismatch += 1
        else:
            row["seldepth"] = seldepth
            row["reproduced"] = (score["kind"] == row["score_kind"]
                                 and score["value"] == row["score_value"])
            if not row["reproduced"]:
                mismatch += 1
                row["repro_note"] = (f"re-run gave {score['kind']} {score['value']}, "
                                     f"harvest had {row['score_kind']} {row['score_value']}")
            row["rerun_nodes"] = nodes
        # Depth-minus-seldepth is the honest selectivity margin of the label.
        if row.get("seldepth") is not None:
            row["seldepth_minus_depth"] = row["seldepth"] - row["depth"]
        out.append(row)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(rows)}  mismatches so far {mismatch}", flush=True)

    out_path = paths.work_file("harvest_seldepth.jsonl")
    with open(out_path, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(f"\nwrote {len(out)} rows, {mismatch} did not reproduce")
    sd = [r["seldepth"] for r in out if r.get("seldepth") is not None]
    if sd:
        print(f"seldepth: min {min(sd)} median {sorted(sd)[len(sd)//2]} max {max(sd)}")


if __name__ == "__main__":
    main()
