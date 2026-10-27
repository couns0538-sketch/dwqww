# S45 [Sol leftover] New-lock rebase readiness for speed and search candidates — DONE

`SOL_LEFTOVERS_FOR_CLAUDE.md`, section 2, item 27. The spec is Sol's inventory (`jobs[]` S45); crew rework: "lock-agnostic,
with a dry run on both candidate bases". Sol never started it: there are no S45 files on `17aa0cae`. Work and results by
a sub-agent; this report text is its hand-back.

Branch `opus-sol-S45` = `d4f4312` + `0d99f02` cherry-picked (`14ad2d1d`) + `5abecd3a` (`[skip ci]`) + the REPORT commit.
**Tool only:** `git diff --stat 294dbed..HEAD -- src include tests tools bench CMakeLists.txt` is empty.
Machine exclusive: **no**; nice 19 / Idle, one compiler or engine process at a time, free RAM ≥ 6 GB. **No Elo or
speed claim.**

## Result
- **Spec candidates:** all 7 are READY on all three bases (P23b, P27R, buffix, timepack4, S11, S13, S29; S12 and
  S14 have nothing to rebase).
  - AL1 s198: the base that confirmed (G120 H1 + G120c H1), so this is the real run.
  - e48f006 and e48f029 on the AL1 tree: dry runs.
- **Opus candidates (extra):** the 9 O/C candidates are READY on e48f006.
- Tables: `REBASE_READINESS_20261027.md`.

## Acceptance
| line | result | evidence |
|---|---|---|
| a script plus a table (lock-agnostic) | **PASS** | `forge_sol_S45_rebase_ready.py` (`run`, `voids`), `REBASE_READINESS_20261027.md`, `README.md` |
| rebuilds the queued search candidates and speed patches on the new base | **PASS** | `candidates_20261027.json`: P23b (G121), P27R (G118), buffix, timepack4, S11, S13, S29 (+ S12/S14 as nothing to rebase); patches in `patches/` with sha256 |
| every patch applies with both commands on the new base | **PASS** | `git apply --check -p1` and GNU `patch -p1 -F0 --dry-run`: 7/7 on each base, 0 offsets (`logs/step4_runs.log`) |
| OFF bench = the new base's bench at all 5 depths | **PASS** | 21/21 candidate-base pairs (`logs/rebase_*.json`); builds with the lock recipe, FMA 0 |
| d16 ON≠OFF precheck per tunable patch | **PASS** | P23b ON 3160733 / 2957682 / 2793391 and P27R ON 2830435 / 3037089 / 3086416, vs OFF 3024920 / 3024381 / 2983425 (AL1 / e48f006 / e48f029); S11/S13/S29 ON = base at all depths; timepack4 inert at fixed depth by design |
| table of void gates | **PASS** | `voids` on read-only copies (manifest `09c995b6…`, results `0864d96d…`). Under AL1: 19 VALID (net candidates rebuilt on AL1), 49 OLD_OPPONENT_COMBINE (vs h256_e12 by QA's policy, incl. G121, G118, G84, G113), 0 VOID. For a new lock (e48f006 or e48f029) those 19 become VOID_OPPONENT (`logs/voids_*.json`) |
| runs only after a confirm H1 (until then dry-run on e48f006); dry run on both candidate bases | **PASS** | AL1 confirmed (G120c H1): real run; e48f006 and e48f029: dry runs |
| bases are the right engines | **PASS** | AL1 pins; e48f006 = spec refs = PC prebench of `forge_h256_f006.exe` (G104); e48f029 = PC prebench of `forge_h256_auto_e48f029.exe` (A-e48f029): 395885/1101387/2983425/9988472/19376304 |
| tests + planted bugs | **PASS** | 18/18 (real git/patch on a tiny tree, fake build/bench, fixture manifests) (`logs/step1_tool_tests.log`); 10/10 caught (`logs/step2_tool_mutants.log`) |
| extra: Opus O/C candidates on e48f006 | **DONE** | O1, O1-LTT, O2, O3, O5, O8, C2, C3, C6 READY; C1 N/A (needs Syzygy tables) (`logs/step5_opus_run.log`) |

## Findings
- A net-only lock change is modelled exactly by swapping `src/nnue_weights.inc` on the AL1 tree; the dry-run bases
  reproduce the gated exes' prebench pins.
- Tunable options stay live on every base, but each net shifts the search differently (P23b d16: e12 2594099 →
  AL1 3160733 → f006 2957682 → f029 2793391). A gate result does not transfer across bases.
- 49 queued or held gates (incl. P23b G121 and P27R G118) still play against h256_e12 under QA's COMBINE_LIST
  policy; when checked, the live gate ran `forge_packb_h256` vs `forge_h256_e12`. Their verdicts cannot promote
  anything over AL1. The rebuilt AL1 versions of P23b and P27R are READY.

## Left / UNVERIFIED
- Re-gating P23b/P27R vs AL1 with new srands: QA's decision.
- QUEUED includes the gate currently running (the manifest cannot tell them apart).
- UNVERIFIED: the real effect of the fixed-depth-inert options (timepack4, C3 HardDeadline, O1 SMP); they need
  timed or multi-thread tests. No strength claim for any candidate.
