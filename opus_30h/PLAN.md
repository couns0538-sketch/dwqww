# Opus 30-h job (branch `opus-30h-<start date>`): v2 net (Item A) + SPSA tuner (Item B) - PLAN

## Context
Couns wants two Forge wins: **A** a much stronger net by finishing the R14 v2-net path (FORGENN2 nets, my bullet
trainer `forge-v2-bullet`, ROCm build 0028dd9c, `opus_r14/b/GPU_REQUEST.md`), and **B** an unattended SPSA tuner for
search constants. The survey (read-only, 2026-11-03 PC clock) found facts that shape the plan:

- **GPU is not free.** npt keeper STATUS (15:48): live line `..._s39`, next `..._s40`, window to 2026-11-08 00:00 PC.
  The prompt says the job starts after Engine QA releases the GPU in writing.
- **Pure big nets lose to the lock.** Four crew gates (10+0.1, 8moves_v3): npt K32H3^ L1-1024 nets vs AL1 lock =
  -86 / -91 / -102 / -116 Elo, ~2 plies shallower (20.0 vs 22.1). QA's bullet K32H3^ net lost 12 +/- 14 to an npt net.
  The lock net is a **residual** 768x256 (HCE + correction, `FORGE_NNUE_RESIDUAL 1`). My R14 trainer as written trains
  **pure** nets (`sigmoid(out)` vs the blended score, no HCE term; `export_v2.py` writes `residual=False`).
- **The lock source has no v2 path.** d4f4312 has `nnue.hpp` only. FORGENN2 (`nnue_v2.hpp`, 705 lines + 218-line search
  wiring) lives in the R3 tree b7c17722, with king buckets 1-32 + mirror, output buckets 1-16, residual flag, O6/O7.
  R14 deferred this port; an exe that loads a v2 net with OFF = lock pins needs it.
- **bullet da426a49**: no CPU backend (every training test needs the GPU), no validation pass ("not currently
  implemented"), but `load_from_checkpoint` + `start_superbatch` exist (resume possible).
- **Data.** npt data = J1 binpack (305.0M records, F:) = the FPOS/FHCE shards 001-039 minus 013/014 re-encoded; the FPOS
  shards (D:\grok-pc-data\forge_push\nnue_data) carry the per-row HCE the lock net was trained against; the binpack does
  not. "P5-relabelled + Astra R13 QC" = jobA `D:\o14b\r2\proof\jobA` (999,921 rows, 20k-node labels, original FENs) +
  Astra's `D:\a13\p5qc\mate_rows.jsonl` (3,718 rows |score| >= 30000; 2,717 in jobA) + job1 (440k, reconstructed
  FENs, lossy). Lock-net split = holdout 013/014; S31 subset `holdout_013_014_s16` (1,024,286 rows): AL1 b0.6 0.014310,
  b1.0 0.004572. Astra R13: production 013/014 game separation UNVERIFIED (original game bindings not recoverable).
- **Item B is half there.** The lock exe (-Expose) already advertises 41 search constants at lock defaults (LmrQuiet*,
  LmrNoisy*, NullMove*, Rfp*, Razor*, Futility*, LmpBase, HistoryPrune*, See*, Singular*, Iir, Probcut*, Qs*,
  AspirationDelta, HistoryBonus*, LmrHistoryDivisor, CheckExtensionDepth, LmrCutoffThreshold, MaterialCorrectionWeight,
  CaptureFutility*, FailLowContinuationBonus) + 10 Tm* (= R9's 51 lock constants). R9's `r9_spsa.py` has resume, CSV, governor, deadline; R9's
  verdict: 832 pairs x 16 params = noise; next time fewer params, larger c.
- **CPU reality.** pc_status 15:56: CPUs 4-15 at 91-100 % (gate 0xFFF0 + self-play), npt trainer Idle on 0-3. Off-gate
  cores = 0-3 = two physical cores. D: 57.2 GB free (7.2 GB above the 50 GB floor), C: 123 GB.

## Decisions at approval (I follow these defaults unless you say otherwise)
- **D1 Start mode:** start now with the CPU-light steps (Phases 0-4: port, scorer, data audit, trainer code, harness,
  options, tools; Idle, CPUs 0-1, <= 2 threads, like R15). GPU training (Phase 5) only after Engine QA's written
  release, quoted into `D:\o30\WINDOW.md`. The 6-h SPSA session and the 400-game matches (heavy CPU) also wait until
  npt is off CPUs 0-3 or the crew frees cores. Alternative: hold the whole job until the release.
- **D2 Disk:** everything under `D:\o30`, budget <= 3 GB (R15 used 1.3 GB for 16 kit builds), data read in place,
  check before every write > 100 MB, stop + report if D: < 50 GB or C: < 30 GB (other jobs move D: by GBs per hour).
  Alternative: allow `C:\o30` as overflow.
- **D3 Shape = residual.** Main line: residual FORGENN2 (HCE + net, like the lock), 768 x KB king buckets (mirrored) ->
  H=256, SCReLU, 8 output buckets. Trained from the FPOS + FHCE shards (= the npt data's source rows + the HCE the lock
  net was trained on). A pure arm runs as a pilot on the same data, so the choice rests on holdout loss, not on
  assumption. O6 threats / O7 pawn pairs are not ported (inference cost; the HCE already covers threats/pawns).
- **D4 Relabelled data role:** jobA minus Astra's mate rows replaces the self-play score of the same (shard, line)
  training rows of FPOS 001/002; jobA's own val split is held out of training and used as a 2nd validation set (deeper
  labels); job1 (440k reconstructed FENs) is not used (Astra R13: lossy).

## Ground rules (from the prompt + standing rules; checked before every command)
- Lock FD3A5190 (sha256 fd3a5190...6873072), pins d11 312866 / d13 862329 / d16 3024920 / d20 12389307 / d22 34048354,
  perft 4865609 / kiwipete 193690690; lock net e32f003rec_s198 (nnue_weights.inc md5 22b4b9e2). Every new option
  default OFF; OFF = exact pins. No Elo claims; own games = tuning / sanity only.
- Writes: `D:\o30\` + branch `opus-30h-<date>` (from main, own CI workflow like R15, worktree `D:\o30\wt`); skills /
  MCP under `C:\Users\Administrator`. Never touch npt, keeper, gates, queue, forge_queue_state.json, other bots'
  processes or Astra's dirs (Astra's mate_rows.jsonl read once, sha256 recorded). Never delete, kill, force-push,
  touch main, create STOP/PAUSE files (cooperative stop = deadline + named event, as R11).
- <= 8 threads total, only on cores outside running gates' masks (pc_gate + cpu_users before each heavy step);
  Idle/BelowNormal; RAM >= 8 GB during GPU runs; never the string `train_res`+`id` in any command.
- Clean-room: no other engine's code/constants/tables/weights; no vendor/model-company names, no licence headers in
  patches, comments or commit messages -> **no Co-Authored-By trailer** (prompt rule, R15 precedent); uci.cpp `id`
  lines, tools/openings, LICENSE untouched (cleanroom_lint + diff check).
- Commit + push about every 10 min, no `[skip ci]` (CI runs per push, cancel-in-progress; must end green); git identity
  `-c user.name=couns0538-sketch -c user.email=couns0538@gmail.com`; literal `git push -q -u origin opus-30h-<date>`.
- No sub-agents. `date` before every written time; time spent only from commit spans. 20-min self-review per block
  (NOT independent), 30-min bug hunt at the end.

## Phase 0 - preflight (~0.5 h, CPU 0-1)
1. pc_gate (R14-B fixed copy) + cpu_users + disks + RAM; read keeper STATUS; WINDOW.md only from a written release.
2. Worktree + branch from main; copy R15/R14-B tools into `opus_30h/tools/` with D:\o30 paths (fresh_lock.sh,
   kit_build -> kit_build_o30.sh, pin_check.ps1, smoke2m.py, cleanroom_lint.py, pc_gate.ps1, lowrun.ps1, abba.py,
   gate_summary.py, make_index.py, index_check.py, commit_span.py); PLAN.md, STATUS.md, IDEA_SOURCE.md; first push.
3. Re-verify the base: fresh lock export -> kit v2.3 `-Expose` pc1 and pc2 -> sha256 == fd3a5190... both; pin_check -Full.

## Phase 1 - Item A engine: FORGENN2 path on the lock (~5 h, CPU)
1. Fresh LF lock copy `D:\o30\src\v2port` (scratch git at d4f4312); port with the forge-lock-port pattern:
   - from b7c17722 `include/forge/nnue_v2.hpp`: loader (FNV-1a, exact size, header checks, int16 range), feature_set 0
     only (PSQ, king buckets + mirror, output buckets, residual flag), AVX2 / SSE / scalar output kernels, refresh cache;
     files with O6/O7 bits are rejected with an `info string` error, never a silent fall-back;
   - own width `FORGE_NNUE_V2_HIDDEN` (build switch, default 256), separate from the embedded lock net -> the lock net
     stays H256 and untouched (removes R14's zero-padding risk); `FORGE_NNUE_V2_SCALAR` test define forces scalar;
   - search wiring at the hook points R10 used for EvalFileHalfKA on this tree (lazy per-worker accumulators);
     residual = the lock's own HCE + v2 cp, combined exactly where the lock adds its residual net;
   - UCI string option `EvalFileV2` (empty = OFF); load line echoes path, checksum, H, KB, OB, mirror, residual.
2. Checks: plain build OFF pins + uci list = lock + EvalFileV2; R14 parity flow (`parity_v2.sh`, eval_ref.py, Rust
   feature lists) extended to KB/mirror/residual: random nets at H256 (and H512 if used) with KB 1 and 4m, OB 8 ->
   reference vs engine harness AVX2 / SSE / scalar 10000/10000 exact, planted bug FAILS; incremental == refresh walk
   1M plies (king-bucket crossings, mirror flips, castling, ep, promotions) 0 mismatches; ON bench stable twice.
3. Kit `-Expose` build at H256 (pc1 = pc2), OFF pins, ON live with a random net; CI row (ASan+UBSan self-play,
   OFF + ON random net, Threads 1/2). Outputs `opus_30h/a/v2port.patch`, `opus_30h/a/RESULTS.md`.

## Phase 2 - Item A data, scorer, trainer code (~4 h, CPU; no GPU)
1. Data audit -> `opus_30h/a/DATA.md` + `D:\o30\data\`: sha256 of every input; FPOS row counts vs J1 binpack
   records; holdout key set (32-byte board + stm, all 013+014 rows) -> count + skip list of training rows that hit it
   (S16 saw 6,069), same for jobA; mate rows (|score| >= 30000) excluded everywhere, counts per source; statement:
   separation is by self-play file + position-level overlap removed; authentic game-level proof is not possible
   (Astra R13). HCE check: lock-source HCE vs FHCE on 100k rows (report equal count; FHCE is what the lock net used).
2. Holdout scorer (own C++, links the ported nnue_v2.hpp + lock nnue.cpp): b0.6 / b1.0 MSE with the S31 target
   (`b*sigmoid(clamp(score*K, +-40)) + (1-b)*stm_result`, K = 2.25/400). Control: AL1 on s16 must print 0.014310 /
   0.004572 before any v2 number counts. Scores pure (`sigmoid(K*net)`) and residual (`sigmoid(K*(net+hce))`) files,
   plus the jobA-val metric.
3. Trainer = my R14 `forge-v2-bullet`, extended (copy in `opus_30h/a/forge_v2_bullet`; private bullet da426a49 copy
   `D:\o30\bullet` (MIT; F:\bullet_hip untouched); CARGO_HOME copy `D:\o30\cargo_home`):
   - residual: optional per-row base input added to the output before the loss (dense input = hce_stm / eval_scale;
     ~30-line patch to the value mapper + builder);
   - own record type + reader for FPOS + FHCE (+ jobA overrides, skip list, mate filter), deterministic shuffle by
     (seed, superbatch) so `--resume <ckpt> --start-sb N` continues the same stream;
   - ForgeV2 inputs with king buckets + mirror exactly as nnue_v2.hpp; target b = 0.6 (WDL 0.4), eval scale 400/2.25;
   - CLI: residual, kb map, mirror, hidden, wdl, lr, superbatches, save-every, resume, seed, until;
   - export_v2.py writes residual flag, king map, mirror.
   CPU proofs before any GPU minute: mock-backend build 0 warnings; reader unit tests (decode == S31 reader on 10k rows,
   stm/score/result/HCE signs); feature map == engine on 10k FENs (KB/mirror); random-net parity (Phase 1); ROCm build
   (Engine NNUE env from build_rocm_r14.bat, D:\o30 paths, CPU only).
4. `run_train_o30.ps1`: checks before and during each run (WINDOW.md, keeper `npt trainer running | NO`, no production
   python on the GPU, RAM >= 8 GB, disk, cores), Idle + mask, <= 2 loader threads, deadline, checkpoint every
   <= 30 min (cadence from measured superbatch time), `last` + `best` (by s16 loss via the scorer); nothing deleted.

## Phase 3 - Item B harness + exposure (~2.5 h, CPU)
1. Option inventory: each of the 41 advertised search constants checked live (d11 bench moves when changed, returns to
   pins at default) -> table.
2. New OFF-safe options (R15 tune:: pattern, R9 `patch_r9_search.py` as the map of literal sites), default = lock
   literal: LmrCutNode, LmrNotImproving, LmrTtPv, LmrGivesCheck, NmpEvalBase, SingularDoubleMargin, HistoryMalusPercent,
   QuietCheckBonus -> 49 exposed search constants; OFF pins and on-at-defaults pins; each new option live.
3. `tune_spsa.py` = port of r9_spsa.py (keep its tested core) + param CSV (name,start,min,max,c,a), thread cap, CPU mask
   outside gate masks re-checked per batch (shrink / wait), `--until`, per-iteration CSV, resume after crash / reboot via
   the re-runnable `tune_spsa.ps1`; R9 sim tests + new ones (hard-exit resume, CSV rows = iterations, deadline stop).
4. `spsa_dashboard.py` (markdown table: start, now, delta, z vs null-gradient sigma; SVG per parameter, R9 svg code).
5. README + `selftest_10min.ps1` (2 params, 1+0.01, 10 min, resume one batch, checks state + CSV).
6. Item B exe: kit `-Expose` pc1 = pc2, OFF pins; later the same patch + `O30Tuned` switch (OFF default) after Phase 7.

## Phase 4 - tools, skills, MCP (~2 h, spread over the job)
`net_pack.ps1` (export -> sha256/md5 -> parity AVX2/SSE/scalar -> s16 score -> bench ON d11/13/16 + perft -> INDEX row),
`run_train_o30.ps1`, `sanity_match.ps1` (fastchess 400 games, conc from free cores, gate_summary), smoke2m.py
`--seconds 300`, pin_check.ps1 with EvalFileV2, SPSA tools. Skills (user scope + branch copies): `forge-o30-v2net`,
`forge-o30-spsa`. MCP: add `net_score` / `spsa_status` to my forge-uci server (own code) with a re-runnable setup
script. `D:\o30\TOOLS.md`: purpose + verify command per item.

## Phase 5 - [GPU window only] training (~6-8 GPU h, background; CPU work continues)
- First 10 minutes = smoke: loss falls; exported net's eval == trainer forward on 1k rows; pos/s measured.
- Pilots (same data, ~1.0G positions each): P1 residual KB1 H256 OB8; P2 pure KB1 H256 OB8; P3 residual KB4m H256 OB8.
  Rule: keep the arm with the lowest s16 b0.6; pure only if it beats residual.
- Main runs ~8G positions each (~ the lock net's 7.4G presentations), cosine LR, checkpoints <= 30 min, each one
  exported + scored on CPU: M1 = best arm; M2 = second arm or b = 0.75 of the same shape (same H -> one exe). Optional
  M3 H512 only if M1/M2 beat AL1's 0.014310 offline and time remains.

## Phase 6 - per-net packaging + checks (~3 h)
Exe: kit `-Expose` of the port at the nets' H (pc1 = pc2, OFF pins). Per net: sha256 + md5; parity 10000/10000
(AVX2 = SSE = scalar = trainer reference); bench ON d11/d13/d16 (twice equal); perft 5 + kiwipete 5 = pins; 5-min smoke
0 illegal / 0 crashes / 0 time losses; NPS ABBA vs lock >= 5 pairs (median, A/A noise, load written next to it);
400 games 10+0.1 vs lock on <= 8 threads off gate cores (sanity only). `D:\o30\nets\INDEX.md`: path, sha256,
settings, s16 + jobA-val losses vs AL1, exe path + sha256, gate line `EvalFileV2=<path>`, checks.

## Phase 7 - [free cores] SPSA session (~6 h) + packaging
10-12 params (LmrQuietBase, LmrQuietDivisor, LmrCutNode, HistoryMalusPercent, NullMoveEvalDivisor, RfpMargin,
FutilityMultiplier, SeeQuietMultiplier, ProbcutMargin, SingularDoubleMargin, AspirationDelta, LmrHistoryDivisor),
c ~2x R9's, 8+0.08, Threads 1, Hash 16, UHO book (read-only, the crew's gate book), <= 8 threads off gate cores.
Expect 1,500-2,500 pairs (R9 rate); the report states measured slots and pairs and does not promise convergence.
Deliver CSV, final values, convergence table + SVG, null-gradient sigma; `TUNED_OPTIONS.txt`; Item B exe with
`O30Tuned` (bench ON == explicit option list); gate line for UHO [0,5] + 8moves_v3 confirm.

## Phase 8 - wrap-up (~1.5 h, and whenever usage runs low)
30-min bug hunt (re-run checks, read diffs); `D:\o30\FINAL_REPORT.md` pushed: everything done with full paths and
full md5/sha256, unfinished + exact resume commands, every check result, gate-next list ranked by expected Elo, own
review of every patch (NOT independent); TOOLS.md, skills, memory file; time from commit spans.

## Verification (end to end)
- Base: kit rebuild of unpatched lock = fd3a5190 (pc1, pc2). Every exe: pin_check OFF = pins, perft pins, kit pc1 = pc2,
  cleanroom_lint PASS, uci list diff = only the new options, CI row green.
- Item A: parity 10000/10000 x {AVX2, SSE, scalar} at the delivered H (random + trained nets), planted bug fails;
  1M-ply walk 0 mismatches; scorer reproduces AL1 0.014310 / 0.004572; per-net checks of Phase 6; index_check on INDEX.md.
- Item B: option live/identity table; sim tests + selftest_10min PASS; resume proof (hard exit -> rows continue);
  O30Tuned bench == explicit list bench.
- Docs: doc_lint, hash_sweep (every cited hash matches a file), times <= `date`.

## Risks
No window before the job ends -> Item A stops at "port + scorer + trainer ready, parity proven" (Item B still
completes). Residual bullet patch is testable only on the GPU -> 10-minute smoke first. CPU starvation -> fewer SPSA
pairs / slower matches (measured, reported). D: drift by other jobs -> stop + report. Kit profile is trained with
EvalFileV2 OFF (cold-optimised v2 path) -> ABBA shows it; noted in the review.

## Reuse (paths)
`opus-r13-p4-v2nets` (forge_v2_bullet, export_v2.py, eval_ref.py, parity_v2.sh, legal_fens.py, build_harness_r14.sh),
`opus-r13-p4-v2nets:opus_r14/b/{GPU_REQUEST.md,build_rocm_r14.bat}`, b7c17722 `include/forge/nnue_v2.hpp` +
`src/search/evaluation_v2.inc`, `opus-r10-halfka` (lock-tree eval hook points), `opus-r9-spsa:opus_r9/{tuner,tools}`,
`D:\o15\wt\opus_r15\tools\*` + `.github/workflows/opus-r15-san.yml` (CI pattern), `opus-r14b-status:opus_r14b/tools`
(abba.py, pc_gate.ps1, lowrun.ps1), S31 scorer + `F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.*`.
