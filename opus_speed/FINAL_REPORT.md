# Forge speed job - FINAL REPORT

State: FINAL 13:36 (PC clock = Vienna time; drafted from 10:15). Job window 2026-11-05 08:38 -> 14:38; due 14:08.
Follow-ups after FINAL (records in section 8): CR SHOULD leftovers 19:43-19:47 and leftover jobs 1-3 19:5x-20:10.
The live lock since QA's publish is trial_w6 (sha256 4181A589...), and every lock decision is against it.
Every timing and proof run of the job has finished; nothing of this job runs after the final push except the three
idle processes named in section 8.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Scratch `F:\ospd\`. Crew vote: A (speed-only lock path) >
B (bit-exact hot-path changes) > C (gate wall time); D only if A-C are done. No Elo claims anywhere; speed numbers
only from this job's ABBA CSVs (named per row); everything else is UNPROVEN.
**Status tag for every speed number in this report** (lock-path rule, `skills/forge-speed-lock-path/SKILL.md`: 1 BIT-EXACT
incl. the full 12k, 2 L3b warm-table identity, 3 Threads 2-4 smoke, 4 ABBA WIN, 5 QA's own re-time): the six stacks of
sections 3c / 5 have steps 1-4 and are **NOT a lock** - step 5 is owed to QA; the single changes of 3a / 3b have BIT-EXACT
on 2,000 FENs + ABBA only (no L3b, no smoke) and are screening results, not lock candidates on their own. BIT-EXACT +
ABBA alone is never a lock. Nothing in this report is locked.

## 0. Summary
- **Job A (vote 1) - DONE.** A one-command speed-only lock path: `speed_pack.ps1` turns a source tree into an LTO+PGO
  exe built with QA's kit command lines (it reproduces the lock exe FD3A5190 byte for byte), checks pc1 = pc2, runs
  the bit-exact proof (bench net on + off d11-d22, perft, 12k six-field FENs at depth 13, MSVC ASan + g++ UBSan) and
  an ABBA nps comparison against the lock, and writes a QA hand-off file. All three success tests pass (lock-vs-lock
  pack inside the A/A band; a one-constant mutant and a move-order mutant both fail before any ABBA; the best flag
  variant got a full pack). Independent review: no BLOCKER; its 4 SHOULD and 11 LOW items are fixed. No compiler
  flag or build mode beats the lock's own LTO+PGO recipe; a PGO profile taken with the net OFF would cost 29 % - the
  lock is safe from that because its embedded net is ON in the frozen workload.
- **Job B (vote 2) - DONE.** Seven own build switches (nine variants) plus the R14 SPEED2 switch rebased onto them,
  each OFF by default and proven bit-exact (bench net on + off, perft, 2,000 FENs per single / all 12,000 per stack,
  MSVC ASan + g++ UBSan); the all-switches-0 build of every stacked tree is the lock exe byte for byte. Protocol
  (wall nps) winners vs the lock: NO_ZERO_MOVELISTS=2 +3.6 % (mode 1 alone +3.3 %), SPEED2 +3.2 %, and on 26 pooled
  rounds (first run + one 16-round re-time) TT_NOTLS +2.9 %, SLIDER_PEXT +1.5 %, PREFETCH_EARLY +1.4 %, NNUE_ZMM
  +1.4 % (weak: its re-time alone and its pooled cpu metric are NO-WIN); losers: PICKBEST 1 / 2, MATKEY_FAST.
  **stack_w2 = TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2: +11.5 % wall / +11.3 % cpu vs the lock** - QA first
  (section 5). **All six stacked (trial_w6): +14.9 % wall / +15.3 % cpu vs the lock** - the largest winners-only
  stack, second step; stack_w5 = the same without the weak NNUE_ZMM. Measured in one session, trial_w6 is +4.4 %
  faster than stack_w2 (WIN). Every stack: bit-exact incl. the full 12k set, switch-0 build = the lock exe, QA's own
  kit rebuilds it byte for byte. Independent review of the six patches: no BLOCKER, no SHOULD (5 LOW). No Elo claim;
  QA re-times on its own cores. **Status of these headline numbers: lock-path steps 1-4 done for every stack (BIT-EXACT
  full 12k, L3b warm-table identity IDENTICAL 13:27-13:35, Threads 2-4 soak PASS 14:47 - soak only -, ABBA WIN); NOT a
  lock until QA's own re-time (step 5).** The single-change percentages are BIT-EXACT (2,000 FENs) + ABBA only.
- **Job C (vote 3) - DONE** (worker jobc, coordinator re-run ALL PASS): gate replay / LLR projection / throughput /
  adjudication / book / pre-gate screen / concurrency tools; wall time is set by slot count x games; idle gaps are
  small except empty-queue periods.
- **Job D (optional) - DONE as a plan** (worker jobd): the GPU guard has throttled training since Nov 1 because its
  HWiNFO date filter needs a two-digit day (owner item, re-checked).
- Code Review CR_OPUS_SPEED_TOOLS_637B: BLOCKER and SHOULD 1-3 fixed with tests (13/13); the 3 LOW notes were not
  visible on the PC.

## 1. Job A - the speed-only lock path (tools, opus_speed/tools)
| tool | what it does | usage |
|---|---|---|
| build_variants.ps1 | QA kit v2.3 command lines token for token (lp_v1 of the lock source = lock exe FD3A5190 byte for byte); O3 / LTO / PGO / LTO+PGO, flag and PGO-workload variants; pc1 = pc2 with -Twice; fail-closed pins | `build_variants.ps1 -SrcDir <tree> -Tag <t> -Variant lp_v1[,..] [-Twice]` |
| bitexact_check.ps1 | L1 bench d11-22 net on + off, L2 perft, L3 12k six-field FENs at depth 13 (-Quick: 2,000), L4 MSVC ASan + g++ UBSan bench 16; stops at the first FAIL | `bitexact_check.ps1 -Cand <exe> -Out <dir> [-Quick] [-SanSrc <tree>]` |
| abba.ps1 | ABBA/BAAB rounds (>= 10) on CPU 2, fresh copies per round, wall and CPU-time nps, median + Student-t interval, A/A band, WIN rule | `abba.ps1 -A <lock> -B <cand> -Out <dir> -Depth 20 -Rounds 10 -AaCsv <A/A runs.csv>` |
| abba_queue.ps1 / abba_table.py | back-to-back ABBA list, one table from the summaries | |
| speed_pack.ps1 | source tree in -> pack out: flip switch defaults (kit takes no -D), pc1 = pc2, bit-exact proof, ABBA, candidate file | `speed_pack.ps1 -SrcDir <tree> -Name <n> [-Define SW=1] [-Quick] [-ReuseBuildDirs a,b]` |
| make_stack.sh | stacks patches on a fresh lock copy (no fuzz, switch defaults checked) | `bash make_stack.sh <name> <p1.patch> ...` |
| abba_recheck.py | recomputes ABBA summaries from runs.csv with the exact t quantile; `--pool` joins a borderline run and its re-time | `python -I -B abba_recheck.py <dir>..` / `--pool <dir> <dir>` |
| pack_table.py | one markdown table of pack folders (switches, exe, bit-exact state, wall / cpu, verdicts, CSV md5) | `python -I -B pack_table.py F:/ospd/packs --only a,b` |
| warm_identity.py | warm-table identity vs the lock: N FENs with `go nodes`, no ucinewgame, Hash / Clear Hash / UseNNUE changes every 25 FENs, `bench 1` + `go perft 1` as first commands, `bench 13` at the end | `python -I -B warm_identity.py <lock> <cand> <fens> <out> --n 1000 --nodes 20000` |
| commit_push.sh, name_lint.py, ctrl_char_check.py, ps_parse_check.ps1, pgn_positions.py | checked commits, vendor-name lint, control bytes, PS 5.1 parse, game positions | |
Facts the tools are built on (checked 2026-11-05):
- The lock's net is embedded (`nnue_weights.inc`) and ON by default (`UseNNUE` default true). QA's frozen v1 PGO
  workload (`bench 11/13/16`, no setoption) therefore already profiles the net path: the ~12 % "net loaded" loss
  measured earlier belonged to the HalfKA EvalFile builds, not to this lock. Net off = `setoption name UseNNUE value
  false` (pins 375354 / 907205 / 2448617 / 13573040 / 24506465).
- `build_variants -Variant lp_v1` on the exact lock source reproduces the lock exe FD3A5190 byte for byte (sha256
  fd3a5190...; 09:10, and again as pc1 = pc2 inside the lock-vs-lock pack) = our pipeline is QA's kit.
- The R14 SPEED2 switch ported with R14's own script and built here gives exe de20653c..., R14's kit exe byte for byte.
- `fens_12k.txt` (placement-only) is rejected by the lock; L3 uses `fens_12k_v2.txt` (md5 e7dbf2c8): the lock's
  full 12k reference has 12,000 distinct rows (2,261 s on two Idle CPUs under load), and a byte copy of the lock exe
  reproduces it 12,000 / 12,000 (2,463 s; `F:\ospd\logs\bx_lockcopy_full12k\bitexact.log`): the reference is
  deterministic, so any L3 difference is the candidate's.
- MSVC builds can never match g++ node counts (std::sort orders equal scores differently), so L4's ASan run is
  compared with the MSVC ASan build of the lock source, UBSan (g++) with the candidate's own count.
- BOLT: one recorded try = not possible here (no llvm-bolt on the PC; BOLT handles ELF only, deep research T5).
Tests:
- Kit self-test: PASS (above).
- Test 2 (one search constant changed, HistoryMax 16384 -> 16000): bitexact_check FAILS at L1 (10/10 bench lines
  differ), no ABBA (09:15); with the Code Review fix the build itself already fails closed on the pin DIFF.
- Job B test 2 (move order changed, pick_best tie-break `>` -> `>=`): speed_pack stops with exit 3 before any ABBA,
  and bitexact_check on the kept exe says NOT BIT-EXACT at L1 (test_moveorder_mutant 3/3 PASS, 09:53; again 3/3 at
  13:20-13:23 after all tool fixes).
- Code Review tests: 13/13 PASS (`tests/test_cr_637b.ps1`; again 13/13 at 13:18-13:20 after all tool fixes).
- Test 1 (lock-vs-lock pack) and test 3 (best variant full pack): see section 2.

## 2. Job A results - build modes, flags and PGO workloads (ABBA vs the lock, d20 x 10, CPU 2)
All variants are built from the exact lock source by build_variants.ps1 (bench pins checked fail-closed) and timed
against the lock exe FD3A5190 with abba.ps1 (net loaded, ABBA/BAAB, fresh copies; `F:\ospd\abba\q2\<run>\`).
Session A/A (aa_lock_d20_s3): wall 1.0066 [0.9968, 1.0111] sd 0.99 %, cpu 1.0050 [0.9940, 1.0087] sd 1.02 %.
| run | wall B/A median [95 %] sd | cpu B/A median [95 %] sd | verdict wall / cpu | runs.csv md5 |
|---|---|---|---|---|
| lp_part1 (-flto-partition=one) | 1.0100 (+1.00%) [0.9875, 1.0323] 3.10% | 1.0081 (+0.81%) [0.9902, 1.0202] 2.09% | NO-WIN / NO-WIN | a173d744 |
| lp_wmix (PGO + 300 game positions, go nodes 20000) | 1.0149 (+1.49%) [0.9814, 1.0390] 3.99% | 1.0074 (+0.74%) [0.9939, 1.0238] 2.08% | NO-WIN / NO-WIN | 382e6bd4 |
| lp_ipapta (-fipa-pta) | 1.0051 (+0.51%) [0.9957, 1.0218] 1.80% | 1.0069 (+0.69%) [0.9940, 1.0214] 1.90% | NO-WIN / NO-WIN | 38813037 |
| lp_af64 (-falign-functions=64) | 0.9951 (-0.49%) [0.9777, 1.0108] 2.33% | 1.0043 (+0.43%) [0.9796, 1.0134] 2.37% | NO-WIN / NO-WIN | 320122d5 |
| lp_z4 (-march=znver4) | 0.9917 (-0.83%) [0.9809, 1.0107] 2.10% | 0.9972 (-0.28%) [0.9820, 1.0122] 2.12% | NO-WIN / NO-WIN | 49a48d15 |
| lp_ppt (-fprofile-partial-training) | 0.9973 (-0.27%) [0.9846, 1.0111] 1.86% | 0.9959 (-0.41%) [0.9844, 1.0114] 1.89% | NO-WIN / NO-WIN | 40c25b4f |
| lp_pvw256 (-mprefer-vector-width=256) | 0.9925 (-0.75%) [0.9761, 1.0195] 3.04% | 0.9932 (-0.68%) [0.9817, 1.0036] 1.54% | NO-WIN / NO-WIN | 1ad33c8d |
| pgo (PGO without LTO) | 0.9891 (-1.09%) [0.9730, 1.0170] 3.09% | 0.9877 (-1.23%) [0.9738, 1.0151] 2.90% | NO-WIN / NO-WIN | f636124d |
| lto (LTO without PGO) | 0.9747 (-2.53%) [0.9589, 0.9902] 2.24% | 0.9750 (-2.50%) [0.9650, 0.9801] 1.09% | NO-WIN / NO-WIN | b022da54 |
| o3 (plain lock line) | 0.9711 (-2.89%) [0.9318, 1.0088] 5.56% | 0.9664 (-3.36%) [0.9518, 0.9895] 2.71% | NO-WIN / NO-WIN | a69dafc0 |
| **lp_wnonet (PGO trained with UseNNUE=false)** | **0.7090 (-29.10%) [0.6880, 0.7194]** 3.12% | **0.7057 (-29.43%) [0.6964, 0.7104]** 1.40% | NO-WIN / NO-WIN | 75bd6e62 |
| lp_noplt, lp_nosi, lp_pvw512 | = lock exe (byte-identical, not timed) | | | |
| lp_w12k (PGO + 300 of the 12k FENs, go depth 10) | 0.9940 (-0.60%) [0.9500, 1.0492] 6.94% | 0.9954 (-0.46%) [0.9777, 1.0197] 2.94% | NO-WIN / NO-WIN | d9040545 |
Reading: the lock's own recipe (LTO+PGO, frozen v1 workload) is the fastest build mode here; no flag beats it inside
the noise, and three flags change nothing at all on a static PE exe. The PGO workload matters a lot: a profile taken
with the net OFF makes the net-on engine **29 % slower** (2.14 M -> 1.50 M nps at bench d20) - the risk the brief named.
The lock is not exposed to it: its embedded net is ON by default, so the frozen v1 workload already runs the net path;
richer net-on workloads (game positions, 12k sample) add nothing measurable. Job A test 3 (full pack of the best flag
variant, lp_part1): pc1 = pc2 (33ed7a53), bit-exact L1-L4 with the full 12k L3, ABBA cpu +0.66 % [0.9895, 1.0181] /
wall -0.01 % [0.9792, 1.0432] = NO-WIN (`opus_speed/candidates/var_lp_part1.md`). Job A test 1 (lock-vs-lock pack,
locklock_v1c): the lock source through the whole path gives pc1 = pc2 = FD3A5190 (the lock exe byte for byte), bench
signature = the lock pins net on and net off, bit-exact L1-L4, and ABBA vs the lock cpu -0.29 % [0.9866, 1.0054],
wall -0.98 % [0.9522, 1.0269] - both intervals contain 1.000 and sit inside the session's A/A band: PASS
(`opus_speed/candidates/locklock_v1c.md`).

## 3. Job B - bit-exact hot-path changes
Every change is a build switch (default 0, new code inside `#if`, lock text verbatim under `#else`); the kit takes no
-D flags, so each pack flips the one `#define <SWITCH> 0` line in a copy (`src_kit`). Order of work followed the deep
research's Track 5 ranking, restricted to what applies to this lock (its net has no L1 layer: VNNI / find-nnz /
sparse-L1 items belong to the HalfKA path only). Each row: pack = LTO+PGO pc1 = pc2, bit-exact L1-L4 (L3 on the
first 2,000 of the 12k FENs), then ABBA vs the lock at bench d20, 10 rounds ABBA/BAAB, CPU 2, net loaded, fresh
copies per round; interval = 95 % Student-t of the per-round log ratios; A/A of the session (aa_lock_d20_s3): wall
1.0066 [0.9968, 1.0111], cpu 1.0050 [0.9940, 1.0087].
The PROTOCOL verdict is the wall one (the engine's own bench nps, as the brief defines it); the CPU-time metric is
advisory (it removes preemption by other programs, not SMT-sibling contention). The changes (switch = value):
- `FORGE_SPD_TT_NOTLS=1`: the worker that holds the TT's exclusive lease (one-thread search) probes / stores without
  `lock_stripe()`, whose emulated-TLS lookup and lease walk only ever returned an unlocked lock there.
- `FORGE_SPD_NO_ZERO_MOVELISTS=1|2`: 1 = move arrays are no longer zero-filled at construction (every slot is written
  before it is read); 2 = also a quiets-only generation mode for the move picker (same quiets, same order as the
  lock's full list after its filter).
- `FORGE_SEARCH_SPEED2=1`: the R14 switch (TT prefetch after every make - it adds one after the null-move and
  ProbCut makes, which the lock does not prefetch -, MovePicker history / piece hoist, table piece_type), rebased
  onto the NZM code (`r14_speed2_after_nzm.patch`) for stacking.
- `FORGE_SPD_PREFETCH_EARLY=1`: prefetch the child's TT cluster before make_move from an exact cheap key.
- `FORGE_SPD_SLIDER_PEXT=1`: slider attack tables indexed with PEXT (same tables and attack sets, no magic search).
- `FORGE_SPD_NNUE_ZMM=1`: the net's output layer in one AVX-512 register per 16 hidden units, same lane order and
  reduction, separate multiply and add (no FMA).
- `FORGE_SPD_MATKEY_FAST=1`, `FORGE_SPD_PICKBEST=1|2`: cheaper material-key update; branch-free pick_best.

### 3a. Single changes (pack per change; `python -I -B tools/pack_table.py`)
| pack | switches | exe (pc1 = pc2) | bit-exact | wall B/A [95 %] | cpu B/A [95 %] | verdict wall / cpu | runs.csv md5 |
|---|---|---|---|---|---|---|---|
| b1_tt_notls_b | FORGE_SPD_TT_NOTLS = 1 | 9b6aae65 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0419 (+4.19%) [0.9947, 1.0734] | 1.0369 (+3.69%) [1.0147, 1.0492] | NO-WIN / WIN | ec2e8683 |
| b2_nzm2 | FORGE_SPD_NO_ZERO_MOVELISTS = 2 | ac287b2d (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0361 (+3.61%) [1.0161, 1.0606] | 1.0426 (+4.26%) [1.0360, 1.0479] | WIN / WIN | 664d3b5d |
| b2_nzm1 | FORGE_SPD_NO_ZERO_MOVELISTS = 1 | 3e52ed13 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0326 (+3.26%) [1.0177, 1.0442] | 1.0275 (+2.75%) [1.0160, 1.0460] | WIN / WIN | 1f41b6d0 |
| r14_speed2_b | FORGE_SEARCH_SPEED2 = 1 | de20653c (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0315 (+3.15%) [1.0165, 1.0443] | 1.0287 (+2.87%) [1.0157, 1.0425] | WIN / WIN | 1166c21b |
| b2_nnue_zmm_c | FORGE_SPD_NNUE_ZMM = 1 | 809f03df (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0199 (+1.99%) [0.9999, 1.0578] | 1.0156 (+1.56%) [0.9987, 1.0449] | NO-WIN / NO-WIN | bcc00d27 |
| b2_slider_pext | FORGE_SPD_SLIDER_PEXT = 1 | 46bf171b (pc1 = pc2) | BIT-EXACT (L1-L3; L3 on 2000 FENs = quick subset; L4 UBSan PASS, MSVC ASan PASS in the 12:25 re-run with /D__BMI2__) | 1.0137 (+1.37%) [0.9993, 1.0210] | 1.0122 (+1.22%) [0.9982, 1.0195] | NO-WIN / NO-WIN | 8e9c8e82 |
| b1_prefetch_early | FORGE_SPD_PREFETCH_EARLY = 1 | ec5af9b0 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0111 (+1.11%) [0.9889, 1.0322] | 1.0152 (+1.52%) [1.0026, 1.0288] | NO-WIN / WIN | cfe32f4f |
| b2_pickbest1 | FORGE_SPD_PICKBEST = 1 | 13e34185 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0108 (+1.08%) [0.9909, 1.0214] | 1.0113 (+1.13%) [0.9981, 1.0198] | NO-WIN / NO-WIN | 81c03507 |
| b2_matkey_fast | FORGE_SPD_MATKEY_FAST = 1 | 434920e5 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0084 (+0.84%) [0.9887, 1.0379] | 1.0077 (+0.77%) [0.9919, 1.0258] | NO-WIN / NO-WIN | f97da2f0 |
| b2_pickbest2 | FORGE_SPD_PICKBEST = 2 | 2e86d2c7 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset) | 1.0008 (+0.08%) [0.9833, 1.0293] | 1.0034 (+0.34%) [0.9965, 1.0208] | NO-WIN / NO-WIN | 04132c8c |
Rows sorted by the wall median. Verdict column = this 10-round run only; TT_NOTLS, SLIDER_PEXT, PREFETCH_EARLY and
NNUE_ZMM (weak) are protocol winners on the pooled rounds (3b); NO_ZERO_MOVELISTS=1 is a winner too but is a subset
of mode 2, which the stacks use. Losers: PICKBEST 1 / 2 and MATKEY_FAST (switches stay at 0).

### 3b. Borderline singles: one 16-round re-time each, decision on the pooled rounds
Rule: a single whose first run is not a wall WIN but has a median of at least +1 % or a cpu WIN got ONE 16-round
re-time against the lock (queued 12:01 TT, 12:06 slider + prefetch, 12:12 zmm - before any re-time had finished).
Its status is decided on all 26 rounds pooled (`abba_recheck.py --pool`), never on the re-time alone. **Rule since
the CR leftovers of 00d19e56 (skill verdict rules):** these pooled statuses are screening labels, not verdicts - a pool
never decides a lock; NNUE_ZMM's own two runs are both wall NO-WIN, so its "WIN, weak" exists only in the pool. The pooling
rule itself was written at 12:22, after the first re-time (slider) had finished; it is the stricter reading there
(slider re-time alone +1.92 %, pooled +1.52 %).
| change | first run, 10 rounds: wall [95 %] | re-time, 16 rounds: wall [95 %] | POOLED 26 rounds: wall [95 %] / cpu [95 %] | status (pooled wall) | runs.csv md5 (first / re-time) |
|---|---|---|---|---|---|
| TT_NOTLS | +4.19 % [0.9947, 1.0734] NO-WIN | +2.62 % [1.0108, 1.0344] WIN | **+2.86 % [1.0117, 1.0419]** / +2.97 % [1.0198, 1.0368] | **WIN** | ec2e8683 / 4368e42b |
| SLIDER_PEXT | +1.37 % [0.9993, 1.0210] NO-WIN | +1.92 % [1.0045, 1.0305] WIN | **+1.52 % [1.0061, 1.0232]** / +1.43 % [1.0064, 1.0197] | **WIN** | 8e9c8e82 / 2b0788dd |
| PREFETCH_EARLY | +1.11 % [0.9889, 1.0322] NO-WIN (cpu WIN) | +1.49 % [1.0025, 1.0214] WIN | **+1.35 % [1.0021, 1.0205]** / +1.90 % [1.0089, 1.0219] | **WIN** | cfe32f4f / a3d720c7 |
| NNUE_ZMM | +1.99 % [0.9999, 1.0578] NO-WIN | +0.98 % [0.9967, 1.0238] NO-WIN | **+1.41 % [1.0042, 1.0303]** / +0.93 % [1.0025, 1.0237] (cpu NO-WIN) | **WIN, weak** (re-time alone and pooled cpu NO-WIN) | bcc00d27 / 22093c2c |
Folders: first runs `F:\ospd\packs\<pack>\abba_d20`, re-times `F:\ospd\abba\retime_<pack>_d20_r16`; pooled numbers
from `abba_recheck.py --pool <first> <re-time>` (it refuses runs of different exes). The TT gain is smaller than
its noisy first run suggested (+2.9 % pooled, not +4.2 %).

### 3c. Stacks (each timed against the lock in its own session)
| pack | switches | exe (pc1 = pc2) | bit-exact | wall B/A [95 %] | cpu B/A [95 %] | verdict wall / cpu | runs.csv md5 |
|---|---|---|---|---|---|---|---|
| stack_w1 | NO_ZERO_MOVELISTS=2, SPEED2=1 | 05928226 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.0731 (+7.31%) [1.0565, 1.1031] | 1.0713 (+7.13%) [1.0657, 1.0881] | WIN / WIN | 87de6a9e |
| stack_w2 | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SPEED2=1 | db957393 (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.1148 (+11.48%) [1.0734, 1.1217] | 1.1134 (+11.34%) [1.0990, 1.1191] | WIN / WIN | 16368782 |
| stack_w4 | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SPEED2=1, SLIDER_PEXT=1 | c883623c (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.1204 (+12.04%) [1.0929, 1.1388] | 1.1223 (+12.23%) [1.1003, 1.1350] | WIN / WIN | 0fc1fae1 |
| stack_w3 | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SPEED2=1, PREFETCH_EARLY=1 | 4b49ae4b (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.1142 (+11.42%) [1.0869, 1.1548] | 1.1183 (+11.83%) [1.1036, 1.1339] | WIN / WIN | fc582ffe |
| stack_w5 | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1 | 060c578c (pc1 = pc2) | BIT-EXACT (L1-L4; L3 on 2000 FENs = quick subset); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.1194 (+11.94%) [1.1013, 1.1425] | 1.1260 (+12.60%) [1.1103, 1.1471] | WIN / WIN | ba6c47b4 |
| trial_w6 | TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1 | 4181a589 (pc1 = pc2) | BIT-EXACT (L1-L3 on 2000 FENs = quick subset; L4 UBSan + MSVC ASan PASS in the 12:24 re-run with /D__BMI2__); full 12k: BIT-EXACT (L1-L3; L3 on 12000 FENs) | 1.1492 (+14.92%) [1.1351, 1.1666] | 1.1531 (+15.31%) [1.1387, 1.1698] | WIN / WIN | 5b0af24b |
Direct comparison in one session (A = stack_w2, B = trial_w6, d20, 10 rounds ABBA/BAAB, `F:\ospd\abba\direct_w6_vs_w2_d20`, runs.csv md5 c5308b93): wall +4.39% [1.0305, 1.0643], cpu +4.15% [1.0307, 1.0647]; VERDICT wall WIN / cpu WIN = what PREFETCH_EARLY + SLIDER_PEXT + NNUE_ZMM add on top of stack_w2.
Each stack row is timed against the lock in its own session; between sessions the lock itself ran at 2.15-2.19 M nps at d20, so stack-to-stack differences of a few percent across rows are not measured differences (only the direct row above is). Exes, candidate files: `F:\ospd\packs\<stack>\`, `opus_speed/candidates/<stack>.md`. Every stack row also has: the full-12k run (12,000 / 12,000, `bitexact_full12k`), a
byte-identical rebuild by QA's own kit (`F:\ospd\qakit`), 0 FMA instructions, and warm-table identity with the lock
over 1,000 `go nodes 20000` searches with 40 Hash / Clear Hash / UseNNUE changes and no ucinewgame
(`tools/warm_identity.py`, `F:\ospd\warm2\<stack>\`, all six IDENTICAL, 13:27-13:35). Stack w4's candidate-file note
"max winners-only stack" was written at 12:52, before PREFETCH_EARLY's re-time made it a winner; it is corrected there.

Losers stay switches at 0 (no code path in the default build). Notes per change (design, lines, why node-identical,
proofs incl. verify / poison / counter builds): `opus_speed/jobb/<name>.md`; patches `opus_speed/patches/`.

## 4. Job C - gate wall time (worker jobc, DONE 09:59; coordinator re-run 10:01 ALL PASS)
Scripts for the crew to review; the running queue, its config, gate folders and the lock were read only. The crew
vote is unchanged; projections and audits are planning input, never a stop rule. Details and every number's source:
`opus_speed/jobc/README.md`, `opus_speed/jobc/RESULTS.md`; skill `skills/forge-gate-walltime/SKILL.md`.
| tool | what |
|---|---|
| gate_replay.py | replays a finished gate (exact fastchess 1.8.2 GSPRT after every pair, strict PGN / log pairing) and checks the recorded verdict; corrupt or truncated input -> exit 2, no verdict |
| llr_project.py | seeded projection to the cap: P(H1 / H0 before the cap), games to a decision - queue ordering only |
| queue_throughput.py | games/h per gate and per slot, idle gaps between gates |
| adjudication_audit.py | adjudication / book / TC settings per gate and what draw / resign rules would save (report only) |
| book_load_check.py | book load / index times on copies |
| pregate_screen.py | cheap rejects before games: PE header, uciok, options, pins, perft, 20-position movetime smoke with legality check, WAC subset |
| concurrency_plan.py | math only: games/h and hours to each cap for given cores at Threads=1 |
Success tests: (1) replay of 13 finished gates from FORGE_RESULTS.csv: 13/13 same verdict, W/D/L, pentanomial,
Elo / nElo / LLR within 0.006 of RESULT.md, first crossing pair = printed pair count; formula check on all 111 CSV
rows with a pentanomial: 0 differ by more than 0.006. (2) Deliberate failures: 9 corrupt / truncated / unpaired /
duplicated PGN copies x with and without the log = 18/18 exit 2 with an error line and no verdict. Coordinator re-run
of the whole suite at 10:01: ALL PASS (`jobc/results/tests_20261105_100109_coordinator_rerun.md`).
Findings (measured on 109 gates / 260.7 h): every concurrency slot yields 108-124 games/h, so wall time is set by
slots x games; idle between gates is small (median 94 s, 1.25 % of the time) except five > 30 min gaps of an empty or
paused queue (29.7 h); one gate ran at concurrency 2 without a recorded reason (11 h for 2,360 games); adjudication is
off everywhere - fishtest-like draw / resign rules would save ~11-14 % of engine time but change 12-52 results per gate
(a crew decision, not taken here); book loading costs 0.1-1.3 s (no change worth making); the pre-gate screen rejects
broken candidates in under a minute (lock PASS in 58 s). The cheapest wall-time lever is therefore keeping the queue
full and the slot count right (concurrency_plan.py), not per-game settings.

## 4b. Job D - faster net pipeline (optional; worker jobd, DONE 11:54; plans and read-only scripts only)
Started after A-C were in their machine-bound phase; no GPU use, no trainer process touched, nothing written outside
`opus_speed/jobd/`. Plan `opus_speed/jobd/PLAN.md` (ranked D1-D9, measurement protocol, what not to do); read-only
log profilers `jobd/tools/npt_epochs.py`, `guard_duty.py`, `export_times.py` (outputs in `jobd/logs/`). Top items
(effects UNPROVEN; owner / QA decisions):
- **D1 (owner item, biggest): the GPU guard throttles training since 2026-11-01.** Its HWiNFO row filter
  (`F:\forge_nnue_train\tools\gpu_guard.ps1`, `Read-Row`: `'^\d\d\.\d\d\.\d{4}'`) needs a two-digit day, but HWiNFO
  writes `5.11.2026,12:5:28.561`, so every November row before the 10th is dropped and the guard falls back to the
  ADLX feed (`src=adlx` in every window since 2026-10-31 23:51:46) with the no-fan thresholds. Daily run_frac went
  from 0.90-1.00 (Oct 28-31) to 0.33-0.64 (Nov 1-5); same recipe epochs from 8.3-9.2 min (Oct 31) to 15.0-16.7 min
  (Nov 4) while the running it/s is unchanged. Coordinator re-check (read only, 12:0x): the regex line and the
  HWiNFO row format are as described; the last guard lines read `src=adlx ... run_frac=0.501` and `0.368`. Prediction
  the owner can check for free: on 2026-11-10 the day becomes two-digit, `src` flips back to `hwinfo` and run_frac
  rises (until 2026-12-01). Months 1-9 would never match either.
- D2: the trainer's RAM floor (free < 6 GB -> exit 97) fires during its own end-of-epoch validation / checkpoint and
  repeats whole epochs on resume (s47 today: 4 aborts, epoch 6 trained five times, ~50 min of finished training
  lost + 29 min backoff); suggested: never abort during the own save, resume at the next epoch, shorter backoff.
- D3: the R14-B fast loader's gain is bounded while D1 throttles (the GPU is the limit while the trainer runs);
  its RAM saving helps D2. Not bottlenecks (measured): export 5-15 s per net, validation 1-15 s per epoch,
  conversion 6.3 min per 305 M records.

## 5. What QA should time first
Status of items 1-3 (lock-path rule in `skills/forge-speed-lock-path/SKILL.md`): steps 1-4 done - BIT-EXACT incl. the
full 12k, L3b warm-table identity IDENTICAL, Threads 2-4 soak PASS (soak only), ABBA WIN - and **NOT a lock** until QA's
own re-time (step 5). Item 4's single changes: BIT-EXACT on 2,000 FENs + ABBA only (no L3b, no soak).
1. **stack_w2** = lock source + `opus_speed/patches/trial_w2.patch` (md5 80f8124f; = b1_tt_notls + b2_no_zero_movelists +
   r14_speed2_after_nzm) with `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1` flipped in
   the source (`F:\ospd\packs\stack_w2\src_kit`, so QA's kit builds it without -D flags). Exe
   `F:\ospd\packs\stack_w2\forge_stack_w2.exe` sha256 db957393 78e21771 e0b03e42 e258f551 ebeb3b66 f1151f23 2f4f1b89 e7f933a9
   (md5 1d4080bc), pc1 = pc2. Bit-exact: L1-L4 + full 12k L3 12,000 / 12,000. This job's ABBA vs the lock: wall +11.48 %
   [1.0734, 1.1217], cpu +11.34 % [1.0990, 1.1191] (candidate file `opus_speed/candidates/stack_w2.md`). Verified
   12:34: QA's own kit v2.3 (`build_ltopgo.ps1 -Expose -Kit <kit folder>`) on `src_kit` gives this exe byte for byte
   (sha256 db957393...) and its plain-vs-LTO+PGO node identity is ALL OK. QA: rebuild pc1 + pc2 with the kit, re-run
   the pins / 12k identity, and time it on QA's own cores.
2. **trial_w6** = all six switches ON (source: lock + `opus_speed/patches/trial_w6.patch`, defaults flipped in
   `F:\ospd\packs\trial_w6\src_kit`): every member is a protocol winner (TT_NOTLS, SLIDER_PEXT, PREFETCH_EARLY,
   NNUE_ZMM on 26 pooled rounds, by the rule set before any re-time finished), so this is the largest winners-only
   stack. Exe sha256 4181a589..., pc1 = pc2; bit-exact L1-L4 (ASan via the 12:24 re-run) + full 12k 12,000 /
   12,000; QA's own kit rebuilds it byte for byte; ABBA vs the lock wall **+14.92 % [1.1351, 1.1666]**, cpu +15.31 %
   [1.1387, 1.1698] (`opus_speed/candidates/trial_w6.md`). Six changed code paths instead of three; the PEXT slider
   index needs BMI2 and the output kernel AVX-512F, both present on every CPU that can run the lock's znver5 build.
   Time it after stack_w2, as the second step.
3. **stack_w5** = trial_w6 without NNUE_ZMM, the one weak winner (pooled wall +1.41 %, but its re-time alone and its
   pooled cpu metric are NO-WIN): every member wins on BOTH metrics. Numbers: section 3c /
   `opus_speed/candidates/stack_w5.md`. The choice between 2 and 3 is QA's (one more, weakly proven, kernel).
4. The changes one by one, if QA prefers single steps: b2_nzm2 (+3.6 %), r14_speed2_b (+3.2 %), b1_tt_notls_b
   (+2.9 % pooled), b2_slider_pext (+1.5 % pooled), b1_prefetch_early (+1.4 % pooled), b2_nnue_zmm_c (+1.4 % pooled, weak).
stack_w1, stack_w3 and stack_w4 are intermediate data points (section 3c), not separate recommendations. PREFETCH_EARLY
moves the lock's two TT prefetches (qsearch, main search) before make_move; SPEED2 adds prefetches at other sites
(the null-move and ProbCut makes), so the two do not overlap. Nothing here is locked or queued by this job; QA decides.

## 6. Skills created or improved (on this branch; the project copies on D: were not touched)
- NEW `skills/forge-speed-lock-path/SKILL.md`: the whole speed-only lock path (tools, ABBA protocol with wall as the
  protocol verdict, bit-exact levels incl. the MSVC ASan comparison, re-time / pooling rule, stacking with
  make_stack, warm-table identity, proven facts and the day's results, 17 pitfalls hit today). Also installed user-scope
  (`C:\Users\Administrator\<cfg>\skills\forge-speed-lock-path\`), like forge-gate-walltime.
- NEW `skills/forge-gate-walltime/SKILL.md`: Job C tools, the facts they rely on, the measured gate numbers.
- IMPROVED `skills/forge-ltopgo-pgo/SKILL.md` (copy + section "Speed job 2026-11-05"): the lock's net is embedded and
  ON (v1 workload profiles it), net-off profile -29 %, flags that give the identical exe, flag / build-mode table,
  switch-0 = lock byte for byte, SPEED2 reproduction.
- IMPROVED `skills/forge-pc-rules/SKILL.md` (copy + section "Speed job"): CPUs 0-3 rule set, restart re-pin, heredoc
  backslash and `$1` pitfalls, `git rm` refusal.
- Helper scripts (opus_speed/tools): commit_push.sh (gated commits), make_stack.sh, pack_table.py, abba_table.py,
  abba_recheck.py (exact-t re-check + pooling), warm_identity.py (warm-table identity), ctrl_char_check.py,
  name_lint.py, ps_parse_check.ps1, pgn_positions.py.

## 7. Code Review 637B report-back
See `CR_637B_REPORT.md` (BLOCKER + SHOULD 1-3 fixed, tests 13/13; the 3 LOW notes were not visible on the PC).

## 8. Deviations, incidents, owner items
Deviations (each disclosed where it happened):
- One read-only `find` during orientation (08:4x) listed three tool paths under D:\o30\wt before the "don't touch
  D:\o30" rule was applied; nothing was read or written there afterwards.
- D: writes: only the worker-board lines the owner's worker rule requires (claim / release / done lines).
- Application restart by the owner at ~09:32: the new session process ran at 0xFFFF / Normal until 09:33 (one status
  query ran in that window), then was pinned to 0x3 Idle; own jobs started before the restart kept running.
- ABBA protocol: rounds alternate A B B A / B A A B (default; `-Order ABBA` keeps the literal order) and the process
  CPU time of the bench window is evaluated next to the engine's wall-clock nps. Reason: A/A runs on this shared PC
  showed per-slot differences of ~1-2 % and wall-clock noise up to 3.8 %/round; the balanced A/A at d20 has
  ~1 %/round for both metrics. Every summary states the order and both verdicts; the WIN rule is applied per metric.
- L4 sanitizers: ASan from MSVC (`cl /fsanitize=address`) on a port copy with one extra TT-index line, compared with
  the MSVC ASan build of the lock source; UBSan from the lock's g++ in trap mode. Reason: MSYS2 g++ has no ASan
  runtime and the PC's LLVM 18 does not accept the installed MSVC STL.
- Candidate packs use L3 on the first 2,000 of the 12k FENs (`-Quick`) for screening; the final stack and any exe
  handed to QA as a lock candidate get the full 12k set.
- No co-author trailer in commits (the brief bans model-company names), as in the deep-research job.
- Three own processes left running, idle (no-kill rule): the first warm_identity attempt (13:21) waited for a line
  starting with `bench depth`, but the engine prints `info string bench depth ...`, so its reader blocked for good:
  python.exe PIDs 11168 and 7524 and the lock exe PID 11900 (run in place, read-only, as bitexact_check does),
  0.05 s CPU, ~61 MB in total, mask 0x3 Idle. The tool was fixed (reader thread + timeout + `quit`, never a hang)
  and re-run; the owner may end those three PIDs at any time (nothing is written by them).
- Worker b1tt wrote one scratch diff outside its write area (C:\...\Temp\b1_tt_notls_check.diff, 12.6 KB, 09:14,
  self-reported); left in place (no-delete rule).
Own tool bugs found and fixed during the job (all before any candidate was called valid): fail-open pin DIFF (Code
Review blocker), ordered-dictionary int indexing (all pins looked DIFF at 637be9af), swallowed L1/L2 lines,
`-File` list parameters, native stderr under `Stop`, placement-only FENs (L3 compared one position; withdrawn),
slot-order bias in plain ABBA, `speed_pack.ps1` not parsing under PS 5.1, a BEL byte in a log path (heredoc),
`-Twice` never reporting REPRO (output-stream pollution), stdin-file sharing between two trainings, a race on the
shared L3 reference cache (three packs superseded), MSVC vs g++ node counts in L4 (four packs re-run), L4 ASan N/A
for PEXT sources (MSVC lacks `__BMI2__`; fixed 12:2x, both PEXT builds re-run: ASan PASS), an `-OnlyL4` run printing
the full-proof verdict text (fixed 12:2x; the two L4-only logs of 12:24-12:27 carry the old text and prove L4 only).
Review passes: independent tool review (worker toolrev, `REVIEW_TOOLS_INDEPENDENT.md`, fixes in `REVIEW_FIXES.md`);
independent patch review of all six switches (worker patchrev, 12:26-12:46, `REVIEW_PATCHES_INDEPENDENT.md`):
**no BLOCKER, no SHOULD**, five LOW - L1 a pre-existing lock bound (below, owner item), L2 the `__BMI2__` guard vs
MSVC (handled in bitexact_check; the guard itself unchanged), L3 the zmm kernel relies on `-ffp-contract=off`
(checked: 0 `vfn?m(add|sub)` instructions in the lock and all six stack exes, 13:20), L4 PREFETCH_EARLY does
useless work on a non-GNU compiler (not the kit's case), L5 the TT_NOTLS invariant is asserted only in the assert
build (keep that build as a CI row). Its QA test list (warm TT, option changes, stop / ponder, Threads soak, poison
build of the stacked source, extreme positions, net-off subset) is in its section 4. Run here on all six stacks,
IDENTICAL to the lock (`OWN_CHECKS.md` #11): its test 2 (scaled up: 1,000 unrelated FENs, `go nodes 20000`, no
ucinewgame), test 8 (first commands) and the option-change part of test 1. Not run in the job itself: test 1's
game-continuation replay and the rest of that list. **Follow-up 14:13-14:52 (`PATCHREV_QA.md`, NOT independent):** on
all six stacks vs the lock, the game-continuation replay (gate game 379, 177 plies, `go depth 10`, two passes, option
changes) is IDENTICAL, stop / ponder PASS, the Threads 2-4 soak PASS (soak only, not a lock proof), the 0xA5 poison build
of every stacked source BIT-EXACT and a move-order mutant of every stack stops speed_pack before any ABBA, the extreme
positions (kit, UBSan and MSVC ASan exes; `data/extreme_fens.tsv`) PASS; test 7's net-off 2k subset was not in the
follow-up brief and was not run. bitexact_check.ps1 and the skill now state that BIT-EXACT + ABBA is not a lock until
the warm-table identity and a Threads 2-4 smoke have passed. Scratch at the end: `F:\ospd` 5.7 GB (cap 8 GB), F: 55 GB free, C: 93 GB (13:38). The coordinator's own re-check
(`OWN_CHECKS.md`, NOT independent): every ABBA summary recomputed with the exact t quantile, patches = timed sources,
kit sources = patched trees + switch lines only, QA's kit rebuilds all six stacks byte for byte.
**CR leftovers, 2026-11-05 19:43-19:47 PC clock (start tip 00d19e56, WIP 8b170996, NOT independent):** the independent
Code Review of 73f4041d..00d19e56 (APPROVE, 0 BLOCKER) left 4 SHOULD tooling notes, all fixed: (1) `tools/warm_identity.py`
pins itself to 0x3 Idle and reads mask + class back on itself and on every engine it starts, fail closed - DONE; (2) the skill's
verdict rules (wall nps decides, CPU time must not contradict it, `abba_recheck.py --pool` never decides) - DONE;
(3) the QA owner item below (L3b + Threads 2-4 soak + independent ABBA vs trial_w6 before any lock) - DONE;
(4) `tools/patchrev_qa.py` LOCK / LOCK_SHA = the live lock trial_w6 (`F:\ospd\packs\trial_w6\forge_trial_w6.exe` =
sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0) - DONE. The live lock was published by QA
and is not touched here. KING_LINES (W9) and bundles a-d were NOT retimed, restacked or locked; no ABBA, soak or
12k run. Tests: `tests/test_cr_should_w8.ps1` 8 / 8 PASS (run 20261105-194720-5676, lock exe only, CPUs 0-1 Idle).
Details: `CR_SHOULD_W8.md`.
**Leftover jobs 1-3, 2026-11-05 from 19:5x PC clock (start tip 38559f1b, owner brief, NOT independent):**
- Job 1 DONE 20:02: the tool default lock is the live lock trial_w6 (see the owner item below).
- Job 2 DONE 20:03: the warm_identity refusal path is tested by fault injection (`tests/warm_refusal_check.py`).
  - A mask or Idle read-back that does not match (a setter that reports success but changes nothing) gives exit 1
    before the out dir or any engine.
  - An engine that inherits a wrong mask / class is refused and gets quit + EOF; its PID ends.
  - `tests/test_cr_should_w8.ps1`: 14 / 14 PASS (run 20261105-200352-9252).
- Job 3 DONE 20:07 (the CR NITs of 00d19e56):
  - 3a: `patchrev_qa.py` takes the timing mutex before it moves onto the mask; an invalid mask is still refused at
    once.
  - 3b: a K3 contract comment at the `is_legal` declaration of the trial_w9 / w9dev board.hpp. It is comment only;
    both KING_LINES patches were regenerated and proven to apply to a fresh lock copy (`W9_KING_LINES.md`).
  - 3c: the CR test takes `-Py` / OSPD_PY instead of a hard-coded interpreter and fails closed without one.
  - Test 14 / 14 PASS (run 20261105-200713-5164).
- Bug-hunt pass 20:08-20:10 (own, NOT independent): one whitespace glitch fixed (`CYCLE =[`); re-run 14 / 14 PASS
  (20261105-200930-9164). Two LOW notes are left in `CR_SHOULD_W8.md`: two other scripts still name the venv python,
  and warm_identity's fixed 0x3 mask.
- Extras 20:12-20:15:
  - `pin_check` of the default lock exe trial_w6: PASS (bench d11-d22 + perft5 = the pin tables).
  - `tests/test_stack_poison.ps1` takes `-Py` / OSPD_PY.
  - Skill rows for both tests.
  - `tests/test_cr_637b.ps1` re-run after the default-lock change: 13 / 13 PASS (20261105-201312-4460, o3 builds
    only, no ABBA).
  - Nothing of this follow-up is running.
- Live lock trial_w6, 4181A589..., is not touched. KING_LINES and bundles a-d were not retimed or locked. No ABBA,
  soak, 12k or L3b ran.
Owner items:
- The 3 LOW notes of Code Review CR_OPUS_SPEED_TOOLS_637B were not visible on the PC; please send their text.
- D: free space read 50.0 GB at 12:29 (`pc_status`), i.e. at the brief's floor; this job wrote only worker-board
  lines there, the space is used by other jobs.
- QA, before ANY lock of a WIN candidate (the six stacks, bundles a-d, KING_LINES; this job never locks anything):
  (a) L3b `tools/warm_identity.py` vs the live lock trial_w6 (IDENTICAL), (b) a Threads 2-4 soak (`patchrev_qa.py
  soak --mask 0xF`, soak only), and (c) an independent ABBA on QA's own cores vs the **live lock trial_w6** (sha256
  4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0), not vs the old lock FD3A5190, judged by the
  skill's verdict rules (wall nps decides, CPU time must not contradict it, a pooled run never decides). Every ABBA
  number in this report is vs FD3A5190.
- DONE 20:02 (leftover job 1, start tip 38559f1b): `tools/uci_lib.ps1` `$OspdLockExe` / `$OspdLockSha` now name the
  live lock trial_w6 (`forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`, sha256 4181A589...). These are the
  defaults of abba_queue, speed_pack and bitexact_check, and their "lock" labels now say trial_w6. The FD3A5190 exe
  stays as `$OspdOldLockExe` and its source as `$OspdLockSrc`, for search identity only. The pin tables are
  unchanged. The first bitexact_check with the default -Ref builds a new reference cache `F:\ospd\ref\4181a589\`;
  the FD3A5190 cache stays.
- Lock correctness item (patch review L1, PLAUSIBLE, pre-existing, NOT changed by any switch): `MovePicker` writes
  `bad_captures_[bad_count_++]` without a bound against its 64 slots (`src/search.cpp` of the lock, the write path the
  patches keep), unlike `quiets_tried` / `captures_tried`. A contrived node with more than 64 SEE-negative captures /
  promotions would overflow; not reached by bench, the 12k FENs or gate play as far as the proofs show. A bound (or
  256 slots) is a separate engine change with its own gate decision, not part of the speed stack.
- QA kit v2.3 (`kit_v23\build_ltopgo.ps1`) under Windows PowerShell 5.1 without `-Kit`: `$PSScriptRoot` is empty in
  the param default, so `$Kit` is empty, every `Join-Path $Kit ...` fails, and with `$ErrorActionPreference =
  'Continue'` the preflight sha256 checks of the frozen workload and bench FENs are skipped silently (the `if`
  statements abort before their `throw`). The run then fails closed at training ("training gave 0 bench lines",
  FAILED marker; seen 12:31 in `F:\ospd\qakit\qakit_stack_w2_pc1`). Passing `-Kit <kit folder>` avoids it; a
  `if (-not $Kit) { throw }` line would make the preflight fail closed too. Not changed here (QA's file).
- Robustness note, no Elo / node effect: `Worker::clear()` assigns a ~1.4 MB `ContinuationHistory{}` temporary on the
  stack; MSVC's 1 MB default stack overflowed under ASan (MinGW's 2 MB default hides it). An in-place reset would
  remove the dependence (not changed here: not a speed item).
- Two different files named `fens_12k.txt` exist (branch file: six fields; scratch copy: placement only); see
  `opus_speed/data/README.md`. Earlier jobs used the six-field branch file (their 12k results stand).

## 9. Hunt vs the live lock trial_w6 (2026-11-05 from 20:41 PC clock; owner /plan brief; plan `PLAN_HUNT.md`)
Sections 0-8 above are the earlier job's records and stay as written (their ABBA numbers are vs FD3A5190). This
section is the next job: NEW bit-exact switches on top of trial_w6 (all six ON), each proven node-identical (bench
net on and net off, perft, 2,000 / 12,000 FENs, sanitizers) and timed against trial_w6 itself. Screening only: no
lock, no publish; QA re-times. Start tip 3ca407b3.
- Method per idea: switch `FORGE_SPD_<X>` default 0; identity builds all switches 0 = FD3A5190 and six ON + new OFF =
  4181A589 (byte for byte); `speed_pack -Quick -SkipAbba` with the six + the new define (pc1 = pc2, bitexact vs
  trial_w6); `abba.ps1` vs trial_w6 alone on CPU 2 (d20, 10 rounds); verdict rules of the skill (wall decides, cpu
  must not contradict, a pool never decides, one 16-round re-time for a borderline run).
- Results: see the table in `STATUS.md` (filled per idea) and the subsections below.

### 9.1 Profile of trial_w6 (rip_sampler, 2026-11-05 ~20:50 PC clock)
`tools/rip_sampler.py` on a byte copy of the live lock exe (4181a589), bench 20 x 3 (12,389,307 nodes each; 2.40 / 2.11
/ 2.42 M nps while the live trainer shared CPUs 0-3), engine on CPU 1 Idle, sampler 0x3 Idle: 7,734 samples, 98.9 %
inside .text (`C:\ospd_hunt\prof\w6_b20_r1\`, `profile_remap.txt` after the section-label fix). Flat self time:
| function | share | hottest spot |
|---|---|---|
| Worker::search | 28.3 % | +0x145d 3.3 %: record_move's 32-byte reload of the DirtyPieces temporary right after its narrow stores (store-forwarding stall); +0x3dc 1.2 %: first key compare of the TT probe (cluster load) |
| evaluate_position (HCE) | 17.2 % | rook PEXT table loads (800 KB table) 0.6 % + 0.5 % |
| static_evaluate (net update + output, inlined) | 12.2 % | +0x23e 1.5 %: 8-byte reload of a 1-byte bool spill (setg -> mov qword); output kernel's add chain 1.0 % |
| qsearch | 12.0 % | TT probe first compare 0.8 %; material-correction load 0.6 % |
| MovePicker::next | 11.0 % | pick_best selection scan |
| generate_pseudo_legal | 6.2 % | |
| see_ge | 5.1 % | |
| std::sort parts (insertion + introsort) | 3.2 % | |
| make_move | 1.8 % | |
| record_move (out-of-line clone, qsearch) | 0.5 % | 36 of its 40 samples on the same DirtyPieces reload |
Reading: two store-forwarding stalls (record_move's DirtyPieces copy, ~3.8 % of all samples; a bool spill in the net
update, ~1.5 %) and the TT cluster's first touch (~2 %) are the clearest bit-exact targets; the HCE is spread out.

### 9.2 The ideas (each one switch, default 0, new code under `#if`, the trial_w6 text under `#else`)
All trees: `make_stack.sh h<N>_<x> trial_w6.patch h<N>_<x>_after_w6.patch`; identity builds all switches 0 = FD3A5190
and the six ON + new OFF = 4181A589 byte for byte (`tools/hunt_identity.sh`); candidate = `tools/hunt_candidate.sh`
(the six trial_w6 values + the new one, speed_pack -Quick -SkipAbba).
| # | switch | what changes | why the nodes cannot change | own proof besides bitexact |
|---|---|---|---|---|
| H1 | FORGE_SPD_LARGEPAGES=1 | TT clusters in 2 MB pages (the engine enables SeLockMemoryPrivilege in its own token; silent fallback to new TTCluster[n]()) | same cluster count, zeroed + constructed as before, same index function: every probe / store sees the same entries | lp_probe: the privilege enables, 16 MB in 0.2-9.4 ms |
| H2 | FORGE_SPD_DIRTY_INPLACE=1 | record_move writes the dirty pieces straight into (ss+1)->dirty | same entries, same order, same count; every reader stops at count | tests/dirty_inplace_diff.cpp: 18.9M moves, 0 mismatches; mutant FAIL |
| H3 | FORGE_SPD_NNUE_COLUMNS=1 | nnue::update takes each change's w1 column for both perspectives from one integer computation | the same column as feature_index(); the same float operations in the same order | tests/nnue_update_diff.cpp: update == refresh byte for byte, 2.03M updates; mutant FAIL |
| H4 | FORGE_SPD_SLIDER_PDEP16=1 | slider entries stored as 16 bits (PEXT over the empty-board rays), rebuilt with PDEP (rook table 800 -> 200 KB) | pdep(pext(a, rays), rays) = a for every attack set a inside its rays | tests/slider_pdep16_diff.cpp: 4.43M lookups = ray walk; mutant FAIL |
| H5 | FORGE_SPD_MOVE_STORE32=1 | the NZM2 generator writes each Move with one 32-bit store | the same four bytes in the same slots | tests/movegen_hash.cpp: switch 0 = 1 over 4.75M lists; mutant changes the hash |
| H6 | FORGE_SPD_PICK_FIRST=1 | the scoring loops keep the first maximum; the first pick of a list uses it instead of the scan | the scan's result (first maximum, strict >) over the same unchanged array | scratch verify build: 1,732,892 first picks = scan; bench 13 / 16 = pins |
| H7 | FORGE_SPD_LARGEPAGES=2 | H1 + net w1 + one block per worker for the six history / correction tables | same sizes, value-initialised as before, same indexing | as H1 |
| H8 | FORGE_SPD_HCE_LOCALS=1 | evaluate_pieces keeps its five accumulated fields in locals, stored once | nothing else in that function reads them: the same final values and the same adds | tests/hce_hash.cpp: same HCE incl. traced coefficients over 1.58M evaluations; mutant changes it |
| H9 | FORGE_SPD_PTYPE_ARITH=1 | piece_type() = p > 6 ? p - 6 : p instead of the table load | equal to the table for all 13 Piece values (static_assert) | compile-time proof |
Skipped after reading the code / profile: moving quiets_tried / captures_tried out of the search frame (the frame stays
over 4 KB, so ___chkstk_ms (0.55 %) stays); a SIMD pick_best scan (PICKBEST's vectorised scan already lost, and a 64-byte
load over fresh 8-byte stores would stall); int16 w1 (research: -1..+1 % for this net, rewrites the NNUE_ZMM input);
pawn-cache entry layout (its probe is ~0.3 %).

### 9.3 Timing vs trial_w6 (abba.ps1, d20, ABBA/BAAB alternating, fresh copies per round, CPU 2 BelowNormal)
Definitions: "per-round range" = max - min of the 10 round ratios (B1 + B2) / (A1 + A2); an A/A is SANE when its
median is within +-1.0 % and its per-round range <= 4.0 % (`tools/aa_sane.py`). The brief does not say which "range" it means;
the second reading, the width of the A/A's 95 % interval, is given next to every A/A (A/A 1 5.89 %, A/A 2 1.98 %, A/A 3
3.98 %, 4a 4.56 %, 4b 4.70 %, 4c 4.42 %, quiet qa 2.56 %). Even on the quiet PC the per-round sd is ~1.8 % (abba.ps1
times fresh byte copies every round on purpose; earlier jobs measured 3-5 % between copies of one exe), so ten rounds
almost always span more than 4 %: the per-round reading can fail on a quiet machine, the width reading cannot unless
the noise is real. Verdicts below say which reading their A/A meets.
**QA rule (23:1x, Couns-approved; binding for this table):** "range" = the width of the A/A's 95 % interval. A/A SANE =
|median| <= 0.5 % and width <= 4.0 % (`tools/aa_sane.py`); the per-round spread is information only. A candidate is a
WIN only if its 95 % interval lies fully above 1.000 and its median gain beats the A/A width / 2
(`tools/qa_verdict.py`: wall decides, the same test on CPU time must not contradict). By it A/A 1-4c are NOT SANE
(median or width), the quiet A/As qa and qb are SANE. Resolution: a 10-round run's 95 %
half-width is about 2.26 x sd / sqrt(10) = 1.0 % at sd 1.4 % (A/A 2) and 2.1 % at sd 2.9 % (H1 run 1): under A/A 3
conditions a true +2 % cannot reach WIN, so every result taken next to a failed A/A is information, not a verdict.
| run | when (PC clock) | load cpu2 / cpu3 start -> end | wall B/A [95 %] sd | cpu B/A [95 %] sd | verdict wall / cpu | runs.csv md5 |
|---|---|---|---|---|---|---|
| A/A 1 | 20:42-20:47 | 38 / 36 -> 44 / 38 % | 0.9961 [0.9730, 1.0319] 4.10 % (range 11.72 %) | 0.9995 [0.9825, 1.0225] 2.79 % | NOT SANE | b3e7cd37 |
| A/A 2 | 21:20-21:26 | 58 / 56 -> 72 / 58 % | 0.9945 [0.9828, 1.0026] 1.40 % (range 4.32 %) | 0.9968 [0.9891, 1.0022] 0.92 % | NOT SANE (range just over) | e7d0f995 |
| A/A 3 | 21:34-21:39 | 71 / 62 -> 79 / 67 % | 0.9924 [0.9683, 1.0081] 2.82 % (range 8.36 %) | 0.9902 [0.9703, 1.0010] 2.17 % | NOT SANE | (aa_w6_d20_s3) |
| H1 run 1 | 21:39-21:45 | 72 / 70 -> 100 / 100 % | 1.0139 [0.9886, 1.0304] 2.90 % | 1.0104 [0.9891, 1.0183] 2.03 % | NO-WIN / NO-WIN (fallback path, see below) | b9d82cba |
| A/A 4a (gate try 1) | 22:18-22:24 | 3 / 5 -> 83 / 86 % (trainer restart mid-run) | 0.9982 [0.9735, 1.0191] 3.20 % (range 11.34 %) | 0.9966 [0.9815, 1.0133] 2.23 % | NOT SANE | (aa_w6_d20_s4a) |
| A/A 4b (gate try 2) | 22:32-22:37 | 62 / 61 -> 76 / 70 % (trainer steady ~190-220 %) | 0.9898 [0.9624, 1.0094] 3.33 % (range 12.58 %) | 0.9957 [0.9579, 1.0096] 3.67 % | NOT SANE | (aa_w6_d20_s4b) |
| A/A 4c (gate try 3) | 22:45-22:51 | 69 / 61 -> 90 / 96 % | 1.0065 [0.9833, 1.0275] 3.07 % (range 10.38 %) | 0.9977 [0.9879, 1.0103] 1.56 % | NOT SANE (gate exhausted) | (aa_w6_d20_s4c) |
| H2 run 1 | 22:51-22:56 | 78 / 72 -> 13 / 2 % (QA pause took effect) | 1.0048 [0.9784, 1.0271] 3.39 % | 1.0047 [0.9946, 1.0248] 2.09 % | NO-WIN / NO-WIN (information: next to a failed A/A) | 77ccf5f5 |
| H3 run 1 | 22:56-23:01 | 23 / 0 -> 3 / 1 % (quiet) | 1.0057 [0.9862, 1.0120] 1.80 % | 1.0048 [0.9835, 1.0119] 1.99 % | NO-WIN / NO-WIN (information: before the quiet gate) | d4df0016 |
| quiet A/A qa (gate try 1) | 23:01-23:06 | 41 / 1 -> 4 / 2 % (quiet) | 1.0003 [0.9919, 1.0175] 1.78 % (range 6.50 %, width 2.56 %) | 1.0000 [0.9909, 1.0154] 1.71 % | SANE (QA rule; per-round spread 6.50 % = information) | (aa_w6_d20_qa) |
| quiet A/A qb (gate try 2) | 23:08-23:13 | 7 / 1 -> 1 / 1 % (quiet) | 1.0018 [0.9920, 1.0112] 1.34 % (spread 4.23 %, width 1.92 %) | 1.0019 [0.9918, 1.0129] | SANE (QA rule) | (aa_w6_d20_qb) |
| quiet A/A qc (gate try 3) | 23:15-23:20 | quiet | 1.0003 [0.9891, 1.0082] 1.34 % (width 1.91 %) | - | SANE (QA rule): band of the quiet decision block | (aa_w6_d20_qc) |
| H2 h2_dirty_inplace q | 23:20-23:25 | 2 / 1 -> 1 / 1 % (quiet) | 1.0053 (+0.53 %) [1.0006, 1.0151] sd 1.01 % | 1.0019 (+0.19 %) [0.9981, 1.0135] sd 1.07 % | NO-WIN (QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN) | 832eaf3b |
| H3 h3_nnue_columns q | 23:25-23:30 | 3 / 1 -> 0 / 1 % (quiet) | 1.0081 (+0.81 %) [1.0009, 1.0262] sd 1.74 % | 1.0086 (+0.86 %) [1.0017, 1.0254] sd 1.64 % | NO-WIN (QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN) | e8c5ead1 |
| H6 h6_pick_first q | 23:30-23:35 | 1 / 0 -> 3 / 0 % (quiet) | 1.0060 (+0.60 %) [0.9994, 1.0248] sd 1.75 % | 1.0067 (+0.67 %) [0.9969, 1.0259] sd 2.00 % | NO-WIN (QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall NO-WIN / cpu NO-WIN) | 77befd39 |
| H5 h5_move_store32 q | 23:35-23:40 | 2 / 0 -> 1 / 0 % (quiet) | 1.0121 (+1.21 %) [1.0024, 1.0194] sd 1.18 % | 1.0125 (+1.25 %) [1.0033, 1.0213] sd 1.25 % | WIN (QA rule vs aa_w6_d20_qc (need low > 1.000, gain > 0.96 %): wall WIN / cpu WIN) | 552ea065 |
Notes:
- The live NNUE trainer restarted at 21:39:04 (new PID 9380, Idle, mask 0xF) and has run at ~190-200 % CPU on CPUs
  0-3 since (the old PID 3940 ran at ~73 %). Observed, not caused: at that moment the only own process on CPUs 0-3
  was the A/A's BelowNormal engine on CPU 2; free RAM 12.3 GB of 31.6 GB at 21:50 (the trainer's floor is 6 GB).
- H1 / H7 (large pages) depend on the PC's memory state: the probe got 16 MB of 2 MB pages at 20:53, but at 21:51 every
  request failed with ERROR_NO_SYSTEM_RESOURCES (1450) - in 5 / 5 fresh processes of a verify copy driven exactly as
  abba.ps1 drives the exe (UCI searcher 32 MB + bench 1 16 MB + bench 20 16 MB) and in the standalone probe (each failed
  attempt 3-14 ms). H1 run 1 therefore measured the silent fallback (4 KB pages), not large pages. Large-page ABBAs now
  run only when the probe succeeds in the same step (runner v3 `abba_lp`).

### 9.4 Own review of the nine patches (22:40 PC clock; structured self-review, NOT independent)
- H2: fill_dirty_pieces writes the same entries as dirty_pieces (mover removed, captured piece removed at the ep square
  when en passant, mover or promoted piece added, the two rook entries when castling), the same count; slots at or
  above count are never read (update / update_runtime_psqt loop below count; the lock itself leaves stale slots after
  record_null_move, which only sets count = 0).
- H3: the three update paths keep the lock's per-lane order ((src - rem) + add; ((src - rem0) - rem1) + add; copy then
  add / sub in change order); null move (count 0) and castling (count 4) take the generic path as before;
  change_columns equals feature_index for every Piece the search can pass (1..12).
- H5: bits = from | to << 8 | promotion << 16 | flags << 24 is the Move's byte order (static_assert on the offsets);
  `flags | Promotion` is cast to 8 bits exactly as the lock's cast.
- H6: only a generation resets index_ / list_start_, so index_ == list_start_ means the untouched fresh list; quiet,
  capture, evasion and ProbCut / qsearch pickers each recompute first_best_ when they generate.
- H8: no reader of the five fields between the loop and the write-back; the trace path is the same template.
- H1 / H7: allocation only; failure leaves the lock's allocation and contents; no output.
- H4 / H9: proven by their harness / static_assert; H4 needs SLIDER_PEXT (#error otherwise).
No issue found. The H6 verify copy and the H1 large-page verify copy are scratch builds outside the patches.
- 22:5x: QA paused NNUE training, gates and self-play for this hunt (Couns-approved; CPUs 0-6 + GPU free until usage
  runs out). From then on: A/A gate with the normal rule, then fresh 10-round ABBAs of every pack on CPU 2 with CPU 3
  idle, one at a time. Large pages were available again at 22:57 (probe 6 / 6 OK), so H1 / H7 are timed.
