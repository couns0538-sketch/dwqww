# S15 SPSA harness (v2): `forge_sol_S15_spsa_v2.py`

A box-side SPSA tool for Forge's `tune::` search parameters. It is a tool only: it never edits engine source,
never changes a default and never applies a tune. Python 3.10+ standard library; tested on Windows CPython 3.14.7.
v2 is Sol's prepared v1 (`forge_sol_S15_spsa_20261027.py`, sha256 `5f1f5978…72f6`, on `forge/sol-pack31-20261025`
@ `17aa0cae`) plus a PC driver (`run`) and the fixes found on the PC. `logs/v1_to_v2_tool.diff` shows every change.

## Modes
| mode | what it does | starts processes |
|---|---|---|
| `catalog` | parses every `tune::` integer (name, default, minimum, maximum) from `<source>/src/search.cpp`, fail closed | no |
| `demo` | N-iteration SPSA on a synthetic objective (convergence and determinism check) | no |
| `plan` | one iteration's fastchess command from a captured UCI reply (Sol's ask step) | no |
| `observe` | reads one finished paired PGN through the owned `tools/match/pgn_stats.py` (sha256-pinned) and makes one SPSA update | no |
| `run` | the PC driver: captures the engine's own `uci` reply, then for each iteration: `plan` → proves that both probe settings are applied → runs the planned fastchess command → `observe` → cross-checks the pentanomial with fastchess's own report | yes (engine for UCI capture, fastchess) |

The lock tree (AL1 s198, `src/search.cpp` sha256 `44680416…0e55`) has **51** ranged tunables. **NetScale does not
exist** in it and stays unsupported (`unsupported_requested: ["NetScale"]`); no range or alias is invented.

## Engine requirement: an exposed build
The release lock exe accepts tunables through `setoption` but does not advertise them, and fastchess `-strict`
refuses options an engine does not advertise (`logs/step3_fastchess_probes.log`, probe C). Build the unchanged lock
source with `-DFORGE_EXPOSE_TUNABLES=1` (an existing CMake option of the lock tree; it only adds `option name …`
lines). The PC box recipe:
```
nice -n 19 bash build_pc.sh <lock tree> F:/opus_scratch/sol_s15/build/forge_s15_exposed.exe -DFORGE_EXPOSE_TUNABLES=1
python -I -B <lock archive>/2_build/uci_check.py <exposed exe> --full     # must print ALL OK (AL1 bench x5, perft)
```
The exposed build advertises each tunable with its *current* value, so `uci`, `setoption …`, `uci` proves that the
engine applied a setting. `run` does this for the plus and the minus setting of every iteration.

## Usage
```
# the parameter table
python -I -B forge_sol_S15_spsa_v2.py catalog --source <lock tree> --out <NEW dir>
# synthetic 20-iteration dry run (all 51 parameters, no engine)
python -I -B forge_sol_S15_spsa_v2.py demo --source <lock tree> --seed 20261027 --iterations 20 --out <NEW dir>
# the PC fixture run used for acceptance (2 parameters x 4 iterations x 2 pairs, Idle priority)
nice -n 19 python -I -B forge_sol_S15_spsa_v2.py run --source <lock tree> \
  --engine <exposed exe> --fastchess C:/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe \
  --openings <lock tree>/tools/openings/forge-10000.epd --select LmrQuietBase,QsSeeMargin \
  --iterations 4 --pairs 2 --tc 2+0.02 --seed 20261027 --gain 0.05 --perturbation 0.1 \
  --priority idle --iteration-timeout 120 --max-wall-seconds 540 --min-free-ram-gib 6 --out <NEW dir>
```
`plan`/`observe` can also be driven by hand (see Sol's deferred-smoke notes); `run` chains them through
`--state <observed_state.json>`. Always pass `--tc`: the inherited default `0.25+0.01` is too short for a loaded PC.

## Safety properties (each is tested; `mutation_check_v2.py` plants a bug for each one)
- Writes only into a NEW `--out` directory (refuses an existing one; every file is created exclusively). Inputs are
  sha256-pinned and re-checked; a changed engine, fastchess, opening file, UCI capture or source fails the step.
- Children start at **Idle** (default) or BelowNormal priority (Windows priority class; POSIX nice 19/10), never
  above the caller. On this PC the gate engines run at BelowNormal and self-play/training at Idle, so use `idle`.
- One engine thread (`option.Threads=1`), `Hash=16`, `OwnBook=false`, `-concurrency 1`, reversed colours per pair.
- Fail closed: a non-zero fastchess exit, a timeout (the child is killed), a non-normal termination, an incomplete
  pair, openings that differ from the plan, a pentanomial that disagrees with fastchess's own report, hidden
  tunables or a setting the engine did not apply all stop the run with status `FAILED` and no gradient. Free RAM
  below `--min-free-ram-gib` or a wall budget that cannot fit another iteration stop it before the next iteration.
- `run_summary.json` always records `tune_applied: false`, `engine_source_modified: false`, `strength_claim: null`.

## v2 changes to Sol's v1 (all marked `v2:` in the source)
1. **No `-maxmoves 200`.** Fastchess tags a max-moves draw `[Termination "adjudication"]`; the owned checker rejects
   that, so any game reaching the cap voided its iteration (the PC probe had a 252-ply game). Games end by the rules.
2. **En-passant normalization.** Fastchess writes an e.p. square that no pawn can capture as `-`; v1 compared all four
   FEN fields and failed (3,209 of the 10,000 book openings carry an e.p. square). v2 matches placement, side and
   castling exactly and the e.p. field equal or `-`; each played FEN must match exactly one planned opening.
3. **Openings rotate per iteration** (`sha256(seed:iteration\nfen)` order); v1 replayed the same pairs every iteration.
4. **Windows determinism:** explicit UTF-8 reads; SHA256SUMS and EPD written in binary (LF), so outputs are byte-equal
   to Sol's Linux outputs (the 20-iteration demo reproduces his losses and 21 of 21 files byte for byte);
   CRLF-tolerant PGN parsing (the original bytes are still copied unchanged).
5. `-report penta=true` for the cross-check; `main` split into `execute` (raises) and `main` (prints); new `run` mode.

## Tests
```
FORGE_S15_TEST_ROOT=<NEW dir> python -I -B test_forge_sol_S15_spsa_v2.py -v     # 29 tests, about 3 s
python -I -B mutation_check_v2.py <NEW dir>                                       # 16 planted bugs, about 2 min
```
13 tests are Sol's v1 tests (assertions unchanged; paths ported). 16 v2 tests cover the changes above, the process
priority and timeout, and the `run` loop with a Python fake engine and an in-process fake fastchess (state chaining,
rotation, the fail-closed paths, RAM and wall guards). No real engine or fastchess runs in the tests.

## Limitations
- The proposed values from a 16-game fixture run are noise. Real tuning needs thousands of games per parameter and
  belongs on a quiet machine or CI, then a gate; this tool does not do that and claims nothing about strength.
- Execution binding is partial: `run` proves the exact pinned binary applies both settings and that fastchess's
  own result equals the checker's, but a PGN still cannot prove move legality (fastchess `-strict` checks that).
- `catalog` is an exact parser for the lock's `tune` namespace layout, not a general C++ parser; another layout fails
  closed.
