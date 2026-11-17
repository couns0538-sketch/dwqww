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

## STATE AT THIS PUSH: cases 1-6 measured and committed; case 7 running

| case | state | headline |
| --- | --- | --- |
| 0 harness self-test | **DONE 11/11**, exits 1 against a lying engine | planted hang / invalid-FEN / slow / multi-info all caught |
| 1 opponent's clock, 300 s | **DONE 8/8** | does NOT terminate: ran 288.7 s, depth **39**, 416,554,567 nodes, **zero** diagnostics; only `stop` ended it |
| 2 movetime 10/30/60 s | **DONE 11/11** | all three terminate on the CLOCK at depth 27/29/30, never reaching the depth-64 clamp; soft==hard on this path, no 60% rule |
| 3 increment > clock | **DONE 21/21** | clock 1000 inc 2000 plans hard 594 (59.4% of clock) and soft is pulled DOWN to 594; no row plans the whole clock |
| 4 zero/negative clocks | **DONE 26/26** | `wtime 0`, `-100`, `0 btime 0`, `0 winc 5000`, `-3000000000` all answer legally in <1.5 ms; no forfeit, no hang |
| 5 huge clocks | **DONE 27/27** | 2e9 / 3e9 / int64-max / 36,028,797,018,963,967 / one-past / 30 digits: all accepted, none answers inside 8 s, all answer `stop` |
| 6 repeated `go` | **DONE 15/15** | nothing accumulates: 6 goes at a fixed 1000 ms clock spent 485 ms total, each planning from the same 1000 ms |
| 7 20 games at 3+2 | **RUNNING** | in flight at this push |

## Two measurements that correct the brief's framing
1. **"Does a 300 s one-sided clock terminate?"** — No, not by itself. It was still searching at depth 39
   after 288.7 s and required an explicit `stop`. The depth-64 ceiling would have bound eventually, but
   nothing in the engine says so and it prints no diagnostic (case 1).
2. **`wtime 0` is not a 0-node reply.** Holding stdin open, the engine prints one
   `info depth 1 ... nodes 26 ... pv d2d4` line and answers in ~1 ms. The 0-node / `a2a3` answer that a
   plain `printf ... | ./forge` pipe produces is an **EOF artifact**: closing stdin aborts the search.
   Both are measured and recorded in FINDINGS.md; only the first is clock behaviour.

## Harness rules in force
- stdout is a daemon thread over `os.read` on the fd; no `select()` + `readline()`.
- every `bestmove` wait has an explicit timeout; `go infinite`/unbounded cases send `stop`.
- the `invalid FEN` diagnostic is scanned in **BOTH** the `position` reply and the `go` output. Measured on
  this build: with `isready` between them it lands in the position reply (`info string invalid FEN: invalid
  FEN fields` then `readyok`); without it, in the go output ahead of `bestmove`. Both confirmed by hand.
- every FEN (and every move list) is validated with python-chess before it is sent.

## Next
- finish case 7, write FINDINGS.md / CLOCK_TABLE.md, push.
