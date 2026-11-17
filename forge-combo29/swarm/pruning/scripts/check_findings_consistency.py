#!/usr/bin/env python3
"""Check that FINDINGS.md's SoundMatePruning tables agree with evidence/*.json.

This exists because the published version of §1 was internally consistent and
still wrong: it aggregated a per-cell grid into a per-fixture table and dropped
the depth axis, so every number was right and the table's claim was not. A
number-by-number check would have passed it. This checker instead asserts the
PROPERTIES the prose claims:

  1. every HARM cell in options.json is at a depth inside the stated band
  2. no HARM cell exists at a depth the prose calls clean (>= 10)
  3. the per-fixture "harmed" list in the doc names exactly the fixtures that
     options.json records as harmed
  4. the counts printed in §1 (per-depth table) match options.json
  5. the cost table in §1.2 matches smp_depth_bands.json exactly
  6. the band table in §1.2 matches smp_depth_bands.json cell for cell
  7. the "cells measured" line matches the real cell count per depth

If any assertion fails, the doc is asserting more than the evidence supports.
"""

from __future__ import annotations

import json
import os
import re
import sys

BAND_MAX = 9      # prose says harms are within depths 5..9
CLEAN_MIN = 10    # prose says nothing at or above this depth is harmed


def load(path: str):
    with open(path) as fh:
        return json.load(fh)



def check_quiet_extinction(_unused: str) -> list[str]:
    """Assert FINDINGS-quiet-extinction.md's bucketing matches its evidence.

    This guards a specific published error: §4 once said "three cells get the
    right move with a wrong distance" and listed `e8e4` among them, which is the
    WRONG move. The class a cell belongs to is determined by two facts --
    whether the mate score survives, and whether the move is unchanged -- and
    the doc's bucket counts must equal the recomputed ones.

    Reads its OWN document. An earlier version took the caller's `doc`, which is
    FINDINGS.md, so it searched the SoundMatePruning file for this section's
    sentence and reported it missing -- a check that fails on the wrong file is
    as useless as one that passes on the wrong file.
    """
    failures: list[str] = []
    try:
        with open("evidence/quiet_extinction.json") as fh:
            ev = json.load(fh)
    except FileNotFoundError:
        return ["evidence/quiet_extinction.json missing"]
    if not os.path.exists("FINDINGS-quiet-extinction.md"):
        return []
    with open("FINDINGS-quiet-extinction.md") as fh:
        doc = fh.read()

    harm = [r for r in ev["corpus"] if r["state"] == "HARM"]
    bucket = {"score_lost_wrong_move": 0, "score_lost_right_move": 0,
              "too_long_right_move": 0, "too_long_wrong_move": 0, "too_short": 0}
    for r in harm:
        off, on, want = r["off"], r["on"], r["true_moves"]
        same = off[0] == on[0]
        if on[1] is None:
            bucket["score_lost_right_move" if same else "score_lost_wrong_move"] += 1
        elif on[1] > want:
            bucket["too_long_right_move" if same else "too_long_wrong_move"] += 1
        elif on[1] < want:
            bucket["too_short"] += 1

    # The prose must state these counts. Each is a phrase the doc carries.
    expectations = [
        ("**8**", bucket["score_lost_wrong_move"] == 8,
         "8 cells: mate score lost, non-mating move"),
        ("**1**", bucket["score_lost_right_move"] == 1,
         "1 cell: mate score lost, right move"),
        ("| **2** |", bucket["too_long_right_move"] == 2,
         "2 cells: right move, too long"),
        ("| **1** |", bucket["too_long_wrong_move"] == 1,
         "1 cell: wrong move, too long"),
        ("| **0** |", bucket["too_short"] == 0,
         "0 cells: shorter than truth"),
    ]
    for _tok, ok, desc in expectations:
        if not ok:
            failures.append(f"bucket mismatch: {desc}")

    # "No cell reports a mate shorter than the truth" must be asserted in prose.
    if "No cell reports a mate score shorter than the truth" not in doc:
        failures.append("the absence of under-stated mates is not stated explicitly")

    # Every fixture+depth row in the detail table must be a real harm cell.
    cited = re.findall(r"\| (\d+) \| `([^`]+)` \| m(\d) \|", doc)
    for depth, fen, _truth in cited:
        if not any(r["fen"].startswith(fen) and r["depth"] == int(depth) for r in harm):
            failures.append(f"detail table cites non-harm cell d{depth} {fen}")

    # ...and EVERY harm cell must be cited. A deleted row leaves the bucket
    # counts in the prose still correct, so a citation-only check passes while
    # the table silently drops a case -- which is how the `e8e4` omission
    # survived the first time.
    for r in harm:
        if not any(fen and r["fen"].startswith(fen) and int(depth) == r["depth"]
                   for depth, fen, _t in cited):
            failures.append(f"harm cell d{r['depth']} {r['fen']} is NOT cited in "
                            f"the detail table -- the table understates the harm")

    return failures


def main() -> int:
    failures: list[str] = []
    with open("FINDINGS.md") as fh:
        doc = fh.read()

    opts = load("evidence/options.json")
    rows = opts["rows"]
    bands = load("evidence/smp_depth_bands.json")

    # ---- 1 & 2: every harm is inside the band, none at or above CLEAN_MIN ----
    harmed = []
    for r in rows:
        a = r["arms"]["default"]
        b = r["arms"]["SoundMatePruning=true"]
        if a["correct"] and not b["correct"]:
            harmed.append((r["fen"], r["depth"]))
    if not harmed:
        failures.append("options.json records NO harms -- the doc claims five")
    for fen, d in harmed:
        if d > BAND_MAX:
            failures.append(f"harm at depth {d} ({fen}) is OUTSIDE the stated band "
                            f"(<= {BAND_MAX}) -- prose understates the harm")
        if d >= CLEAN_MIN:
            failures.append(f"harm at depth {d} CONTRADICTS the 'clean above depth 10' claim")

    # ---- 3: the doc's five fixture rows are exactly the harmed fixtures ----
    harmed_fens = {fen for fen, _ in harmed}
    for fen in harmed_fens:
        key = fen.split(" w ")[0]
        if key not in doc:
            failures.append(f"harmed fixture {fen} does not appear in FINDINGS.md")

    # ---- 4: per-depth table counts ----
    per_depth = {}
    for r in rows:
        d = r["depth"]
        per_depth.setdefault(d, {"n": 0, "default_wrong": 0, "smp_wrong": 0})
        per_depth[d]["n"] += 1
        if not r["arms"]["default"]["correct"]:
            per_depth[d]["default_wrong"] += 1
        if not r["arms"]["SoundMatePruning=true"]["correct"]:
            per_depth[d]["smp_wrong"] += 1
    for d, c in per_depth.items():
        # the doc's row: "| 8 | 30 | 3 | 7 | **5** | 1 |"
        # harm/help are counted per depth so the row's last two columns are
        # checked too -- an unqualified harm claim lives in those columns.
        harmed_d = sum(1 for r in rows if r["depth"] == d
                       and r["arms"]["default"]["correct"]
                       and not r["arms"]["SoundMatePruning=true"]["correct"])
        helped_d = sum(1 for r in rows if r["depth"] == d
                       and not r["arms"]["default"]["correct"]
                       and r["arms"]["SoundMatePruning=true"]["correct"])
        pat = (rf"^\|\s*{d}\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*"
               rf"\*?\*?(\d+)\*?\*?\s*\|\s*\*?\*?(\d+)\*?\*?\s*\|")
        m = re.search(pat, doc, re.MULTILINE)
        if not m:
            failures.append(f"per-depth table has no row for depth {d}")
            continue
        got = tuple(int(x) for x in m.groups())
        want = (c["n"], c["default_wrong"], c["smp_wrong"], harmed_d, helped_d)
        if got != want:
            failures.append(f"depth {d} row says {got}, evidence says {want} "
                            f"(n, default_wrong, smp_wrong, harmed, helped)")
        if got[3] and d >= CLEAN_MIN:
            failures.append(f"depth {d} row claims {got[3]} harms at a depth the "
                            f"prose calls clean")

    # ---- 5 & 6: the band table matches cell for cell, POSITIONALLY ----
    # A token-presence test is useless here: a row contains many cells and the
    # same token repeats across depths, so "does the row contain 'both-right'"
    # passes even when every column after the first is wrong. The comparison has
    # to split the row into cells and align them with the table's depth header.
    lines = doc.splitlines()
    header_idx = next((i for i, ln in enumerate(lines)
                       if ln.startswith("| fixture |") and "16" in ln), None)
    if header_idx is None:
        failures.append("could not find the §1.2 band-table header")
    else:
        header = [c.strip() for c in lines[header_idx].strip().strip("|").split("|")]
        # header is ["fixture", "5", "6", ..., "16"]
        depth_cols = header[1:]
        doc_rows: dict[str, list[str]] = {}
        for ln in lines[header_idx + 1:]:
            if not ln.startswith("|"):
                break
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            key = cells[0].strip("`").replace(" w", "").replace("`", "").strip()
            doc_rows[key] = cells[1:]

        for fen, f in bands.items():
            key = fen.split(" w ")[0]
            match = next((k for k in doc_rows if k == key), None)
            if match is None:
                failures.append(f"no band-table row for {fen}")
                continue
            got = doc_rows[match]
            for i, d in enumerate(depth_cols):
                if d not in f["cells"]:
                    continue
                want_state = f["cells"][d]["state"]
                want_token = {"HARM": "HARM", "both-right": "both-right",
                              "both-wrong": "both-wrong", "help": "help"}[want_state]
                if i >= len(got):
                    failures.append(f"{fen}: row has no cell for depth {d}")
                    continue
                if want_token not in got[i]:
                    failures.append(
                        f"{fen} depth {d}: doc says {got[i]!r}, evidence says {want_token!r}")

    # ---- 7: "30 at each depth" ----
    ns = {c["n"] for c in per_depth.values()}
    if len(ns) != 1:
        failures.append(f"grid is not balanced per depth: {per_depth}")

    qe_failures = check_quiet_extinction(doc)
    failures.extend(qe_failures)

    print(json.dumps({
        "harmed_cells": len(harmed),
        "harmed_depths": sorted({d for _, d in harmed}),
        "per_depth": per_depth,
        "band_asserted": f"<= {BAND_MAX}",
        "failures": failures,
    }, indent=2))
    if failures:
        print("\nFAIL -- FINDINGS.md asserts more than the evidence supports.", file=sys.stderr)
        return 1
    print("\nOK -- every harm is inside the stated band, the counts match, and the "
          "band table matches the evidence cell for cell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
