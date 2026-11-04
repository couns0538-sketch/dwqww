---
name: forge-o30-v2net
description: Forge v2 nets (FORGENN2) on the lock engine - the EvalFileV2 port (opus_30h/a/v2port.patch on the lock d4f4312), its proofs (lock net as v2 = lock pins, parity 10000/10000 x AVX2/SSE/scalar vs an own float32 reference, accumulator walk, in-search verify build), the holdout scorer that reproduces the crew's S31 numbers, the training-data audit, the CPU fine-tune trainer warm-started from the lock net, net_pack.sh, the sanity match, and the kit choice (v2.4 -PartialTraining, else the v2 path is cold). Use for any v2 / EvalFileV2 net, a new trained net to check or package, a holdout-loss question, or a speed question about an option-only code path in a kit exe.
---

# Forge v2 nets on the lock (Opus 30-h job, branch opus-30h-20261103)

Tools: `D:\o30\wt\opus_30h\a\` (branch copy `opus_30h/a/`), scratch `D:\o30`. Rules first: forge-pc-rules (latest
round), own work at Idle on CPUs 0-1, D: >= 50 GB / C: >= 30 GB, never delete / kill, no sub-agents.

## Facts
- The lock (FD3A5190, source d4f4312) has no v2 code; `v2port.patch` adds it: header-only `include/forge/nnue_v2.hpp`
  (FORGENN2 loader, king buckets 1-32 + mirror, output buckets 1-16, residual flag; feature set 0 only), loader at the
  end of `src/nnue.cpp`, `Worker::static_evaluate_v2` in `src/search.cpp` (lazy accumulators reuse
  `SearchStack::accumulator`; king-bucket changes refresh through a per-worker cache), UCI string `EvalFileV2`
  (empty = off; a bad file prints `info string ERROR EvalFileV2 ...` and leaves no v2 net active).
- v2 hidden size = the engine's (256). Weights int16 / 4096 like the lock net: every accumulator value is exact, so
  incremental = cached = full refresh bit for bit, and the output kernel has the lock's lane order: the lock net written
  as v2 (`o30_v2net.py from-lock`, any king map without mirror / any output-bucket count) gives the lock's bench
  pins d11-d22 exactly. That is the port's identity test; a random net must be LIVE.
- Residual (flag bit 0) = the lock's HCE + the net, like the compiled-in net. FHCE files = the lock's
  `Evaluator::evaluate_uncached` on every holdout row (checked on 1,024,286 rows).
- Kit: v2.3 profiles the OFF path only -> the v2 path is cold-optimised (0.71x the lock's speed on the same tree).
  Build v2 exes with kit v2.4 `-PartialTraining` (`tools/kit24_build_o30.sh`, kit exported from opus-r12-pgo-net):
  0.959x (CI 0.929-0.990). A plain build has no gap (0.998x).

## Checks (in this order)
1. `pin_check.ps1 -Exe X -Full` (OFF pins); lock net as v2 + `-Expect` the lock pins (PASS); random net ON = LIVE;
   missing file = FAIL with the ERROR line.
2. `bash build_harness_o30.sh <port repo> <new dir>`; `bash parity_o30.sh <new dir> C:\o13\p4\fens10k.txt <harness>
   <nets...>` -> PARITY PASS + planted bug caught; `v2_eval_avx2.exe --walk <net> <seed> 3000 300` -> 0 mismatches
   (use a random KB4 mirrored net: replicated weights hide king-bucket bugs).
3. Verify build: `plain_build_o30.sh <repo> <dir> -DFORGE_NNUE_V2_VERIFY=1` + bench with a random KB4m net: no abort.
4. Holdout: `D:\o30\tools_bin\o30_score_v2.exe --net <file> --pos <S31 .pos> --hce <S31 .hce>`: lock as v2 = b0.6
   0.014310027 / b1.0 0.004572428 (the crew's AL1 numbers); jobA val (`D:\o30\data\jobA_val.*`, 20k-node labels):
   lock 0.013272058.
5. A trained net: `bash net_pack.sh <name> <net> <kit exe> <harness dir>` -> D:\o30\nets\<name>\RESULT.json.
6. Sanity match: `sanity_match.py --out <new dir> --cand-exe <exe> --cand-opt "EvalFileV2=<net>" --games 400 --conc 2`
   then `tools/gate_summary.py <dir>`; sanity only, never an Elo claim.

## Training on the CPU (no GPU window)
- Data: `o30_data.py --out <new dir>`: train = FPOS / FHCE shards 001-039 minus 013 / 014 = the npt binpack's
  304,999,573 rows; skip lists (holdout-overlap board+stm keys 7,706 rows, jobA val, mates), jobA 20k-node overrides.
- `o30_fit.py selfcheck` must reproduce the scorer before training. `fit_bg.sh <name> <mask> --init lock ...`;
  ~50-60k positions/s per CPU (1 torch thread). Checkpoints every --save-minutes, last.pt / best.pt / best.nnue2,
  val.csv per checkpoint; `o30_fit.py stop <run>` (named event) saves and exits; `--resume` continues the same stream.
- Measured: the lock net is converged on its data. KB1 / OB8 fine-tune, 30M positions: lr 5e-6 -> S31 b0.6 -0.8e-6,
  lr 2e-5 -> -0.4e-6 (seed noise of b0.6 ~7e-6; lr 1e-4 made it worse first). Gains need capacity (king buckets) or
  better labels, not more steps.

## Pitfalls (all hit on 2026-11-03)
- Bash-tool commands collapse `\\` before `$var` -> a literal `$var` (a run dir named `runs$1`, a net path the engine
  could not open). Use forward slashes or `cygpath -w`.
- Never cut pin_check output with `head` (the FAIL / ERROR line is the first or the last line).
- `export_src.sh` copies the WORKING tree per kit side: do not edit the scratch repo while a kit build runs (pc2 is
  exported after pc1 finishes).
- JSON from C++ tools: escape the backslashes of Windows paths (the first scorer printed invalid JSON).
