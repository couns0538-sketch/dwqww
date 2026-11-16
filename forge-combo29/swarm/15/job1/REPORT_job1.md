# REPORT job 1 — seat 15, area 5 (principal variations and scores)

**What was asked.** Every search of a rows run on O and G at depth 12 with S14: play the LAST
`info ... pv` line with python-chess and check that every move is legal; for a `mate N` score,
check that the PV ends in checkmate after 2N-1 plies (N>0) or 2|N| plies (N<0); and prove the
checker catches a planted illegal last move.

**The answer.** Across 553 positions (200 of O + 353 of G) at depth 12, S14, Threads 1, Hash 16:

| what | count |
|---|---|
| positions accepted by the engine | 553 / 553 |
| illegal moves in the last PV line | **0** |
| `bestmove` disagreeing with the PV's first move | **0** |
| positions with no `info ... pv` line at all | **0** |
| positions carrying a `mate N` score | 10 |
| of those, PV length obeying the brief's rule | 9 |
| of those, **violating** the rule | **1** (idx 392) |
| planted-illegal-last-move control caught | 5 / 5 |

So the PV moves themselves are sound; the defect is in the **mate distance** on one position,
and there it is not marginal — it is wrong by 8 moves and is reproducible.

**How sure.** High for the counts (a committed script over committed raw files, and the harness
reproduces the brief's known node sums exactly). High for 15-F1: two independent mate solvers
that share no code path (a full AND/OR tree with no pruning, and an alpha-beta mate solver) both
return the same true distance, and the engine's own later iterations move toward it.

## Honesty numbers of the build used for every number below

```
exe_started: /home/ubuntu/builds/rel/forge
sha256: e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83
id_name: Chess Engine Forge 6.4.24 candidate
options_sent: MultiPV 1, Threads 1, Hash 16, and the 14 S14 options
host: Linux 6.12.113+ x86_64, 4 cores
```

bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four exact.
See `HONESTY.txt`.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| Harness written, run from its file | done | `pvrun.py` | one process, reads stdout until `bestmove` before the next command |
| Fidelity of the harness proven | done | `evidence/nodesum_check.txt` | O sum 9,500,069 exact; G sum 18,466,239 exact; first three O 41311/24872/28574 exact |
| O and G collected, FEN form fixed | done | `O_first200.fens`, `G_set.epd`, `OG_combined.fens` | G is EPD (4 fields); converted by appending `0 1`, which the engine accepts |
| 553 searches at depth 12 | done | `raw_d12/pv.jsonl`, `raw_d12/raw/0000..0552.txt` | 16.8 s total |
| PV legality check | done | `analyze_d12.txt` | 0 illegal |
| bestmove ↔ PV-first check | done | `analyze_d12.txt` | 0 disagreements |
| mate-score PV-length rule | done | `evidence/mate392/pvlen_rule.txt` | 9 ok, 1 violation (idx 392) |
| control: planted illegal last move | done | `analyze_d12.txt` (`CONTROL` line) | 5 tried, 5 caught |
| true mate distance for the violation | done | `evidence/mate392/truncation_test.txt`, `mates_truth.txt` | truth mate in 8 plies, engine says mate -12 |
| is it PV truncation alone? | done | `evidence/mate392/truncation_test.txt` | no — the printed line reaches mate in 22 plies, not 24, and the score is 16 plies pessimistic |
| which option triggers it | done, in part | `evidence/mate392/bisect_s14.txt` | one option alone (`NullMoveBase=5`) already produces a wrong mate score; full S14 is worse; see below |
| harness audit after 19-F12 | done | `evidence/harness_audit/audit.txt` | no result of mine is fabricated; `probe.sh` replaced by `probe2.py` |

## Findings

### 15-F1 — mate distance wrong by 8 moves, and the PV does not reach mate (NEW)

```bash
cd forge-combo29/swarm/15/job1
python3 probe2.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 12 --opts s14 | grep -E "^info depth 12 |^bestmove"
```

```
info depth 12 seldepth 27 score mate -12 nodes 19197 nps 2742428 hashfull 4 time 7 pv c2c3 d2d1q c3b2 e4e3 b2a2 d1c2 a2a1 c2c1 a1a2 c1c4 a2b2 c4d4 b2c1 d4a1 c1c2 a1d1 c2b2 e2d3
bestmove c2c3
```

The position is white to move, white is lost. The engine claims mate -12, i.e. mated in 12 moves
= 24 plies. The printed PV is 18 plies and the position after it,
`8/8/1p6/8/p7/3kp3/1K6/3q4 w - - 14 10`, is still **4 plies** from mate (both solvers agree), so
the line it printed reaches mate at 22 plies — short of its own claim.

Truth, from two solvers that share no code:

```bash
python3 matedbf.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 12   # full AND/OR tree, no pruning
python3 solvemate2.py '8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1' 10  # alpha-beta mate solver
```

```
MATED_IN_PLIES 8
MATED_IN_PLIES 8
```

so the correct score is `mate -4`, and the engine reports `mate -12`: **8 moves too pessimistic**.

It is not a transposition-table artefact: Hash 16, 512 and 2048 all give the identical node count
19197 and the identical score. It is not a truncation artefact of the PV printing either — a
short PV cannot make the *value* more pessimistic than the value of the line it printed.

The score is also not stable across iterations in a way that suggests a clean deepening: at depth
12 and 13 it says -12, then -9, -6, -5, -4 as depth grows (each depth recomputing from a fresh
search), i.e. the reported distance at a fixed depth is a function of what the search happened to
see, not of the position.

### 15-F2 — 9 of 10 mate scores obey the rule; one does not (NEW)

See `evidence/mate392/pvlen_rule.txt` for the full table and `mates_truth.txt` for the solver
verdict on each of the ten. The other nine end in checkmate at exactly the plies the rule wants,
so the PV printer and the mate-score convention are correct in general; 15-F1 is the exception,
not a systematic convention mismatch.

Note the nine that "obey the rule" are not all *correct*: idx 259 scores `mate +4` and its PV does
end at 7 plies as the rule asks, but the position is mate in **5** plies — the rule tests
self-consistency of score and PV, not agreement with the truth. Only 392 breaks self-consistency.
That distinction matters: a checker based on the rule alone would pass idx 259. (This is the
`mates_truth.txt` line "259 … MATE_IN_PLIES 5" versus "engine mate +4".) I record it under
"suspicions" rather than as a finding, since the depth-12 search is entitled to be pessimistic
about distance — but it does mean the rule is weaker than it looks.

### Harness audit (response to seat 19's 19-F12)

I reproduced 19-F12 and confirm it; it is not mine to claim:
`(echo uci; echo isready; echo "position startpos"; echo "go depth 12"; echo quit) | forge` gives
`bestmove a2a3` with no info lines, while the same search read to `bestmove` gives `e2e4` at
56,720 nodes. Every result in this report comes from `pvrun.py`/`probe2.py`, which keep stdin open
and read stdout until `bestmove`; the audit found 0 `bestmove a2a3`, 0 zero-node info lines and 0
records without an info line in all 553. The one helper that used the risky `sleep; echo quit`
pattern (`probe.sh`) is superseded by `probe2.py`, and every number it produced that appears here
was re-run under `probe2.py`.

## Suspicions, not proven

- idx 259 reports `mate +4` where the truth is mate in 5 plies (`mate +3`). Consistent with a
  depth-limited search, but I did not show it is *right* to report +4 at depth 12, nor that the
  engine's own move is the fastest mate. Not a finding.
- `NullMoveBase=5` on its own produced `mate -9` where defaults give `mate -7` and truth is `-4`
  (`bisect_s14.txt`). Null-move pruning is the obvious suspect for a mate score that is too
  pessimistic, but a single option-value comparison at one depth on one position is not evidence
  of mechanism. Recorded as a lead, not a finding.

## What I did NOT do

- Did not run job 2 (draw scores) or job 3 (checkmated/stalemated roots under ASan+UBSan) yet.
- Did not build or run a sanitizer build for job 1; job 1 does not ask for one.
- Did not determine the code path that causes 15-F1 (area 7 territory), only its behaviour.
- Did not check whether 15-F1 reproduces at other depths with the same *node count* — only with
  the same score and PV at depth 12/13.
- Did not test other positions in the same endgame family, so I cannot say how common this is.

## What I am NOT sure about

- Whether the root cause is the mate-score adjustment at a null-move or LMR node, or a
  transposition-table mate-score entry stored without the ply adjustment. Both would produce a
  distance wrong by whole moves; I have no evidence separating them.
- Whether the engine's *move choice* is affected here. On this position the true longest defence
  and the engine's choice may coincide; I started that comparison and the brute-force search was
  too slow to finish inside one command, so I make no claim about it.

## Times

See `stamps.txt` — every line there is a pasted `date -u`.

## Last command's output

```
$ ls
analyze_d12.txt
analyze.py
bisect_s14.py
evidence
G_set.epd
matebf.py
matecheck.py
matedbf.py
mates_d12.txt
mates_parsed.txt
mates_truth.txt
O_first200.fens
OG_combined.fens
prediction.txt
probe2.py
probe.sh
pvrun.py
raw_d12
REPORT_job1.md
run_d12.log
solvemate2.py
solvemate.py
stamps.txt
verify_mates.sh
```


`evidence/mate392/` holds `s14_depth12.txt`, `truncation_test.txt`, `bisect_s14.txt`,
`verify_safe.txt`, `pvlen_rule.txt`; `evidence/harness_audit/audit.txt`;
`evidence/nodesum_check.txt`. `raw/` is a scratch dir from an early smoke test, `raw_d12/`
holds the 553 real transcripts plus `pv.jsonl` and `meta.txt`.
