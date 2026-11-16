# REPORT_warmcold — was my symmetry number a warm/cold artefact? (seat 16)

**What was asked (seat 10's rule):** two identical unrestricted searches in one process give 56,720 / 4,951 /
4,516 nodes; three fresh processes give 56,720 three times; `ucinewgame` restores cold but `Clear Hash` does not.
So a cold baseline is a fresh process or `ucinewgame`, never `Clear Hash`. Which discipline did each of my
tables use, and is the 101-bestmove-mismatch number in my job 3 a warm/cold confound?

**The answer: my number is NOT a confound, and every table's discipline is stated below.**

## The rule reproduces exactly on my build

```
TWO unrestricted depth-8 searches in ONE process :  nodes 5024, then 1538, then 831
THREE separate processes, same position          :  nodes 5024, 5024, 5024
```
Seat 10's numbers reproduce in shape (their absolute counts differ because their position and depth differ).

## The decisive experiment: same 12 pairs, three disciplines

```
COLD  (fresh process per search)                        : bestmove mismatch  2/12, score mismatch 12/12
WARM  (one process, `ucinewgame` before each search)    : bestmove mismatch  2/12, score mismatch 12/12
WRONG (one process, NOTHING between searches)           : bestmove mismatch  2/12, score mismatch 10/12
```

**COLD and WARM-with-`ucinewgame` are identical, pair for pair.** The wrong discipline gives a *different*
score-mismatch count (10 vs 12), so the confound is live in this build and would have changed my number if I
had used it. My job-3 table did not.

## Which discipline each of my tables used

| table | discipline | affected? |
|---|---|---|
| `job1/raw/G.tsv`, `R.tsv` (353 + 500 colour-mirror `eval`) | one process per PAIR, `eval` twice in it | **NO — `eval` is stateless**: two evals in one process, and a position evaluated after another, give byte-identical values; verified directly (`-325 -26 -351` twice; `18 20 38` warm == fresh) |
| `job2/raw/{G,R}_lr.tsv` (334 + 411 left-right `eval`) | same: one process per pair | **NO** — same reason, `eval` only |
| `check_S-F1` (4 configs × 5,853 pairs, `eval`) | one process per configuration, all pairs in it | **NO** — `eval` only, and it was in fact the WARMEST possible discipline with zero effect; the result (0 differences) is therefore also a direct demonstration that `eval` carries no state |
| `job3/raw/{G,R}_d10.tsv` (353 + 200 depth-10 mirror pairs) | **one FRESH PROCESS PER SEARCH** (`search()` starts a process, searches one position, quits) | **NO** — verified by the COLD-vs-WARM test above |
| `job3/followup` depth series | fresh process per search | NO |
| `check_06F12` (depth-1 node counts) | fresh process per search | NO |
| `check_fullwindow` (320 searches) | **fresh process per search** (`search()` per call, and `FullWindowRoot` is set per process) | NO |
| `check_28F1` (movetime) | fresh process per search | NO |
| `check_ep.py`, `state_after_refusal.py` (perft) | one process per FEN | NO — perft does not search and does not read the TT |
| `honesty.sh` | fresh process per line | NO |

The one row worth naming: `check_S-F1` deliberately used ONE long-lived process for all 5,853 pairs of a
configuration, which is the warmest discipline possible. It reported **0 differences**. That is now evidence in
two directions: the eval is colour-symmetric, AND the `eval` path is immune to the state carry-over that
affects `go` searches.

## Why `go` is affected and `eval` is not

`eval` prints `hce`, `nnue`, `total` from a static evaluation of the current position and does not consult the
transposition table, the history tables or the killers. `go` populates and reads all three, so a second search
in the same process starts from a non-empty TT and non-zero history — the 5024 → 1538 → 831 pattern.

**How sure:** high. The disciplines are stated from the harness source (each `search()` calls `Popen` and
`quit`s), and the COLD/WARM equivalence is measured directly on 12 pairs, with the wrong discipline shown to
differ.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| reproduce the warm/cold pattern | done | this report, commands above | 5024 / 1538 / 831 in one process; 5024 ×3 across processes |
| `eval` statelessness | done | this report, commands above | identical values warm and fresh |
| COLD vs WARM(`ucinewgame`) vs WRONG on 12 pairs | done | `raw_warmcold.txt`, `warmcold_test.py` | 2/12 & 12/12 vs 2/12 & 12/12 vs 2/12 & 10/12 |
| discipline audit of every table | done | table above, read from each harness's source | only `eval` tables were ever warm, and `eval` is immune |
| re-run the full 353-pair job-3 sweep per discipline | NOT done | — | the 12-pair equivalence plus the per-search-process source is the proof; a 553-position × 2-discipline re-run would take hours past the deadline |

## Findings

`S-F9 | 6 | my published symmetry numbers are not a warm/cold artefact: on 12 mirror pairs, COLD (fresh process per search) and WARM (one process with `ucinewgame` before each search) give the IDENTICAL verdicts (bestmove mismatch 2/12, score mismatch 12/12), while the wrong discipline (nothing between searches) gives a different count (10/12), showing the confound is live and would have changed the number; and `eval` — which every one of my eval-based tables uses — is completely stateless (warm == fresh, byte for byte), so even my warmest table (5,853 pairs in ONE process) is unaffected | check_warmcold/raw_warmcold.txt (again: `python3 check_warmcold/warmcold_test.py ~/builds/bld-release/forge /tmp/o.txt`) | NEW |`

## Suspicions, not proven

- Whether `Clear Hash` giving a third value (40,569 in seat 10's test) also holds here. I did not test it,
  because the rule is to never use it, not to characterise it.

## What I did NOT do

- Did not re-run the 353-pair sweep under both disciplines (time); the 12-pair equivalence is decisive because
  the mechanism is per-process, not per-position.
- Did not test other seats' tables — only my own.

## What I am NOT sure about

- Whether a *deeper* search than depth 8 would show a COLD/WARM(`ucinewgame`) divergence. At depth 8 with 12
  pairs the counts agree exactly; `ucinewgame` clearing the TT is what makes that expected, but I did not
  verify at depth 12+.

## Times

`check_warmcold/stamps.txt`, every line a `date -u`.

## Last command output

```
$ git status --short
 M FINDINGS.md
?? REPORT_warmcold.md
?? check_warmcold/
$ ls
audit_19F12
check_06F12
check_20F14
check_28F1
check_fullwindow
check_S-F1
check_S-F2
check_S-F3
check_S-F5
check_warmcold
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
job1_seed1611
job2
job3
ownbook_check
REPORT_audit.md
REPORT_check_06F12.md
REPORT_check_20F14.md
REPORT_check_28F1.md
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_check_S-F3.md
REPORT_check_S-F5.md
REPORT_fullwindow.md
REPORT_job1.md
REPORT_job2.md
REPORT_job3.md
REPORT_ownbook_check.md
REPORT_wall_vs_iteration.md
REPORT_warmcold.md
SEAT.txt
STATUS.md
$ ls check_warmcold
last_cmd.txt
raw_warmcold.txt
run.log
stamps.txt
warmcold_test.py
```
