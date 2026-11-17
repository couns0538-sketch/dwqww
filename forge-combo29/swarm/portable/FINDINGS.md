# Portable builds: what a lower ISA actually costs

Audit of `forge-combo29` at base commit `6b98f217`. Every number below was produced by
the scripts in `scripts/` on this machine; the raw outputs are in `evidence/`.

**The question this answers.** Prior work established one narrow thing: the NNUE kernel
computes the same values at scalar, AVX2 and AVX-512. It did not establish that a whole
build at a lower ISA is correct, and it did not time one. Both are now measured.

---

## Verdict

**The engine is portable in practice, and the portable build costs about 4% of wall time.**

- The `FORGE_PORTABLE` path **exists and works**. It is a CMake option that drops the two
  ISA-bound speed switches (`FORGE_SPD_SLIDER_PEXT`, `FORGE_SPD_NNUE_ZMM`). Nothing had to
  be invented for this audit.
- **`-march=x86-64-v3 -DFORGE_PORTABLE=ON` is the recommended portable build**: all 11
  LOCK.md pins exact, perft exact, identical search on 120 positions, **+4.2% wall**
  (CI 1.0372–1.0450, slower on 106 of 120 positions).
- **`-march=x86-64-v2` is correct but expensive: +16.1%**, slower on **120 of 120**.
- **A lower `-march` alone does not compile.** With `FORGE_PORTABLE=OFF` the source fails
  with an explicit `#error`, not a miscompile — see §2. That is the right failure.
- **`FORGE_PORTABLE=ON` leaves performance on the table at v3.** It disables PEXT
  unconditionally, but `x86-64-v3` includes BMI2. Enabling PEXT at v3 cuts the cost from
  +4.2% to **+1.4%**. The one-line fix is in §6.

**The engine's correctness does not depend on the ISA.** Every pin, perft count, eval
value and searched node count is identical across all three builds. The cost of a portable
build is entirely speed.

---

## 1. The native baseline, and the two build traps

The native build must reproduce the lock pins *before* it can be a reference. It does:

| pin | expected | native | v2 | v3 |
|---|---|---|---|---|
| bench 11 (net on) | 312,866 | 312,866 | 312,866 | 312,866 |
| bench 13 (net on) | 862,329 | 862,329 | 862,329 | 862,329 |
| bench 16 (net on) | 3,024,920 | 3,024,920 | 3,024,920 | 3,024,920 |
| bench 20 (net on) | 12,389,307 | 12,389,307 | 12,389,307 | 12,389,307 |
| bench 22 (net on) | 34,048,354 | 34,048,354 | 34,048,354 | 34,048,354 |
| bench 11 (net off) | 375,354 | 375,354 | 375,354 | 375,354 |
| bench 13 (net off) | 907,205 | 907,205 | 907,205 | 907,205 |
| bench 16 (net off) | 2,448,617 | 2,448,617 | 2,448,617 | 2,448,617 |
| bench 20 (net off) | 13,573,040 | 13,573,040 | 13,573,040 | 13,573,040 |
| bench 22 (net off) | 24,506,465 | 24,506,465 | 24,506,465 | 24,506,465 |
| perft 5 startpos | 4,865,609 | 4,865,609 | 4,865,609 | 4,865,609 |

**All 11 pins match on all three builds. No pin moved.** That is the primary result of
measurement (1), and it is why measurement (2)'s "if a pin moves" has no entries.

Both traps are real and both were hit:

- `/usr/bin/c++` is clang 18 with a broken header path. `-DCMAKE_CXX_COMPILER=/usr/bin/g++`
  with `LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13` is required.
- The native build flags resolve to `-march=sapphirerapids`, not a conservative native.
  Confirmed with `g++ -march=native -Q --help=target`.

---

## 2. A lower `-march` alone does not compile — and that is the correct outcome

`FORGE_PORTABLE=OFF` (the default) at a lower ISA fails at compile time with a specific
diagnostic:

```
src/nnue.cpp:28:2: error: #error "FORGE_SPD_NNUE_ZMM=1 needs an AVX-512F target
                            (the lock builds with -march=znver5)"
include/forge/bitboard.hpp:15:2: error: #error "FORGE_SPD_SLIDER_PEXT=1 needs BMI2
                                 (the lock builds with -march=znver5)"
```

The switches are guarded by `#if !defined(__AVX512F__) #error` and `#if !defined(__BMI2__)
#error` respectively. **This is a compile-flag guard doing its job**, and it is worth
stating plainly because the alternative — a build that silently emits instructions the
target cannot run — is how a portable build becomes a crash on someone else's machine.

Logs: `evidence/logs/v2-switchon.build.log`, `evidence/logs/v3-switchon.build.log`.

---

## 3. Correctness across builds: not just nodes, five fields

Node counts alone would not prove the builds agree, because a build could reach the same
node count with a different score. Five fields were compared per position.

**`go depth 12` on 120 real positions, all three builds, one cold process per search:**

| comparison | positions | mismatches |
|---|---|---|
| bestmove | 120 | **0** |
| node count | 120 | **0** |
| score value | 120 | **0** |
| score kind (cp/mate) | 120 | **0** |
| depth reached | 120 | **0** |

**Static evaluation** was compared separately on the same 120 positions via the `eval`
command (`hce`, `nnue`, `total`, `incheck`): **0 differing of 120**. Example line:
`eval hce -297 nnue 41 total -256` — identical on all three.

**Perft**, which exercises move generation with no evaluation and no search, and so
isolates the bitboard/PEXT path:

| position | depth | native | v2 | v3 |
|---|---|---|---|---|
| startpos | 5 | 4,865,609 | 4,865,609 | 4,865,609 |
| kiwipete | 4 | 4,085,603 | 4,085,603 | 4,085,603 |
| pos3 | 4 | 43,238 | 43,238 | 43,238 |
| pos4 | 4 | 422,333 | 422,333 | 422,333 |
| pos5 | 4 | 2,103,487 | 2,103,487 | 2,103,487 |
| en-passant-heavy | 4 | 10,152 | 10,152 | 10,152 |

**So the two ISA-bound paths are numerically equivalent to their portable replacements,
in whole-build terms and not only in the kernel.** The PEXT slider tables return the same
attack sets as the multiply magics; the AVX2 NNUE output kernel returns the same values as
the AVX-512 one.

---

## 4. Timing: the ratio, its CI, and the direction share

Design: fixed `go nodes 200000` so both builds search the identical tree (node counts
matched 120 of 120 — a per-node cost measurement, not a search comparison); `ucinewgame`
before every search because it is the only cold reset (§7 item 3); Threads 1, Hash 16,
OwnBook false. Order per position is **ABBA**, two runs per build per position, median.

**A/A control, and why it changes how the number is reported.** The same binary in both
slots returned a median ratio of **0.9890** — the B slot is 1.10% faster than the A slot,
for reasons that have nothing to do with any build. **That is a bias in the ABBA design
itself, so no single-arm ratio can be read at face value.** Every ratio below therefore
uses two arms run in opposite slot order; a constant multiplicative slot bias cancels
exactly in their geometric mean.

The correction is validated, not assumed: the four raw medians of each pair imply their own
slot bias via `sqrt(fwd / rev⁻¹)`, a value the estimator cannot tune. It lands on the
separately measured A/A value to within **0.43%** on every pair (table, last column).

| build | ratio vs native | cost | CI95 | slower / 120 | implied slot bias | vs A/A |
|---|---|---|---|---|---|---|
| **x86-64-v2, PORTABLE=ON** | **1.1614** | **+16.14%** | 1.1572–1.1671 | **120** | 0.9857 | 0.34% |
| **x86-64-v3, PORTABLE=ON** | **1.0422** | **+4.22%** | 1.0372–1.0450 | 106 | 0.9892 | 0.01% |
| x86-64-v3, PEXT=1 ZMM=0 | 1.0143 | +1.43% | 1.0090–1.0202 | 88 | 0.9887 | 0.04% |
| x86-64-v4, PEXT=1 ZMM=1 (CMake default) | 1.0228 | +2.28% | 1.0142–1.0337 | 84 | 0.9929 | 0.39% |
| x86-64-v4, PEXT=0 ZMM=0 | 1.0384 | +3.84% | 1.0310–1.0446 | 101 | 0.9864 | 0.27% |
| x86-64-v4, PEXT=1 ZMM=0 | 1.0286 | +2.86% | 1.0217–1.0318 | 92 | 0.9892 | 0.02% |
| x86-64-v4, PEXT=0 ZMM=1 | 1.0232 | +2.32% | 1.0134–1.0308 | 85 | 0.9933 | 0.43% |

Sign test on per-position direction: **p ≤ 1.4e-5 on every row**, so the direction share
is not a coin flip anywhere in the table.

**The headline: v2 is +16.1% and slower on every one of 120 positions; v3 is +4.2% and
slower on 106 of 120.** Neither is a mean over a noisy spread — the direction is unanimous
at v2 and 88% at v3.

### What that decomposition does and does not say

Attribution by subtraction across *separate* runs does **not** telescope: measured directly,
switches-off is **+3.25%** against switches-on (CI 1.0267–1.0375, slower on 92 of 120),
whereas the two separate-vs-native ratios imply about +5.6%. **So read the per-switch rows
as "each switch is worth roughly 0.5–1.5%", not as components that sum to the whole.**

### A limit on the CIs that must travel with them

The CI95 above covers **within-run sampling across positions only**. A repeat of the v2
forward arm returned **1.1299 against 1.1453** on the same pair and corpus — **1.4%
between-run drift, wider than the interval.** The v2 and v3 *conclusions* are unaffected
(+16% and +4% are far outside that drift; the direction shares are 120/120 and 106/120), but
the **+1.4% and +2.3% rows rest on differences comparable to the drift and should be treated
as approximate.** The honest form is that this machine gives about ±1.4% reproducibility
between sessions, and only effects larger than that are solid.

---

## 5. The drawn-root bail is identical, as it must be

The bail is `board.is_repetition()` on the searched position's own count — not arithmetic,
so no compile flag can reach it. "Identical" is therefore a *prediction*, and it was tested
rather than assumed, because a prediction that costs nothing to check should be checked.

| case | native | v2 | v3 |
|---|---|---|---|
| threefold via move list, `go depth 8` | `a2a3`, 0 nodes, cp 0, pv empty | identical | identical |
| generator head (independent reference) | `a2a3` | `a2a3` | `a2a3` |
| twofold control (must search) | `d2d4`, 4,099 nodes, cp 26 | identical | identical |
| same board as a bare FEN (must search) | `d2d4`, 4,099 nodes, cp 26 | identical | identical |
| threefold with `go nodes 50000` | `a2a3`, 0 nodes | identical | identical |
| threefold with `go nodes 500000` | `a2a3`, 0 nodes | identical | identical |
| **mate-in-one threefold** | `a1b1`, 0 nodes, cp 0 | identical | identical |
| **mate-in-one twofold (control)** | `a1a8`, mate 1 | identical | identical |

**All eight cases byte-identical across the three builds**, including the documented
mate-in-one forfeit. The bail returns the head of the generator's move list on every build
(verified against `go perft 1`, an independent reference), and it is budget-independent on
every build. **Nothing about the bail is ISA-sensitive, and the measurement confirms it
rather than merely expecting it.**

### A fixture that had to be rebuilt to mean anything

The first version of the mate-in-one case used a FEN with **Black in check and White to
move** — illegal. The engine **silently kept the previous board** (§7 item 3ab: an
unrecognised or invalid position is ignored with no diagnostic) and returned startpos's
`d2d4`. **That row would have read as a pass while testing nothing.** It was caught because
two different boards returned identical node counts, which is impossible, and the fixture
was replaced with a verified one: `6k1/5ppp/8/8/8/8/8/R3K3`, where `Ra8` is mate in one,
confirmed by `go perft 1` on the mated position returning `nodes 0`. The control column
above is what proves the rebuilt fixture discriminates — the twofold searches and reports
`mate 1`, the threefold bails and reports nothing.

---

## 6. `FORGE_PORTABLE=ON` is not the cheapest portable configuration

The option disables PEXT and ZMM together, but the two have different requirements:

- `FORGE_SPD_NNUE_ZMM` needs **AVX-512F** — genuinely absent below v4.
- `FORGE_SPD_SLIDER_PEXT` needs **BMI2** — which **`x86-64-v3` includes**.

So at v3 the default portable build gives up PEXT for no reason. Built by hand with
`-march=x86-64-v3 -DFORGE_SPD_SLIDER_PEXT=1 -DFORGE_SPD_NNUE_ZMM=0`: **all pins exact, all
perft exact, +1.43% instead of +4.22%.** That is a **2.8-point** improvement in the
portable build's cost, from one flag.

**Suggested change** (not applied — this audit measures, it does not patch): let the CMake
default follow the target rather than hard-coding both off, e.g. enable PEXT when
`FORGE_MARCH` is v3 or better, or expose the two switches as separate options so a v3 build
can keep PEXT. A v2 target must still leave both off; `.github`-style cross-checking is
unnecessary because the `#error` guards already refuse the bad combination.

---

## 7. Execution on real older CPUs — and the limit of that evidence

Static disassembly confirms the instruction floor, and it is reported here because it is
what makes the `-march` label meaningful:

| binary | ymm | zmm | k-regs | pext | verdict |
|---|---|---|---|---|---|
| native | 344 | 551 | 66 | 128 | AVX-512 + BMI2 |
| v2 | **0** | 0 | 0 | 0 | SSE4.2 + POPCNT (×228), no AVX |
| v3 | 1,028 | 0 | 0 | 0 | AVX2, no AVX-512 |
| v3 + PEXT | 1,024 | 0 | 0 | **127** | AVX2 + BMI2 |

Executed under `qemu-x86_64`, which **does** emulate SSE2, AVX2 and BMI2:

| build | emulated CPU | result |
|---|---|---|
| v2 | **Nehalem** (2008; no AVX, no BMI2) | **all 11 pins exact, perft 5 exact** |
| v3 | Haswell (AVX2, no AVX-512) | bench 11 = 312,866 exact |
| v3 | SandyBridge (AVX, **no AVX2**) | SIGILL — correct, the build needs AVX2 |
| native | Nehalem / Haswell | SIGILL — correct, needs AVX-512 |

**The v2 build runs correctly on a 2008 CPU and produces every lock pin.** That is the
strongest form of the portability claim available here: not "it should work on old
hardware" but "it produced the exact pins on emulated old hardware".

**The limit, stated because it is easy to over-read:** qemu 8.2's TCG **cannot emulate
AVX-512 at all** — every CPU model reports `avx512f=0`, including `max` and
`SapphireRapids`. So the native build's SIGILL under emulation is **qemu's gap, not evidence
about the binary**, and no AVX-512 build could be executed this way. The AVX-512 results in
this document come from disassembly and from the pins on the real machine, not from
emulation. The SandyBridge SIGILL on v3 is still meaningful as a negative control because
AVX2 *is* emulated and correctly reported absent there.

---

## 8. What this does and does not establish

**Established:**
- The `FORGE_PORTABLE` path exists, builds, and is correct at v2 and v3 — 11 pins, 6 perft
  positions, 120 positions × 5 fields, 120 static evals, all exact.
- Portable costs **+16.1%** at v2 and **+4.2%** at v3 against a native `sapphirerapids`
  build, at a fixed node budget, with the direction share given for each.
- The drawn-root bail, including the mate-in-one forfeit, is **byte-identical** on all
  three builds.
- The v2 build executes correctly on emulated Nehalem and reproduces every pin.
- The default portable option is **2.8 points more expensive at v3 than it needs to be**.

**Not established:**
- **NPS on the owner's machine.** This is a different CPU (Xeon, 4 cores) from the lock's
  `znver5`; the ratios are this machine's. The v3 PEXT result in particular should be
  re-timed on the owner's hardware before the CMake change in §6 is made.
- **Anything at AVX-512 beyond disassembly.** No AVX-512 build was executed in a
  lower-ISA environment, because no available emulator can.
- **Whether a v2 build is *adequate* for play.** A 16% slowdown is a real cost to search
  depth at fixed time, but no game-level measurement was made, so no Elo statement is
  possible in either direction.
- **The +1.4% and +2.3% rows**, which are of the same order as this machine's 1.4%
  between-run drift (§4).

---

## Reproducing

```bash
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
git worktree add /tmp/wt/base 6b98f217

scripts/build_all.sh                       # builds native, v2, v3, v4both + 2 controls
scripts/check_pins.sh /tmp/build/native/forge    # the gate; must pass before comparing

python3 scripts/identity.py                # §3 correctness sweep
python3 scripts/bail.py                    # §5 drawn-root bail
python3 scripts/abba.py <A> <B> <fens> "go nodes 200000" out.json   # one arm
#   ... run both arms (A,B) and (B,A), then:
python3 scripts/final_table.py             # §4 corrected ratios
```

The scripts expect `/tmp/build/<name>/forge`; `PORTABLE_WORK` in `abba.py`'s caller and the
`SRC`/`OUT` env vars in `build_all.sh` relocate them.
