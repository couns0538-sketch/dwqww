"""Opus 2026-11-23: tools/budget.py, version 2 (SETUP_PLAN 2.2's settled D3, D4, D5 and failure row 3), against
answers worked out BY HAND before the tool ran; P2 and N3 are the plan's own numbers. Standard library only.
    python -I -B test_budget.py <budget.py> <NEW out folder>
Exit 0 = all pass, 1 = a check failed.

BASE, every case unless it says otherwise:
  plan: target 2,000,000,000; lease end 90,000 s; closing 1,800 s; game margin 300 s; K = 1; floor 0.5; match
        margin 1.10; owner choice "reduced target" with 1,546,400,000; queue a 2000, b 2000, big 100000, c 2000.
        D = min(82,800, 90,000 - max(3,600, 1,800)) = 82,800.
  state: now 7,200 s, C4 34,400,000 -> left 75,600 s (the plan's "two hours gone leaves 21, not 22"), deficit
        1,965,600,000, n = 26,000 exactly; floor 13,000; matches from 28,600.
  pilot: 1 whole round of 1, queues empty, no carry-in; cohort 125,000 games, 16,000,000 raw rows (128 a game),
        15,200,000 C4 (kept share 0.95), 500 s -> end to end 30,400. Stages: 2,000,000 games an hour -> 67,555.556,
        C1 100,000 raw -> 95,000, C2 100,000 -> 95,000, C3 1,000 games -> 121,600, C4 90,000. Longest game 300 s ->
        dispatch stops at 82,800 - 600 = 82,200. 12,000 match games an hour = 0.3 s a game.
  sources (failure row 3): every measured key (plan lease_end_s, closing_s; state c4_rows; every pilot key) names
        one raw file written by this test, with its sha256, unless a case says otherwise.
  M   base: r 30,400 (end to end) > 28,600 -> SELF_PLAY_AND_MATCHES, exit 0; margin 4,400 / 26,000 = 0.169231.
      SETUP_PLAN 2.5 (Fable 14:51, by hand; recounted by Opus): spare 75,600 - 1.1 x 1,965,600,000 / 30,400 =
      75,600 - 71,123.684 = 4,476.316 s -> floor(4,476.316 x 12,000 / 7,200) = 7,460 pairs: a 2000 (600 s),
      b 2000 (600 s), big gets 2 x 5,460 = 10,920 of 100,000 (3,276.0 s) and the queue ends there (c gets none);
      matches 4,476.0 s, self-play 71,124.0 s; forecast 34,400,000 + 30,400 x 71,124 = 2,196,569,600.
      (Before 2.5 the whole surplus went to the queue: 18,236 pairs, forecast 2,000,015,360, the target itself.)
  S   cohort 560 s: r = 15,200,000 / 560 = 27,142.857 -> SELF_PLAY, exit 0; margin 0.043956; no match;
      forecast 34,400,000 + 15,200,000 x 135 = 2,086,400,000.
  S2  stage C4 26,000: r = n exactly, from C4 (the LOWER decides) -> SELF_PLAY, margin 0.0; forecast 2,000,000,000.
  M2  stage C4 28,600: r = 1.10 n exactly -> 2.5's strict door: SELF_PLAY, exit 0, margin 0.1, no match, no
      spare_s; forecast 34,400,000 + 28,600 x 75,600 = 2,196,560,000 (before 2.5: SELF_PLAY_AND_MATCHES).
  O   cohort 760 s: r 20,000; 13,000 <= r < 26,000 -> OWNER_CHOICE, exit 3. Reduced: (1,546,400,000 - 34,400,000) /
      75,600 = 20,000 -> covered (r = n' exactly); margin -0.230769; no match; forecast 1,546,400,000.
  F2  stage C4 13,000: r = the floor exactly -> OWNER_CHOICE (not STOP), exit 3; the reduced target not covered.
  X   cohort 1,520 s: r 10,000 < 13,000 -> STOP, exit 4.
  N1  state C4 0: n = 2,000,000,000 / 75,600 = 26,455.026455, printed rounded UP as 26,456 (the old tool printed
      26455.0); stage C4 26,455 -> OWNER_CHOICE, exit 3; reduced n' 20,455.026455 (20,456), covered.
  N2  as N1 with stage C4 26,456 -> SELF_PLAY, exit 0; margin 26,456 x 75,600 / 2e9 - 1 = 0.0000368 -> 0.000037;
      forecast 26,456 x 75,600 = 2,000,073,600.
  N3  the plan's section 5: 36,000,000 credited, 1,964,000,000 / 75,600 = 25,978.835979 -> 25,979; base pilot ->
      SELF_PLAY_AND_MATCHES (30,400 >= 28,576.7).
  P2  the plan's "the server makes 25,000 a second while home keeps 20,000: 23 hours credit at most 1.656 billion":
      now 0, C4 0, left 82,800; n = 24,154.589372 -> 24,155 (the plan's section 5); pilot 120,000 games,
      16,000,000 raw, 14,400,000 C4 (share 0.9), 400 s -> end to end 36,000; 750,000 games an hour -> production
      25,000; C1 and C2 90,000; C3 120,000; C4 20,000 -> r 20,000 from C4; floor 12,077.3 <= r < n -> OWNER_CHOICE,
      exit 3; margin 0.828 - 1 = -0.172; forecast 20,000 x 82,800 = 1,656,000,000; reduced n' 18,676.328502
      (18,677), covered.
  H   now 82,800, C4 1,900,000,000, no pilot -> SHORT, exit 5, deficit 100,000,000, left 0.0 (the old tool: bad input).
  H2  now 80,000, exclusive 3,000, base pilot -> left 82,800 - 80,000 - 3,000 = -200 -> SHORT, exit 5.
  R   now 40,000, C4 2,000,000,000, base pilot -> REACHED, exit 0; left 42,800 s -> 71,333 pairs: all four matches
      whole (106,000 games, 31,800 s), self-play 11,000 s.
      CHANGED 23 Nov 14:2x by Astra's boundary (a) (debate msg 20261123T143323Z: "Target reached. No self-play
      dispatch is needed"): self-play 0.0, the 11,000 s after the matches are idle_s.
  R2  as R without a pilot -> REACHED, no match (no measured match rate, D11); self-play 0.0, idle 42,800.
  ASTRA'S FOUR BOUNDARIES (msg 20261123T143323Z, through Fable's FABLE-2311-WORKER-V2-ANSWERS), worked by hand:
  A1  (a) now 81,900 (left 900), C4 2,000,000,000, a pilot whose every measured rate and match rate is 0 -> REACHED,
      exit 0, decided before any rate is qualified: no match, matches 0.0, self-play 0.0, idle 900.0.
  A2  (b) now 82,800 (left 0), C4 1,999,999,999 -> SHORT, exit 5, deficit exactly 1, left 0.0 (never bad input).
  A2b (b) now 82,800, C4 2,000,000,000 -> REACHED, exit 0, left 0.0, no match, self-play 0.0, idle 0.0.
  A3  (c) now 81,800 (left 1,000), C4 1,974,999,999 (25,000,001 to make), cohort 1,216 s -> end to end 15,200,000 /
      1,216 = 12,500 exactly, the lowest -> 2 x 12,500,000 milli < 25,000,001 milli -> under half -> STOP, exit 4;
      n 25,000.001 (25,001 rounded up); printed exactly: r "12500", n "25000001/1000", floor "25000001/2000".
  A3c the control: C4 1,975,000,000 (25,000,000 to make): the floor is 12,500 = r exactly -> OWNER_CHOICE, exit 3.
  A4a (d) now 2,800 (left 80,000), C4 0, stage C4 26,000 -> n 25,000, r 26,000 from C4 -> SELF_PLAY, exit 0, margin
      0.04, no match, forecast 2,080,000,000.
  A4b (d) stage C4 27,500 = 1.10 n exactly -> 2.5's strict door: SELF_PLAY, exit 0, margin 0.1, no match,
      self-play 80,000.0 s, forecast 27,500 x 80,000 = 2,200,000,000 (before 2.5: matches 7,272.6 s).
  A5  (Astra 154854Z, through Fable 14:51) now 2,800, C4 0, stage C4 30,000: n 25,000, r 30,000 > 27,500 ->
      SELF_PLAY_AND_MATCHES; spare 80,000 - 73,333.333 = 6,666.667 s -> 11,111 pairs: a, b, big 18,222 (5,466.6 s);
      matches 6,666.6 s, self-play 73,333.4 s, forecast 30,000 x 73,333.4 = 2,200,002,000.
  P3a (2.5 point 3) stage C4 28,600.1: r just above 1.10 n; spare 75,600 - 11 x 1,965,600,000 / 286,001 =
      75,600 / 286,001 = 0.264 s, under one pair (0.6 s) -> SELF_PLAY, exit 0, spare_s 0.264, no match, margin
      0.100004, forecast 34,400,000 + 28,600.1 x 75,600 = 2,196,567,560.
  P3b (2.5 point 3) match_games_per_h 0, r 30,400 far above -> SELF_PLAY, spare_s 4,476.316, no match, forecast
      34,400,000 + 30,400 x 75,600 = 2,332,640,000. P3c the same with an empty queue.
  U1  no pilot -> UNQUALIFIED, exit 6. U2 rounds_whole 0. U3 carry-in 5 rows. U4 queues not empty. U5 C2 not
      measured (0). U6 K = 2 declared, 1 whole. All exit 6.
  W1  failure row 3: the pilot's cohort_c4_rows names no file -> UNQUALIFIED, exit 6.
  W2  the state's c4_rows names a file that does not exist -> UNQUALIFIED, exit 6 (before any row).
  W3  the plan's closing_s names the raw file with another sha256 (stale) -> UNQUALIFIED, exit 6.
  W4  as R, the pilot's match_games_per_h names no file -> REACHED, no match.
  T1  lease end 84,000: D = 80,400, dispatch 79,800, left 73,200, n 26,852.459 -> 26,853; r 30,400 >= 29,537.7 ->
      SELF_PLAY_AND_MATCHES. T2 closing 8,000: D = min(82,800, 82,000) = 82,000.
  W5  (Fable's B2) the pilot's cohort_c4_rows names the raw file by a RELATIVE path (it exists from the folder the
      tool runs in) -> UNQUALIFIED, exit 6, "not absolute" (before: accepted).
  Y   state with c1_raw_rows 60,000,000 and c2_raw_rows 50,000,000: M unchanged; both printed back, never counted.
  B1 to B10, bad input, exit 2 with an error: no owner_choice; odd match games; floor 1.5; margin 0.9; reduced =
      target; state without c4_rows; pilot without c3_games_per_s; more kept than raw rows; a number written as a
      string; owner_choice without a name.
  B11 to B18 (2.5 point 4, Fable's B1 in Neon's form; B3), exit 2: c4_rows 1999999999.5; target_rows 2000000000.5;
      c4_rows true; reduced_target_rows 1546400000.5; cohort_games 125000.5; carry_in_rows 0.5 (before: UNQUALIFIED);
      target_rows written 2000000000.0; rounds_whole 5 with K = 1. M itself is the control that 2000000000 passes.
Version 5 (the seats' nine points of 23 November; every case below fails on budget.py c7aab952):
  F  the dispatch fence, D - g = 82,800 - (300 + 300) = 82,200 (Astra 161757Z 1, 162047Z). Target met:
     F1 now 82,799: REACHED, no match, idle 1.0 (before: 2 new games). F2 now 82,200, exactly at the fence: no match,
     idle 600.0 (before: 2,000 games). F3 now 82,199, one second before it: floor(1 x 12,000 / 7,200) = 1 pair of
     "a", 0.6 s, idle 600.4. One row missing (C4 1,999,999,999, r 30,400): F4 now 82,200: SELF_PLAY, no match,
     self-play 600.0, forecast 1,999,999,999 + 30,400 x 600 = 2,018,239,999 (before: 1,998 games). F5 now 82,199:
     1 pair, self-play 600.4. F6 now 81,600: the spare is 1,199.99996 s but only 600 s lie before the fence:
     floor(600 x 12,000 / 7,200) = 1,000 pairs = "a" whole, 600.0 s (before: 1,999 pairs, "a" and 1,998 of "b").
  X, A3  STOP authorizes nothing (Astra 161757Z 2): self_play_s 0.0, matches_s 0.0, no forecast_c4_at_D_scenario;
     X's full-run figure 34,400,000 + 10,000 x 75,600 = 790,400,000 stands as forecast_if_run_scenario.
  T1 lease_end_s 86,399.96 (Astra 161757Z 3): D = 82,799.96 = 2069999/25, dispatch end 82,199.96 = 2054999/25;
     cutoff_floor_s 82,799, dispatch_end_floor_s 82,199. TS0 = M: 82,800 and 82,200.
  Version 6 (Astra 165415Z, 165505Z): every window is computed from the whole seconds the control carries. With
     that lease D is 82,799 and the dispatch end 82,199: D_s 82,799.0, dispatch_stop_s 82,199.0, left 75,599.0.
     W1 target met, now 82,199: no match (before: one pair). W2 one row missing, now 82,199: SELF_PLAY, no match.
     W3 target met, now 82,198: one second is left, floor(1 x 12,000 / 7,200) = 1 pair (before: three pairs, 1.8 s).
     W4 now 82,199.1: no match. W5 now 82,198.1 and one exclusive second: no match. W6 one row missing, now 82,799:
     SHORT, deficit 1, left 0.0 (before: SELF_PLAY with one second). W7 now 82,798 and one exclusive second: SHORT.
     W8 now 82,798: SELF_PLAY, left 1.0, forecast 1,999,999,999 + 30,400 = 2,000,030,399.
     The fence cases are named FD1 to FD6 and the times TS0, TS1 (F2 and T1 are older cases: every case keeps its
     own files in the test folder). Y: a finding of failure row 3 names no path: the reason holds no part of the
     test folder's path, and local_only names the file.
  I  the inputs (Astra 162047Z): I1 names the sha256 of the three files as written; two pilots with the same
     numbers and another note give two different results; the same input twice gives the same result; I2 without
     a pilot: pilot_sha256 null.
  J  json (Neon 162055Z 2), exit 2: J1 c4_rows twice (0, then 2,000,000,000; before: REACHED); J2 an extra key NaN;
     J3 Infinity; J4 1e500 (before: each exit 0 with a token that is not json). J5: M's own output parses with a
     reader that refuses those tokens.
  L  longest_game_s 0 (Neon 3): L1 UNQUALIFIED, exit 6, names longest_game_s (before: matches). L2 with the target
     met: REACHED and no match (no dispatch end can be named; Fable's choice).
  Q  a match without a name (Neon 4), exit 2: "" and "  ".
  P  in one process, as a guard that imports the tool would call it (Neon 1 and 4): P1 decide() on good files:
     SELF_PLAY_AND_MATCHES; P2 the raw file overwritten, decide() again: UNQUALIFIED, "stale" (before: unchanged);
     P3 the raw file restored but its opening refused (PermissionError): UNQUALIFIED, "unreadable" (before: the
     error escaped decide()).
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
from decimal import Decimal

tool, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
assert not os.path.exists(out), out
os.makedirs(out)
PLAN = {"target_rows": 2000000000, "lease_end_s": 90000, "closing_s": 1800, "game_margin_s": 300,
        "pilot_rounds_declared": 1, "floor_fraction": 0.5, "match_margin": 1.10,
        "owner_choice": {"name": "reduced target", "reduced_target_rows": 1546400000},
        "match_queue": [["a", 2000], ["b", 2000], ["big", 100000], ["c", 2000]]}
STATE = {"now_s": 7200, "c4_rows": 34400000}
PILOT = {"rounds_whole": 1, "queues_empty_at_start": True, "carry_in_rows": 0, "cohort_games": 125000,
         "cohort_raw_rows": 16000000, "cohort_c4_rows": 15200000, "cohort_seconds": 500, "games_per_h": 2000000,
         "c1_raw_rows_per_s": 100000, "c2_raw_rows_per_s": 100000, "c3_games_per_s": 1000,
         "c4_kept_rows_per_s": 90000, "longest_game_s": 300, "match_games_per_h": 12000}
RAW = os.path.join(out, "raw_measurements.txt")
with open(RAW, "w", encoding="utf-8") as fh:
    fh.write("stand-in raw file: every measured input of these cases names it\n")
with open(RAW, "rb") as fh:
    SRC = {"path": RAW, "sha256": hashlib.sha256(fh.read()).hexdigest()}
NEEDS = {"plan": ("lease_end_s", "closing_s"), "state": ("c4_rows",), "pilot": tuple(PILOT)}
NO = object()
fails = []


def RawNumber(d):
    """A Decimal goes into the json text as its own digits (1999999999.5, 2000000000.0): a float would round it."""
    assert isinstance(d, Decimal), d
    return "@@NUM@@" + str(d) + "@@NUM@@"


def with_(base, **kw):
    d = copy.deepcopy(base)
    for k, v in kw.items():
        if v is NO:
            d.pop(k)
        else:
            d[k] = v
    return d


def sourced(kind, obj, drop=(), **over):
    """obj with failure row 3's sources: every measured key names RAW, except `drop`; `over` replaces entries."""
    s = {k: SRC for k in NEEDS[kind] if k not in drop}
    if kind == "state" and obj.get("exclusive_s") not in (None, 0) and "exclusive_s" not in drop:
        s["exclusive_s"] = SRC                  # version 7: a nonzero exclusive time names its raw file
    s.update(over)
    return dict(obj, sources=s)


def run(name, plan=PLAN, state=STATE, pilot=PILOT):
    paths = []
    for kind, obj in (("plan", plan), ("state", state), ("pilot", pilot)):
        if obj is not None:
            if "sources" not in obj:
                obj = sourced(kind, obj)
            p = os.path.join(out, f"{name}_{kind}.json")
            with open(p, "w", encoding="utf-8") as fh:   # a Decimal is written as its digits, exactly
                fh.write(json.dumps(obj, default=lambda d: RawNumber(d)).replace('"@@NUM@@', "").replace('@@NUM@@"', ""))
            paths.append(p)
    r = subprocess.run([sys.executable, "-I", "-B", tool, *paths], capture_output=True, text=True)
    try:
        return r.returncode, json.loads(r.stdout or "{}")
    except ValueError:
        return r.returncode, {"unparsed": r.stdout[-300:] + r.stderr[-300:]}


def check(name, got, want):
    ok = got == want
    print(f"{'PASS' if ok else 'FAIL'} {name}: got {got!r}" + ("" if ok else f", want {want!r}"))
    if not ok:
        fails.append(name)


def case(name, want_rc, want, **kw):
    rc, res = run(name, **kw)
    check(f"{name} exit", rc, want_rc)
    for k, v in want.items():
        if k == "reason_has":
            check(f"{name} reason holds {v!r}", v in res.get("reason", ""), True)
        else:
            check(f"{name} {k}", res.get(k), v)


M_MATCHES = [["a", 2000, 2000, 600.0], ["b", 2000, 2000, 600.0], ["big", 100000, 10920, 3276.0]]
case("M", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "c4_rows": 34400000, "deficit_rows": 1965600000, "D_s": 82800.0,
              "dispatch_stop_s": 82200.0, "left_s": 75600.0, "n_exact": 26000.0, "n_ceil": 26000, "r": 30400.0,
              "r_from": "end_to_end", "kept_share": 0.95, "floor_rows_per_s": 13000.0,
              "matches_from_rows_per_s": 28600.0, "margin": 0.169231, "matches": M_MATCHES, "matches_s": 4476.0,
              "spare_s": 4476.316, "self_play_s": 71124.0, "forecast_c4_at_D_scenario": 2196569600,
              "rates": {"end_to_end": 30400.0, "production": 67555.556, "C1": 95000.0, "C2": 95000.0,
                        "C3": 121600.0, "C4": 90000.0}})
case("S", 0, {"outcome": "SELF_PLAY", "r": 27142.857, "r_from": "end_to_end", "margin": 0.043956, "matches": [],
              "matches_s": 0.0, "self_play_s": 75600.0, "forecast_c4_at_D_scenario": 2086400000},
     pilot=with_(PILOT, cohort_seconds=560))
case("S2", 0, {"outcome": "SELF_PLAY", "r": 26000.0, "r_from": "C4", "margin": 0.0,
               "forecast_c4_at_D_scenario": 2000000000}, pilot=with_(PILOT, c4_kept_rows_per_s=26000))
case("M2", 0, {"outcome": "SELF_PLAY", "r": 28600.0, "r_from": "C4", "margin": 0.1, "matches": [], "matches_s": 0.0,
               "spare_s": None, "self_play_s": 75600.0, "forecast_c4_at_D_scenario": 2196560000},
     pilot=with_(PILOT, c4_kept_rows_per_s=28600))
case("O", 3, {"outcome": "OWNER_CHOICE", "r": 20000.0, "owner_choice": "reduced target", "margin": -0.230769,
              "reduced": {"target_rows": 1546400000, "covered": True, "n_exact": 20000.0, "n_ceil": 20000},
              "matches": [], "forecast_c4_at_D_scenario": 1546400000}, pilot=with_(PILOT, cohort_seconds=760))
case("F2", 3, {"outcome": "OWNER_CHOICE", "r": 13000.0, "r_from": "C4",
               "reduced": {"target_rows": 1546400000, "covered": False, "n_exact": 20000.0, "n_ceil": 20000}},
     pilot=with_(PILOT, c4_kept_rows_per_s=13000))
case("X", 4, {"outcome": "STOP", "r": 10000.0, "r_from": "end_to_end", "matches": [], "matches_s": 0.0,
              "self_play_s": 0.0, "forecast_c4_at_D_scenario": None, "forecast_if_run_scenario": 790400000},
     pilot=with_(PILOT, cohort_seconds=1520))
N1_STATE = with_(STATE, c4_rows=0)
case("N1", 3, {"outcome": "OWNER_CHOICE", "n_exact": 26455.026455, "n_ceil": 26456, "r": 26455.0, "r_from": "C4",
               "reduced": {"target_rows": 1546400000, "covered": True, "n_exact": 20455.026455, "n_ceil": 20456}},
     state=N1_STATE, pilot=with_(PILOT, c4_kept_rows_per_s=26455))
case("N2", 0, {"outcome": "SELF_PLAY", "n_ceil": 26456, "r": 26456.0, "margin": 0.000037,
               "forecast_c4_at_D_scenario": 2000073600},
     state=N1_STATE, pilot=with_(PILOT, c4_kept_rows_per_s=26456))
case("N3", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "n_exact": 25978.835979, "n_ceil": 25979},
     state=with_(STATE, c4_rows=36000000))
case("P2", 3, {"outcome": "OWNER_CHOICE", "left_s": 82800.0, "n_exact": 24154.589372, "n_ceil": 24155,
               "r": 20000.0, "r_from": "C4", "kept_share": 0.9, "margin": -0.172,
               "rates": {"end_to_end": 36000.0, "production": 25000.0, "C1": 90000.0, "C2": 90000.0,
                         "C3": 120000.0, "C4": 20000.0},
               "reduced": {"target_rows": 1546400000, "covered": True, "n_exact": 18676.328502, "n_ceil": 18677},
               "forecast_c4_at_D_scenario": 1656000000},
     state={"now_s": 0, "c4_rows": 0},
     pilot=with_(PILOT, cohort_games=120000, cohort_c4_rows=14400000, cohort_seconds=400, games_per_h=750000,
                 c4_kept_rows_per_s=20000))
case("H", 5, {"outcome": "SHORT", "deficit_rows": 100000000, "left_s": 0.0, "dispatch_stop_s": None},
     state={"now_s": 82800, "c4_rows": 1900000000}, pilot=None)
case("H2", 5, {"outcome": "SHORT", "left_s": -200.0, "dispatch_stop_s": 82200.0},
     state={"now_s": 80000, "c4_rows": 1900000000, "exclusive_s": 3000})
R_STATE = {"now_s": 40000, "c4_rows": 2000000000}
case("R", 0, {"outcome": "REACHED", "deficit_rows": 0, "left_s": 42800.0,
              "matches": [["a", 2000, 2000, 600.0], ["b", 2000, 2000, 600.0], ["big", 100000, 100000, 30000.0],
                          ["c", 2000, 2000, 600.0]], "matches_s": 31800.0, "self_play_s": 0.0, "idle_s": 11000.0},
     state=R_STATE)
case("R2", 0, {"outcome": "REACHED", "matches": [], "matches_s": 0.0, "self_play_s": 0.0, "idle_s": 42800.0},
     state=R_STATE, pilot=None)
ZERO = with_(PILOT, **{k: 0 for k in ("cohort_games", "cohort_raw_rows", "cohort_c4_rows", "cohort_seconds",
                                      "games_per_h", "c1_raw_rows_per_s", "c2_raw_rows_per_s", "c3_games_per_s",
                                      "c4_kept_rows_per_s", "match_games_per_h")})
case("A1", 0, {"outcome": "REACHED", "left_s": 900.0, "matches": [], "matches_s": 0.0, "self_play_s": 0.0,
               "idle_s": 900.0}, state={"now_s": 81900, "c4_rows": 2000000000}, pilot=ZERO)
case("A2", 5, {"outcome": "SHORT", "deficit_rows": 1, "left_s": 0.0}, state={"now_s": 82800, "c4_rows": 1999999999})
case("A2b", 0, {"outcome": "REACHED", "left_s": 0.0, "matches": [], "self_play_s": 0.0, "idle_s": 0.0},
     state={"now_s": 82800, "c4_rows": 2000000000})
case("A3", 4, {"outcome": "STOP", "r": 12500.0, "r_from": "end_to_end", "n_exact": 25000.001, "n_ceil": 25001,
               "self_play_s": 0.0, "matches": [], "forecast_c4_at_D_scenario": None,
               "exact": {"r": "12500", "n": "25000001/1000", "floor": "25000001/2000",
                         "matches_from": "275000011/10000"}},
     state={"now_s": 81800, "c4_rows": 1974999999}, pilot=with_(PILOT, cohort_seconds=1216))
case("A3c", 3, {"outcome": "OWNER_CHOICE", "r": 12500.0, "floor_rows_per_s": 12500.0},
     state={"now_s": 81800, "c4_rows": 1975000000}, pilot=with_(PILOT, cohort_seconds=1216))
case("A4a", 0, {"outcome": "SELF_PLAY", "n_exact": 25000.0, "r": 26000.0, "r_from": "C4", "margin": 0.04,
                "matches": [], "forecast_c4_at_D_scenario": 2080000000},
     state={"now_s": 2800, "c4_rows": 0}, pilot=with_(PILOT, c4_kept_rows_per_s=26000))
case("A4b", 0, {"outcome": "SELF_PLAY", "r": 27500.0, "margin": 0.1, "matches": [], "matches_s": 0.0,
                "spare_s": None, "self_play_s": 80000.0, "forecast_c4_at_D_scenario": 2200000000},
     state={"now_s": 2800, "c4_rows": 0}, pilot=with_(PILOT, c4_kept_rows_per_s=27500))
case("A5", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "r": 30000.0, "r_from": "C4", "spare_s": 6666.667,
               "matches": [["a", 2000, 2000, 600.0], ["b", 2000, 2000, 600.0], ["big", 100000, 18222, 5466.6]],
               "matches_s": 6666.6, "self_play_s": 73333.4, "forecast_c4_at_D_scenario": 2200002000},
     state={"now_s": 2800, "c4_rows": 0}, pilot=with_(PILOT, c4_kept_rows_per_s=30000))
case("P3a", 0, {"outcome": "SELF_PLAY", "r": 28600.1, "r_from": "C4", "margin": 0.100004, "spare_s": 0.264,
                "matches": [], "matches_s": 0.0, "self_play_s": 75600.0, "forecast_c4_at_D_scenario": 2196567560},
     pilot=with_(PILOT, c4_kept_rows_per_s=Decimal("28600.1")))
case("P3b", 0, {"outcome": "SELF_PLAY", "r": 30400.0, "spare_s": 4476.316, "matches": [], "matches_s": 0.0,
                "self_play_s": 75600.0, "forecast_c4_at_D_scenario": 2332640000},
     pilot=with_(PILOT, match_games_per_h=0))
case("P3c", 0, {"outcome": "SELF_PLAY", "spare_s": 4476.316, "matches": [], "forecast_c4_at_D_scenario": 2332640000},
     plan=with_(PLAN, match_queue=[]))
case("U1", 6, {"outcome": "UNQUALIFIED", "reason_has": "no pilot record"}, pilot=None)
case("U2", 6, {"outcome": "UNQUALIFIED", "reason_has": "0 of 1 declared rounds"}, pilot=with_(PILOT, rounds_whole=0))
case("U3", 6, {"outcome": "UNQUALIFIED", "reason_has": "5 carried-in rows"}, pilot=with_(PILOT, carry_in_rows=5))
case("U4", 6, {"outcome": "UNQUALIFIED", "reason_has": "queues were not empty"},
     pilot=with_(PILOT, queues_empty_at_start=False))
case("U5", 6, {"outcome": "UNQUALIFIED", "reason_has": "c2_raw_rows_per_s"}, pilot=with_(PILOT, c2_raw_rows_per_s=0))
case("U6", 6, {"outcome": "UNQUALIFIED", "reason_has": "1 of 2 declared rounds"},
     plan=with_(PLAN, pilot_rounds_declared=2))
case("W1", 6, {"outcome": "UNQUALIFIED", "reason_has": "pilot.cohort_c4_rows: no raw file named"},
     pilot=sourced("pilot", PILOT, drop=("cohort_c4_rows",)))
case("W2", 6, {"outcome": "UNQUALIFIED", "reason_has": "state.c4_rows: raw file missing"},
     state=sourced("state", STATE, c4_rows={"path": os.path.join(out, "no_such_file.txt"), "sha256": SRC["sha256"]}))
case("W3", 6, {"outcome": "UNQUALIFIED", "reason_has": "plan.closing_s: raw file changed"},
     plan=sourced("plan", PLAN, closing_s={"path": RAW, "sha256": "0" * 64}))
case("W4", 0, {"outcome": "REACHED", "matches": [], "self_play_s": 0.0, "idle_s": 42800.0},
     state=R_STATE, pilot=sourced("pilot", PILOT, drop=("match_games_per_h",)))
case("W5", 6, {"outcome": "UNQUALIFIED", "reason_has": "pilot.cohort_c4_rows: the raw file's path is not absolute"},
     pilot=sourced("pilot", PILOT, cohort_c4_rows={"path": os.path.relpath(RAW), "sha256": SRC["sha256"]}))
case("T1", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "D_s": 80400.0, "dispatch_stop_s": 79800.0, "left_s": 73200.0,
               "n_ceil": 26853}, plan=with_(PLAN, lease_end_s=84000))
case("T2", 0, {"D_s": 82000.0}, plan=with_(PLAN, closing_s=8000))
case("Y", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "matches": M_MATCHES, "matches_s": 4476.0,
              "forecast_c4_at_D_scenario": 2196569600,
              "other_counts": {"c1_raw_rows": 60000000, "c2_raw_rows": 50000000}},
     state=with_(STATE, c1_raw_rows=60000000, c2_raw_rows=50000000))
for name, kw in (("B1", {"plan": with_(PLAN, owner_choice=NO)}),
                 ("B2", {"plan": with_(PLAN, match_queue=[["a", 2001]])}),
                 ("B3", {"plan": with_(PLAN, floor_fraction=1.5)}),
                 ("B4", {"plan": with_(PLAN, match_margin=0.9)}),
                 ("B5", {"plan": with_(PLAN, owner_choice={"name": "x", "reduced_target_rows": 2000000000})}),
                 ("B6", {"state": with_(STATE, c4_rows=NO)}),
                 ("B7", {"pilot": with_(PILOT, c3_games_per_s=NO)}),
                 ("B8", {"pilot": with_(PILOT, cohort_c4_rows=17000000)}),
                 ("B9", {"pilot": with_(PILOT, cohort_seconds="500")}),
                 ("B10", {"plan": with_(PLAN, owner_choice={"reduced_target_rows": 1546400000})}),
                 ("B11", {"state": with_(STATE, c4_rows=Decimal("1999999999.5"))}),
                 ("B12", {"plan": with_(PLAN, target_rows=Decimal("2000000000.5"))}),
                 ("B13", {"state": with_(STATE, c4_rows=True)}),
                 ("B14", {"plan": with_(PLAN, owner_choice={"name": "x", "reduced_target_rows": Decimal("1546400000.5")})}),
                 ("B15", {"pilot": with_(PILOT, cohort_games=Decimal("125000.5"))}),
                 ("B16", {"pilot": with_(PILOT, carry_in_rows=Decimal("0.5"))}),
                 ("B17", {"plan": with_(PLAN, target_rows=Decimal("2000000000.0"))}),
                 ("B18", {"pilot": with_(PILOT, rounds_whole=5)})):
    rc, res = run(name, **kw)
    check(f"{name} exit", rc, 2)
    check(f"{name} names its error", "error" in res, True)

# ------------------------------------------------------------------------------- version 5: the seats' nine points
MET, ONE = 2000000000, 1999999999
case("FD1", 0, {"outcome": "REACHED", "left_s": 1.0, "dispatch_stop_s": 82200.0, "new_dispatch_s": 0.0, "matches": [],
               "matches_s": 0.0, "self_play_s": 0.0, "idle_s": 1.0}, state={"now_s": 82799, "c4_rows": MET})
case("FD2", 0, {"outcome": "REACHED", "left_s": 600.0, "new_dispatch_s": 0.0, "matches": [], "matches_s": 0.0,
               "self_play_s": 0.0, "idle_s": 600.0}, state={"now_s": 82200, "c4_rows": MET})
case("FD3", 0, {"outcome": "REACHED", "left_s": 601.0, "new_dispatch_s": 1.0, "matches": [["a", 2000, 2, 0.6]],
               "matches_s": 0.6, "self_play_s": 0.0, "idle_s": 600.4}, state={"now_s": 82199, "c4_rows": MET})
case("FD4", 0, {"outcome": "SELF_PLAY", "left_s": 600.0, "new_dispatch_s": 0.0, "matches": [], "matches_s": 0.0,
               "spare_s": 600.0, "self_play_s": 600.0, "forecast_c4_at_D_scenario": 2018239999,
               "reason_has": "dispatch end"}, state={"now_s": 82200, "c4_rows": ONE})
case("FD5", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "left_s": 601.0, "new_dispatch_s": 1.0,
               "matches": [["a", 2000, 2, 0.6]], "matches_s": 0.6, "self_play_s": 600.4},
     state={"now_s": 82199, "c4_rows": ONE})
case("FD6", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "left_s": 1200.0, "new_dispatch_s": 600.0, "spare_s": 1200.0,
               "matches": [["a", 2000, 2000, 600.0]], "matches_s": 600.0, "self_play_s": 600.0},
     state={"now_s": 81600, "c4_rows": ONE})
case("TS0", 0, {"D_s": 82800.0, "cutoff_floor_s": 82800, "dispatch_end_floor_s": 82200, "new_dispatch_s": 75000.0,
               "bounds_exact": {"D_s": "82800", "dispatch_end_s": "82200"}})
FRAC = with_(PLAN, lease_end_s=Decimal("86399.96"))
case("TS1", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "D_s": 82799.0, "dispatch_stop_s": 82199.0, "left_s": 75599.0,
                "cutoff_floor_s": 82799, "dispatch_end_floor_s": 82199,
                "bounds_exact": {"D_s": "2069999/25", "dispatch_end_s": "2054999/25"}}, plan=FRAC)
case("W1", 0, {"outcome": "REACHED", "left_s": 600.0, "new_dispatch_s": 0.0, "matches": [], "matches_s": 0.0,
               "idle_s": 600.0}, plan=FRAC, state={"now_s": 82199, "c4_rows": MET})
case("W2", 0, {"outcome": "SELF_PLAY", "left_s": 600.0, "new_dispatch_s": 0.0, "matches": [], "matches_s": 0.0},
     plan=FRAC, state={"now_s": 82199, "c4_rows": ONE})
case("W3", 0, {"outcome": "REACHED", "left_s": 601.0, "new_dispatch_s": 1.0, "matches": [["a", 2000, 2, 0.6]],
               "matches_s": 0.6}, plan=FRAC, state={"now_s": 82198, "c4_rows": MET})
case("W4", 0, {"outcome": "REACHED", "new_dispatch_s": 0.0, "matches": []}, plan=FRAC,
     state={"now_s": Decimal("82199.1"), "c4_rows": MET})
case("W5", 0, {"outcome": "REACHED", "new_dispatch_s": 0.0, "matches": []}, plan=FRAC,
     state={"now_s": Decimal("82198.1"), "c4_rows": MET, "exclusive_s": 1})
case("W6", 5, {"outcome": "SHORT", "deficit_rows": 1, "left_s": 0.0}, plan=FRAC, state={"now_s": 82799, "c4_rows": ONE})
case("W7", 5, {"outcome": "SHORT", "deficit_rows": 1, "left_s": 0.0}, plan=FRAC,
     state={"now_s": 82798, "c4_rows": ONE, "exclusive_s": 1})
case("W8", 0, {"outcome": "SELF_PLAY", "left_s": 1.0, "matches": [], "forecast_c4_at_D_scenario": 2000030399},
     plan=FRAC, state={"now_s": 82798, "c4_rows": ONE})
GONE = os.path.join(out, "a_raw_file_that_is_not_there.txt")
rc, res = run("Y", state=dict(STATE, sources={"c4_rows": {"path": GONE, "sha256": "0" * 64}}))
check("Y exit, outcome", (rc, res.get("outcome")), (6, "UNQUALIFIED"))
check("Y the reason names the key and the kind", "state.c4_rows: raw file missing" in res.get("reason", ""), True)
check("Y the reason holds no path", os.path.basename(out) in res.get("reason", "x" + os.path.basename(out)), False)
check("Y local_only names the file", (res.get("local_only") or {}).get("raw_files"),
      [["state.c4_rows", "raw file missing", GONE]])
# Version 7 (Astra 165715Z): M with 75,000 exclusive seconds decides STOP with 600 s left; without a raw file named
# for that number the answer is UNQUALIFIED; a zero needs no source.
rc, res = run("E1", state=dict(STATE, exclusive_s=75000, sources={"c4_rows": SRC}))
check("E1 exit, outcome", (rc, res.get("outcome")), (6, "UNQUALIFIED"))
check("E1 the reason names the key", "state.exclusive_s: no raw file named" in res.get("reason", ""), True)
case("E2", 4, {"outcome": "STOP", "left_s": 600.0}, state=dict(STATE, exclusive_s=75000))
case("E3", 0, {"outcome": "SELF_PLAY_AND_MATCHES", "left_s": 75600.0},
     state=dict(STATE, exclusive_s=0, sources={"c4_rows": SRC}))


def sha_of(name, kind):
    with open(os.path.join(out, f"{name}_{kind}.json"), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


rc, res = run("I1")
check("I1 inputs", res.get("inputs"), {"plan_sha256": sha_of("I1", "plan"), "state_sha256": sha_of("I1", "state"),
                                       "pilot_sha256": sha_of("I1", "pilot")})
rc, again = run("I1")
check("I1 the same input twice: the same result", again == res and rc == 0, True)
rc, res_a = run("Ia", pilot=with_(PILOT, note="cohort of run A"))
rc, res_b = run("Ib", pilot=with_(PILOT, note="cohort of run B"))
check("Ia, Ib equal numbers", {k: v for k, v in res_a.items() if k != "inputs"} ==
      {k: v for k, v in res_b.items() if k != "inputs"} and res_a.get("outcome") == "SELF_PLAY_AND_MATCHES", True)
check("Ia, Ib two pilots are two pieces of evidence", res_a != res_b and
      (res_a.get("inputs") or {}).get("pilot_sha256") == sha_of("Ia", "pilot") and
      (res_b.get("inputs") or {}).get("pilot_sha256") == sha_of("Ib", "pilot"), True)
rc, res = run("I2", state=R_STATE, pilot=None)
check("I2 inputs without a pilot", res.get("inputs"), {"plan_sha256": sha_of("I2", "plan"),
                                                        "state_sha256": sha_of("I2", "state"), "pilot_sha256": None})


def put(name, kind, obj, front=""):
    """One input file as run() writes it; `front` is json text put directly behind the opening brace."""
    if "sources" not in obj:
        obj = sourced(kind, obj)
    text = json.dumps(obj, default=lambda d: RawNumber(d)).replace('"@@NUM@@', "").replace('@@NUM@@"', "")
    assert text.startswith("{")
    p = os.path.join(out, f"{name}_{kind}.json")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("{" + front + text[1:])
    return p


def refuse(token):
    raise ValueError(token)


for name, front, shown in (("J1", '"c4_rows": 0, ', "c4_rows twice"), ("J2", '"extra": NaN, ', "NaN"),
                           ("J3", '"extra": Infinity, ', "Infinity"), ("J4", '"huge": 1e500, ', "1e500")):
    state = with_(STATE, c4_rows=MET) if name == "J1" else STATE
    paths = [put(name, "plan", PLAN), put(name, "state", state, front), put(name, "pilot", PILOT)]
    r = subprocess.run([sys.executable, "-I", "-B", tool, *paths], capture_output=True, text=True)
    check(f"{name} {shown}: exit", r.returncode, 2)
    try:
        strict = json.loads(r.stdout, parse_constant=refuse)
    except ValueError:
        strict = None
    check(f"{name} {shown}: one json error object", isinstance(strict, dict) and "error" in strict, True)
paths = [put("J5", "plan", PLAN), put("J5", "state", STATE), put("J5", "pilot", PILOT)]
r = subprocess.run([sys.executable, "-I", "-B", tool, *paths], capture_output=True, text=True)
try:
    strict = json.loads(r.stdout, parse_constant=refuse).get("outcome")
except ValueError:
    strict = None
check("J5 control: the good output parses with the strict reader", (r.returncode, strict), (0, "SELF_PLAY_AND_MATCHES"))

case("L1", 6, {"outcome": "UNQUALIFIED", "reason_has": "longest_game_s"}, pilot=with_(PILOT, longest_game_s=0))
case("L2", 0, {"outcome": "REACHED", "matches": [], "matches_s": 0.0, "idle_s": 42800.0}, state=R_STATE,
     pilot=with_(PILOT, longest_game_s=0))
for name, q_ in (("Q1", [["", 2000]]), ("Q2", [["a", 2000], ["  ", 2000]])):
    rc, res = run(name, plan=with_(PLAN, match_queue=q_))
    check(f"{name} exit", rc, 2)
    check(f"{name} names its error", "error" in res, True)

# P: one process, several decisions
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("budget_under_test", tool)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
RAW2 = os.path.join(out, "raw_for_P.txt")
GOOD = b"stand-in raw file of the cases P\n"
with open(RAW2, "wb") as fh:
    fh.write(GOOD)
SRC2 = {"path": RAW2, "sha256": hashlib.sha256(GOOD).hexdigest()}
objs = []
for kind, obj in (("plan", PLAN), ("state", STATE), ("pilot", PILOT)):
    got = mod.load(put("P", kind, dict(obj, sources={k: SRC2 for k in NEEDS[kind]})))
    objs.append(got[0] if isinstance(got, tuple) else got)


def decide_p():
    try:
        res = mod.decide(*objs)
        return res.get("outcome"), res.get("reason", "")
    except Exception as e:  # the answer of a tool that lets the error out
        return f"{type(e).__name__} escaped decide()", ""


check("P1 good files", decide_p()[0], "SELF_PLAY_AND_MATCHES")
with open(RAW2, "wb") as fh:
    fh.write(b"TAMPERED DATA!")
o, why = decide_p()
check("P2 the raw file changed between two decisions", (o, "stale" in why), ("UNQUALIFIED", True))
with open(RAW2, "wb") as fh:
    fh.write(GOOD)
check("P2 control: restored, it passes again", decide_p()[0], "SELF_PLAY_AND_MATCHES")
real_open = open


def no_open(path, *a, **kw):
    if os.path.abspath(path) == RAW2:
        raise PermissionError(13, "planted: permission denied", RAW2)
    return real_open(path, *a, **kw)


mod.open = no_open
o, why = decide_p()
del mod.open
check("P3 a raw file that cannot be read", (o, "unreadable" in why), ("UNQUALIFIED", True))
check("P3 control: readable again, it passes", decide_p()[0], "SELF_PLAY_AND_MATCHES")

print(f"{len(fails)} failed: {fails}" if fails else "ALL PASS")
sys.exit(1 if fails else 0)
