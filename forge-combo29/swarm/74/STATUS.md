# STATUS — swarm/74 movegen-correctness seat

Branch: `for-fable-and-opus/swarm-74`
Base: `6b98f217` ("Checkpoint standalone NNUE v3 work and evidence")
Work directory: `forge-combo29/swarm/74/`
Engine source: **unmodified**. This seat adds a test harness and fixtures only.

## Verdict

**Move generation is correct at every edge tested. Nothing was broken.**

| item the brief asked for | state |
|---|---|
| 1. Standard perft suite vs published counts, depth 5–6 | done — 42 cells, 42 agree |
| 2. Special-move edges, one fixture each, independent python-chess count | done — 11 fixtures, 33 cells, 0 problems |
| 3. Fuzz 2,000 random legal positions, `go perft 3` vs python-chess | done — 2,000 compared, **0 mismatches** |
| 4. Report every disagreeing position with FEN and divide | nothing to report — 0 disagreements |
| FEN validated with python-chess before use | done, gate 1 in every comparison |
| `info string invalid FEN` detected in the stream | done in both locations (position reply and `go` output) |
| `go perft N` synchronous, Threads 1 | done |
| Every script proven able to fail | done — all four scripts have a self-test |
| Print denominators as literals | done — counts stated as integers throughout |

**Headline: 0 mismatches out of 2,000 random positions.**

## Numbers, as literals

- Standard suite: 42 cells compared, 42 agree, 0 mismatches, 28 published counts
  independently re-derived with python-chess (28/28 agreed).
- Fixtures: 11 fixtures, 33 cells compared, 0 problems.
- Fuzz: 2,000 generated, 2,000 compared, 0 mismatches, 0 refusals, 64,383,829
  nodes summed, seed 74000.
- Directed en passant: 500 compared, 500/500 with a live ep capture, 0 mismatches.
- Directed castling: 500 compared, 371/500 with castling available, 0 mismatches.
- Total: 3,075 comparisons, 0 mismatches.

## Files

| path | what it is |
|---|---|
| `forge-combo29/swarm/74/uci_perft.py` | UCI harness + the four FEN-trap gates + `self_test()` |
| `forge-combo29/swarm/74/suite.py` | standard CPW suite, 7 positions, 42 cells |
| `forge-combo29/swarm/74/fixtures.py` | 11 special-move fixtures, with `--self-test` |
| `forge-combo29/swarm/74/fuzz.py` | fuzz at perft 3; `--ep` / `--castle` directed modes; `--self-test` |
| `forge-combo29/swarm/74/PERFT_TABLE.md` | every suite cell, published beside measured |
| `forge-combo29/swarm/74/FINDINGS.md` | the report, including the measured FEN trap |
| `forge-combo29/swarm/74/*.json` | raw results: `perft_rows`, `fixture_rows`, `fuzz_rows`, `fuzz_ep`, `fuzz_castle` |

## Things worth the coordinator's attention

1. **The FEN trap manufactures false movegen bugs, and it is easy to hit.** A
   refused FEN leaves the board on the previous position, so `go perft 1` after a
   bad `position` returned **`nodes 48`** (kiwipete's count) with the diagnostic
   buried one line earlier. Any perft comparison that does not prove board
   identity is measuring the wrong board. Board identity now costs one extra
   `go perft 1` plus a move-set comparison; I recommend anyone else wiring a
   perft harness copies gate 4 from `uci_perft.py`.
2. **Uniform random play barely reaches the edges that matter.** Promotion was
   available in 19 of 2,000 positions, en passant in 8. A fuzz pass that only
   reports "2,000 positions, 0 mismatches" without coverage numbers is close to
   uninformative about promotions and ep. The directed modes in `fuzz.py` fix
   this cheaply and are reusable.
3. **Build note:** `cmake` picks clang here and clang cannot link `libstdc++` on
   this image (`cannot find -lstdc++`). `-DCMAKE_CXX_COMPILER=g++` works and
   reproduces every published count. Anyone else building this repo on this
   image will hit the same wall.
4. Four faults in my own test scaffolding were caught by the gates (a double push
   onto an occupied square, a push by a pinned pawn, a misread `board.pin()` mask,
   and two illegal fixture FENs). Details in `FINDINGS.md` §6. The gates caught
   all of them, which is the strongest evidence available here that the gates
   work.

## Not established by this seat

- Depth 3 for the fuzz is shallow; this is a movegen test, not a search test.
- Perft compares move counts, not move identity, so a same-count substitution bug
  would survive the fuzz. The fixtures compare move sets at depth 1 and would
  catch it there.
- No engine source was touched, so nothing here speaks to behaviour after edits.

## Reproduce

```bash
cd forge-combo29 && cmake -S . -B build-swarm74 -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=g++ && cmake --build build-swarm74 -j4
cd swarm/74 && python3 uci_perft.py ../../build-swarm74/forge \
  && python3 suite.py ../../build-swarm74/forge \
  && python3 fixtures.py ../../build-swarm74/forge \
  && python3 fuzz.py ../../build-swarm74/forge --count 2000 --seed 74000
```
