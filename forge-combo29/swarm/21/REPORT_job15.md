# REPORT job15 — area 1 job 2, THIRD pass (SEED 2121 run), seat 21

**What was asked.** A third pass over the extreme-FEN-field cases. The case list is fixed by
the job's definition, so unlike job7 and job14 there is no new input set to build: what this
run adds is a repeat of the whole measurement with the current safe driver and, in the same
job folder, the mate-at-100 control re-run beside it.

**The answer.** Identical to job3 and job8. Every halfmove value ≥ 100 (100, 150, 9999, 2^31,
65535, 65536, and five seed-drawn values up to 161,959) answers `score cp 0 nodes 0`; a mate
in 1 at counter 100 is missed by `go depth 5`, `go nodes 100` and `go movetime 50` while the
same board at 99 finds it by all three; no accepted FEN disagreed with python-chess; no case
was missing a `nodes` line; 0 crashes.

**How sure.** High, and this is the third time the same numbers came out, which is the point.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job15/prediction.txt` | 6 predictions |
| extreme-field cases | done | `job15/out/summary.md` (extreme_safe) | 29 cases, 0 perft mismatches |
| mate-at-100 control, re-run | done | `job15/out/summary.md` (mate100) | 6/6 missed at 100, 6/6 found at 99 |
| `nodes` line asserted present | done | both scripts | never fired |

## Key figures (pasted from `job15/out/summary.md`)

```
accepted-but-wrong-perft: none
searches that answered with 0 nodes: ['hm_100', 'hm_150', 'hm_9999', 'hm_2147483648',
 'hm_65535', 'hm_65536', 'hm_91102', 'hm_128221', 'hm_98147', 'hm_119640', 'hm_161959',
 'hm100_mate_in_1', 'hm100_black_mate_in_1']
cases where a `nodes` line was MISSING (would be a parser failure): none
```

| case | mate | go depth 5 | go nodes 100 | go movetime 50 |
|---|---|---|---|---|
| black_mate hm100 | a8a1 | f7f6 missed | f7f6 missed | f7f6 missed |
| black_mate hm99 | a8a1 | a8a1 FOUND | a8a1 FOUND | a8a1 FOUND |

## Prediction outcome

P1–P6 all held.

## Findings

No new finding; this is the third reproduction of 21-F9's behaviour. Three independent runs
of the same measurement agreeing is what makes 21-F9 safe to act on.

## Suspicions, not proven

- `extreme_safe.py` still contains the illegal black-side FEN from job8
  (`6k1/5ppp/8/8/8/8/5PPP/4r1K1 b`), which Forge refuses. Its row in this run is therefore a
  stale-board answer, not a statement about that position. The legal board in `mate100.py`
  (`r5k1/5ppp/8/8/8/8/5PPP/6K1 b`) is the one the conclusion rests on. I have left the bad
  case in place and flagged it rather than quietly deleting evidence.

## What I did NOT do

- Did not add new extreme case kinds; this is a repeat, not an extension.

## What I am NOT sure about

- Whether a fourth pass adds anything. Three is enough for a stable picture; more runs of the
  same measurement are waste the owner is paying for.

## Times

see `job15/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job15
out  prediction.txt  stamps.txt
```
