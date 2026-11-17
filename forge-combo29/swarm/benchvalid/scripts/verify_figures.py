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
STATUS_PATH = HERE.parent / "STATUS.md"
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

# --- 2b. the SENSITIVITY RANGE is derived, not typed ----------------------
# An earlier draft of §0 said "one by 4.5 % to 64 %". Neither figure exists in the
# evidence: no base-to-mutant shift on any pin gives 4.5 % or 64 %, and neither does any
# pairwise difference between mutants on bench 13. A typed range is exactly the kind of
# number that survives a re-run; these are computed.
BASE_PINS = {"bench11": 312866, "bench13": 862329, "bench16": 3024920}
movers = [r for r in SENS.values() if r["kind"] == "should-move"]
expect("five movers", len(movers), 5)
shifts13 = [abs(100 * (r["pins"]["bench13"] - BASE_PINS["bench13"]) / BASE_PINS["bench13"])
            for r in movers]
shifts_all = [abs(100 * (r["pins"][k] - base) / base)
              for r in movers for k, base in BASE_PINS.items()]
lo13, hi13 = round(min(shifts13), 1), round(max(shifts13), 1)
lo_all, hi_all = round(min(shifts_all), 1), round(max(shifts_all), 1)
expect("bench13 range low", lo13, 2.2)
expect("bench13 range high", hi13, 30.3)
expect("all-pin range low", lo_all, 2.0)
expect("all-pin range high", hi_all, 30.3)
for doc, name in ((DOC, "FINDINGS.md"), (STATUS_PATH.read_text(), "STATUS.md")):
    if f"{lo13} % to {hi13} %" not in doc and f"{lo13} %\u2013{hi13} %" not in doc:
        fails.append(f"{name} does not state the derived bench13 range "
                     f"{lo13}..{hi13} %")
# Scope: a withdrawn figure may appear INSIDE the paragraph that withdraws it
# ("An earlier draft said ..."). Search only text that is not part of a withdrawal.
DOC_LIVE = DOC[:DOC.find("## 8. What I had to withdraw")] if "## 8. What I had to withdraw" in DOC else DOC
live_parts = []
for chunk in DOC_LIVE.split("An earlier draft"):
    live_parts.append(chunk)
# the first chunk is everything before the first withdrawal note; later chunks start with
# the withdrawal sentence, so drop their first line and keep the rest as live prose.
live_doc = live_parts[0] + "".join(c.split("\n", 1)[1] if "\n" in c else "" for c in live_parts[1:])
for stale in ("4.5 % to 64 %", "4.5 \u201364 %", "4.5% to 64%", "4.5%-64%"):
    if stale in live_doc or stale in STATUS_PATH.read_text():
        fails.append(f"the withdrawn sensitivity range {stale!r} is still asserted")

# perft must be flat for every mover: that is a claim in §2.1
for r in movers:
    expect(f"{r['mutant']} perft flat", r["pins"]["perft5"], 4865609)

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

# The percentages must be the ones in the JSON, not merely present somewhere in the file.
# An earlier guard checked only `"63.0 %" in DOC`, so planting 68.0 in the headline table
# left it green because a second correct "63.0 %" survived in the section 3 table.
b_lines, b_funcs = pct("coverage_bench13.json")
p_lines, p_funcs = pct("coverage_pins_only.json")
c_lines, c_funcs = pct("coverage_combined.json")
headline = (f"**{b_lines} % of lines, {b_funcs} % of functions**")
if headline not in DOC:
    fails.append(f"the headline coverage figure is not {headline!r}")
# The pins and combined workloads appear in the section 3 table as "= **64.1 %** ... 61.1 %",
# so match that shape; requiring one fixed format would be a check on prose style rather
# than on the figure.
for (ln, fn), label in (((p_lines, p_funcs), "pins_only"), ((c_lines, c_funcs), "combined")):
    if not re.search(rf"= \*\*{re.escape(str(ln))} %\*\*[^\n]*\b{re.escape(str(fn))} %", DOC):
        fails.append(f"the {label} coverage figures ({ln}, {fn}) are not quoted in the "
                     f"\u00a73 table")
# and no OTHER percentage may be presented as the bench13 line figure
for m in re.finditer(r"\*\*(\d+\.\d) % of lines, (\d+\.\d) % of functions\*\*", DOC):
    if (float(m.group(1)), float(m.group(2))) != (b_lines, b_funcs):
        fails.append(f"a bench13 coverage headline of {m.group(0)} disagrees with "
                     f"the evidence ({b_lines}, {b_funcs})")

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
expect("row count", len(GOR), 5)
expect("fresh process", GOR["A_fresh_process"], [50541])
expect("twice in one process", GOR["B_same_process_twice"], [50541, 11696])
expect("after three others", GOR["C_after_three_others"], [72365])
expect("clear hash", GOR["D_fresh_plus_clearhash"], [50541])
expect("target first then again", GOR["E_target_first_then_again"], [50541, 13235])

# The ratio figures are DERIVED, because the first draft of this document quoted
# "6.4x" as the swing and no pair in the evidence gives 6.4. A typed ratio is a
# number that can drift from the JSON; these four cannot.
ALL = [v for vs in GOR.values() for v in vs]
expect("distinct node counts", len(set(ALL)), 4)
expect("full spread 6.19x", round(max(ALL) / min(ALL), 2), 6.19)
expect("repeated-search 4.32x", round(GOR["B_same_process_twice"][0] / GOR["B_same_process_twice"][1], 2), 4.32)
expect("target-again 3.82x",
       round(GOR["E_target_first_then_again"][0] / GOR["E_target_first_then_again"][1], 2), 3.82)
expect("order-only 1.43x",
       round(GOR["C_after_three_others"][0] / GOR["A_fresh_process"][0], 2), 1.43)

# and the document must quote all four, not just the biggest
for needle in ("6.19\u00d7", "4.32\u00d7", "3.82\u00d7", "1.43\u00d7"):
    if needle not in DOC:
        fails.append(f"FINDINGS.md does not quote the derived ratio {needle!r}")
# the withdrawn ratio must not survive as a live claim
body_g6 = DOC.split("### 6.1 G6 exists")[1].split("### 6.2")[0]
if "6.4\u00d7" in body_g6.split("An earlier draft")[0]:
    fails.append("the withdrawn 6.4x ratio is still asserted in \u00a76.1")

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

# --- 9b. EVERY count-of-nine statement must agree with the evidence -------
# A guard that passes because SOME sentence happens to be right is not a guard. An
# earlier version of this check searched for the correct phrasing anywhere in the file,
# so planting "5 of 9" in §0 while "Six of nine" survived in §3.2 left it green.
# This one finds EVERY "<n> of (the) nine" / "<word> of nine" in the prose and requires
# each to equal the derived count. The planted fault is in scripts/plant_check.sh.
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
         8: "eight", 9: "nine", 10: "ten"}
WORD_TO_INT = {v: k for k, v in WORDS.items()}
blind_pass = sum(1 for m, r in BLIND.items()
                 if r["pins_all_match"] and r["verdict"] == "gate-passes-a-real-change")
total_blind = len(BLIND)
expect("blind-spot count", (blind_pass, total_blind), (6, 9))

COUNT_RE = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|[0-9]+) of (?:the )?(?:nine|9)\b",
                      re.IGNORECASE)


def _as_int(token: str):
    t = token.lower()
    if t.isdigit():
        return int(t)
    return WORD_TO_INT.get(t)


for path, label in ((HERE.parent / "FINDINGS.md", "FINDINGS.md"),
                    (STATUS_PATH, "STATUS.md")):
    text = path.read_text()
    # A withdrawal record must be able to quote the wrong value in order to withdraw it.
    # Everything from the withdrawal heading onward is repair, not assertion.
    _cut = text.find("## 8. What I had to withdraw")
    if _cut > 0:
        text = text[:_cut]
    seen = 0
    for line_no, line in enumerate(text.splitlines(), 1):
        for m in COUNT_RE.finditer(line):
            seen += 1
            got = _as_int(m.group(1))
            if got != blind_pass:
                fails.append(f"{label}:{line_no} says {m.group(0)!r} "
                             f"({got}), evidence says {blind_pass} of {total_blind}")
            if m.group(0).split()[-1].isdigit() and m.group(0).split()[-1] == "9":
                pass  # "6 of 9" is fine
    if seen == 0:
        fails.append(f"{label} states no blind-spot count at all")

# --- 9c. NO EVIDENCE FILE MAY DISAGREE WITH ITSELF ------------------------
# A summary field that omits a row is the defect this audit wrote a trap about. One
# intermediate copy of go_repeatability.json read distinct_values [11696, 13235, 50541]
# while its rows contained 72,365, because a row whose search returned None dropped out
# of the set comprehension. This checks every committed JSON that has both.
for jf in sorted(EV.glob("*.json")):
    d = json.load(open(jf))
    if isinstance(d, dict) and "distinct_values" in d and "rows" in d:
        flat = [v for vs in d["rows"].values() for v in vs]
        recomputed = sorted(set(flat))
        expect(f"{jf.name} distinct_values", d["distinct_values"], recomputed)
        expect(f"{jf.name} no null measurements", any(v is None for v in flat), False)
    if isinstance(d, dict) and "rows" in d and jf.name == "go_repeatability.json":
        expect("go_repeatability row count", len(d["rows"]), 5)
        expect("go_repeatability measurement count", d.get("measurement_count"), 7)

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
