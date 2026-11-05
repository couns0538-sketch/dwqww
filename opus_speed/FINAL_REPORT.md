# Forge speed job - FINAL REPORT (DRAFT, filled as results land)

State: DRAFT (started 10:15 PC clock = Vienna time). Job window 2026-11-05 08:38 -> 14:38; this report is due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Scratch `F:\ospd\`. Crew vote: A (speed-only lock path) >
B (bit-exact hot-path changes) > C (gate wall time); D only if A-C are done. No Elo claims anywhere; speed numbers
only from this job's ABBA CSVs (named per row); everything else is UNPROVEN.

## 0. Summary
- **Job A (vote 1) - DONE.** A one-command speed-only lock path: `speed_pack.ps1` turns a source tree into an LTO+PGO
  exe built with QA's kit command lines (it reproduces the lock exe FD3A5190 byte for byte), checks pc1 = pc2, runs
  the bit-exact proof (bench net on + off d11-d22, perft, 12k six-field FENs at depth 13, MSVC ASan + g++ UBSan) and
  an ABBA nps comparison against the lock, and writes a QA hand-off file. All three success tests pass (lock-vs-lock
  pack inside the A/A band; a one-constant mutant and a move-order mutant both fail before any ABBA; the best flag
  variant got a full pack). Independent review: no BLOCKER; its 4 SHOULD and 11 LOW items are fixed. No compiler
  flag or build mode beats the lock's own LTO+PGO recipe; a PGO profile taken with the net OFF would cost 29 % - the
  lock is safe from that because its embedded net is ON in the frozen workload.
- **Job B (vote 2) - DONE.** 10 bit-exact switches written and proven (all OFF by default; the default build of the
  final stack is the lock exe byte for byte). Protocol (wall nps) winners: no-zero move lists + quiets-only
  generation (+3.6 %) and the R14 SPEED2 switch (+3.2 %); TT access without the TLS lease check is +3.7 % on CPU
  time (+4.2 % wall in a noisy run, re-timed). **Stack TT_NOTLS + NO_ZERO_MOVELISTS=2 + SPEED2: +11.5 % wall /
  +11.3 % cpu vs the lock, bit-exact incl. the full 12k set** (stack_w2; stack_w3 with prefetch-early +11.4 % /
  +11.8 %). This is the first thing for QA to time (section 5). No Elo claim; QA re-times on its own cores.
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
  and bitexact_check on the kept exe says NOT BIT-EXACT at L1 (test_moveorder_mutant 3/3 PASS, 09:53).
- Code Review tests: 13/13 PASS (`tests/test_cr_637b.ps1`).
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
PENDING_B_TABLE
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
1. **stack_w2** = lock source + `opus_speed/patches/trial_w2.patch` (md5 80f8124f; = b1_tt_notls + b2_no_zero_movelists +
   r14_speed2_after_nzm) with `FORGE_SPD_TT_NOTLS=1`, `FORGE_SPD_NO_ZERO_MOVELISTS=2`, `FORGE_SEARCH_SPEED2=1` flipped in
   the source (`F:\ospd\packs\stack_w2\src_kit`, so QA's kit builds it without -D flags). Exe
   `F:\ospd\packs\stack_w2\forge_stack_w2.exe` sha256 db957393 78e21771 e0b03e42 e258f551 ebeb3b66 f1151f23 2f4f1b89 e7f933a9
   (md5 1d4080bc), pc1 = pc2. Bit-exact: L1-L4 + full 12k L3 12,000 / 12,000. This job's ABBA vs the lock: wall +11.48 %
   [1.0734, 1.1217], cpu +11.34 % [1.0990, 1.1191] (candidate file `opus_speed/candidates/stack_w2.md`). QA: rebuild
   `src_kit` with the kit (must give sha256 db957393...), re-run the pins / 12k identity, and time it on QA's own cores.
2. The same three changes one by one, if QA prefers single steps: b2_nzm2 (+3.6 / +4.3 %), r14_speed2_b (+3.2 / +2.9 %),
   b1_tt_notls_b (cpu +3.7 %).
3. stack_w3 (= stack_w2 + prefetch_early): see section 3 for its ABBA; only worth it if it beats stack_w2.
Nothing here is locked or queued by this job; QA decides.

## 6. Skills created or improved (on this branch; the project copies on D: were not touched)
- NEW `skills/forge-speed-lock-path/SKILL.md`: the whole speed-only lock path (tools, ABBA protocol with wall as the
  protocol verdict, bit-exact levels incl. the MSVC ASan comparison, re-time / pooling rule, stacking with
  make_stack, proven facts and the day's results, 16 pitfalls hit today). Also installed user-scope
  (`C:\Users\Administrator\<cfg>\skills\forge-speed-lock-path\`), like forge-gate-walltime.
- NEW `skills/forge-gate-walltime/SKILL.md`: Job C tools, the facts they rely on, the measured gate numbers.
- IMPROVED `skills/forge-ltopgo-pgo/SKILL.md` (copy + section "Speed job 2026-11-05"): the lock's net is embedded and
  ON (v1 workload profiles it), net-off profile -29 %, flags that give the identical exe, flag / build-mode table,
  switch-0 = lock byte for byte, SPEED2 reproduction.
- IMPROVED `skills/forge-pc-rules/SKILL.md` (copy + section "Speed job"): CPUs 0-3 rule set, restart re-pin, heredoc
  backslash and `$1` pitfalls, `git rm` refusal.
- Helper scripts (opus_speed/tools): commit_push.sh (gated commits), make_stack.sh, pack_table.py, abba_table.py,
  ctrl_char_check.py, name_lint.py, ps_parse_check.ps1, pgn_positions.py.

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
- Worker b1tt wrote one scratch diff outside its write area (C:\...\Temp\b1_tt_notls_check.diff, 12.6 KB, 09:14,
  self-reported); left in place (no-delete rule).
Own tool bugs found and fixed during the job (all before any candidate was called valid): fail-open pin DIFF (Code
Review blocker), ordered-dictionary int indexing (all pins looked DIFF at 637be9af), swallowed L1/L2 lines,
`-File` list parameters, native stderr under `Stop`, placement-only FENs (L3 compared one position; withdrawn),
slot-order bias in plain ABBA, `speed_pack.ps1` not parsing under PS 5.1, a BEL byte in a log path (heredoc),
`-Twice` never reporting REPRO (output-stream pollution), stdin-file sharing between two trainings, a race on the
shared L3 reference cache (three packs superseded), MSVC vs g++ node counts in L4 (four packs re-run).
Owner items:
- The 3 LOW notes of Code Review CR_OPUS_SPEED_TOOLS_637B were not visible on the PC; please send their text.
- QA: re-time the WIN candidates on QA's own cores before any lock (this job never locks anything).
- Robustness note, no Elo / node effect: `Worker::clear()` assigns a ~1.4 MB `ContinuationHistory{}` temporary on the
  stack; MSVC's 1 MB default stack overflowed under ASan (MinGW's 2 MB default hides it). An in-place reset would
  remove the dependence (not changed here: not a speed item).
- Two different files named `fens_12k.txt` exist (branch file: six fields; scratch copy: placement only); see
  `opus_speed/data/README.md`. Earlier jobs used the six-field branch file (their 12k results stand).
