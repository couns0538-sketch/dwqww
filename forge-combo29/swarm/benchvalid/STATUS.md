# STATUS — swarm/benchvalid

## 2026-11-17 (seat start → close)

**Area**: is `bench` a sound gate at all? Not a re-derivation — the seat takes as given
that bench never reads `Threads`, that `bench N` on argv is silent, and that per-node cost is
6× optimistic. It measures what is left: what bench *is*, whether it can move, what it
covers, and what to replace it with.

**Base**: `6b98f217`. **Branch**: `swarm/benchvalid`. **Folder**: `forge-combo29/swarm/benchvalid/`.
**Machine**: 4 cores, Intel Xeon (KVM), 1 thread/core, no SMT, 15 GB.

### Gate

| pin | expected | got |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| perft 5 | 4,865,609 | **4,865,609** |

Binary sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` — **the same
binary sha the `swarm/threads` seat recorded**, so this seat's numbers and that seat's are
directly comparable. Gate: **PASS 4/4**. `evidence/pins_base.json`.

### Done

| part | what | evidence |
|---|---|---|
| build | g++ 13.3.0, `-DCMAKE_CXX_COMPILER=/usr/bin/g++`, `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13`, `-DFORGE_MARCH=x86-64-v4` | `pins_base.json` |
| **gate** | 4/4 honesty pins, sent on **stdin** | `pins_base.json` |
| argv trap | `bench 11/13/99` on argv: **exit 0, 0 bytes stdout, 0 bytes stderr** | `argv_trap.txt` |
| **what bench is** | 8 FENs printed, all validated with python-chess, 7/8 White, **8/8 halfmove clock 0**, none refused | `fen_check.txt`, `bench_positions_d13.txt` |
| **independence** | `clear()` really does make the 8 positions independent: forward = reverse = **fresh searcher** = 862,329; the no-clear control gives **956,783** | `order_independence.txt` |
| **sensitivity (must move)** | 5/5 behavioural mutants move the pin — eval weights, 3 search constants, a SEE constant. Range 4.5 %–64 % | `sensitivity.json` |
| **sensitivity (must not)** | 5/5 source-noise mutants leave every pin bit-identical — comment, struct reorder, rename, dead function, whitespace | `sensitivity.json` |
| **coverage** | `bench 13` = **63.0 % of lines / 59.6 % of functions**; four pins 64.1 / 61.1; pins + behavioural 70.1 / 70.7 | `coverage_*.json` |
| **blind functions** | **22** functions the pin cannot reach: 4 book, 8 uci, 7 search, 3 board | `blind_functions.json` |
| **blind spots (behavioural)** | **6 of 9 real changes pass a green 4/4 gate**: book on/off, Book Variety, Threads default, Move Overhead, fifty-move leaf, drawn-root move | `blindspots.json` |
| **Hash trap** | pin **862329 at Hash 1/16/64/256/1024** while a real `go depth 14` moves **109,247 → 101,640** — the option is live and bench is deaf | `hash_trap.json` |
| **\`go\` is not pinnable** | one FEN, one depth, **four distinct node counts** by session order (50,541 / 11,696 / 72,365 / 13,235) | `go_repeatability.json` |
| **proposal** | `forge gate`: **7 checks, 2.4 s**, all 7 fire cleanly on their own planted fault | `gate_selfcheck.json`, `gate_cost.txt` |
| **G2 can pass** | a minimal drawn-root repair flips G2 red→green with **all four pins unchanged** | `g2_can_move.json` |
| **documents check themselves** | every quoted figure is a lookup into `evidence/`; `verify_figures.py` PASS, and it was proven to fire by corrupting the doc and an evidence file | `scripts/verify_figures.py` |

### Headline results

1. **The pins are a real instrument.** 5 of 5 should-move mutants moved them; 5 of 5
   should-not-move mutants did not. The audit had been treating them as unvalidated.
2. **The pins are not a certificate.** 6 of 9 real behaviour changes pass a green 4/4 —
   including **`Threads` (findings decision #3)** and **the drawn-root bail (decision #2)**.
3. **`clear()` is the load-bearing call.** Reverse order and a fresh `Searcher` per
   position give the identical total; removing `clear()` gives 956,783 and leaks a mate
   score between positions. Any replacement built on `go depth N` **does not inherit this**:
   a bare `go` returns four different node counts for one position in one session.
4. **Coverage is 63 % and that number is misleading**, because the missing 37 % is *sorted*
   — book, clock parsing, UCI surface, drawn root, MultiPV, Hash. 22 named functions.
5. **A 2.4 s gate covers what 1.9 s of pins cannot**, and every check is proven able to
   fail and (for G2) proven able to pass.

### Withdrawn

- **"Book Variety is invisible to the gate"** — my probe at n = 5 read the mutant as inert
  because the book move is clock-seeded and five draws coincided. At n = 20 it is a live
  gate-passing change.
- **"A clocked search differs across these mutants"** — my probe ran on `startpos`, which
  the book answers with a clock-seeded move. Three fresh base runs gave three different
  moves. Every row resting on it was noise.
- **"Move Overhead is invisible to the gate and the probe agrees"** — the probe's margin
  (1,000 ms) was larger than the fault (390 ms). At 100 ms the arms separate 2,789 nodes
  from 60. The finding survived; the probe demonstrating it did not.

All three are the brief's rule 3 class: **a control that silently does nothing.**

### Not done

- No SPRT / Elo / game play — 2.4 s does not buy strength measurement.
- No `MultiPV`, ponder, or `go infinite`+`stop` in the gate. The coverage workload reaches
  them (70.1 %), but none is proven to discriminate, and an unproven check is the defect
  this document is about.
- No external book-file (`.bin`) arm; only the embedded book.
- The drawn-root repair in `g2_can_move.py` is **mine, not the shipped patch** — the patch
  files (`swarm/12/job1/two_doors_mate.patch.txt`, `swarm/27/...`) are not in this
  checkout. It exists only to prove G2 can pass.

### Next command I would run

```
python3 scripts/gate_selfcheck.py        # 7 plants, ~85 s, expect 7/7 fired-cleanly
```

then add a `MultiPV 2` check to `gate.py` and prove it with a planted fault before
believing it — the only check in the proposal that is currently unproven is the one
that is not there.
