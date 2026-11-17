# STATUS — swarm 66 (clock behaviour seat)

## Identity
- seat/worker: swarm 66
- branch: `for-fable-and-opus/swarm-66`
- work dir: `forge-combo29/swarm/66/`
- base commit: `6b98f2170` ("Checkpoint standalone NNUE v3 work and evidence")
- engine under test: **base tree 6b98f2170**, built here
  - `g++-13` 13.3.0, `-O3 -DNDEBUG`, `-DFORGE_MARCH=native`, CMake Release
  - binary `/tmp/w66/build/forge` (786696 bytes; rebuild command below)
  - honesty pin reproduced: `bench 11` = **312866** (LOCK.md pin, identical)

## Build and re-run
```bash
ln -sf /usr/lib/x86_64-linux-gnu/libstdc++.so.6 /tmp/w66/lib/libstdc++.so   # host lacks the dev symlink
cmake -S forge-combo29 -B /tmp/w66/build -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_COMPILER=g++-13 -DFORGE_MARCH=native \
      -DCMAKE_EXE_LINKER_FLAGS="-L/tmp/w66/lib"
cmake --build /tmp/w66/build -j4
cd forge-combo29/swarm/66 && python3 selftest.py /tmp/w66/build/forge
```

## STATE AT THIS PUSH: cases 1-6 and 7a/7c measured and verified; only the 3+2 set (7b) still accumulating

| case | state | headline |
| --- | --- | --- |
| 0 harness self-test | **DONE 12/12**, exits 1 against a lying engine | planted hang / invalid-FEN / slow / multi-info all caught |
| 1 opponent's clock, 300 s | **DONE 8/8** | never answers: ran the **full 330 s allowance**, depth **39**, 416,554,567 nodes, **zero** diagnostics; only `stop` ended it |
| 2 movetime 10/30/60 s | **DONE 11/11** | all three terminate on the CLOCK at depth 27/30/32, never reaching the depth-64 clamp; soft==hard on this path, no 60% rule |
| 3 increment > clock | **DONE 21/21** | clock 1000 inc 2000 plans hard 594 (59.4% of clock) and soft is pulled DOWN to 594; no row plans the whole clock |
| 4 zero/negative clocks | **DONE 26/26** | `wtime 0`, `-100`, `0 btime 0`, `0 winc 5000`, `-3000000000` all answer legally in <1.5 ms; no forfeit, no hang |
| 5 huge clocks | **DONE 27/27** | 2e9 / 3e9 / int64-max / 36,028,797,018,963,967 / one-past / 30 digits: all accepted, none answers inside 8 s, all answer `stop` |
| 6 repeated `go` | **DONE 15/15** | nothing accumulates: 6 goes at a fixed 1000 ms clock spent 485 ms total |
| 7a 20 games at 1000+100 | **DONE 9/9** | **0 forfeits / 0 hangs / 0 illegal / 0 refused over 20 games and 3,071 plies**; max move-time/clock **0.5937**; floor reached: max **114.5 ms** at a ≤200 ms clock = 0.6×(200−10) |
| 7b 20 games at 3000+2000 | **PARTIAL, 2 of 20 games** (0 forfeits; clock never fell below 3000 ms) | at 3+2 the clock GROWS, so this control cannot test the floor |
| 7c drain control | **DONE** | 10× overcharge reaches clock 0; 60/60 moves legal in 0.1–0.6 ms, both with and without increment |

## Three measurements that correct the brief's framing
1. **"Does a 300 s one-sided clock terminate?"** — No. It is a **hang**, not a slow move: it never printed
   `bestmove` in the full 330 s allowance, was still at depth 39 (25 depths short of the ceiling), and was
   ended only by an explicit `stop`, with no diagnostic at all (case 1).
2. **`wtime 0` is not a 0-node reply.** Holding stdin open, the engine prints one
   `info depth 1 ... nodes 26 ... pv d2d4` line and answers in ~1 ms. The 0-node / `a2a3` answer that a
   plain `printf ... | ./forge` pipe produces is an **EOF artifact**: closing stdin aborts the search.
   Both are measured and recorded in FINDINGS.md; only the first is clock behaviour.
3. **At 3+2 the clock grows and the floor is never tested.** The per-move spend is smaller than the
   2000 ms increment, so the remaining time rises from 3000 ms to ~3900 ms over a game. A control that
   actually reaches the floor is required, so this audit adds a 1000+100 match and a 10× drain. At
   1000+100 the floor is measured: **max 114.5 ms at a clock ≤200 ms** = `0.6 × (200 − 10)`.

## Harness rules in force
- stdout is a daemon thread over `os.read` on the fd; no `select()` + `readline()`.
- every `bestmove` wait has an explicit timeout; `go infinite`/unbounded cases send `stop`.
- the `invalid FEN` diagnostic is scanned in **BOTH** the `position` reply and the `go` output. Measured on
  this build: with `isready` between them it lands in the position reply (`info string invalid FEN: invalid
  FEN fields` then `readyok`); without it, in the go output ahead of `bestmove`. Both confirmed by hand.
- every FEN (and every move list) is validated with python-chess before it is sent.

## Next
- Nothing is outstanding for the deliverables. The 3+2 set (7b) is still appending to
  `case7_partial_20_3000_2000.json`; if it finishes, run
  `python3 case7_analyse.py case7_partial_20_3000_2000.json` and update the 7b row in FINDINGS/CLOCK_TABLE.
  No conclusion in this report depends on it — the floor claim rests on the 1000+100 match (7a) and the drain
  control (7c), both complete.
