#!/usr/bin/env python3
"""Check every figure quoted in FINDINGS.md against a committed evidence file.

The brief's rule 6: a figure that moves toward the hypothesis every time it is re-measured
is evidence about the measurement. The defence is to make each quoted number a lookup into
evidence/, so a re-run that disagrees breaks the document loudly instead of quietly
updating a sentence.

Prints FAIL per claim and exits 1 on any failure.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
EV = HERE.parent / "evidence"
DOC = (HERE.parent / "FINDINGS.md").read_text()

fails: list[str] = []


def expect(label: str, actual, wanted) -> None:
    if actual != wanted:
        fails.append(f"{label}: evidence says {actual!r}, document says {wanted!r}")


# --- 1. the four pins -----------------------------------------------------
PINS = json.load(open(EV / "pins_base.json"))
for k, v in (("bench11", 312866), ("bench13", 862329), ("bench16", 3024920), ("perft5", 4865609)):
    expect(f"pin {k}", PINS[k]["nodes"], v)

# --- 2. sensitivity: the five that must move ------------------------------
SENS = {r["mutant"]: r for r in json.load(open(EV / "sensitivity.json"))["results"]}
for name, expected in [
    ("M1_eval_pawn_psqt", {"bench11": 306660, "bench13": 1003472, "bench16": 3386079, "perft5": 4865609}),
    ("M2_lmr_quiet_base", {"bench11": 263851, "bench13": 881235, "bench16": 2758866, "perft5": 4865609}),
    ("M3_rfp_margin", {"bench11": 226823, "bench13": 601295, "bench16": 2275803, "perft5": 4865609}),
    ("M4_null_move_off", {"bench11": 330705, "bench13": 815534, "bench16": 3183377, "perft5": 4865609}),
    ("M5_see_pawn_value", {"bench11": 276397, "bench13": 901998, "bench16": 2947795, "perft5": 4865609}),
]:
    expect(f"{name} moved", SENS[name]["any_pin_moved"], True)
    for k, v in expected.items():
        expect(f"{name} {k}", SENS[name]["pins"][k], v)

# --- 3. sensitivity: the five that must not -------------------------------
for name in ("N1_add_comment", "N2_reorder_struct_members", "N3_rename_local",
             "N4_dead_function", "N5_whitespace"):
    expect(f"{name} did not move", SENS[name]["any_pin_moved"], False)

# --- 4. blind spots -------------------------------------------------------
BLIND = {r["mutant"]: r for r in json.load(open(EV / "blindspots.json"))["results"]}
for m in ("B1_book_off", "B4_book_variety0", "B5_threads_default2",
          "B6_move_overhead", "B8_fifty_move_leaf", "B9_drawn_root_move"):
    expect(f"{m} pins match", BLIND[m]["pins_all_match"], True)
    expect(f"{m} verdict", BLIND[m]["verdict"], "gate-passes-a-real-change")
for m in ("B2_draw_jitter", "B3_rule50_damp", "B7_qs_futility"):
    expect(f"{m} moved a pin", BLIND[m]["pins_all_match"], False)


# --- 5. coverage ----------------------------------------------------------
def pct(fname: str) -> tuple[float, float]:
    d = json.load(open(EV / fname))["files"]
    tot = sum(f["lines"] for f in d.values())
    hit = sum(f["lines_hit"] for f in d.values())
    fns = sum(f["functions"] for f in d.values())
    fh = sum(f["functions_called"] for f in d.values())
    return round(100 * hit / tot, 1), round(100 * fh / fns, 1)


expect("bench13 coverage", pct("coverage_bench13.json"), (63.0, 59.6))
expect("pins_only coverage", pct("coverage_pins_only.json"), (64.1, 61.1))
expect("combined coverage", pct("coverage_combined.json"), (70.1, 70.7))

BLF = json.load(open(EV / "blind_functions.json"))
expect("blind function total", BLF["count"], 22)
for f, n in (("board", 3), ("book", 4), ("search", 7), ("uci", 8)):
    expect(f"blind {f}", len(BLF["by_file"][f]), n)

# --- 6. Hash trap ---------------------------------------------------------
HASH = json.load(open(EV / "hash_trap.json"))
expect("bench13 invariant over Hash", HASH["bench13_invariant"], True)
expect("Hash does move a real search", HASH["go_start_d14_distinct_values"] > 1, True)
rows = {r["hash_mb"]: r for r in HASH["rows"]}
expect("Hash 1 -> 109,247", rows[1]["go_start_depth14"]["nodes"], 109247)
expect("Hash 16 -> 101,640", rows[16]["go_start_depth14"]["nodes"], 101640)
for h in (1, 16, 64, 256, 1024):
    expect(f"bench13 at Hash {h}", rows[h]["bench13_after_setoption"], 862329)

# --- 7. independence ------------------------------------------------------
ORDER = (EV / "order_independence.txt").read_text()
totals = [int(m) for m in re.findall(r"^TOTAL\t(\d+)$", ORDER, re.M)]
expect("forward, reverse, fresh all 862,329; noclear differs",
       totals, [862329, 862329, 956783, 862329])

# --- 8. go repeatability --------------------------------------------------
GOR = json.load(open(EV / "go_repeatability.json"))["rows"]
expect("fresh process", GOR["A_fresh_process"], [50541])
expect("twice in one process", GOR["B_same_process_twice"], [50541, 11696])
expect("after three others", GOR["C_after_three_others"], [72365])
expect("clear hash", GOR["D_fresh_plus_clearhash"], [50541])
expect("target first then again", GOR["E_target_first_then_again"], [50541, 13235])

# --- 9. the gate ----------------------------------------------------------
GSC = json.load(open(EV / "gate_selfcheck.json"))
for r in GSC["results"]:
    expect(f"gate {r['check']} fired cleanly", r["verdict"], "fired-cleanly")
    expect(f"gate {r['check']} target failed", r["target_failed"], True)
    expect(f"gate {r['check']} no collateral", r["also_failed"], [])
G2 = json.load(open(EV / "g2_can_move.json"))
expect("G2 flipped", G2["G2_flipped"], True)
expect("G2 repair cost no pin", G2["pins_unchanged"], True)

COST = [float(x) for x in (EV / "gate_cost.txt").read_text().split()]
expect("gate wall under 3 s for every run", all(c < 3.0 for c in COST), True)
expect("gate wall sample count", len(COST), 5)

# --- 9b. COUNT WORDS must agree with the evidence -------------------------
# A stale count word is the failure this document complains about: every number correct,
# the sentence around it wrong. Two rows of an earlier draft still said "four" and "five"
# after a probe fix had made the real count six. These are derived, never typed.
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten"}
blind_pass = sum(1 for m, r in BLIND.items()
                 if r["pins_all_match"] and r["verdict"] == "gate-passes-a-real-change")
total_blind = len(BLIND)
expect("blind-spot count", (blind_pass, total_blind), (6, 9))
for stale in ("Four of the nine", "Five of nine", "five of nine",
              "Five of the nine", "seven of nine"):
    if stale in DOC:
        fails.append(f"stale count word {stale!r}; evidence says {blind_pass} of {total_blind}")
if f"{WORDS[blind_pass].capitalize()} of the nine" not in DOC and \
   f"{WORDS[blind_pass].capitalize()} of nine" not in DOC:
    fails.append(f"the document does not state the blind-spot count as "
                 f"{WORDS[blind_pass]!r} of nine")

# --- 10. the document actually quotes the figures -------------------------
for needle in ("63.0 %", "59.6 %", "64.1 %", "61.1 %", "70.1 %", "70.7 %",
               "862,329", "3,024,920", "109,247", "101,640", "956,783",
               "50,541", "11,696", "72,365", "13,235", "2,789",
               "2.4 s", "22 functions"):
    if needle not in DOC:
        fails.append(f"FINDINGS.md does not quote {needle!r}")

# --- 11. the seat's own withdrawn numbers must not reappear as live claims --
# Scoped to the body BEFORE §3.3 and before §8. Both of those sections ARE the repair:
# §3.3 is "three of my controls had to be repaired" and §8 is "what I had to withdraw".
# Naming a withdrawn claim inside a repair record is the fix; naming it anywhere else is
# the un-repaired claim coming back.
body = DOC.split("### 3.3 Three of my controls")[0].lower()
for banned in ("book differs", "clocked search differs", "mutant changed nothing"):
    if banned in body:
        fails.append(f"a withdrawn claim is asserted before its repair section: {banned!r}")

if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("PASS  all quoted figures resolve against evidence/ "
      "(4 pins, 10 sensitivity mutants, 9 blind spots, 3 coverage workloads, "
      "5 Hash rows, 5 go-repeatability rows, 7 gate self-checks)")
