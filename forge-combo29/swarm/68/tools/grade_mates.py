#!/usr/bin/env python3
"""Grade engine mate labels with the independent verifier.

Reads the JSONL that collect_mates.py writes. For each FINAL mate score on each
MultiPV line it asks the verifier for the exact DTM and compares.

Two comparisons are reported separately, because they answer different
questions:

  1. LABEL vs TRUTH -- does the engine's `mate N` match the exact distance? This
     is the wrong-mate rate the audit is about.
  2. PV LENGTH vs N -- does the PV have the length the score implies? This is the
     existing filter, included so its blind spot can be measured on the same
     lines rather than asserted: a line can pass (2) and fail (1).

Every count prints numerator and denominator.
"""
import json
import subprocess
import sys
from collections import Counter

HERE = __file__.rsplit("/", 1)[0]
VERIFY = HERE + "/mateverify"


def expected_pv_len(n):
    """The existing filter's rule: 2|N|-1 for a win, 2|N| for a loss."""
    return 2 * abs(n) - 1 if n > 0 else 2 * abs(n)


def verify(fen, claimed, timeout=600):
    try:
        r = subprocess.run([VERIFY, "--one", fen, str(claimed)],
                           capture_output=True, text=True, timeout=timeout)
        return json.loads(r.stdout.strip())
    except subprocess.TimeoutExpired:
        return {"status": "VERIFIER_TIMEOUT"}
    except json.JSONDecodeError:
        return {"status": "VERIFIER_PARSE_ERROR"}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "mates_mpv1_d12.jsonl"
    out = sys.argv[2] if len(sys.argv) > 2 else src.replace(".jsonl", "_graded.jsonl")
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9

    rows = []
    with open(src) as f:
        for line in f:
            rows.append(json.loads(line))

    # Collect one label per (position, multipv) using the FINAL mate score.
    labels = []
    for r in rows:
        if r.get("refused") or r.get("timed_out"):
            continue
        by_mpv = {}
        for rec in r["info"]:
            if rec.get("score_type") != "mate":
                continue
            by_mpv[rec["multipv"]] = rec   # later depth overwrites earlier
        for mpv, rec in sorted(by_mpv.items()):
            labels.append({
                "fen": r["fen"], "multipv": mpv, "depth": rec.get("depth"),
                "n": rec["score_value"], "pv": rec.get("pv", []),
                "nodes": rec.get("nodes"),
            })

    print(f"source {src}: {len(rows)} positions")
    print(f"mate labels to grade: {len(labels)} "
          f"(final mate score per position per MultiPV line)")
    labels = labels[:limit]

    out_rows = []
    status = Counter()
    direction = Counter()
    pv_pass = 0
    pv_fail = 0
    both_fail = 0
    pv_pass_but_wrong = 0
    pv_fail_but_correct = 0
    by_mpv = Counter()
    by_mpv_wrong = Counter()

    for i, lab in enumerate(labels):
        v = verify(lab["fen"], lab["n"])
        st = v.get("status", "?")
        status[st] += 1
        by_mpv[lab["multipv"]] += 1
        # PV-length filter verdict
        need = expected_pv_len(lab["n"])
        pv_ok = len(lab["pv"]) == need
        pv_pass += pv_ok
        pv_fail += (not pv_ok)

        if st == "WRONG":
            direction[v.get("direction", "?")] += 1
            by_mpv_wrong[lab["multipv"]] += 1
            if pv_ok:
                pv_pass_but_wrong += 1
        if st == "WRONG" and pv_ok:
            pass
        if (not pv_ok) and st == "CORRECT":
            pv_fail_but_correct += 1
        if (not pv_ok) and st == "WRONG":
            both_fail += 1

        out_rows.append({**lab, "verdict": v, "pv_len": len(lab["pv"]),
                         "pv_len_required": need, "pv_length_filter": "pass" if pv_ok else "fail"})
        print(f"\r  graded {i + 1}/{len(labels)}", end="", flush=True)
    print()

    with open(out, "w") as f:
        for row in out_rows:
            f.write(json.dumps(row) + "\n")

    graded = sum(status.values())
    wrong = status.get("WRONG", 0)
    correct = status.get("CORRECT", 0)
    incon = status.get("INCONCLUSIVE", 0) + status.get("VERIFIER_TIMEOUT", 0)

    print(f"\nwrote {out}: {graded} graded labels")
    print(f"  CORRECT       {correct}/{graded}")
    print(f"  WRONG         {wrong}/{graded}")
    print(f"  INCONCLUSIVE  {incon}/{graded}")
    print(f"  wrong by direction: " + ", ".join(f"{k} {v}" for k, v in sorted(direction.items())))
    print(f"  per MultiPV: " + ", ".join(f"MPV{k} {by_mpv_wrong[k]}/{by_mpv[k]} wrong"
                                          for k in sorted(by_mpv)))
    print("\nPV-length filter on the same lines:")
    print(f"  pass {pv_pass}/{graded}, fail {pv_fail}/{graded}")
    print(f"  BLIND SPOT -- passed the length filter but verifier says WRONG: "
          f"{pv_pass_but_wrong}/{pv_pass}")
    print(f"  length filter rejects but label is actually CORRECT: "
          f"{pv_fail_but_correct}/{pv_fail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
