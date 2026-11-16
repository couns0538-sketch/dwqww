# REPORT job 2 — seat 17, area 7 (move picker and histories)

## What was asked / the answer / how sure

**What was asked.** Area 7 job 2: read the move picker and the histories for faults, with a TEST for every
suspicious line and anything untested placed under "suspicions, not proven".

**The answer.** No fault in the picker or the histories. Four things are worth having on record: the history
arithmetic survives every tunable at both advertised extremes under ASan+UBSan (S-F7); the picker de-duplicates
repeated `searchmoves` entries correctly (S-F8); a `searchmoves` root with no legal match ignores the node and
movetime budgets and prints 64 zero-node depth lines (S-F8, detail for 07-F1); and the known "restricted root
searches a smaller tree" item is quantified at about half the nodes for an identical bestmove (S-C7).

**How sure.** The negatives are certain within the scope stated below. S-F8's terminal-root behaviour is
certain (raw logs, 64 lines, all `nodes 0`).

## Honesty numbers

Base `6b98f217`, release, GCC 13.3.0; see `HONESTY.txt`. All four pins matched at the start of this job and
were not re-measured during it (no engine source was modified, so they cannot have changed).

## Step / done-partly-not done / evidence table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| Read `MovePicker` (search.cpp 577-998) in full | done | this report + `job2/` | stages, `push_scored`, `pick_best`, three generators read |
| Read the history helpers (`apply_history`, `history_bonus`, `quiet_history`, `update_quiet_stats`) | done | this report | arithmetic saturates by construction |
| History tunables at advertised max and min, under ASan+UBSan | done | `job2/hist_extremes.json` | 10 searches, 0 sanitizer lines, 40x node spread proves the options applied |
| Restricted root vs unrestricted, same depth | done | `job2/allmoves_parity.json` | restricted = ~half the nodes, same bestmove |
| `searchmoves` with duplicate entries | done | `job2/sm_dup.log` | de-duplicated, answers e2e4 |
| `searchmoves` (no legal match) + nodes / movetime / MultiPV / mate limits | partly | `job2/sm_nodes.log`, `sm_movetime.log`, `sm_mate.log`, `sm_mpv.log` | see S-F8; the `go infinite` and `go ponder` variants are NOT counted (see "what I did NOT do") |
| Per-root-move effort readout to detect a duplicated or lost root move | not done | — | the engine exposes no per-root-move report, so I could not measure that property directly |

## Findings, each with a command that shows it again

**S-F7 — history arithmetic is clean at both extremes.**
Every history/LMR/ordering tunable at its advertised maximum, and then at its minimum, 5 G positions each at
depth 12 under ASan+UBSan: 0 sanitizer lines. The options demonstrably applied — the max set produced
6,380-29,330 nodes and the min set 91,404-567,342 on the same positions.
Command: `cd forge-combo29/swarm/17/job1 && python3 -c "import json;d=json.load(open('job2/hist_extremes.json'));print([(r['set'],r['max_nodes']) for r in d])"`

**S-F8 — `searchmoves` with no legal match ignores the node and movetime budgets.**
`go nodes 1000 searchmoves e7e5` and `go movetime 100 searchmoves e7e5` both print 64 `info depth` lines,
depth 1 through 64, every one of them `nodes 0`. No search happens, so the budget is never consumed and the
terminal-root loop runs to the depth cap. Repeated move names are de-duplicated correctly
(`searchmoves e2e4 e2e4 e2e4` answers `e2e4`).
Command: `cd forge-combo29/swarm/17/job1 && grep -c 'info depth' job2/sm_nodes.log && grep 'info depth' job2/sm_nodes.log | tail -1`

**S-C7 — the known restricted-root item, quantified.**
With all legal moves listed in `searchmoves`, the tree is about half the unrestricted tree at every depth
(1451 vs 2986 at d8; 5763 vs 11342 at d10; 29306 vs 50704 at d12) and the bestmove is identical.
Command: `cd forge-combo29/swarm/17/job1 && python3 -c "import json;print(json.load(open('job2/allmoves_parity.json')))"`

**Warm/cold — S-C8, and the correction it forced on my S-C6.**
Reproduced seat 10's rule exactly on my build: one process, three identical searches = 56720 / 4951 / 4516;
three processes = 56720 each; `ucinewgame` between = 56720 / 56720; `Clear Hash` between = 56720 / 40569.
My earlier S-C6 used a fresh process against a post-`Clear Hash` search, which conflates warm drift with a TT
clear; that line is re-labelled in FINDINGS and only the narrower claim (the TT is emptied - `hashfull` drops
to 0 - so the residual drift is the histories) is kept.
Command: `cd forge-combo29/swarm/17/job1 && cat seat10/cold_warm_clear.json`

## Suspicions, not proven

- `MovePicker::moves_` (256 slots) and `MoveList` (256 slots) are written through `count_++` with only an
  `assert` and `NDEBUG` is set. The known maximum of 218 legal moves leaves headroom, so I did not reach an
  overflow and am not claiming one.
- `pick_best`'s `seeded_` fast path swaps `moves_[index_]` with `moves_[seeded_at_]`; I read it as correct
  for the first pick only, and the first-pick-only guard (`index_ == list_start_`) looks right, but I did not
  build a test that would catch a wrong quiet-order tie-break.

## What I did NOT do

- Did not complete the `go infinite searchmoves e7e5` and `go ponder ... searchmoves e7e5` variants inside
  the harness: my driver waits for `bestmove` before sending `stop`, so it timed out. Driving those by hand
  showed `go infinite ...` answers `bestmove 0000` immediately, but I did not run the ponder variant by hand,
  so it is NOT counted as a result here.
- Did not measure per-root-move effort (no such output exists).
- Did not write any patch or modify engine source.

## What I am NOT sure about

- Whether the 64 zero-node depth lines under a node budget would confuse a GUI in practice; it is a protocol
  oddity, and 07-F1 owns the presentation claim.
- Whether the tuned extremes I chose are the extremes that matter: I used the advertised min/max of each spin,
  which bounds the option but not every internal intermediate.

## Times

see `job2/…` logs and `STATUS.md` blocks; `date -u` stamps are in the run metadata.

## Last commands' output

```
=== git status --short
(clean at the commit that adds this report)

=== ls job2
allmoves_parity.json  hist_extremes.json  hist_max_0.log .. hist_min_4.log
sm_dup.log  sm_empty_moves.log  sm_mate.log  sm_mpv.log  sm_nodes.log  sm_promo.log
sm_combos2.json  allmv_restricted_*.log  allmv_unrestricted_*.log
```
