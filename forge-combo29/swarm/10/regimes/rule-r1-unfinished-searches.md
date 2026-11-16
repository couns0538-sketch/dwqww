# rule-r1-unfinished-searches.md

One page. Apply it to recorded engine output to find searches that were CUT OFF before they finished, which
is the silently-wrong-data case: the engine answers a real move with a wrong score and nothing says so.

## The rule

> **R1: a record is UNFINISHED if and only if its LAST `info depth <N>` has N less than the depth that was
> requested.**
>
> **Also UNFINISHED: a `bestmove` line with ZERO `info depth` lines.** (The search was interrupted before its
> first iteration; there is no score at all. The depth test cannot see this case.)

Both clauses are needed. Neither alone is sufficient.

## Use it

```bash
python3 forge-combo29/swarm/10/regimes/is_unfinished.py RECORDED_FILE --requested-depth 12
```

- Exit code **1** = at least one record looks unfinished; **0** = all look finished.
- `--quiet` prints only the summary line.
- Output per record: `record N: finished|UNFINISHED  <the reason>`.

**If the requested depth was not recorded** (old data, match files), use **R2** instead — no flag needed,
the checker falls back to it automatically:

> **R2: a record is UNFINISHED iff its last depth is LESS than the largest depth appearing anywhere in the
> same file at the same settings.**
>
> Requires the file to contain at least one completed search. If every search in the file was truncated the
> same way, R2 cannot fire and the data cannot be salvaged by this method.

## Evidence (why you can trust it)

112 recorded searches, 4 positions x 2 builds x 7 middle-band delays x 2 repetitions, depth 12 requested:

| | count | R1 caught | false alarms |
|---|---|---|---|
| genuinely truncated | **90** | **90 (all)** | — |
| byte-identical to a finished search | 19 | — | **0** |
| `bestmove` with no `info` line | 3 | flagged by the second clause | 0 |

The 19 records that reached depth 12 were **not truncations**: identical nodes, pv and score — the search
had already finished before the `quit` arrived. **There is no undetectable middle band**: every genuinely
short record ends below the requested depth.

## What does NOT work (measured, so nobody retries it)

| candidate signal | why it fails |
|---|---|
| "there is a `bestmove` line" | **109 of 112** interrupted records have one |
| "the pv is short" | a fail-low pv is legitimately short |
| "nodes are 0" | true only in the ≤20 ms regime, never in the middle band |
| "the score jumped" | there is no score at all in the ≤20 ms regime |

## The fault being detected, for context

If stdin closes (or `quit` arrives) while a search runs, the engine stops and prints a `bestmove` that is
**not** the finished answer:

| interruption | what you get | vs the truth |
|---|---|---|
| ≤ 25 ms | a legal move, **no score**, 0 `info` lines | can be a **losing move where mate was available** |
| middle band | a legal move with a **wrong score** | up to **53 cp** off, on a normal-looking move |
| ≥ 35–50 ms | identical to the finished search | — |

The boundary is **position-dependent** (30–50 ms measured), so **no fixed timeout is safe**: wait for
`bestmove` itself.

## The correction worth keeping

A report circulating in the swarm said a terminal root emits "**64 info lines**". That 64 is **the depth cap
the engine was asked for** (`go nodes 100` and `go movetime 50` both run to the cap on a terminal root), not
a constant of the fault. Measured: `go depth 5` emits **5** lines, `go depth 64` and `go depth 70` emit
**64** (clamped). **Never key a check on 64** — key it on the requested depth, which is exactly what R1 does.

## Files

- rule: this page
- checker: `forge-combo29/swarm/10/regimes/is_unfinished.py`
- evidence: `regimes/detect/detect.json`, `regimes/detect/CHECKER_RESULT.txt`, `regimes/detect/FALLBACK_RESULT.txt`
- repository scan: `regimes/scan/scan_repo.json` (8,672 records over 3,192 files; **0 unfinished in the
  repository's own data**; all 257 flags were in one of my own discarded harness runs, which the checker
  independently re-detected)
