# REPORT job3 — seat 05, area 5 (PRINCIPAL VARIATIONS AND SCORES)

## 1. the three lines

**What was asked.** Checkmated and stalemated root positions, 10 of each, under ASan + UBSan, with `go depth 5`,
`go nodes 100` and `go movetime 50`: the exact answer lines.

**The answer.** 60 runs (10 checkmate roots × 3 commands + 10 stalemate roots × 3), **0 crashes, 0 hangs,
0 sanitizer lines**. Every run answers `bestmove 0000`. The scores are `mate 0` at all 30 checkmate runs and
`cp 0` at all 30 stalemate runs, always with `nodes 0`. Two anomalies in the *depth reporting*: `go nodes 100` and
`go movetime 50` both run to **depth 64** instead of stopping at their limit, and `go infinite` at a terminal root
**never returns** a bestmove at all (I had to kill it; that run is not counted above).

**How sure.** High on the sanitizer result — both proofs the brief demands are in place (§4). High on the exact
answer lines (they are the literal raw output, in `out_asan/*.raw.txt`). The `go infinite` hang I observed directly
but only once per position, so I state it as an observation, not a rate.

## 2. honesty numbers

`../HONESTY.txt` 4/4 (312866 / 862329 / 3024920 / 4865609), **re-verified** after seat 19's harness warning with a
read-to-terminator harness (`../audit19f12/out/recheck.txt`, 4/4 OK).

## 3. the job, step by step

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 10 checkmate roots and 10 stalemate roots, each ASSERTED with python-chess | done | `make_roots2.py`, `out_roots_verify.txt`, `positions/*.epd` | 10/10 and 10/10 verified (`is_checkmate` / `is_stalemate` printed per position) |
| first attempt at roots by hand | **failed, discarded** | `make_roots.py`, `out_roots_verify.txt` (first block) | only 4/10 and 6/10 of my hand-typed FENs were what I claimed; I generated and asserted them instead |
| ASan + UBSan build of 6b98f217 | done | `/tmp/build-asan`, meta in `out_asan/meta.txt` | 35 `__asan_` and 15 `__ubsan_` symbols in the exe |
| **sanitizer proof 1**: instrumented exe | done | `out_asan/meta.txt` | `nm -C | grep -c __asan_` = 35, `__ubsan_` = 15 |
| **sanitizer proof 2**: one planted fault counted by the same runner | done | `planted_fault.patch.txt`, `out_planted/meta.txt`, `out_planted/table.txt` | heap over-read (read one past a `new int[4]`) behind a FEN ending `777 1`; **3 sanitizer lines per run** through the same runner |
| 60 runs, `go depth 5` / `go nodes 100` / `go movetime 50` | done | `out_asan/mate.raw.txt`, `out_asan/stale.raw.txt`, `out_asan/table.txt` | 60/60 with a bestmove, 0 crashes, 0 hangs, 0 sanitizer lines |
| exact answer lines tabulated | done | `run_job3.py`, `out_asan/table.txt`, `out_answer_summary.txt` | see §5 |
| depth/limit behaviour probed | partly | `terminal_root_probe.py`, `out_terminal_probe.txt` | `go nodes 100` and `go movetime 50` run to depth 64; `go infinite` never returned |
| harness audited against seat 19's 19-F12 | done | `../audit19f12/RESULT.md` | this runner reads to `bestmove` before quitting — clean |

## 4. the two sanitizer proofs (both required by the brief)

1. **The exe really is instrumented.** `out_asan/meta.txt` records `nm_asan_symbols: 35` and
   `nm_ubsan_symbols: 15` for the exact exe sha256 that ran.
2. **The runner really can report.** I built a scratch copy with ONE planted fault — in `apply_position`, when the
   FEN ends in `777 1`, read `probe[4]` from a `new int[4]` — as a text patch (`planted_fault.patch.txt`), built it
   with the same sanitizer flags in `/tmp` (never in the repository), and ran it through **the same runner**.

| build | sanitizer lines counted by the runner |
|---|---|
| planted-fault build | **3 lines per planted-fault run** (ASan `heap-buffer-overflow` / `READ of size 4`), all three probes |
| real build | 0 lines, all 60 runs |

So "0 sanitizer lines" is a shown result, not an unshown one.

## 5. exact answer lines

From `out_asan/*.raw.txt` (`out_answer_summary.txt` is the generated table):

| root kind | go command | info lines per run | bestmove | depth reached | score | nodes |
|---|---|---|---|---|---|---|
| checkmate | `go depth 5` | 5 | `bestmove 0000` | 1..5 | `mate 0` | 0 |
| checkmate | `go nodes 100` | 64 | `bestmove 0000` | 1..64 | `mate 0` | 0 |
| checkmate | `go movetime 50` | 64 | `bestmove 0000` | 1..64 | `mate 0` | 0 |
| stalemate | `go depth 5` | 5 | `bestmove 0000` | 1..5 | `cp 0` | 0 |
| stalemate | `go nodes 100` | 64 | `bestmove 0000` | 1..64 | `cp 0` | 0 |
| stalemate | `go movetime 50` | 64 | `bestmove 0000` | 1..64 | `cp 0` | 0 |

A representative block, verbatim:

```
info depth 5 seldepth 5 score mate 0 nodes 0 nps 0 hashfull 0 time 0 pv
bestmove 0000
```

## 6. findings

### S-F7 — `go nodes 100` and `go movetime 50` iterate to depth 64 at a terminal root instead of stopping
At a checkmated or stalemated root the engine emits one `info` line per depth and keeps going to **depth 64** for
both a node limit and a wall-clock limit, instead of stopping at the limit. `go depth 5` correctly stops at 5.
Reproduce:

```
python3 terminal_root_probe.py /tmp/build-rel/forge "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1" "go nodes 100"
python3 terminal_root_probe.py /tmp/build-rel/forge "8/8/8/8/8/6K1/8/Q5k1 b - - 0 1" "go movetime 50"
```

This is cosmetic for a terminal root (the answer is `0000` either way) but it is wrong limit accounting, and I note
it rather than file it as a search fault.

### S-F8 — `go infinite` at a terminal root does not answer
`go infinite` on the same board produced no `bestmove` within 25 s and had to be killed; every bounded command
answered in 0.02–0.03 s. Recorded as an observation from one position; I did not repeat it per position because a
hanging probe costs a full timeout each time.

## 7. suspicions, NOT proven
- **Whether the depth-64 iteration is a real loop or just the reported depth counter.** The node count stays 0 and
  the wall time is 0.02–0.03 s, so nothing is being searched; it may be that the depth counter simply advances
  because the terminal root returns instantly and the time manager never sees a node. I did not read the loop.
- **Whether `go infinite` also hangs at NON-terminal roots.** Seat 01's S-F5 and my own job2 show the engine has
  short-circuit paths at dead roots; `go infinite` may be hitting one of those. Not tested.
- **Whether `bestmove 0000` here is computed or fabricated.** Seat 19's 19-F12 says a quit during a search can
  fabricate a bestmove; my runner reads to `bestmove` before quitting, but at a terminal root the bestmove may be
  emitted before any search. It does not affect my claims (which are about sanitizer silence), and I do not cite
  job3 for the value of the move.

## 8. what I did NOT do
- I did not run job3 under TSan (that is area 4's tool); only ASan + UBSan as the job says.
- I did not test `go infinite` more than once per root, and I have no count of how often it hangs.
- I did not investigate what the engine does with `ponder`, `stop` or `ponderhit` at a terminal root.
- The 20 roots are all K+Q versus K (plus a black pawn in the stalemate set); I did not include mates delivered by
  minor pieces, by en passant, or by promotion.

## 9. what I am NOT sure about
- Whether the depth-64 behaviour is a defect or an artefact of how the engine reports iteration at a terminal node.
  Without reading the loop I cannot tell, and I did not read it.
- Whether a real GUI would ever send `go nodes`/`go movetime` at a terminal root (it should not need to), so the
  practical weight of S-F7/S-F8 is unclear to me.

## 10. times
See `stamps.txt`.

## 11. last command's output

```
$ git status --short
(clean at the commit that added this report)
$ ls
PREDICTION.md (none for job3 — this job is measurement, not a hypothesis test)
make_roots.py  make_roots2.py  out_roots_verify.txt  out_answer_summary.txt  out_terminal_probe.txt
plant_fault_inspect.py  planted_fault.patch.txt  positions  run_job3.py  stamps.txt
terminal_root_probe.py  out_asan  out_planted
```
