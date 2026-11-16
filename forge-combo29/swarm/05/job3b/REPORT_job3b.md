# REPORT job3b — seat 05, area 5 — job 3 repeated on fresh root sets (seed 521)

## 1. the three lines

**What was asked.** Job 3 of my area, again, with the next seed and new positions (the brief's cycle step c):
10 checkmated and 10 stalemated roots under ASan + UBSan with `go depth 5`, `go nodes 100`, `go movetime 50`.

**The answer.** 60 of 60 runs answer `bestmove 0000`; checkmate roots score `mate 0`, stalemate roots `cp 0`, all
with `nodes 0`; 0 crashes, 0 hangs, 0 sanitizer output. **S-F7 reproduces on positions it was never found on**: both
`go nodes 100` and `go movetime 50` iterate to depth 64 instead of stopping at their limit, while `go depth 5` stops
at 5.

**How sure.** High — 7 of 7 predictions held, and the root sets are verifiably disjoint from the first job3 sets
(0 positions in common), so this is a genuine repeat and not a re-measurement of the same boards.

## 2. what differs from the first job3 run
| aspect | job3/ | this repeat |
|---|---|---|
| seed | 501 | **521** |
| roots | 10 + 10 generated at seed 501 | **10 + 10 generated at seed 521, 0 in common with the first set** |
| build | ASan+UBSan | same (`/tmp/build-asan/forge`) |
| result | 0000 / mate 0 / cp 0 / 0 nodes; S-F7 seen | **identical** |

## 3. predictions — all held
| # | predicted | actual | verdict |
|---|---|---|---|
| 1 | `bestmove 0000` in all 60 | `{bestmove 0000}` | HELD |
| 2 | checkmate `mate 0`, stalemate `cp 0` | exactly that | HELD |
| 3 | nodes 0 | `{0}` | HELD |
| 4 | `go depth 5` gives 5 info lines | `{5}` | HELD |
| 5 | `go nodes 100` and `go movetime 50` reach depth 64 (S-F7 repeats) | `{64}` both | HELD |
| 6 | 0 crashes / hangs / sanitizer lines | 0 / 0 / 0 | HELD |
| 7 | no overlap with the seed-501 roots | 0 in common | HELD |

## 4. the job, step by step
| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| fresh roots generated and ASSERTED | done | `make_roots3.py`, `positions/*_521.epd` | 20/20 pass `is_checkmate`/`is_stalemate`, 0 assertion failures |
| overlap control vs the first sets | done | `out_predictions.txt` (control printed above it) | **0 of 20 in common** |
| PREDICTION pushed alone before measuring | done | `PREDICTION.md` (commit `4ff92bd88`) | 7 predictions |
| 60 runs under ASan+UBSan | done | `out_asan_b/mate.raw.txt`, `out_asan_b/stale.raw.txt`, `out_asan_b/table.txt`, `out_asan_b/meta.txt` | 60/60, see §5 |
| predictions compared | done | `out_predictions.txt` | 7/7 HELD |

## 5. results
| root kind | go command | bestmove | score | nodes | info lines |
|---|---|---|---|---|---|
| checkmate | `go depth 5` | 0000 | mate 0 | 0 | 5 |
| checkmate | `go nodes 100` | 0000 | mate 0 | 0 | 64 |
| checkmate | `go movetime 50` | 0000 | mate 0 | 0 | 64 |
| stalemate | `go depth 5` | 0000 | cp 0 | 0 | 5 |
| stalemate | `go nodes 100` | 0000 | cp 0 | 0 | 64 |
| stalemate | `go movetime 50` | 0000 | cp 0 | 0 | 64 |

## 6. findings
No new finding id: this run **reproduces S-F7** on fresh positions, which is recorded in that finding's evidence
list rather than as a new one. The value of the run is that S-F7 is not a property of the specific seed-501 boards.

## 7. suspicions, NOT proven
Unchanged from `../job3/REPORT_job3.md`: no mechanism for S-F7 is claimed, and I still have not read the search loop.

## 7b. the sanitizer proof, now attached to THIS run's own files
`out_planted_b/` is this exact runner run against the scratch planted-fault build (`../job3/planted_fault.patch.txt`,
built in `/tmp` only), with the planted-fault FEN added as an extra position:

| proof | value, from `out_planted_b/meta.txt` |
|---|---|
| exe is instrumented | `nm_asan_symbols: 35`, `nm_ubsan_symbols: 15` |
| the runner counts a report when there is one | **9 sanitizer lines, 3 crashes** across the 3 planted probes |

versus the real build through the same runner: **0 sanitizer lines, 0 crashes** across 60 runs. So job3b's
"0 sanitizer output" is a shown result on this report's own evidence, not borrowed from `../job3/`.

## 8. what I did NOT do
- I did not re-derive anything about `go infinite` here (S-F8 stands as one observation).
- I did not test `go infinite` again (it hangs per S-F8; one observation stands, no rate claimed).
- I did not vary the go commands beyond the three the job names.

## 9. what I am NOT sure about
- Same as job3: whether S-F7 is a defect or an artefact of how iteration is reported at a terminal node.

## 10. times
See `stamps.txt`.

## 11. last command's output
```
$ git status --short
(clean at the commit that added this report)
$ ls
PREDICTION.md  make_roots3.py  out_asan_b  out_predictions.txt  positions  run_job3b.py  stamps.txt
$ ls out_asan_b | tr '\n' ' '
mate.raw.txt meta.txt stale.raw.txt table.txt
```
