# S45 — new-lock rebase readiness for speed and search candidates (lock-agnostic tool)

## What is here
| path | what |
|---|---|
| `forge_sol_S45_rebase_ready.py` | the tool: `run` (rebuild every queued candidate on a base, bench it, precheck its option) and `voids` (which queued gates become void for a given lock) |
| `candidates_20261027.json` | the queued candidates: P23b, P27R, buffix, timepack4 (search / time management) and S11-S14, S29 (speed) |
| `patches/` | the candidate patches (copies; sha256 in the config and in `FILES.txt`) |
| `run_s45.sh` | the runs of 2026-10-27: AL1 (the base that confirmed), e48f006 and e48f029 (dry runs) |
| `test_forge_sol_S45_rebase_ready.py`, `mutation_check_s45.py` | tests (real `git apply` / GNU `patch` on a tiny tree; fake build/bench; fixture manifests) and planted bugs |
| `REBASE_READINESS_20261027.md` | the result tables (per base, void gates) |
| `logs/` | step logs, per-base JSON reports, void-gate JSON, build logs (tar.gz) |

## `run`
```sh
python -I -B forge_sol_S45_rebase_ready.py run --config candidates_20261027.json --base-name "<name>" \
  --base-tree <source tree> [--net <net.inc>] [--base-ref d11,d13,d16,d20,d22] --work <new dir> --out-json r.json --out-md r.md
```
- **Base.** The tool copies `--base-tree` (src, include, tests, bench, tools, CMakeLists.txt). With `--net`, that net
  becomes `src/nnue_weights.inc`, which is how a net-only lock change is modelled. It then builds the base with the
  lock recipe (`build_pc.sh`: g++ 15.2 ucrt64, -O3, znver5, static, FMA count printed) and benches it at
  d11/13/16/20/22. `--base-ref` turns that bench into an identity check of the base.
- **Per candidate** (on a fresh copy of the base):
  1. `git apply --check -p1` **and** GNU `patch -p1 -F0 --dry-run` (no fuzz; offsets reported). Both must pass.
  2. Apply the patch. The net file must stay untouched.
  3. Build OFF (default flags), check FMA 0, and bench all 5 depths: they must equal the base.
  4. The ON check, by kind:
     - `tunable`: ON options at d16, nodes must **differ** from OFF. This catches an option that silently does
       nothing on the new base, for example a misspelled hidden tunable;
     - `node_exact`: ON build flags and options at all depths, nodes must **equal** the base;
     - `fixed_depth_inert`: options that by design do nothing at fixed depth (time management), so ON must
       equal OFF at d16, and the real effect needs a timed test (UNVERIFIED);
     - `bugfix_node_identical`: the OFF bench is the check;
     - `none`: nothing to rebase.
- **Verdict.** READY only if every check passes; otherwise NOT READY with the reasons.
- **Safety.** One compiler or engine process at a time, Idle priority. Writes only `--work` and the `--out` files,
  never under `forge_push`, `selfplay_out`, `forge_nnue_train` or `C:\Users\Administrator\grok-pc`. Run the tool
  itself with `nice -n 19`.

## `voids`
```sh
python -I -B forge_sol_S45_rebase_ready.py voids --manifest <copy of forge_gates.json> --results <copy of FORGE_RESULTS.csv> \
  --lock-name <lock name> [--lock-sha <exe sha256>] --out-json v.json --out-md v.md
```
State of each manifest gate:
- DONE: a row in `FORGE_RESULTS.csv`;
- DROPPED: `ok`/`status` says DROPPED;
- HELD: `status` starts with HELD;
- QUEUED: everything else. This includes a gate that is running now; the manifest cannot tell it apart.

Class of each queued or held gate, for the given lock:
- **VALID**: its opponent is the lock (name or exe sha256).
- **VOID_OPPONENT**: its opponent is another engine and the gate carries no policy to keep that opponent. Its
  verdict cannot promote anything over the lock: rebuild the candidate on the lock, then a new gate vs the lock
  with a new srand.
- **OLD_OPPONENT_COMBINE**: QA's explicit policy, "keeps old opponent; an H1 goes to COMBINE_LIST". Only the gate's
  current note counts; a superseded policy quoted after "Old note:" does not. Such a gate is informative only for
  the lock: adoption needs the rebuild (the `run` table) and a new gate vs the lock.

The "candidate built on" column comes from `ag_rebuilt_on`, or else from the exe-name convention (`_AL1`,
`h256`, `ep10`).

## Re-run on the PC
`bash run_s45.sh <this folder> <AL1 tree> <nets dir> <out dir>`. Inputs are read-only copies:
- the AL1 tree comes from `git archive d4f4312`;
- the nets come from the lock archive `5_nnue/nets`;
- the manifest and results are copies of `C:\Users\Administrator\grok-pc\forge_push\autorestart\forge_gates.json` and
  `D:\grok-pc-data\forge_push\FORGE_RESULTS.csv`.

Run it at nice 19 with free RAM ≥ 6 GB. Tests: `python -I -B test_forge_sol_S45_rebase_ready.py`, then
`python -I -B mutation_check_s45.py --work <new dir>`.
