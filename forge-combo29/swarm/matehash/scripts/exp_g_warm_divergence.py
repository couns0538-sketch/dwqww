"""Experiment G: is a warm/cold mate-distance difference an ENCODING error?

THE DISTINCTION THIS MAKES, AND WHY IT IS THE WHOLE POINT

    A warm search reports a different mate distance than a cold one. Two very
    different things produce that, and only one is this seat's subject:

    ENCODING   the entry holds the right mate but the PLY ADJUSTMENT is wrong, so
               the distance read back is off by an amount determined by the ply
               difference. Diagnostic: the engine's own PV is a real forced mate
               of the TRUE length while the score says another length. The delta
               is a function of (ply_stored - ply_read) and is therefore
               REPRODUCIBLE and EVEN-PLY for a whole-move error.

    PRECISION  the warm search simply SEARCHED DIFFERENTLY -- table cutoffs
               short-circuit lines, so it returns a longer (or shorter) mate that
               is still a real forced mate at ITS OWN length. That is ordinary
               search instability, already documented in the findings doc
               (§7 item 3: warm state moves scores), and it is NOT an encoding
               defect. Diagnostic: the PV mates in exactly the claimed plies.

    A delta of an ODD number of moves cannot be an even-ply adjustment error at
    all, so parity alone rules encoding out for those rows. This experiment
    records the parity explicitly rather than relying on the argument.

For each divergent row: replay the warm PV, replay the cold PV, and report which
of the two hypotheses the evidence supports. A row whose PV does not mate is
UNVERIFIABLE (truncated PVs are unverifiable, not false -- findings doc).

Output: evidence/G_warm_divergence.jsonl
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dtm import _mate_within, _mated_within  # noqa: E402
from exp_f_classify import pv_outcome, shortest_dtm_plies  # noqa: E402


def pv_from_raw(rec):
    """The PV lives in the raw info line; exp_c records `last_raw` but not a
    parsed `pv` field, so the first version of this classifier read None for
    every row and returned UNVERIFIABLE 14 of 14 -- a checker that never fired.
    Parse it here instead of trusting a field that was never written."""
    raw = rec.get("last_raw")
    if not raw:
        return []
    marker = " pv "
    if marker not in raw:
        return []
    return raw.split(marker, 1)[1].split()


def classify_row(row):
    fen = row["child_fen"]
    warm, cold = dict(row["warm"]), dict(row["cold"])
    warm["pv"] = pv_from_raw(warm)
    cold["pv"] = pv_from_raw(cold)
    board = chess.Board(fen)
    dtm = shortest_dtm_plies(board)
    out = {
        "fen": fen,
        "expected": row["expected"],
        "warm_mate": warm["mate"], "warm_depth": warm["depth"], "warm_seldepth": warm["seldepth"],
        "cold_mate": cold["mate"], "cold_depth": cold["depth"], "cold_seldepth": cold["seldepth"],
        "dtm_plies": dtm,
        "warm_pv": warm.get("pv"),
        "cold_pv": cold.get("pv"),
    }
    w_pv = pv_outcome(fen, warm.get("pv") or [])
    c_pv = pv_outcome(fen, cold.get("pv") or [])
    out["warm_pv_outcome"] = w_pv
    out["cold_pv_outcome"] = c_pv

    def claim_plies(m):
        if m is None:
            return None
        return (2 * abs(m) - 1) if m > 0 else (2 * abs(m))

    w_claim, c_claim = claim_plies(warm["mate"]), claim_plies(cold["mate"])
    out["warm_claim_plies"] = w_claim

    # Encoding would show as: PV mates, but at a DIFFERENT ply count than claimed.
    if w_pv.get("mates") and w_claim is not None:
        out["warm_pv_matches_claim"] = w_pv["plies"] == w_claim
    else:
        out["warm_pv_matches_claim"] = None
    if c_pv.get("mates") and c_claim is not None:
        out["cold_pv_matches_claim"] = c_pv["plies"] == c_claim
    else:
        out["cold_pv_matches_claim"] = None

    delta = None
    if warm["mate"] is not None and cold["mate"] is not None:
        delta = warm["mate"] - cold["mate"]
    out["delta_moves"] = delta
    out["delta_plies"] = None if delta is None else 2 * delta
    out["delta_is_odd_moves"] = None if delta is None else (abs(delta) % 2 == 1)

    if warm["mate"] is not None and cold["mate"] is not None:
        if out["warm_pv_matches_claim"] is True:
            out["verdict"] = "PRECISION-warm-honest-at-its-own-length"
        elif out["warm_pv_matches_claim"] is False:
            out["verdict"] = "ENCODING-suspect"
        else:
            out["verdict"] = "UNVERIFIABLE"
    else:
        out["verdict"] = "UNVERIFIABLE"
    return out


def main():
    here = __file__.rsplit("/", 2)[0]
    rows = [json.loads(l) for l in open(here + "/evidence/C_reprobe.jsonl") if '"summary"' not in l]
    # The population that matters: cold was RIGHT, warm was not. Anything else
    # confounds the comparison with the cold arm being wrong.
    div = [r for r in rows if r["cold_ok"] and not r["warm_ok"]]
    classified = [classify_row(r) for r in div]

    # POSITIVE CONTROL: the classifier must be able to say ENCODING-suspect.
    # Plant a claim that the PV cannot support (claim one move shorter than the
    # PV actually mates) on a row that DID verify, and require the classifier to
    # flip it. Without this, "0 encoding suspects" would be indistinguishable
    # from a classifier that only ever returns PRECISION.
    control_rows = []
    for r in div:
        warm = dict(r["warm"])
        pv = pv_from_raw(warm)
        if not pv or warm["mate"] is None:
            continue
        # Take a row whose warm PV is a REAL mate at its claimed length, then
        # plant the claim that it is one move longer. A classifier that can
        # detect an encoding error must now say so: the PV mates at 2k-1 plies
        # while the score claims 2(k+1)-1.
        out_real = pv_outcome(r["child_fen"], pv)
        if not out_real.get("mates"):
            continue
        shifted = dict(r)
        shifted["warm"] = dict(warm)
        shifted["warm"]["mate"] = warm["mate"] + 1
        shifted["warm"]["last_raw"] = "info depth 12 score mate %d pv %s" % (
            warm["mate"] + 1, " ".join(pv))
        c = classify_row(shifted)
        control_rows.append({
            "fen": r["child_fen"],
            "real_claim": warm["mate"],
            "planted_claim": warm["mate"] + 1,
            "real_pv_mates_at_plies": out_real["plies"],
            "verdict": c["verdict"],
            "fired": c["verdict"] == "ENCODING-suspect",
        })
        break
    control_fires = any(c["fired"] for c in control_rows)

    counts = {}
    for c in classified:
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    odd = sum(1 for c in classified if c["delta_is_odd_moves"])
    summary = {
        "n_cold_correct": sum(1 for r in rows if r["cold_ok"]),
        "n_cold_correct_warm_wrong": len(div),
        "warm_wrong_rate_given_cold_correct": round(len(div) / max(1, sum(1 for r in rows if r["cold_ok"])), 4),
        "verdicts": counts,
        "encoding_suspect": sum(1 for c in classified if c["verdict"] == "ENCODING-suspect"),
        # An odd move delta cannot come from an even-ply adjustment error.
        "delta_odd_moves": odd,
        "delta_even_moves": len(classified) - odd,
        "classifier_positive_control_fires": control_fires,
        "classifier_positive_control": control_rows,
        "dtm_equals_expected": sum(1 for c in classified
                                  if c["dtm_plies"] is not None and c["expected"] is not None
                                  and (2 * abs(c["expected"]) - (1 if c["expected"] > 0 else 0)) == c["dtm_plies"]),
    }
    print(json.dumps({"summary": summary}, indent=2))
    for c in classified:
        print(json.dumps({k: c[k] for k in ("fen", "expected", "warm_mate", "cold_mate", "delta_moves",
                                           "delta_is_odd_moves", "warm_pv_matches_claim", "verdict")}))
    with open(here + "/evidence/G_warm_divergence.jsonl", "w") as fh:
        for c in classified:
            fh.write(json.dumps(c) + "\n")
        fh.write(json.dumps({"summary": summary}) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
