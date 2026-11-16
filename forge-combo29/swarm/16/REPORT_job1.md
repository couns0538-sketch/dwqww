# REPORT_job1 — area 6 (SYMMETRY), seat 16

**What was asked:** the static evaluation of every G position (353) and 500 R positions, each compared with
its colour-flipped mirror; list every difference with its FEN; then read the evaluation code and name the
term with file and line; control = a position against itself.

**The answer:** the static evaluation is colour-symmetric on all 853 positions — `hce`, `nnue` and `total`
were bit-identical against python-chess `board.mirror()`. Zero differences, so there is no term to name.
The self-control shows 0 differences, which alone would not prove the harness can see a difference at
all; that is why the forced-asymmetry control below matters.

**How sure:** high that 6b98f217's static eval is colour-symmetric on these 853 positions; NOT a proof
for all positions (see "what I did NOT do"). Confident in the harness: `positive_control.py` shows it
reports all three fields as different when it is fed a wrong (non-mirror) second position, so
"0 differences" is not a blind result.

## Honesty numbers (build used for every number here)

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id name Chess Engine Forge 6.4.24 candidate
bench 11 -> 312866   bench 13 -> 862329   bench 16 -> 3024920   go perft 5 -> 4865609   (all equal)
```

## The `eval` command

`eval` prints one line: `info string eval hce <n> nnue <n> total <n>` and nothing else. All three numbers
were compared; equality was required for something to count as symmetric.

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 353 G positions, static eval vs colour mirror | done | `raw/G.tsv`, `raw/G.meta`, `raw/G.summary` | 353 rows, 0 differences in hce/nnue/total |
| 500 R positions (seed 1601, one position every 7 plies) | done | `raw/R.tsv`, `raw/R.meta`, `raw/R.summary`, `set_R_seed1601.fens` | 500 rows, 0 differences |
| control: a position against itself | done | `raw/ctrl.tsv`, `raw/ctrl.meta` | 2 rows (G[0] twice), 0 differences |
| control: startpos vs its mirror | done | `raw/startpos.tsv`, `raw/startpos.meta` | equal: hce 18 nnue 20 total 38 both sides |
| positive control A: three true mirror pairs | done | `positive_control.txt` | 0 differences (Q/Q, P/p, R/r all equal) |
| positive control B: forced asymmetry | done | `positive_control.txt` | harness reports hce/nnue/total all different (825 vs 685) |
| read the eval code, name the asymmetric term | not done — not required | — | no difference existed to explain |
| "the evaluation is `eval`-only symmetric, not search" | not done, out of this job | — | job 3 covers the search at depth 10 |

Totals: 853 positions compared, 853 identical, 0 differ. Distinct `hce` values across the run: 690
(the numbers genuinely vary, so a constant answer is not being read). `total` range −3626 … 3763.

## Findings

**None new.** The result is a negative one (no asymmetry found), which is not a finding.

## Suspicions, not proven

- NNUE and HCE both being exactly symmetric is consistent with a net trained on mirrored data and with
  hand-written terms that use only colour-relative piece-square tables, but I did not read that far.
- One asymmetry class is out of this job's reach: positions where the *side to move* matters to a term
  that is not colour-flipped (e.g. a tempo bonus must flip sign with the side to move). A tempo term that
  does not flip would still compare equal when both sides are mirrored AND the side to move flips with
  the board, which is exactly what `mirror()` does — so this comparison cannot see a non-flipping tempo
  term that is constant. Not proven either way.

## What I did NOT do

- Did not test every reachable position (853 of ~10^44); a rare configuration could still be asymmetric.
- Did not test left-right (horizontal) mirror — that is job 2 of this area.
- Did not test depth-10 search equality — job 3.
- Did not set a random seed on the engine; the engine uses no randomness in `eval` (the option list has
  `DrawJitter` default 0, and `eval` is a static call).

## What I am NOT sure about

- Whether `eval` returns the *search* evaluation at a node (it prints hce, nnue and total separately, so it
  is the static pair), and whether `total` is the number the search actually uses — I did not read the code
  to confirm that `total` is the leaf value the search adds its corrections to.
- Whether positions with an en-passant square that python-chess keeps but the engine ignores could differ;
  the R set almost never has one, and G has few. A targeted ep set would settle it.

## Times

See `stamps.txt` (each line is a `date -u`).

## Last command output

```
$ git status --short
?? REPORT_job1.md
?? job1/__pycache__/
?? job1/analyse.py
?? job1/ctrl_same_twice.epd
?? job1/last_cmd.txt
?? job1/mirror_eval.py
?? job1/positive_control.py
?? job1/positive_control.txt
?? job1/raw/
?? job1/run_job1.log
?? job1/run_job1.sh
?? job1/stamps.txt
$ ls
honesty.sh
HONESTY.txt
job0_honesty
job1
REPORT_job1.md
SEAT.txt
STATUS.md
$ ls job1
analyse.py
ctrl_same_twice.epd
gen_R.py
last_cmd.txt
mirror_eval.py
positive_control.py
positive_control.txt
prediction.txt
__pycache__
raw
run_job1.log
run_job1.sh
set_G.epd
set_R_seed1601.fens
stamps.txt
$ ls job1/raw
analysis.txt
ctrl.meta
ctrl.summary
ctrl.tsv
G.meta
G.summary
G.tsv
R.meta
R.summary
R.tsv
startpos.meta
startpos.tsv
```

