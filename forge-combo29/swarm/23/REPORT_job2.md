# REPORT job 2 — swarm seat 23, AREA 3 (special move-type positions vs python-chess)

**What was asked:** 500 special positions found by filtering R and G with python-chess (castling with an
attacked transit square, en passant that would expose the king, a capture-promotion with check, double check,
a pinned piece that can capture its pinner); perft 1 to 4 on each.

**The answer:** the filter found 58 qualifying positions in 5,000 R + 353 G positions (not 500 — see below), and
the engine matched python-chess exactly on all 58 at depths 1..4, 0 mismatches, 77,220,237 nodes per side. The
en-passant-pin class came out EMPTY from random play, so I built three such positions by hand and verified them:
the engine correctly REFUSES the pinned ep capture in all three, and correctly allows it in the negative control.

**How sure:** high on what was measured. NOT sure that 58 positions is the "500" the job asked for — it is
everything the two position sets contain, and I say so rather than padding the set.

## Honesty numbers

Same build as job 1: 6b98f217, Release, `-DFORGE_MARCH=x86-64-v4`, GCC 13.3.0, exe sha256 e06310ec…, honesty
4/4 (`HONESTY.txt`). No sanitizer claims.

## The table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| classify R+G by python-chess into C1..C5 | done | `job2/special_filter.py` → `special_classes.json` | 58 distinct positions: C1 17, C2 0, C3 23, C4 1, C5 17 |
| reach 500 positions | **NOT DONE — impossible from these sets** | `special_classes.json` | the 5,353 available positions contain 58 of these classes; the job's 500 was a target, not a measurement, and I did not duplicate or pad positions to reach it |
| engine perft 1..4 on the 58 | done | `job2/engine_S.jsonl`, `engine_S.log` | 58/58 in 0.5 s |
| python-chess perft 1..4 on the 58 | done | `job2/pych_S_0.jsonl`, `pych_S.log` | 58/58 |
| compare | done | `job2/compare_perft.py` → `compare_S.out` | 0 mismatches at every depth |
| C2 (ep pin) from random play | **empty** | `special_classes.json` | 0 found in 5,353 positions |
| C2 built by hand and verified | done | `job2/make_ep_pin.py` → `ep_pin_cases.json` | 3 kept, 2 rejected (1 invalid board, 1 negative control) |
| engine behaviour on the 3 hand-built ep pins + control | done | `job2/ep_pin_engine.sh` → `ep_pin_engine.out` | engine omits the pinned capture in all 3 and emits it in the control |

The comparison, pasted from `compare_S.out`:

```
positions actually compared: 58 of expected 58
depth | engine nodes | reference nodes | equal | mismatching positions
    1 |         2067 |            2067 |   yes | 0
    2 |        65776 |           65776 |   yes | 0
    3 |      2358146 |         2358146 |   yes | 0
    4 |     77220237 |        77220237 |   yes | 0
```

## Findings

- **23-F5** — the en-passant-pin class does not occur in 5,353 randomly generated/game positions, so any claim
  that a perft suite "covers ep pins" through random sampling is unsupported; it must be constructed.
  `cd forge-combo29/swarm/23/job2 && python3 special_filter.py`
- **23-F6** — the engine correctly refuses a pinned en-passant capture (verified on 3 hand-built positions with a
  negative control). `bash forge-combo29/swarm/23/job2/ep_pin_engine.sh`

## My prediction, scored

| # | prediction | outcome |
|---|---|---|
| P1 | 15..120 positions found | **HELD** (58) |
| P2 | C1 < 10 positions | **KILLED** — 17 (my expected rarity was wrong) |
| P3 | C2 ≥ 1 from random play | **KILLED** — 0 |
| P4 | 0 mismatches | **HELD** (0 at all depths) |
| P5 | every class non-empty | **KILLED** — C2 empty |
| P6 | whole run < 20 min | **HELD** (reference 58 positions in ~1 min) |

## Suspicions, not proven

- C1's filter uses "castling right + attacked transit square" because "legal castling move with attacked transit"
  is impossible by definition (castling through check is illegal). If the job's author meant something else by
  "castling with an attacked transit square", my 17 are not what was wanted. What I verified is: in 17
  positions the engine has a castling right whose transit square is attacked, and in all 17 its perft matched
  python-chess (which is the property that matters — the engine must not castle there).
- C5's definition ("a pinned piece that can capture its pinner") was wrong in my first pass: I accepted any
  pinned capture. The corrected version requires the capture target to BE the pinner. 17 positions qualify.
- My C2 filter looks only for pseudo-legal ep moves that are illegal *because the king is exposed*; an ep move
  illegal for another reason would be missed. In practice ep is illegal only for that reason or because of
  check, so I believe the class is complete, but it is a filter, not a proof.

## What I did NOT do

- Did not reach 500 special positions; the position pool does not contain them. Reported, not padded.
- No hand-built cases for C1/C3/C4/C5 (only C2 got them), because time ran out at the owner's 22:30 deadline.
- No sanitizer runs.

## What I am NOT sure about

- Whether 58 positions is enough to call the rare-move-type generator "checked". It is a small sample; each
  position is compared at 4 depths with exact counts, but 58 boards is still 58 boards.

## Times

`job2/stamps.txt`, `job2/*.log`.

## Last command's output

`job2/final_status.txt` holds `git status --short` and `ls` of this folder.
