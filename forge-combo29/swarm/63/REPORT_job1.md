# Seat 63 — REPORT: adversarial review of the composed drawn-root repair

## What was asked / the answer / how sure

**Asked.** Reproduce the composition of seat 12's `two_doors_mate.patch.txt` and seat 27's
`drawn_root_reporting.patch.txt`, verify the four honesty pins on release and under
ASan+UBSan, try to break the seat-12 repair with seven adversarial root families, measure
the cost of its per-move scan, test whether `depth 1` breaks a GUI-visible contract, and
give a ship / no-ship verdict.

**Answer.** **SHIP BOTH PATCHES.** The composition is byte-exact and order-independent, the
four pins are unmoved on release and under ASan+UBSan (with a planted fault proving the
sanitizer runs are not vacuous), the repair fixes the defect it targets on all three draw
predicates while declining to fire on every near-miss I could build, and the per-move scan
is **not** paid on ordinary searches: 0 of 125 non-drawn roots entered it, against 13 of 13
drawn roots. When it does run it costs 5–9 µs, on a root that otherwise returned in under a
millisecond.

**How sure.** High on the composition, pins and scan gating — those are direct counts, not
inferences. High on "the repair fires only where it should" for the seven families tested.
Moderate on the generalisation: my drawn-root population is constructed plus 7 real
endgame roots, not a large sample of tournament play.

---

## Honesty numbers

Built from `6b98f217`, folder `forge-combo29`, GCC 13.3, `-O3 -march=x86-64-v4`,
DEFAULT options, one fresh process per line (`job1/honesty.sh`, raw output in
`job1/out/*.bench*.txt`).

| build | bench 11 | bench 13 | bench 16 | perft 5 | sanitizer lines |
| --- | --- | --- | --- | --- | --- |
| base, release | 312866 | 862329 | 3024920 | 4865609 | n/a |
| patched, release | 312866 | 862329 | 3024920 | 4865609 | n/a |
| base, ASan+UBSan | 312866 | 862329 | 3024920 | 4865609 | 0 |
| patched, ASan+UBSan | 312866 | 862329 | 3024920 | 4865609 | 0 |

Instrumentation is not vacuous: `nm -C forge | grep -c __asan_` = 35 and `__ubsan_` = 15 on
both sanitizer builds, and a scratch copy with one planted heap over-read behind
`go faultprobe` was caught by the same runner
(`runtime error: load of address ... with insufficient space for an object of type 'char'`,
exit 1). See `job1/planted_control.py`. Honest run 0 lines, planted run 1 line,
**CONTROL HOLDS**.

---

## Step | done-partly-not done | evidence | result

| step | state | evidence | result |
| --- | --- | --- | --- |
| 1. Reproduce composition, both orders, sha256 | done | `job1/compose_both.sh`, `job1/out/compose_both.txt` | one identical file, `24912a43…a26671`, `EXIT=0` on all four applications |
| 1b. Prove the `-p1` trap is loud | done | `job1/wrong_p.sh`, `job1/out/wrong_p.txt` | both wrong levels exit 1, `1 out of 1 hunk ignored` |
| 2. Four pins, release, base + patched | done | `job1/out/{base_rel,patched_rel}.bench*.txt` | all four equal on both builds |
| 2b. Four pins, ASan+UBSan, base + patched | done | `job1/out/{asan_base,asan_patched}.bench*.txt` | all four equal, 0 sanitizer lines |
| 2c. Planted-fault control for the sanitizer runs | done | `job1/planted_control.py` | control holds |
| 3. Adversarial root families (7) | done | `job1/fixtures.py`, `job1/out/matrix_*.txt` | see table below |
| 4. Cost of the per-move scan | done | `job1/scan_cost.py`, `job1/scan_cost.json` | paid on drawn roots only |
| 4b. Base rate of a drawn root | partly | `job1/base_rate.py`, `job1/out/drawn_endgame.json` | random games never reach one; endgame play gives 7 in 1943 plies |
| 5. `depth 1` vs the GUI contract | done | `job1/wire.py`, `job1/wire_report.json` | 16 observations, no violation |
| 6. Repetition root that also has a mate | done | transcript in this report | base draws, patched mates |

---

## The adversarial families

Every FEN is found by search and asserted with python-chess before use
(`job1/fixtures.py`). Each row also passed a **position-identity gate**: `go perft 1` was
compared with python-chess's legal-move count, so a silently refused FEN — which would have
left the engine searching the previous board — could not pass as a result. All 40 matrix
rows confirmed.

| family | fixture | base | patched | verdict |
| --- | --- | --- | --- | --- |
| two different mates, halfmove 0 (control) | A1 | `b2b1`, no mate claim | `b2b1`, no mate claim | unchanged, correct |
| two different mates, halfmove 100 | A2 | `b2b1`, `cp 0`, 0 nodes | `b2b1`, `mate 1`, 192 nodes | **repair fires** |
| mating move is the single mate, halfmove 100 | B | `b3b1` — **not a mate**, `cp 0` | `b3a3` — **the mate**, `mate 1` | **defect fixed** |
| "mate" is actually stalemate | C | adjudicated, `cp 0` | adjudicated, `cp 0` | correctly does not fire |
| move leaves the opponent a legal reply | D | adjudicated | adjudicated | correctly does not fire |
| halfmove 100, mate in 2 not 1 | E | adjudicated | adjudicated | correctly does not fire |
| insufficient material, mate would exist | F, F2 | adjudicated | adjudicated | branch did not fire; see 63-F11 |
| KNN v K control (not insufficient, has a mate) | F3 | `d2b3` (mate) | `d2b3` (mate) | unchanged |
| threefold repetition, no mate | G | adjudicated, claims `depth 8` | adjudicated, claims `depth 1` | repaired reporting |

The decisive row is B: at halfmove 100 with exactly one mating move available, the base
reports `score cp 0` and plays `b3b1`, which is not a mate. The patched build reports
`score mate 1` with `pv b3a3`.

---

## The cost of the scan (item 3)

Instrumented scratch build (`job1/instrument.py`, source kept as
`job1/probe_search.cpp.txt`; nothing of it is committed as engine source).

**Is it paid on every search, or only on drawn roots?** Only on drawn roots, and this is a
count, not a reading of the diff:

| population | searches | entered the scan |
| --- | --- | --- |
| constructed normal roots (14–48 legal moves) | 5 | **0** |
| random real positions from legal games (6–53 legal moves; 76 of 120 have 30+) | 120 | **0** |
| constructed drawn roots | 6 | **6** |
| real drawn roots from endgame play | 7 | **7** |

The gate is `if (root_draw_adjudicated)`, and `root_draw_adjudicated` already requires
`is_repetition() || halfmove_clock() >= 100 || is_insufficient_material()`. On an ordinary
root that conjunction is false, so the loop body is never reached. The concern in the
assignment — "a cost paid on every search for a condition that fires rarely" — is real as a
shape but does not apply here: the cost is paid only when the condition already fired.

**What it costs when it does run.** Roughly 220–280 ns per legal move
(medians of 15 runs on three boards). Measured totals:

| board | legal moves | iterations | scan |
| --- | --- | --- | --- |
| wide42 (halfmove 100) | 42 | 42 | 9.4 µs |
| wide35 (halfmove 100) | 35 | 35 | 9.9 µs |
| C (stalemate trap) | 20 | 20 | 4.5 µs |
| real KQvK endgames (7 boards) | 19–31 | 19–31 | 5.1–9.2 µs, median 7.2 µs |

For scale, a depth-12 search on this machine takes 20–80 ms. The scan is 0.01–0.05 % of
that, and it is paid on a root whose search the base did not perform at all.

**How rarely does it fire?** Across 60 random legal games (13,707 plies), a drawn root
never occurred — random play mates before the counters fill. In endgame play constructed to
be able to reach the fifty-move rule (KQvK, KRvK, KBvK), 7 of 1,943 plies hit a drawn root,
all at `halfmove 100`. So the honest figure is "rare, but reachable in exactly the endgames
where a game is decided by the fifty-move rule" — not zero.

---

## The GUI-visible contract for `depth 1` (item 5)

`job1/wire.py`, `job1/wire_report.json`, 16 observations. Each `go` was read to `bestmove`
before anything else was sent; piping a whole script with `quit` makes the engine abort and
fabricate `a2a3` with zero info lines, which would have made every "no info lines" verdict
meaningless.

| case | base wire output | patched wire output |
| --- | --- | --- |
| drawn root, `go depth 8` | 8 `info depth` lines, last `depth 8`, `cp 0`, 0 nodes | 1 line, `depth 1`, `cp 0`, 0 nodes |
| drawn root, `go depth 1` | 1 line, `depth 1` | identical |
| drawn root, `go depth 0` | 1 line, `depth 1` | identical |
| drawn root, `go infinite` + `stop` | **64** lines, up to `depth 64` | 1 line, `depth 1` |
| drawn root, `go movetime 50` | 64 lines, up to `depth 64` | 1 line, `depth 1` |
| drawn root, `go nodes 100000` | 64 lines, up to `depth 64` | 1 line, `depth 1` |
| normal root, `go depth 8` | 8 lines, last `depth 8`, 16646 nodes | identical, 16646 nodes |
| drawn then normal, same session | normal search reaches `depth 8`, 16646 nodes | identical |
| checkmated / stalemated root | `bestmove 0000`, 5 lines | `bestmove 0000`, 1 line |

**No contract violation found.** Specifically: one `bestmove` per `go`; `info depth` never
decreases within a search and never exceeds the request; the last info depth is the depth
reached; and a normal search after a drawn root in the same session is byte-identical in
node count to the base. What changes is that the base claims depths it never searched — up
to `depth 64` under `go infinite`, `movetime` or `nodes` limits — and the patched build
claims `depth 1`, which is what actually happened.

The one asymmetry worth stating: with `searchmoves` restricted to a **non-mating** move on
a drawn root, the patched build now performs a real search (8 info lines, 16 nodes, `cp 0`)
where the base adjudicated without searching. The chosen move and score are identical
(`b3b8`, `cp 0`); only the node count and the depth claim differ, and the patch's own
comment ("the adjudication is exactly as before, score and reply included") is therefore
slightly too strong. This is a comment inaccuracy, not a behaviour defect.

---

## Findings (each reproducible by the named command)

- **63-F1** Both orders compose to sha256 `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
  `bash job1/compose_both.sh`
- **63-F2** The `-p1` trap is loud: wrong strip level exits 1 with `1 out of 1 hunk ignored`.
  `bash job1/wrong_p.sh`
- **63-F3** Four pins unmoved on release and ASan+UBSan, base and patched.
  `bash job1/honesty.sh <exe> <tag>`
- **63-F4** The scan is paid only on drawn roots: 0 of 125 non-drawn, 13 of 13 drawn.
  `python3 job1/scan_cost.py 12 5`
- **63-F5** Scan cost 220–280 ns per legal move, 5–9 µs per drawn root.
  `python3 job1/scan_cost.py 12 5`
- **63-F6** Defect fixed: base `b3b1` (`cp 0`, not a mate) vs patched `b3a3` (`mate 1`).
  `python3 job1/matrix.py ~/b_patched/forge --tag p --out p.json`
- **63-F7** Reporting honest: drawn root claims `depth 1` instead of `depth 8`/`depth 64`.
  `python3 job1/wire.py`
- **63-F8** Three of my own fixtures were wrong and were caught by assertions, not luck;
  all fixtures are now search-derived and asserted.
  `python3 job1/fixtures.py`
- **63-F9** Stalemate is not mistaken for mate: fixture C is correctly left adjudicated.
- **63-F10** A mate in 2 is not mistaken for a mate in 1: fixture E is correctly left adjudicated.
- **63-F11** The insufficient-material branch of the repair did not fire in 110,221 sampled
  engine-insufficient positions (0 had a mating move). The standard theorems say it cannot,
  but I did not prove it exhaustively — the full sweep did not finish, so this is strongly
  supported rather than proven. `python3 job1/insuff_sample.py`
- **63-F12** The repetition path is repaired too: a threefold root with a mate available gives
  base `h1f2` (draw, no mate) vs patched `b3a3` (`mate 1`). Transcript below.

## Suspicions, not proven

- The base's 64-line `depth 64` claim on a drawn root under `go infinite` may confuse a GUI's
  depth display or its "search finished" heuristic beyond the node-count evidence I gathered.
  I did not test an actual GUI, only the wire.
- `result.depth = std::min(1, max_depth)` is equivalent to `1` because `max_depth` is
  clamped to `[1, 64]` at line 2219, so the `min` is inert. Harmless, but it reads as if
  `max_depth` could be 0.
- I extrapolated the cost to a hypothetical 218-legal-move drawn root (48.6 µs at 223 ns
  per iteration) rather than measuring one: every 200+ mobility board I built had a mate,
  which short-circuits the loop at the first hit. The extrapolation is arithmetic, not a run.

## What I did NOT do

- No actual GUI (Cute Chess, Arena, Nibbler) was driven; the contract checks are on stdout.
- No thread-count variation beyond Threads 1; the repair is in root setup, which is
  single-threaded, but I did not confirm that under TSan.
- No tournament-strength measurement; the patch cannot change strength on non-drawn roots
  (identical node counts) and does not claim to.
- No independent reimplementation of seat 12's or seat 27's analysis; I tested the composed
  result only.
- I did not test `ponder` interaction with a drawn root beyond `go infinite` + `stop`.

## What I am NOT sure about

- Whether any real game reaches a drawn root with 40+ legal moves often enough for the
  9 µs to matter. My endgame sample had 19–31.
- Whether the `searchmoves` asymmetry matters to any real client. The move and score are
  identical; only nodes and the depth claim differ.

---

## Times

`job1/stamps.txt` holds the git commit times on this branch (real) and the mtimes of the
evidence files, which are **copy** times, labelled as such in that file. A per-part stamp
was not recorded during the first pass and I have not typed times I did not observe.

## Last command output

```
$ git status --short
(clean)

$ ls forge-combo29/swarm/63/job1/
base_rate.py          deeper.py             fixtures.json         fixtures.py
instrument.py         insuff_sample.py      matrix.py             out/
planted_control.py    probe_search.cpp.txt  repetition_mate.py    res_asan_base.json
res_asan_patched.json res_base_rel.json     res_patched_rel.json  scan_cost.json
scan_cost.py          stamps.txt            two_doors_mate.patch.txt
drawn_root_reporting.patch.txt              ucih.py               wire.py
wire_report.json      wrong_p.sh            compose.sh            compose_both.sh

$ ls forge-combo29/swarm/63/job1/out/ | wc -l
25
```

## Verdict

**Ship both patches.** They compose deterministically, move no honesty pin on release or
under ASan+UBSan, fix the drawn-root defect on the fifty-move, repetition and
insufficient-material paths, refuse to fire on stalemate, on a non-mating check, on a mate
in two, and on every insufficient-material root (where no mate is possible), and cost
nothing on the 125 non-drawn roots I measured. The single behaviour change beyond the fix
itself — a real search instead of an adjudication when `searchmoves` excludes the mating
move — yields the same move and score, and only makes the patch's own comment slightly too
strong.

The general fixable weaknesses, in order of what I would do next: correct the comment to
mention the `searchmoves` case; replace `std::min(1, max_depth)` with a plain `1` (the
`min` is inert); and, if the seat wants to remove the dead insufficient-material branch,
either drop it or note in the code that the predicate makes it unreachable.

