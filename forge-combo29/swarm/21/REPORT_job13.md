# REPORT job13 — CHECK of 24-F1 (TSan on Threads/Hash churn), seat 21

**What was asked.** THE CYCLE 2(a): reproduce an unchecked finding from another seat with my
own harness. 24-F1 (seat 24, area 4) was unchecked by anyone.

**The answer.** **CONFIRMS 24-F1.** With my own ThreadSanitizer build of 6b98f217 (21 `__tsan_`
symbols, TSAN_OPTIONS cleared before spawn) and my own 300-round churn sequence from SEED 2101
(Threads 1/2/4/8/16 × Hash 1/4/16/64/256, 122 of 300 followed by `ucinewgame`), the real build
gives **0 TSan reports, 0 crashes, 0 illegal bestmoves, 0 missing bestmoves**. My planted race
— an unlocked global counter written by every worker thread on every `total_nodes()` call — is
counted at **12 report blocks in 12 rounds** by the SAME runner, so the zero is a shown zero.

**How sure.** High. Both 19-F12 and the integrity rule are honoured: each `go depth 8` is read
to `bestmove` before the next command, stdin is never closed mid-search, and the runner records
the `__tsan_` symbol count and a sha256 for each binary. The plant is a real data race in code
any multi-threaded search executes, not a synthetic print.

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `job13/prediction.txt` | 6 predictions, all held |
| TSan build of 6b98f217 | done | `~/b/tsan`, `job13/out/*_summary.txt` (`nm___tsan_: 21`) | instrumented |
| planted-race copy, built the same way | done | `~/b/tsan_planted`, `job13/out/planted_summary.txt` | 12/12 rounds reported |
| real 300-round churn | done | `job13/out/real_raw.txt`, `real_summary.txt` | 0 reports |
| legal bestmove check per round | done | same | 0 illegal |

## Table (pasted from `job13/out/real_summary.txt` and `planted_summary.txt`)

| measure | real build | planted-race build |
|---|---|---|
| `__tsan_` symbols | 21 | 21 |
| rounds | 300 | 12 |
| `ucinewgame` rounds | 122 | 4 |
| Threads changes / Hash changes | 300 / 300 | 12 / 12 |
| TSan report blocks | **0** | **12** |
| crashes | 0 | 0 |
| illegal bestmoves | 0 | 0 |
| missing bestmoves | 0 | 0 |

## Prediction outcome

All 6 held. P5 said "at least 100 of 300 followed by ucinewgame" and the run gave 122, close to
the claim's 131/300 — the mix matches.

## Findings

`21-C5 | CONFIRMS 24-F1` — added to FINDINGS.md.

## Suspicions, not proven

- 24-F1 says its plant is "counted at 9 report blocks"; mine reports 12 in 12 rounds, i.e. one
  per round. The number of blocks depends on how the plant is written, so the two are not
  comparable; what matters is that both are non-zero.
- My churn sends `position startpos moves e2e4 e7e5 g1f3` before each search, so the searches
  are short (depth 8 from a 3-ply game). A race that only manifests in a long multi-threaded
  search would not show here. I did not vary the search length.

## What I did NOT do

- Did not test Threads changes DURING a search (that is a different claim, and 24-F1 is about
  changes between searches).
- Did not run with `Hash 1` and `Threads 16` repeated to exhaustion; the mix is random.
- Did not attempt to reproduce seat 24's exact "9 report blocks" figure.

## What I am NOT sure about

- Whether TSan's default `halt_on_error=0` let the real run continue past a report it did not
  print. TSan always prints before continuing, so 0 printed blocks means 0 detected races; but
  I did not set `TSAN_OPTIONS=halt_on_error=1` to force an abort on the first one.

## Times

see `job13/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job13
churn_tsan.py  out  prediction.txt  real.log  stamps.txt
```
