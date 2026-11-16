# REPORT — seat 03, area 3, extra job: en-passant pin coverage at scale, with a control

**What was asked.** Nothing directly — this is area-3 work I chose after reading seat 23's 23-F5 ("the ep-pin class
does not occur in random play, it must be constructed") and 23-F6 (three hand-built positions). My job 2 had already
found the same rarity (0 in 40,353 filtered positions) and built a 320-position constructor, which let me do at scale
what seat 23 did three times by hand.

**The answer.** On 320 constructed en-passant-pin positions the engine's root move set is identical to
python-chess's (320/320), and the control passes on all 320: removing the pinning slider makes the same ep capture
legal in python-chess, and the engine agrees there too. So the engine refuses exactly the pinned capture and only
that one — not every ep capture in these positions.

**How sure.** High, and the reason is the control, not the zero: a "the engine omits the ep capture" result is
worthless if those positions forbid the capture for some other reason. Here the slider-removal proves the pin is
the only thing forbidding it, in all 320 positions, with the engine re-checked on the stripped position as well.

## Honesty numbers

bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609, all MATCH (HONESTY.txt, re-proved by
honesty2.py). No sanitizer claim is made here.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 320 constructed class-B positions (from job 2) | done | job2/ep_constructed.tsv (+ .rejects) | all verified class-B by a self-tested predicate |
| root move SET comparison engine vs python-chess | done | job2/ep_pin_compare.py, job2/ep_pin_all.txt (+ .raw/) | 320 of 320 agree, 0 missing, 0 extra |
| control: remove the pinning slider, re-ask both sides | done | job2/ep_pin_control.py, job2/ep_pin_control.txt (+ .raw/) | 320 of 320 pass |
| assertion that the ep capture really is illegal in the original | inside ep_pin_compare.py (assertion 1 and 2) | job2/ep_pin_all.txt | every row carries `py_ep_legal=[]` |

## What the control proves, in one line each

For every position (see `job2/ep_pin_control.txt` for the per-position row):

1. the raw ep capture exists (a pawn stands beside the double-pushed pawn) — else `NO_RAW_EP`;
2. with the position as given, that capture is **not** in python-chess's legal moves (`orig_legal=False`);
3. removing the one enemy slider that causes it makes the **same** capture legal (`strip_allows=True`);
4. the engine's move set equals python-chess's in **both** the original and the stripped position.

Columns in `ep_pin_control.txt`: `idx, fen, verdict, ep_capture, pinner=<square> orig_legal=… strip_allows=…
engine_match_orig=… engine_match_strip=…`.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F4 | On 320 constructed en-passant-pin positions the engine's root move set equals python-chess's exactly (0 missing, 0 extra), and the control passes 320/320: deleting the pinning slider legalises the same ep capture, with the engine still matching — so the engine refuses the pinned capture specifically, not ep captures generally. | `cd forge-combo29/swarm/03/job2 && python3 ep_pin_compare.py ~/build-rel/forge ep_constructed.tsv /tmp/a.txt && python3 ep_pin_control.py ~/build-rel/forge ep_constructed.tsv /tmp/b.txt` |

This goes BEYOND seat 23's 23-F6 (three hand-built positions) and 23-F5 (the class is absent from random play): it
supplies 320 positions, a reusable generator, and a slider-removal control none of their three positions carries.

## Suspicions, not proven

- My 320 positions come from a template family (pawn pair, slider type, king/rook ends, black king square), so they
  are 320 *distinct verified* positions but not 320 independent ideas. A hand-built position with a diagonal pin
  (bishop behind the pawn on the ep rank) is in my candidates only if the file/rank combination produces it; I did
  not separately count how many of the 320 rest on a diagonal pin versus a rank pin.

## What I did NOT do

- No sanitizer run (not asked for this job).
- Did not test ep pins at search depths above 1 (perft 1 only here; jobs 1/2 compare depths 1..4, but not on these
  constructed positions at depth 4 — the special set's 314 positions included the 14 real ones).

## What I am NOT sure about

- Whether python-chess's legality for these positions and the engine's agree for the same *reason*; agreement on the
  move set is what I measured, not the internal cause.

## Times

`job2/stamps.txt`.
