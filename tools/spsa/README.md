# Forge offline SPSA tuner (`tools/spsa`, R3-4)

Tunes integer UCI spin options of Forge with SPSA: every iteration plays a short fastchess mini-match between
theta+ = theta + c_k·Δ and theta- = theta - c_k·Δ (Δ = ±1 per parameter), then moves theta along the measured
score difference. Offline means the tuner is a single Python process that drives fastchess on one machine; it is
resumable at any iteration boundary. Python 3.10+, standard library only.

| file | what |
|---|---|
| `opus_spsa.py` | the command-line tool: session loop, state/CSV, `--dry-run`, `--plan`, `--status`, `--synthetic` |
| `opus_spsa_core.py` | the math: schedule, perturbation, rounding, update, state, synthetic objective (no processes) |
| `opus_spsa_fastchess.py` | fastchess command line, output parser (W/L/D, pentanomial, cross-checked), child processes, free RAM |
| `opus_spsa_uci.py` | engine option discovery and the set-and-reread proof that the engine applies each option |
| `opus_spsa_forge20.json` | example session for the 20 search constants (below), with the `dry_run` block |
| `test_opus_spsa.py` | 30 tests (CTest `opus_spsa_tests`, `opus_spsa_engine_options`) |

## The engine side: 20 advertised search constants

fastchess only sends `setoption` for options an engine advertises (with `-strict` it stops on the warning), and
Forge's ~57 search constants (`forge::tune::parameters()`) were accepted but unlisted. Since R3-4 every build lists
the 20 below as `option name <Name> type spin default <current value> min <min> max <max>`; the rest stay
unlisted (FORGE_EXPOSE_TUNABLES builds list them after these). Defaults are unchanged, so bench and perft equal
the AL1 s198 pins. The null-move margin was a literal (`beta - 24 * depth + 180`); it is now
`NullMoveMarginDepth` / `NullMoveMarginBase` with the same defaults.

c_0 is the first perturbation for the example session (2,500 iterations); r_end is 0.002 for all (fishtest's usual
end learning rate). The sensitivity column is the mean |change| of bench-13 nodes for a ±10% step (at least ±1)
from `opus_r3/R3-4/logs/07_sensitivity_d13_final.log`: a liveness check, not a strength measure.

| group | parameter | meaning (src/search) | default | min | max | c_end | c_0 | r_end | nodes ±10% |
|---|---|---|---|---|---|---|---|---|---|
| LMR | LmrQuietBase | quiet reduction table: base (x0.01 ply) | 85 | 0 | 300 | 8 | 17.6 | 0.002 | 2.5% |
| LMR | LmrQuietDivisor | quiet table: ln(d)·ln(m) divisor (x0.01) | 220 | 100 | 500 | 15 | 33.1 | 0.002 | 12.4% |
| LMR | LmrNoisyBase | noisy reduction table: base (x0.01 ply) | 10 | 0 | 300 | 4 | 8.8 | 0.002 | 7.4% |
| LMR | LmrNoisyDivisor | noisy table divisor (x0.01) | 340 | 100 | 800 | 25 | 55.1 | 0.002 | 6.5% |
| LMR | LmrHistoryDivisor | reduction -= history / divisor (±2) | 6000 | 1000 | 30000 | 500 | 1102 | 0.002 | 5.3% |
| LMR | LmrCutoffThreshold | +1 ply when the child had more cutoffs | 3 | 0 | 20 | 0.5 | 1.1 | 0.002 | 15.5% |
| null move | NullMoveBase | R = base + depth/div + min((eval-beta)/evaldiv, 3) | 3 | 1 | 6 | 0.5 | 1.1 | 0.002 | 9.8% |
| null move | NullMoveDepthDivisor | depth divisor of R | 3 | 1 | 10 | 0.5 | 1.1 | 0.002 | 23.4% |
| null move | NullMoveEvalDivisor | eval-margin divisor of R | 200 | 50 | 1000 | 16 | 35.3 | 0.002 | 11.5% |
| null move | NullMoveMarginDepth | try only if static eval >= beta - this·depth + base | 24 | 0 | 100 | 2 | 4.4 | 0.002 | 11.9% |
| null move | NullMoveMarginBase | (the +180 of that margin) | 180 | 0 | 500 | 15 | 33.1 | 0.002 | 5.0% |
| RFP | RfpMargin | return eval if eval - margin·depth (+improving) >= beta | 72 | 10 | 300 | 6 | 13.2 | 0.002 | 17.8% |
| RFP | RfpImproving | margin cut when improving | 40 | 0 | 200 | 4 | 8.8 | 0.002 | 3.0% |
| RFP | RfpDepth | deepest node RFP applies to | 8 | 0 | 15 | 0.5 | 1.1 | 0.002 | 11.8% |
| futility | FutilityBase | skip quiets if static eval + base + mult·lmr_depth <= alpha | 100 | 0 | 500 | 10 | 22.0 | 0.002 | 0.9% |
| futility | FutilityMultiplier | (per lmr_depth) | 110 | 0 | 500 | 9 | 19.8 | 0.002 | 2.3% |
| futility | QsFutilityMargin | quiescence futility base | 160 | 0 | 1000 | 13 | 28.7 | 0.002 | 4.9% |
| SEE | SeeQuietMultiplier | prune quiet if SEE < -mult·lmr_depth² | 24 | 0 | 200 | 3 | 6.6 | 0.002 | 4.5% |
| SEE | SeeNoisyMultiplier | prune capture if SEE < -mult·depth | 150 | 0 | 1000 | 12 | 26.4 | 0.002 | 5.7% |
| aspiration | AspirationDelta | first half-window from depth 4 | 18 | 4 | 200 | 2 | 4.4 | 0.002 | 15.8% |

### Why these 20
The job asked for LMR, null move, reverse futility (RFP), futility, SEE margins and aspiration. Inside those
groups the choice follows three rules:
1. **Mechanism reach.** LMR, null move and RFP act at most non-PV nodes, so their constants come first; every
   constant that shapes the LMR table and the null-move reduction is in.
2. **A measurable gradient.** SPSA needs a step of c_k to change the search. The bench scan shows every chosen
   constant changes the tree. `QsSeeMargin` was the obvious 20th candidate but is left out: SEE balances are
   multiples of 100 (`SeeValue` {100, 300, 300, 500, 900}), so every value 0-99 searches the identical tree
   (bench 13: 862329 nodes at 0, 40 and 99; 824643 at 100-199; `logs/qsseemargin_steps_d13.log`). Steps of
   ±5-12 around 40 would measure nothing. `FutilityDepth` (0.6%) and `NullMoveMinDepth` (5.6%) changed the tree
   less than `LmrCutoffThreshold` (15.5%), which took the slot.
3. **Literal turned tunable where it matters.** The null-move static-eval margin decides whether null move is
   tried at all; it was the literal `24 * depth - 180`, now two tunables (same defaults, same tree).
Small-range integers (`LmrCutoffThreshold`, `NullMoveBase`, `NullMoveDepthDivisor`, `RfpDepth`) are in on purpose;
with `rounding: randomized` a theta of 3.3 plays 3 or 4 with the right odds, so their gradient is estimated
without bias (S-A6 excluded them for deterministic rounding).

## Algorithm
For N iterations (k = 0 .. N-1), A = A_ratio·N, alpha 0.602, gamma 0.101 and per parameter c_end, r_end:
```
c = c_end · N^gamma                 c_k = c / (k+1)^gamma          (c_{N-1} = c_end)
a = r_end · c_end² · (A+N)^alpha    a_k = a / (A+k+1)^alpha        (a_{N-1} = r_end · c_end²)
theta± = clamp(round(theta ± c_k·Δ), min, max)       played as option.<Name>=<int> of engine 1 (+) and 2 (-)
y = wins - losses of theta+ over the mini-match (P game pairs, colours reversed per pair, same opening)
theta  = clamp(theta + a_k / c_k · y · Δ, min, max)  (float; rounded only at match time)
```
This is fishtest's update (R·c·(W-L)·flip with R = a_k/c_k²). The schedule runs over iterations (mini-matches);
y sums the iteration's pairs, so r_end keeps fishtest's meaning, a learning rate per game pair. Over all 2^n
directions the mean step is exactly 2·a_k·∇f (test `test_expected_step_is_the_gradient`).
Rounding: `deterministic` = nearest integer; `randomized` = floor(x + U[0,1)), unbiased (recommended, and needed for
c_end < 0.5). Δ, randomized rounding and the fastchess `-srand` of iteration k are pure functions of (seed, k), so
a resumed session replays exactly what an uninterrupted one would.

## fastchess
One run per iteration (fastchess 1.8.2 tested):
```
fastchess -engine cmd=<forge> name=spsa_plus option.<P>=<v+> ... -engine cmd=<forge> name=spsa_minus option.<P>=<v-> ...
  -each proto=uci tc=<tc> [nodes=<n>] [timemargin=<ms>] option.Threads=1 option.Hash=16 option.OwnBook=false
  -rounds <P> -games 2 -repeat -concurrency <C> -openings file=<book> format=epd order=random -srand <s_k>
  -pgnout file=<iter dir>/games.pgn -autosaveinterval 0 -report penta=true [-strict] [extra_args]
```
`-strict` is off by default: it makes fastchess stop on any warning, and a single time forfeit is one (seen in the
R3-4 dry run at 0.5+0.005 on the loaded PC). Its other use, refusing options the engine does not advertise, is
covered by the tool's own preflight: before every session (and resume) it runs `uci`, sets each tuned option to a
probe value, runs `uci` again and requires the engine to advertise the new value. Time losses are counted per
iteration (`time_losses` in the CSV and in `--status`); raise the TC or `timemargin_ms` if they are frequent.
The result is read from fastchess's last `Results of spsa_plus vs spsa_minus` block (`Games/Wins/Losses/Draws` and
`Ptnml(0-2)`) and must agree with the per-game `Finished game N` lines (W/L/D and, pairing games 2j-1/2j, the
pentanomial), else the iteration fails. Time losses and terminations are counted per iteration; an illegal move,
disconnect, stall or crash fails the iteration. A failed iteration is retried (`retries`, same Δ and seed); if it
fails again the session stops with the state at the last completed iteration.

## Config (`opus_spsa_forge20.json`)
| key | meaning | default |
|---|---|---|
| `engine`, `fastchess`, `book` | paths (relative to the config file; `--engine/--fastchess/--book` override); `fastchess` may be an argv list | -, `fastchess`, - |
| `tc`, `nodes`, `timemargin_ms` | per-move limits for both engines (`tc` and/or `nodes`) | - |
| `threads`, `hash`, `engine_options` | per engine; `engine_options` e.g. `{"OwnBook": "false"}` | 1, 16, OwnBook false |
| `concurrency`, `max_total_threads` | fastchess games in parallel; refuse configs with concurrency·threads above the cap | 1, none |
| `pairs_per_iteration`, `iterations` | P game pairs per mini-match; N | 4, 1000 |
| `seed`, `A_ratio`, `alpha`, `gamma`, `rounding`, `r_end` | schedule (r_end may also be set per parameter) | 1, 0.1, 0.602, 0.101, deterministic, 0.002 |
| `params` | `{"name", "start", "min", "max", "c_end"[, "r_end"]}` per parameter, engine units | - |
| `strict`, `extra_args` | fastchess `-strict`; extra fastchess arguments (e.g. adjudication) | false, [] |
| `priority` | `idle` / `below_normal` / `normal` for fastchess and its engines (job object / nice) | idle |
| `iteration_timeout_s`, `retries` | kill the fastchess tree after this long; attempts per iteration | 900, 1 |
| `min_free_ram_gib`, `ram_wait_minutes` | wait (then stop cleanly) while free RAM is lower | 0, 30 |
| `allow_start_offset` | permit `start` != the engine default on a new session | false |
| `dry_run` | overrides for `--dry-run`: iterations, pairs, concurrency, tc/nodes, params, max_total_threads, ... | 3 it, 1 pair, conc 2, 0.5+0.005, first 3 params, cap 2 |

## Running
```
# 0. build the engine (any build of this branch advertises the 20; box recipe on the PC) and check it
python -I -B tools/spsa/test_opus_spsa.py --root <new dir> --engine <forge exe>
# 1. look at the schedule and the first fastchess command (no games)
python -I -B tools/spsa/opus_spsa.py --config tools/spsa/opus_spsa_forge20.json --workdir <W> --plan --engine <forge> --fastchess <fastchess>
# 2. smoke session: 3 iterations x 1 pair on 3 params at 0.5+0.005, concurrency 2 -> <W>/dry_run
python -I -B tools/spsa/opus_spsa.py --config tools/spsa/opus_spsa_forge20.json --workdir <W> --dry-run --engine <forge> --fastchess <fastchess>
# 3. the session (resumes automatically from <W>/state.json; --stop-after N ends cleanly after N iterations)
python -I -B tools/spsa/opus_spsa.py --config tools/spsa/opus_spsa_forge20.json --workdir <W> --engine <forge> --fastchess <fastchess>
# 4. where it stands / the values to test: theta, rounded, moved/c_end, setoption lines, fastchess option string
python -I -B tools/spsa/opus_spsa.py --workdir <W> --status
```
On this PC: prefix `nice -n 19`, fastchess `C:/Users/Administrator/grok-pc/tools/fastchess/fastchess.exe`,
`<W>` under `F:\opus_scratch`, venv Python `C:/Users/Administrator/grok-pc/nnue/.venv/Scripts/python.exe`, and
`min_free_ram_gib` 6 (the example has it). Ctrl+C (or a reboot) loses only the running iteration.

Files in `<W>`: `state.json` (theta, next iteration, totals, last record; replaced atomically after each iteration),
`spsa_log.csv` (one row per iteration: W/L/D, pentanomial, time losses, and per parameter c_k, a_k, Δ, values
played, theta after; a row lost to a crash between state and CSV is rewritten on resume), `session.log`,
`config_used.json` (the effective config, fingerprint and sha256 pins of engine and book; a resume with a
changed schedule, match settings, engine or book is refused), `games/iter_<k>_a<attempt>/` (fastchess command,
console output, PGN).

## Suggested real session (not run in R3-4)
Throughput basis: the PC's gates took 29 s per game per slot at 10+0.1 (S-A6, 24 gates); S-A6's model
2·(0.8·base + 65·inc) gives 23.2 s at 8+0.08 and 14.5 s at 5+0.05 (ESTIMATES).

| run | iterations x pairs | games | TC | concurrency | wall time (estimate) |
|---|---|---|---|---|---|
| pilot: are the c_end values audible? | 250 x 8 | 4,000 | 8+0.08 | 8 | ~3.2 h |
| full, 20 params | 2,500 x 8 | 40,000 | 8+0.08 | 8 | ~32 h + the per-iteration tail |
| cheaper | 2,500 x 8 | 40,000 | 5+0.05 | 8 | ~20 h + tail |

- Iterations are synchronous: each waits for its slowest game, so keep `pairs_per_iteration` >= `concurrency`
  (the example: 8 pairs = 16 games on 8 slots). Engines start once per iteration.
- 40,000 games for 20 parameters is the low end of public SPSA practice; with fewer games tune fewer parameters
  (e.g. the LMR and null-move groups first, 11 parameters, as S-A6 staged it).
- Use the gate's opening book, Threads 1, Hash 16, OwnBook false; run in QA slots only. `priority: idle` keeps
  it below gates (BelowNormal) and level with self-play/training; use `below_normal` only in a slot that replaces
  a gate.
- Afterwards: `--status`; apply only parameters that moved more than about c_end (the rest is noise), as new
  defaults in `src/search/tune.inc` (values only, reviewed); then an STC gate (SPRT [0,10] at 10+0.1) and an LTC
  confirm before any lock. The bench changes with any new default, so new pins come from QA.

## Tests
`python -I -B tools/spsa/test_opus_spsa.py [--root DIR] [--engine FORGE_EXE]` (about 10 s; writes only under DIR,
deletes nothing):
- schedule end points and formula, monotone gains; rounding (deterministic halves, randomized mean);
- perturbation values and clamping; update direction and clamping; the exact expected step 2·a_k·∇f;
- convergence on a synthetic quadratic Elo landscape, with expected and with sampled game results;
- sessions: stop/resume equals an uninterrupted run (theta, totals, CSV), CSV row repair, changed config /
  engine refused, failed iteration keeps the state;
- fastchess: parser on the 1.8.2 format (colour codes, CRLF, last block wins), inconsistent outputs fail,
  terminations counted; command line; a fake fastchess end to end (restart, failing and inconsistent runs,
  timeout kills the whole process tree);
- config validation, the dry-run block, UCI option parsing; the example config equals the engine source
  (names and order of `AdvertisedParameters`, defaults in `tune.inc`, ranges in `parameters()`);
- `--engine`: the engine advertises exactly these 20 (defaults = start, same ranges) and re-advertises a value set
  by `setoption` (the application proof the tool also runs before every session).

## Limits
- One machine, synchronous iterations; no distributed workers. No Elo claim: a tuned vector must pass a gate.
- Tree-size sensitivity is not strength; c_end values are heuristics (about 5-10% of the default for margins)
  for the pilot to confirm.
- Only fastchess 1.8.2 (f618e34) output was exercised.
