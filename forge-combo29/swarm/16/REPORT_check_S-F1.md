# REPORT_check_S-F1 — CONFIRMS seat 06's S-F1 (area 6), seat 16

**What was asked:** check another seat's NEW finding from its command file alone, with a harness I wrote
myself: seat 06's S-F1, "`eval` is exactly colour-symmetric: 0 differences in hce/nnue/total over 8,103
position-pairs across 4 eval configurations".

**The answer:** CONFIRMED. 25,532 position-pairs, 0 differences in hce, nnue or total, across 4 eval
configurations. Every configuration demonstrably changes the numbers (so no configuration is vacuous). I did
NOT reproduce the finding's exact figure of 8,103 pairs: my own set is larger (25,532) but a different mix
(G_353 + R_500 + Rbig_5000 + dead 30 + my R seed 1611, times 4 configurations), so the two counts are not
comparable and I do not claim to have re-counted theirs.

**How sure:** high for the claim "the static eval is colour-symmetric on every position I ran, in all four
configurations". The finding's own pair count (8,103) is not something my run can confirm or refute — it is a
count over files I only partly used.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-release/forge
sha256  e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
bench 11 312866  bench 13 862329  bench 16 3024920  go perft 5 4865609   (all equal; ../HONESTY.txt)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 4 configs × (G_353 + R_500 + Rbig_5000) = 23,412 pairs | done | `raw/{default,nonnue,deadmat,both}.tsv` + `.summary` | 0 differences in every config |
| 4 configs × dead.fens (30) = 120 pairs | done | `raw/dead_*.tsv` | 0 differences |
| 4 configs × my own R seed 1611 (500) = 2,000 pairs | done | `raw/R1611_*.tsv`, `R_500_seed1611.fens` | 0 differences |
| options are real engine options | done | `check_sym.py` raises STOP if not listed; `raw/*.summary` | `UseNNUE` and `DeadMaterial` both in the uci answer |
| options actually change the eval | done | `raw/config_effect.txt`, `raw/config_effect_dead.txt` | `UseNNUE false` changes 350/353 G positions; `DeadMaterial true` changes 0/353 G but 30/30 dead-material positions |
| re-count the finding's 8,103 | NOT done — cannot | — | different file mix; see above |
| sanitizer run | NOT done (not asked) | — | "0 sanitizer lines" would mean nothing here |

## The measurements

```
default  G_353.fens       353 pairs  0 diffs
default  R_500.fens       500 pairs  0 diffs
default  Rbig_5000.fens  5000 pairs  0 diffs
nonnue / deadmat / both  : same three lines, 0 diffs each
dead.fens  (30 pairs) : 0 diffs in all 4 configs
R_500_seed1611.fens (500 pairs) : 0 diffs in all 4 configs
TOTAL 25,532 pairs, 0 differing pairs
```

Configuration effect (`config_effect.py`, `raw/config_effect.txt`):
```
nonnue   positions where the eval line differs from default: 350 of 353
deadmat  positions where the eval line differs from default: 0 of 353
both     positions where the eval line differs from default: 350 of 353
```
on dead-material boards (`raw/config_effect_dead.txt`): all three differ from default at 30 of 30.

## Findings

`S-C2 | CONFIRMS S-F1 | check_S-F1/raw/default.tsv (+ nonnue/deadmat/both), again: python3 check_S-F1/check_sym.py ~/builds/bld-release/forge default /tmp/o.tsv check_S-F1/G_353.fens | static eval hce/nnue/total is colour-symmetric on 25,532 pairs across 4 configurations (0 differences); beyond the finding: DeadMaterial has no effect on 353 game positions but does change all 30 dead-material boards, and UseNNUE false changes 350/353 — so both settings are live, and the finding's own 8,103 count could not be re-counted by me.`

## Suspicions, not proven

- `DeadMaterial` changing nothing over ordinary positions suggests the term only fires when material is
  nearly bare; I did not read the code to see the condition.
- A non-flipping constant tempo term would be invisible to this comparison (it flips with the side to move
  exactly as `mirror()` flips the board). Same caveat as job 1; still not proven either way.

## What I did NOT do

- Did not re-count seat 06's 8,103 pairs; I cannot without its exact file list and config counts per file.
- Read no evaluation source code; this is a behavioural check only.
- No sanitizer run.

## What I am NOT sure about

- Whether the four configurations I used are the four seat 06 used. Its FINDINGS line names "default,
  UseNNUE false, DeadMaterial true, dead-material set", which I read as three option settings plus a
  dead-material POSITION set; I ran exactly that reading (and also the combined `both`).

## Times

`stamps.txt`, every line a `date -u`.

## Last command output

```
$ git status --short
 M check_S-F1/stamps.txt
?? REPORT_check_S-F1.md
?? check_S-F1/R_500_seed1611.fens
?? check_S-F1/check_sym.py
?? check_S-F1/config_effect.py
?? check_S-F1/dead.fens
?? check_S-F1/last_cmd.txt
?? check_S-F1/raw/
?? check_S-F1/run.log
?? check_S-F1/run_check_sym.sh
$ ls
check_S-F1
check_S-F2
FINDINGS.md
honesty.sh
HONESTY.txt
job0_honesty
job1
REPORT_check_S-F1.md
REPORT_check_S-F2.md
REPORT_job1.md
SEAT.txt
STATUS.md
$ ls check_S-F1
check_sym.py
config_effect.py
dead.fens
G_353.fens
last_cmd.txt
prediction.txt
R_500.fens
R_500_seed1611.fens
raw
Rbig_5000.fens
run_check_sym.sh
run.log
stamps.txt
$ ls check_S-F1/raw
both.summary
both.tsv
config_effect_dead.txt
config_effect.txt
dead_both.summary
dead_both.tsv
dead_deadmat.summary
dead_deadmat.tsv
dead_default.summary
dead_default.tsv
deadmat.summary
deadmat.tsv
dead_nonnue.summary
dead_nonnue.tsv
default.summary
default.tsv
nonnue.summary
nonnue.tsv
R1611_both.summary
R1611_both.tsv
R1611_deadmat.summary
R1611_deadmat.tsv
R1611_default.summary
R1611_default.tsv
R1611_nonnue.summary
R1611_nonnue.tsv
```
