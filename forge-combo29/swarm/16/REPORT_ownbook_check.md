# REPORT_ownbook_check — did the default `OwnBook true` touch my work? (seat 16)

**What was asked (by FABLE_TO_swarm_3):** "Every harness sends `setoption name OwnBook value false` (the PC
always does)." My job-1, job-2 and job-3 runs did NOT. This re-check decides whether my published numbers are
affected.

**The answer:** they are NOT affected, and the reason is specific rather than luck. `src/uci.cpp:516-528`
gates the book on `game_search`, defined as `(limits.time_ms >= 0 || limits.movetime_ms >= 0) && !infinite &&
!ponder && !searchmoves && mate_moves == 0`. A `go depth N` search sets neither `time_ms` nor `movetime_ms`,
so `game_search` is false and the book is never consulted. All my job-2 and job-3 measurements use `go depth`,
and job 1 uses `eval`, which never touches the book. Measured confirmation:

```
PART A  30 G positions at depth 10, default vs OwnBook false:  bestmove same 30/30, score same 30/30
PART B  20 G positions `eval`,           default vs OwnBook false:  identical 20/20
PART C  startpos / 1.e4 / 1.e4 e5 at depth 10: no `info string book move` line on any of the three
```

I now send `OwnBook false` in every harness anyway (`job1/mirror_eval.py`, `job2/mirror_lr.py`,
`job3/search_mirror.py`), so future runs match the PC's convention.

**How sure:** high for "my numbers are unaffected" — it is both a code reading and a 30 + 20 measurement.
The PART C result also means the file's warning, while right as a rule, does not apply to `go depth` searches
on this base tree at all; I say that as a correction, not as a contradiction of the file (the file says what a
harness should send, and sending it is still correct).

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| P1: depth-10 bestmove/score, default vs OwnBook false | done | `raw.txt` PART A | 30/30 bestmove same, 30/30 score same |
| P2: eval line, default vs OwnBook false | done | `raw.txt` PART B | 20/20 identical |
| P3: can the book answer at all | done — prediction WRONG | `raw.txt` PART C | no book line on any of 3 tries; cause found in code (`uci.cpp:524-528`, clock/movetime only) |
| `OwnBook false` added to all three harnesses | done | `../job1/mirror_eval.py`, `../job2/mirror_lr.py`, `../job3/search_mirror.py` | patched |

## Findings

`S-F6 | 6 | the built-in book cannot affect an analysis search: `src/uci.cpp:524-528` only probes it when `game_search` holds, i.e. only for a `go wtime/btime` or `go movetime` search (not `go depth`, not `go nodes`, not `go infinite`); three opening positions at `go depth 10` produce no book line, and 30 G positions give identical depth-10 bestmove and score with OwnBook true and false | ownbook_check/raw.txt, again: `python3 ownbook_check/ownbook_check.py ~/builds/bld-release/forge /tmp/o.txt` | NEW |`

## Suspicions, not proven

- Whether `go nodes` also bypasses the book: `limits.time_ms`/`movetime_ms` are what the gate tests, and a node
  limit sets neither, so I expect it bypasses too — but I did not run a node-limited search to confirm.

## What I did NOT do

- Did not run a clock search (that is area 8's job), which is the only place the book can fire.
- Did not re-run job 1/2/3 in full with OwnBook false: the 50-position re-check plus the code reading is enough
  to show the setting cannot have changed those runs, and a full re-run would cost hours for no new information.

## What I am NOT sure about

- Whether the PC's engine gates the book the same way. I read the base tree only.

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

(pasted into `last_cmd.txt` at commit time)

## Last command output

```
$ git status --short
 M job1/mirror_eval.py
 M job2/mirror_lr.py
 M job3/search_mirror.py
 M ownbook_check/stamps.txt
?? REPORT_ownbook_check.md
?? ownbook_check/last_cmd.txt
?? ownbook_check/ownbook_check.py
?? ownbook_check/raw.txt
$ ls
check_S-F1
check_S-F2
check_S-F3
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job2
job3
ownbook_check
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
SEAT.txt
STATUS.md
$ ls ownbook_check
last_cmd.txt
ownbook_check.py
prediction.txt
raw.txt
stamps.txt
```
