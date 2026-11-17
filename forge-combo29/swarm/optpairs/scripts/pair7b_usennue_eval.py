"""Pair 7b: the UseNNUE x NNUEArch disagreement between `eval` and the search.

Pair 7 found one cell where the two output paths of the engine answer the
"is NNUE on" question differently, and that is a finding in its own right because
a tuning harness reads `eval` to decide whether the evaluator changed.

Measured here as a 2x2 with the search and `eval` side by side:

  cell                          search uses      `eval` reports
  UseNNUE true,  v3 net         v3 net           nnue_v3
  UseNNUE false, v3 net         hand-crafted     nnue_v3     <-- disagreement
  UseNNUE true,  no v3 net      v2 net + HCE     hce/nnue/total
  UseNNUE false, no v3 net      hand-crafted     hce/nnue/total

Proof that the search in the disagreeing cell really is the hand-crafted one, and
not a coincidence: its four-field signature must equal the UseNNUE=false arm with
no net at all, on every position. That is the two-proof rule -- the path ran AND
the other path did not.

Source, base 6b98f217: `uci.cpp:575-582` gates only on `nnue::v3::active()`, which
is `requested && loaded()` (nnue_v3.hpp:156-158) and never consults `enabled`;
`search.cpp:1076` gates on `!nnue::enabled` FIRST, before the v3 branch at :1078.
"""
import json
import os
import subprocess
import sys

import grid
import uci

HERE = os.path.dirname(os.path.abspath(__file__))
NETS = os.path.join(os.path.dirname(HERE), "evidence", "nets")
V3 = "/tmp/build-v3/forge"
V3B = os.path.join(NETS, "v3b.bin")
POS = grid.POSITIONS[:6]
GO = "go depth 10"


def eval_line(options, fen):
    inp = "\n".join(["uci"] + [f"setoption name {n} value {v}" for n, v in options]
                    + ["isready", f"position fen {fen}", "eval", "quit"]) + "\n"
    p = subprocess.run([V3], input=inp, capture_output=True, text=True, timeout=120)
    return next((l for l in p.stdout.splitlines() if l.startswith("info string eval")), None)


ARMS = [
    ("usennue_on_v3", [("UseNNUE", "true"), ("NNUEArchFile", V3B), ("NNUEArch", "true")]),
    ("usennue_off_v3", [("UseNNUE", "false"), ("NNUEArchFile", V3B), ("NNUEArch", "true")]),
    ("usennue_on_nonet", [("UseNNUE", "true")]),
    ("usennue_off_nonet", [("UseNNUE", "false")]),
]


def main():
    out = {"go": GO, "arms": {}, "disagreement": {}}
    for label, options in ARMS:
        rows = {}
        for name, fen in POS:
            r = uci.run(options=[("OwnBook", "false")] + options, position=fen, go=GO, bin_path=V3)
            rows[name] = {"signature": list(uci.sig(r)),
                          "eval": eval_line([("OwnBook", "false")] + options, fen),
                          "accepted": r["accepted"], "exit": r["exit_code"]}
        out["arms"][label] = rows

    on_v3, off_v3 = out["arms"]["usennue_on_v3"], out["arms"]["usennue_off_v3"]
    off_none = out["arms"]["usennue_off_nonet"]
    agree_on = sum(1 for p in off_v3 if off_v3[p]["signature"] == on_v3[p]["signature"])
    agree_hce = sum(1 for p in off_v3 if off_v3[p]["signature"] == off_none[p]["signature"])
    eval_says_v3_when_off = sum(1 for p in off_v3 if "nnue_v3" in (off_v3[p]["eval"] or ""))
    out["disagreement"] = {
        "UseNNUE=false + v3 net: search equals UseNNUE=true + v3 net": agree_on,
        "UseNNUE=false + v3 net: search equals UseNNUE=false + no net": agree_hce,
        "UseNNUE=false + v3 net: eval still reports nnue_v3": eval_says_v3_when_off,
        "positions": len(POS),
        "search_used_handcrafted": agree_hce == len(POS) and agree_on == 0,
        "eval_disagrees_with_search": eval_says_v3_when_off == len(POS),
    }
    with open(os.path.join(grid.EVID, "pair7b-usennue-eval.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print(f"UseNNUE x NNUEArch: search vs `eval`, {GO}, {len(POS)} positions")
    for label, _ in ARMS:
        print(f"  {label:18s} eval says: " +
              "; ".join(sorted({(out['arms'][label][p]['eval'] or '-').split('string ')[-1].split(' ')[0]
                                for p in out['arms'][label]})))
    d = out["disagreement"]
    print(f"  UseNNUE=false + v3 net == UseNNUE=true + v3 net on {d['UseNNUE=false + v3 net: search equals UseNNUE=true + v3 net']}/{d['positions']}")
    print(f"  UseNNUE=false + v3 net == UseNNUE=false + no net   on {d['UseNNUE=false + v3 net: search equals UseNNUE=false + no net']}/{d['positions']}")
    print(f"  `eval` still reports nnue_v3                 on {d['UseNNUE=false + v3 net: eval still reports nnue_v3']}/{d['positions']}")


if __name__ == "__main__":
    sys.exit(main())
