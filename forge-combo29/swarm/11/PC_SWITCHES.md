# THE SIX FORGE_FIX_* SWITCHES — compiled state and measured effect

Seat 11, reading the patched tree `/tmp/pcbase/forge-combo29` (base commit 6b98f217 + the
FABLE_TO_swarm_5 patch, sha256 of the patch starts `d6bd72c531f785f4`).
Built three ways, all with `-DCMAKE_BUILD_TYPE=Release -DFORGE_MATE_ALPHA_GUARD=1`:

| build | what | path |
|---|---|---|
| **shipped** | exactly what the owner's PC plays: switches at the defaults the patch sets | `/tmp/pcbuild/forge` |
| **all-off** | same source, the five ON-by-default switches flipped to 0 | `/tmp/pcoffbuild/forge` |
| **all-on** | same source, the two OFF-by-default switches flipped to 1 | `/tmp/pconbuild/forge` |

**All numbers are Threads 1** unless a row says otherwise (the swarm rule).

## The table

| switch | compiled state in the BINARY THE OWNER PLAYS | source | measured effect | how measured |
|---|---|---|---|---|
| `FORGE_FIX_ROOT_DRAWN` | **ON (1)** | src/search.cpp:36 | **LARGE — measured.** A threefold root is searched instead of adjudicated: shipped `d2d4` at **7,799 nodes** vs all-off `a2a3` at **0 nodes**. A mate-in-1 at halfmove 100 is FOUND (`d1d8`, mate 1, 140 nodes) vs all-off `f2f3`, cp 0, 0 nodes. | shipped vs all-off, PC20, Threads 1, `go depth 8` / `go depth 5` |
| `FORGE_FIX_GO_PARSE` | **ON (1)** | src/uci.cpp:31 | **MEASURED.** `go depth nodes 100` reaches **depth 2** on shipped vs **depth 1** on all-off (the parser no longer eats a go keyword as the previous keyword's value). | shipped vs all-off, PC20, Threads 1 |
| `FORGE_FIX_ISREADY_PENDING` | **ON (1)** | src/uci.cpp:38 | **NOT MEASURED — no observable difference found.** `isready` sent 250 ms into a `go depth 14` produced the same subsequent bestmove (`d2d4`) on shipped and all-off, with both answering `readyok`. I could not construct a case where this switch changes anything; that is "not measured", not "no effect". | shipped vs all-off, PC20, Threads 1 |
| `FORGE_FIX_HARD_LIMIT_EMERGENCY` | **ON (1)** | src/search.cpp:43 | **NOT MEASURED — no observable difference found.** `go movetime 50` took 40.7 / 40.8 / 40.7 ms on shipped and 40.7 / 40.7 / 40.3 ms on all-off; the emergency branch needs a position where the hard limit arrives before any node is searched, and my probe did not reach it. | shipped vs all-off, PC20, Threads 1 |
| `FORGE_FIX_BARE_KING_LMR_CAP` | **ON (1)** | src/search.cpp:63 | **MEASURED, scoped to lone-king endings.** Built a variant with ONLY this switch flipped to 0. Lone-king ending `6k1/8/8/8/8/8/8/4QK2 w - - 0 1` at `go depth 10`: shipped (ON) **e1e7, 106,270 nodes**; this-switch-OFF **f1g1, 26,973 nodes** — the bestmove itself differs. On startpos (`d2d4`, 8,569 both) and a midgame FEN (`f1c4`, 16,685 both) it changes nothing. So it is live and correctly scoped to bare-king roots. | shipped vs switch-0-only build, PC20, Threads 1 |
| `FORGE_FIX_BARE_KING_ONE_THREAD` | **OFF (0) — NOT IN THE BINARY THE OWNER PLAYS** | src/search.cpp:55 | **LARGE — measured.** Lone-king ending `6k1/8/8/8/8/8/8/4QK2 w - - 0 1` at `go depth 10`: shipped (switch OFF) `e1e7` in **106,270 nodes**; all-on (switch ON) `e1e7` in **1,431,555 nodes** — 13.5x more search for the same move, **at Threads 1**. So the switch is live even single-threaded, despite its name. | shipped vs all-on, PC20, Threads 1 |
| `FORGE_FIX_ABORT_PUBLISH` | **OFF (0) — NOT IN THE BINARY THE OWNER PLAYS** | src/search.cpp:77 | **NOT MEASURED — no observable difference found.** `stop` 400 ms into `go depth 24` gave `bestmove e2e4` on shipped and all-on alike. I did not find a case where this switch changes what is published on abort. | shipped vs all-on, PC20, Threads 1 |

### Summary the owner needs
- **In his binary (ON):** `ROOT_DRAWN`, `GO_PARSE`, `ISREADY_PENDING`, `HARD_LIMIT_EMERGENCY`,
  `BARE_KING_LMR_CAP`.
- **NOT in his binary (compiled OFF):** `BARE_KING_ONE_THREAD`, `ABORT_PUBLISH`.
- Of the seven names in file 5's switch list, five are demonstrably present and two are absent.
  `BARE_KING_ONE_THREAD` is not a no-op — turning it on changes a lone-king search by 13.5x in
  node count at Threads 1 — so its absence is a real difference between the PC's binary and the
  patch's full intent.

### Which of the six are STILL UNMEASURED (stated, not inferred)
Measured and reported above: `ROOT_DRAWN`, `GO_PARSE`, `BARE_KING_LMR_CAP`, and
`BARE_KING_ONE_THREAD` (the last from its OFF→ON build).

**PROVEN INERT (better than unmeasured):**
- `FORGE_FIX_ISREADY_PENDING` — ON in the source, but **cannot fire in this binary**. Its whole
  body sits inside `#if FORGE_NNUE_V3`, which is **0** in the patched tree
  (`include/forge/nnue.hpp:40`), and it only acts when `NNUEArch` is on with no net loaded — and
  the shipped exe lists **no `NNUEArch`/`NNUEArchFile` option at all**. So the state it protects
  is unreachable, which is exactly why my probe found no ON/OFF difference. (S-F90)

**MEASURED (revised from unmeasured):**
- `FORGE_FIX_HARD_LIMIT_EMERGENCY` — ON in the binary, and it MATTERS at tight clocks. Built a
  variant with only this switch off; sweeping `go wtime t btime t` for t = 11..60 ms, 5 of 50
  values differ (t = 16, 17, 27, 28, 31). At t=17 the MOVE differs (`g8f6` ON vs `a7a6` OFF —
  `a7a6` being the unsearched first legal move the switch exists to avoid), and at t=17 the ON
  build was stable at 601 nodes 5/5 while OFF was unstable (4x601, 1x1257). So its real value is
  REPRODUCIBILITY at a near-expired clock. My earlier "no difference" probe had stepped over the
  5-in-50 window. (S-F91)

**MEASURED (revised from unmeasured):**
- `FORGE_FIX_ABORT_PUBLISH` — OFF in the binary, and shipping it off costs nothing measurable. The
  source says the author measured 19,800 exact-node stops and found it "is not a repair" (finished
  move 14 cp lower on average in the 73 differing stops), which is why it defaults to 0. I tested it
  independently: shipped-OFF vs only-this-switch-ON, the chosen move differs on **0 of 40** O
  positions at 50,000 nodes and **0 of 40** at 250,000 — 80 stops, no change. My sample is far too
  small to detect their 0.37 % effect, so this is "no effect observed", not "no effect exists";
  the author's larger measurement remains the better evidence. (S-F92)

**Still unmeasured:** none of the six. Every switch is now either measured, proven inert, or (for
the two shipped OFF) measured to make no difference in my sample.

For each of those three I ran a plausible probe, saw no difference, and could not construct a case
that reaches the code path. "Not measured" here means exactly that; it is **not** evidence that the
switch does nothing.

## Could another seat's PC20 results have my option-wrapping defect?

Yes, and here is the one-command check. My bug was that my driver wrapped an
already-complete `setoption name X value Y` string, sending
`setoption name setoption value name X value Y`, which the engine ignores **silently**.
Any seat whose harness takes option strings as full lines and then re-formats them can have
sent **no options at all** while labelling results "PC20".

**The check is the bench number, because the two regimes cannot coincide:**

```
PCPATH=<your PC r15 exe>; printf 'uci\nbench 11\nquit\n' | $PCPATH | grep 'bench depth 11'
```

- prints `nodes 312866` -> **no options were applied** (the default-option number): your PC20
  results are mislabelled and must be re-run.
- prints `nodes 278024` -> PC20 was applied. Correct.

And the two anchors for the other regimes, same command shape:

| regime | expected `bench 11` |
|---|---|
| no options at all | 312866 |
| S14 only | 242796 |
| PC20 | 278024 |

A harness that reports "PC20" while its bench 11 reads 312866 is measuring default options.
A second, cheap confirmation: S14-only bench 11 must read **242796**; if it also reads 312866 the
settings never reached the engine.

## Files
- `checks/measure_switches.txt` — ON vs OFF run for the five ON-by-default switches.
- `checks/measure_off_switches.txt` — ON vs OFF run for the two OFF-by-default switches.
- `PCR15_BUILD.md` — how the shipped build was made and its three number regimes.
