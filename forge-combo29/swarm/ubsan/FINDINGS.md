# Undefined-behaviour sweep — forge-combo29, audit base `6b98f217`

## The flag line first, because this report is about instrumentation

```
/usr/bin/g++ 13.3.0 (Ubuntu 13.3.0-6ubuntu2~24.04.1)  LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
cmake 3.28.3  -DCMAKE_BUILD_TYPE=Release  -DFORGE_MARCH=x86-64-v4

-fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g
```

resolved, from `CMakeFiles/forge.dir/flags.make`:

```
CXX_FLAGS = -fsanitize=undefined,address -fno-sanitize-recover=all -fno-omit-frame-pointer -g -O3 -DNDEBUG -std=c++20 -O3 -ffp-contract=off -fno-fast-math -march=x86-64-v4
```

runtime:

```
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0:report_error_type=1
ASAN_OPTIONS=detect_leaks=1:abort_on_error=1:detect_stack_use_after_return=1
```

binaries:

| build | sha256 |
|---|---|
| UBSan+ASan, the sweep build | `3104e9a5616ee6d4670b8aa97586be7d185b3a4d97cde8e155c0ca298c2cbcaa` |
| no sanitizer (baseline) | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |
| UBSan+ASan with the float checks named | `b6514b9f4a968b3b75ebb99c8810a043443683aa6e44e45ba720cb82c7070427` |

Evidence: `evidence/provenance.json`.

## The answer

**UBSan clean, and the zero is instrumented.** 2,408 bounded probes across 12 phases, **0 UBSan
reports, 0 ASan reports, 0 leak reports at exit**, 0 crashed processes, 0 engine restarts, and the
four honesty pins reproduced exactly on the sanitizer build. Every phase carries positive evidence
that its code actually executed, so the zero is not a corpus that could not reach the condition.

The caveats that belong beside it, and that are worth more than the headline:

- coverage is **not** the whole engine — the audit's own figure is that `bench` reaches 63.0% of
  lines (measured by another seat, not by me; I did not run a line-coverage build), and the paths
  this sweep does not reach are named in "What this does not cover" below;
- the *default* `-fsanitize=undefined` group in GCC 13 **silently omits the two float checks that
  matter most for an NNUE output** (§2), and `-fsanitize=integer` **is rejected by GCC 13.3, the
  only GCC on this image** (§3);
- three of my first twelve planted faults were bad plants, not sanitizer gaps (§1). Diagnosing them,
  rather than reporting them as sanitizer limits, was the most load-bearing part of this seat.

## Four pins on the sanitizer build

Run through the same driver, `bench N` on stdin as UCI commands (`./forge bench 11` as argv prints
nothing and exits 0):

| pin | wanted | measured on UBSan build | match |
|---|---|---|---|
| `bench 11` | 312,866 | 312,866 | yes |
| `bench 13` | 862,329 | 862,329 | yes |
| `bench 16` | 3,024,920 | 3,024,920 | yes |
| `go perft 5` startpos | 4,865,609 | 4,865,609 | yes |

Net-off signature also unchanged, so both nets carry identical arithmetic under instrumentation:
`bench 11/13/16` = 375,354 / 907,205 / 2,448,617, matching `scripts/check_pins.sh`. This is the
expected result — UB instrumentation does not change defined arithmetic — and it doubles as a check
that the instrumented binary is still the same engine.

## 1. Non-vacuity: proof the sanitizer was live and the workload reached the code

A zero from an unproven sanitizer is not a zero.

### Symbols

```
nm build-ubsan/forge | grep -c __ubsan_   ->  15
nm build-base/forge  | grep -c __ubsan_   ->   0
nm build-ubsan/forge | grep -c __asan_    ->  35
nm build-base/forge  | grep -c __asan_    ->   0
```

The 14 distinct handlers are `add_overflow`, `sub_overflow`, `mul_overflow`, `negate_overflow`,
`divrem_overflow`, `shift_out_of_bounds`, `load_invalid_value`, `out_of_bounds`, `type_mismatch_v1`,
`pointer_overflow`, `nonnull_arg`, `builtin_unreachable`, `invalid_builtin`,
`dynamic_type_cache_miss`, plus the `vptr` cache. Evidence: `evidence/symbols.json`.
Reproduce: `scripts/symbol_proof.sh`.

### 12 planted UB classes, one per check class, all caught

Each plant is injected into a path the workload really drives, built with the same flags, and run
through **the same phased harness** that produced the clean result — so the detector that reports
"dirty" here is byte-identical to the one that reports "clean" on the real build.

| # | class planted | caught | report (verbatim) |
|---|---|---|---|
| 1 | signed integer overflow (add) | YES | `uci.cpp:579:41: runtime error: signed integer overflow: 2147483640 + 100 cannot be represented in type 'int'` |
| 2 | shift exponent out of range | YES | `uci.cpp:579:57: runtime error: shift exponent 64 is too large for 64-bit type 'long long unsigned int'` |
| 3 | invalid `bool` value | YES | `uci.cpp:578:38: runtime error: load of value 2, which is not a valid value for type 'bool'` |
| 4 | invalid enum value | YES | `uci.cpp:579:39: runtime error: load of value 9, which is not a valid value for type 'Probe'` |
| 5 | misaligned access | YES | `uci.cpp:149:46: runtime error: load of misaligned address 0x7fff61488bc1 for type 'unsigned int', which requires 4 byte alignment` |
| 6 | null dereference | YES | `uci.cpp:578:37: runtime error: load of null pointer of type 'volatile int'` |
| 7 | negation overflow | YES | `uci.cpp:593:37: runtime error: negation of -2147483648 cannot be represented in type 'int'; cast to an unsigned type to negate this value to itself` |
| 8 | division by zero | YES | `uci.cpp:593:41: runtime error: division by zero` |
| 9 | signed integer overflow (mul) | YES | `uci.cpp:578:41: runtime error: signed integer overflow: 100000 * 100000 cannot be represented in type 'int'` |
| 10 | array index out of bounds | YES | `uci.cpp:579:46: runtime error: index 8 out of bounds for type 'int [8]'` |
| 11 | signed integer overflow (sub) | YES | `uci.cpp:579:44: runtime error: signed integer overflow: -2147483648 - 5 cannot be represented in type 'int'` |
| 12 | pointer index overflow | YES | `uci.cpp:152:19: runtime error: pointer index expression with base 0x7ffef1c4a210 overflowed to 0x80007ffef1c4a210` |
| — | **control**: unplanted build, identical harness | **NO** | (no sanitizer line) |

12 of 12 caught, control clean. Evidence: `evidence/planted-faults.json`.
Reproduce: `scripts/run_plants2.sh`.

### The three plants that failed the first time, and why

My first sweep caught 9 of 12. Reporting 9/12 as a sanitizer result would have been wrong, and
"the sanitizer misses these three classes" would have been a fabricated finding. Each failed plant
was my error:

- **Plant 4 (invalid enum).** I used `enum class P : unsigned char`. With a *fixed underlying type*
  every value of the underlying type is a valid value, so the load is **not** undefined behaviour
  and UBSan is correct to stay silent. Changing to a plain enum with range 0..1 made it fire
  immediately. The microprobe that settled it: a scoped enum with a fixed underlying type accepts 9
  silently; a plain enum reports `load of value 9, which is not a valid value for type 'Scoped'`.
- **Plant 5 (misaligned).** `alignas(8) unsigned char buf[16]` read at `buf+1` inside the same
  function lets the compiler compute the address, so it drops the check entirely — `objdump | grep -c
  ubsan` on that function returned **0**. Passing the pointer through a `noinline` function made it
  fire. The check was never emitted, so this was never a sanitizer gap.
- **Plant 12 (pointer overflow).** `storage + 9223372036854775807LL` is a compile-time-constant
  offset; the compiler folded it and emitted no check. Indexing through a `noinline` helper with a
  runtime index made it fire.

The generalisable rule, and the reason this is in the report rather than a commit message: **a
planted fault that does not fire is evidence about the plant until you have shown the check was
emitted.** `nm` on the binary is not enough — the handler can be linked for other call sites. For
these three, disassembly or a non-foldable reproduction was the discriminator.

## 2. The default `undefined` group omits the float checks, and that is on the NNUE output path

GCC's `-fsanitize=undefined` does **not** include `float-cast-overflow` or
`float-divide-by-zero`. Demonstrated both directions on the same planted fault, on the eval path:

```
volatile float huge = 1e30F;
volatile int sink = static_cast<int>(huge);
```

| flags | sanitizer lines |
|---|---|
| `-fsanitize=undefined,address ...` | **0 — NOT CAUGHT** |
| `-fsanitize=undefined,address,float-cast-overflow,float-divide-by-zero ...` | **10** |

the caught line:

```
/tmp/forge/plants/pf/src/uci.cpp:578:54: runtime error: 1e+30 is outside the range of representable values of type 'int'
```

This is not academic for this engine. `src/nnue.cpp:274` is exactly this construct:

```274:274:forge-combo29/src/nnue.cpp
    return static_cast<int>(std::clamp(centipawns, -30000.0F, 30000.0F));
```

The `std::clamp` is what makes it safe — clamped to ±30000, the conversion cannot leave `int` range
— so **this is not a defect**, and I am not reporting one. What it means is narrower and still
worth recording: the sanitizer configuration the brief specifies was never checking the one
float→int conversion in the evaluation path, so a future edit that moved or removed that clamp would
not have been caught by the sweep described above. The widened arm (`evidence/float-arm-summary.json`)
re-ran eval (240 positions), the stress corpus, `go mate` and the book under the named checks:

**643 probes, 0 sanitizer lines, 0 at exit, 0 crashes**, and the non-vacuity audit passes on it.
That arm is the one that would catch a future regression here.

## 3. `-fsanitize=integer` does not exist in GCC — the requested widening is not runnable here

GCC 13.3 rejects the group outright:

```
g++: error: unrecognized argument to '-fsanitize=' option: 'integer'
g++: error: unrecognized argument to '-fsanitize=' option: 'implicit-conversion'
g++: error: unrecognized argument to '-fsanitize=' option: 'unsigned-integer-overflow'; did you mean 'signed-integer-overflow'?
g++: error: unrecognized argument to '-fsanitize=' option: 'implicit-integer-truncation'
```

`-fsanitize=integer` is a **clang** group. Clang 18 is installed on this image but its UBSan runtime
is not — `libclang_rt.ubsan_standalone-x86_64.a` is absent and `-lstdc++` is not found — so the
integer arm cannot be run here without installing packages, which I did not do.

What that leaves untested, stated plainly: **unsigned integer overflow and implicit integer
conversion are not checked by anything in this report.** `-fsanitize=undefined` includes
`signed-integer-overflow` (plant 1, 9, 11 prove it fires) but deliberately excludes unsigned
wraparound, which is defined behaviour in C++ and therefore not UB. Anything in this engine relying
on a signed→unsigned or narrowing conversion being benign is unchecked. If a future seat reports
`-fsanitize=integer` results on this repo, the flag did not compile.

## 4. Exit-time reports: proven readable, and proven missable

A sanitizer that reports at exit cannot be read to `bestmove`. I did not take that on trust, because
my own clean result depends on it.

I planted an **exit-only** fault — an `atexit` handler that runs after `quit`, after the last
`bestmove`, after `uci_loop` returns 0 — and ran two readers against the same binary:

| reader | verdict | what it saw |
|---|---|---|
| stop at `bestmove`, then kill the child | **CLEAN** | nothing |
| send `quit`, drain to EOF, wait for exit status | **REPORT** | `uci.cpp:155:29: runtime error: signed integer overflow: 2147483640 + 100 cannot be represented in type 'int'`, exit code **1** |

The naive reader records a clean zero on a binary that does have UB, and the exit code (1, not 0) is
the only other tell. Evidence: `evidence/exit-drain-contrast.json`. Reproduce:
`scripts/exit_contrast.py <exe>`.

**How the sweep drains.** Every phase is one engine process. At the end of each phase the harness
sends `quit`, then keeps reading until EOF, then `wait()`s for the exit status. The report separates
in-run sanitizer lines from at-exit ones per phase, and both are zero:

```
"at_exit_sanitizer_lines": 0
```

for all 12 phases, with `"drained_to_eof": true`. The contrast above is what makes that field
meaningful rather than decorative.

## 5. The workload

2,408 bounded probes, 12 phases, ~20 minutes wall on the sanitizer build (1,204.7 s), each phase a
separate process drained to EOF. Nothing was ever piped into a live search: the driver reads to the
terminal token of every command before writing the next, and a watchdog sends `stop` — never `quit`
— to any probe that overruns its bound.

| phase | probes | what it drives | non-vacuous |
|---|---|---|---|
| `pins` | 8 | `bench 11/13/16`, net on and off | 6 node counts, all match |
| `perft` | 50 | `go perft 5` startpos + `go perft 4` on 24 real positions | 24/24 returned `nodes`, startpos = 4,865,609 |
| `depth` | 1,446 | **240 real positions × MultiPV 1/2/4 at depth 12** | 720/720 searches with nodes > 0, 94.6 M nodes |
| `deep` | 42 | depth 16 on 20 positions | 20/20 with nodes > 0, 7.1 M nodes |
| `netoff` | 182 | 60 positions depth 12 + `eval`, net **off** | 60/60 with nodes, 60 eval lines |
| `eval` | 480 | `eval` on all 240 positions, both nets | 240/240 lines contain `hce` and `nnue` |
| `mate` | 30 | `go mate 1/2/3/5` over 6 mate positions | 24/24 searches answered |
| `book` | 54 | embedded polyglot: OwnBook on/off × variety 0/30/100, clocks, `movestogo`, 3 opening sequences | 11 book moves produced |
| `stress` | 44 | 11 extreme-material positions: `eval` + depth 13 + perft 3 | 11/11 with nodes > 0, 11 eval lines |
| `stress_netoff` | 35 | same 11 at depth 12 with the net off | 11/11 with nodes > 0, 29.2 M nodes |
| `malformed` | 17 | `go nodes abc`, `go mate abc`, `go perft 99`, `go depth 999999`, 21-digit node count, `go movestogo 0`, `go mate 99`, `go infinite`, `go ponder`, … | all bounded and replied/refused |
| `protocol` | 17 | 8 malformed `position` forms each followed by a search, `ucinewgame` | 8/8 follow-up searches with nodes > 0 |

**Totals: 2,408 probes, 0 sanitizer lines, 0 at-exit lines, 0 dead processes, 0 restarts.**

Evidence: `evidence/workload-summary.json`.

### Real positions

240 positions sampled from the repo's own self-play PGN chunks (9,726 games parsed, 240 unique
positions, plies 12–119), each validated with python-chess 1.11.2 as `STATUS_VALID` before use, and
each checked to be non-terminal. **The engine was also verified not to have refused a fixture** —
a refused FEN silently searches the previous board, which would make any clean result vacuous. The
`position` barrier is `isready`/`readyok`, not `ready` on a guessed prefix. `scripts/audit_vacuity.py`
fails the `perft` phase outright if any probe carries a refusal, and that assertion has been proven
able to fail: planting one `info string invalid FEN` into a clean run turns the phase red
(`refused_fixtures: 1`, `ran: false`, exit 1) while the clean run stands at 0 refused and exit 0.
Evidence: `evidence/audit-negative-control.json`. In the reported run, refusals in the perft phase: **0**.

### The stress arm: extreme material through the NNUE accumulators

The brief points at the integer accumulators as the most likely home for a shift or overflow that
only fires on extreme values. Extreme material here means up to **9 queens a side plus rook, bishop
and knight (13 men per side)**, and **12 knights a side** — all python-chess-legal, all **live**
(legal moves for the side to move), so a 0-node search could not be explained by a terminal position.

That last part is a correction to my own corpus. The first version had 4 of 11 positions already in
checkmate; they returned `bestmove 0000` with 0 nodes, which looks like coverage but is a terminal
position. I rebuilt the corpus so every position is live, and the count of searches with nodes > 0
went from **7 of 11 to 11 of 11**. The checkmate positions were not evidence, and counting them as
coverage would have inflated the arm by 36%.

What the arithmetic actually saw, for the record: `nnue.cpp` accumulates in `float` lanes
(`Accumulator::values` is `float[HiddenSize][2]`), so the accumulator path is **floating point, not
integer** — there is no integer accumulator to overflow here, and no shift on the NNUE path. The
integer arithmetic in the evaluator is the final `static_cast<int>` (§2), which the widened arm now
covers. Float overflow to infinity is **not** UB and therefore not something UBSan can report at all
— that limit is stated in "What this does not cover".

## 6. What this does not cover

Stated because a clean sweep implies more than it should if these are left implicit.

- **Integer overflow of the unsigned or implicit-conversion kind.** Unreachable on this image (§3).
  Nothing here should be read as "no integer overflow in this engine".
- **Float NaN/Inf propagation.** UBSan cannot report it; it is not UB. If the accumulator produces
  Inf on extreme input, every check in this report stays silent. A `-ffast-math`-off, NaN-tracking
  harness would be a different seat.
- **Strict aliasing.** No UBSan handler exists for it in GCC (`nm | grep -ci alias` = 0) and the
  brief's own list says "where detectable" — it is not, by this tool. A misaligned or
  type-punned access that happens to be aligned will pass silently.
- **Data races and threading.** This is UBSan+ASan, not TSan. `Threads` was left at 1 throughout,
  deliberately, so the run is deterministic; the threaded paths are as unchecked here as they were
  before. This does **not** close any of the 27 findings attributed to the "TSan build".
- **Coverage is a fraction of the binary.** The audit's figure for `bench` is 63.0% of lines (not my
  measurement — I ran no coverage build); this sweep drives much
  more than `bench` (perft, the book, `apply_position` via the protocol phase, `parse_limits` via the
  malformed phase, clock searches), but there is no line-coverage number for this run, so the honest
  statement is "these paths ran", not "all paths ran". Named as unreached: the NNUE v3 path
  (`FORGE_NNUE_V3=0` in this build, so `nnue_v3.cpp` is compiled out entirely), the ponder-hit path
  beyond a single `go ponder`+`stop`, and the Windows-specific build.
- **Duration.** ~20 minutes of engine time. Long by this audit's standards, not a soak.

## 7. One defect found in my own harness, worth recording

My first complete run reported `sanitizer_lines: 0` and it was **not trustworthy**, for a reason that
has nothing to do with the engine: the driver's token matcher accepted a *partial* line. The
terminating line — `nodes 4865609`, every `info string eval`, every bench signature — stayed in the
buffer and never reached the evidence. The run looked clean and its per-probe records were empty.

I found it only because I wrote a non-vacuity audit (`scripts/audit_vacuity.py`) that asserts each
phase produced positive evidence, and it failed on a run whose headline number was 0. Had I trusted
the headline, I would have published a clean negative backed by evidence that had silently dropped
the lines proving anything ran. The fixed matcher requires a complete line; the eval phase went from
`eval_lines_with_hce_and_nnue: 0` to `240`.

Two smaller ones, same family: `bench` prints `info string bench depth D nodes N`, which is not an
`info depth D ... nodes N` search line, so the pin check read `null` until it was taught the bench
form; and a probe that finds its token in the same read as trailing output was not draining the
remainder, which is why the stress `eval` lines were missing for 11 positions that had run fine.

The pattern across all three: **a harness that cannot show its evidence is indistinguishable from a
harness that found nothing**, and the only reason I caught it is that I asked the evidence to prove
it existed instead of asking it to be clean.

## Files

- `scripts/build_sanitizer.sh` — the build, flag line included, reproducible from the file alone
- `scripts/symbol_proof.sh` — `nm` counts on both builds, handler list
- `scripts/driver.py` — bounded UCI driver; reads to the terminal token, never pipes into a search
- `scripts/workload2.py` — the 12-phase workload; one process per phase, drained to EOF
- `scripts/audit_vacuity.py` — per-phase proof that the code ran, not just that nothing was reported
- `scripts/inject_plants.py` — the 12 planted UB classes, one per check class
- `scripts/run_plants2.sh` — builds and runs every plant through the same harness, plus the control
- `scripts/exit_contrast.py` — the `bestmove`-then-kill vs drain-to-EOF contrast
- `scripts/mk_positions.py` — samples and validates the 240 real positions
- `scripts/mk_stress_live.py` — builds the live extreme-material corpus
- `scripts/check_consistency.py` — every number in this report against `evidence/`; 60 checks
- `evidence/provenance.json` — compiler, flags, hashes, env
- `evidence/symbols.json` — sanitizer symbol counts and handler names
- `evidence/planted-faults.json` — 12/12 caught, control clean, verbatim lines
- `evidence/exit-drain-contrast.json` — the two readers on one exit-only fault
- `evidence/float-check-gating.json` — plain vs named float checks on the same fault
- `evidence/workload-summary.json` — per-phase counts, non-vacuity audit, totals
- `evidence/float-arm-summary.json` — the widened arm
- `evidence/audit-negative-control.json` — the refusal check proven able to fail
- `evidence/consistency-negative-control.json` — the report-vs-evidence check proven able to fail
