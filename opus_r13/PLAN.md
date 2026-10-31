# Forge R13 — first plan (Opus): Phase 1 items 1–2, Phase 2 steps 1 / 1a / 1b

## Context
Couns's R13 job (30 h of work, $100 of credits, no sub-agents). This plan covers only the first block: port two near-miss
patches onto the lock tree as gate-ready LTO+PGO `-Expose` candidates (B1 bundle, packa NonPawnCorr w50/w60), then the
speed-stack build with weight alignment and net-path PGO. Everything is UNPROVEN until a crew gate or QA timing says otherwise.
This file is committed as `opus_r13/PLAN.md` on `opus-r13-status` before any other work.

## Facts found (read-only exploration, 2026-10-31)
- Lock source `...\qa_ltopgo_al1_stage\src_al1s198_clean` (20 files) is **byte-identical to git `d4f4312`** (all 20 blobs equal).
  So a fresh lock copy = `git archive d4f4312 src include`, and CI can rebuild it.
- Kit v2.3 `build_ltopgo.ps1` md5 729fe727 (checked). Compiles every `src/*.cpp`, flags `-march=znver5 -DFORGE_NNUE_HIDDEN=256`,
  `-Expose` adds `-DFORGE_EXPOSE_TUNABLES=1`, default `-Work D:\forge_push\ltopgo` (it must always be passed explicitly).
- **Disks:** C: 169.7 GB, D: 82.3 GB, **F: 45.0 GB (already under the 50 GB floor)**. So all scratch, builds and handoff exes go
  to **`C:\o13\`** (short work dir `C:\o13\w`), and this is written in RESULTS.md. Scratch goes to F:\o13 only if F: is back to ≥ 50 GB plus the write size.
- **B1 (item 1):** `forge-bundle-int` @ b7c17722 is the R3 stack (O3 split layout `src/search/*.inc`, 8 search instances).
  The lock tree has one monolithic `search.cpp` (1531 lines), so this is a real port, not a copy. Where each part comes from:
  HistRework = A1 a8b63aae (written on the monolithic tree, applies almost directly); TtPruneV2 = FB2-J3 33e295b4 (monolithic,
  take only the TtPruneV2 hunks); CorrHistPlus = C2 e9307356 and CuckooRep = C6 2cb0babd + 147395c4 + 4d14f3cf (O3 split
  layout; O3 804c6e1b was "no behaviour change", so its hunks map back onto search.cpp); BundlePreset + the CorrHistPlus×HistRework
  interaction = bundle-int `src/search/evaluation.inc`, `src/uci.cpp`.
  **Node reference, B1 ON** (BUNDLES.md, AL1 net, same OFF pins): d11-d22 = **280182 / 758456 / 3357587 / 11208630 / 20560049**;
  TtPruneV2 alone 309157/736967/2960397/12062561/34293668; CorrHistPlus=1 alone d11 318363.
- **packa (item 2):** `opus30h_inputs\packa.patch` dry-runs cleanly on the lock (`patch -p1 --dry-run`) for src/search.cpp,
  search.hpp, board.cpp, board.hpp. Its CMakeLists.txt hunk has no target in the lock tree and is dropped. `tests/nonpawn_key_tests.cpp`
  is kept and built by hand. It was made on the old h256e12 base (different net), so ON nodes will differ from the old base by design.
- **Phase 2 inputs:** R12 bundle 7D5081E3 = QA build `q12_w21pt` from **r10fix1 source** (`F:\opus_scratch\r12\src_r10fix1`,
  git 7f79c349 = lock + EvalFileHalfKA, OFF = lock pins) with workload v2.1 + `-fprofile-partial-training` + Expose. QA's log
  already shows "real missing-profile warnings: 0". S1 LargePages 0A22484F source is
  `forge_push\qa_s1lp_20261031\FORGE_S1_LARGEPAGES_SRC.zip`, which includes `s1_largepages_vs_FD3A5190src.patch` against the lock source.
  Nets: `forge_push\bin\r11_e19_final_bf1e347c.nnue`, `r11_e9_best_5380f866.nnue` (read only).
- `git push -q -u origin opus-*` is on the allow list. Main's tree is 10 files (2.4 MB), so worktrees from main are cheap.

## Step 0 — setup (≈15 min)
1. Worktree `D:\grok-pc-data\dwqww\.claude\worktrees\o13-status` on new branch `opus-r13-status` from `main`
   (`git branch --unset-upstream`). Commit `opus_r13/PLAN.md` (this plan) + `opus_r13/STATUS.md` (one line per phase), push.
2. Add `__pycache__/` and `*.pyc` to `.git/info/exclude`. Commit as `git -c user.name=couns0538-sketch -c user.email=couns0538@gmail.com`.
3. Phase worktrees from main: `o13-p1` (`opus-r13-p1-nearmiss-ports`), later `o13-p2` (`opus-r13-p2-sparse-l1`).
4. Load/disk gate helper `opus_r13/tools/pc_gate.ps1`: free C:/D:/F:, total CPU %, free RAM, per-CPU load.
   A heavy step starts only if C: ≥ 30 GB + its write size, CPU ≤ 85 %, and RAM ≥ 6 GB. Otherwise it waits (Monitor/until loop, no sleeps).
   Own processes run BelowNormal (Idle for long runs) with ≤ 2 threads, pinned to 2 CPUs away from the gates
   (prefer the Idle trainer/self-play CPUs, never 0xFFF0 gate CPUs under load).

## Phase 1 — shared pipeline, then packa (shakedown), then B1
Order: the pipeline is built and proven on packa first (easy, about 1 h), then B1 (hard, about 3-4 h). If credits run out in the middle of B1,
two gate-ready packa lines are already pushed. RESULTS.md still ranks the candidates in the prompt's order (B1 first).

### P1.0 Pipeline tools (`opus_r13/tools/`, committed on the p1 branch)
- `fresh_lock.sh <dir>`: `git archive d4f4312 src include`, then a local scratch git repo with a base commit, so `git diff` gives a/ b/ patches.
- `lineset_diff.py A.patch B.patch`: compares the sorted multiset of +/- lines (whitespace-normalised) and lists only-in-A / only-in-B.
- `kit_build.ps1 <src> <tag> <checkopts…>`: runs pc_gate, then the kit with `-Work C:\o13\w -Expose`, the pins and perft pins, `-CheckOpt` per gate line.
  It is called twice (`<tag>p1`, `<tag>p2`), then checks pc1 = pc2 exe sha256 and copies the exe to `C:\o13\handoff\<item>\`.
- `cand_checks.py <exe> --line "N=V;…"`: `uci` option list (every new option present, default OFF), bench d11/d13 ON,
  T1 and T4 `go movetime 1000` smoke (T4 runs inside a 2-CPU mask, waits for `bestmove`, checks legality with `go perft 1`),
  mate probe OFF/ON (fixed-depth mate FENs, mate found + distance per FEN), JSON + log out.
- CI sanitizer: `.github/workflows/opus-r13-san.yml` on the p1 branch (push on `opus_r13/p1/**`). For each item patch it fetches
  d4f4312, applies `patch -p1 -F0`, builds g++ `-fsanitize=address,undefined -fno-sanitize-recover=all -march=x86-64-v3`,
  and runs `selfplay_smoke.py` (no python-chess; legality via `go perft 1`) for 3 configs: default, gate line, max values.
  It must show 0 sanitizer reports and 0 illegal moves. Nothing runs on the PC.

### P1.2 packa NonPawnCorr → `opus_r13/p1/packa_w50`, `packa_w60` (one exe, two gate lines)
1. Fresh lock copy, `patch -p1 -F0` of the src/include/tests hunks. Port patch = `git diff`.
2. Proof: lineset_diff vs packa.patch shows only the dropped CMakeLists hunk. Plain build bench OFF = pins.
   ON d11/d13 for both lines, plus a search for any AL1-tree bench of packa in the inputs (none expected: old base, so the difference is explained).
   The hand-built `nonpawn_key_tests` passes.
3. Kit pc1/pc2 with `-CheckOpt` lines `NonPawnCorr=1;PawnHist=1;NonPawnCorrWeight=50` and `…=60`. Then cand_checks and CI sanitizer.
4. Handoff READMEs give the exact setoption lines, the exe sha256, and the ON d13 nodes as the PC precondition. Also patch, IDEA_SOURCE.md (from the packa source), logs.

### P1.1 B1 bundle → `opus_r13/p1/b1`
1. Fresh lock copy. Apply A1 HistRework hunks (src/include only). Hand-port the C6 CuckooRep board cuckoo table + search hook
   (one runtime branch in the lock's search/qsearch instead of 8 macro instances, same semantics incl. the halfmove ≥ 3 skip).
   Hand-port C2 CorrHistPlus (full 0..7 bitmask, original name and range). Add the TtPruneV2 hunks from 33e295b4, with a per-search
   snapshot like bundle-int. Mirror bundle-int's evaluation.inc order of the CorrHistPlus / HistRework terms (integer rounding).
   UCI `BundlePreset` accepts `B1` (sets CorrHistPlus 1, HistRework 2, CuckooRep true, TtPruneV2 true). B2–B4 are refused with
   an info string (CorrHistV2/LmrTableV2 not ported).
2. Proof: plain build OFF = pins, and **B1 ON bench d11-d22 = 280182/758456/3357587/11208630/20560049** (the binding port proof).
   On a mismatch, bisect with the singles (TtPruneV2 row, CorrHistPlus d11). If needed, build bundle-int plain once for the
   HistRework-only and CuckooRep-only references. lineset_diff vs the concatenated original diffs, with every O3→monolithic translation line listed.
   Two failures for the same reason → write it up in RESULTS.md, push, and go on to Phase 2.
3. Kit pc1/pc2, `-CheckOpt 'BundlePreset=B1'` plus the 4 single options; cand_checks (mate probe is required: TtPruneV2 prunes); CI sanitizer.
4. Handoff as for packa. Gate line `setoption name BundlePreset value B1` (plus the 4 equivalent lines), UHO book.

## Phase 2 — steps 1, 1a, 1b (branch `opus-r13-p2-sparse-l1`)
- **Step 1, stack:** base = r10fix1 source (the R12 bundle's own source). Check this against QA's `qa_r12fix` notes and the S1 README before building.
  Apply the S1 LargePages patch (ported from the lock src onto r10fix1, dry run first). Build with the w21pt recipe
  (workload v2.1 / R12 kit v2.4 `-Workload v2t1 -PartialTraining -Expose`). Identity: OFF pins, e19/e9 net pins
  (D8D90B68 counts from forge-ltopgo-pgo), LargePages ON = OFF nodes, pc1 = pc2.
- **Step 1a, `FORGE_ALIGN_WEIGHTS` (build switch, default off):** 64-byte alignment of the embedded net's weights and the HalfKA
  weights (2 MB when LargePages is on). Check the column-load offset (16 mod 64 → 0) with a tiny address print in a test build.
  Proof: pins, net pins, and a 10k-FEN eval/`go depth 2` identity, ON = OFF.
- **Step 1b, net-path PGO:** the stack's profile includes the no-net + e19 + e9 bench passes (v2t1 / v2.1). Prove 0 real
  `-Wmissing-profile` warnings and pc1 = pc2, and state the workload version next to every number (never mix v1/v2 builds silently).
- Optional and advisory only: a short ABBA (≥ 10 pairs, one core, Idle) for align ON vs OFF if a CPU pair is free. QA does the official timing.

## Verification (per candidate, all in RESULTS.md with log paths)
pc1 = pc2 exe sha256 · OFF pins 312866/862329/3024920/12389307/34048354 exact · perft 4865609 / 193690690 · ON bench per gate line
≠ OFF · `uci` lists each option, default OFF · T1/T4 smoke legal · CI ASan+UBSan self-play 0 reports / 0 illegal (default, gate, max)
· mate probe OFF/ON · port proof (line set + ON-node reference). Any OFF pin mismatch → the build is invalid and is not handed over.

## Skills, plugins, MCP
- Use: forge-pc-rules, forge-ltopgo-pgo, forge-engine-verify, forge-job-workflow (loaded); forge-search-bug-hunt (mate probe);
  anthropic-skills:skill-creator to write the skills; `gh` CLI for CI runs; Context7 (GCC PGO/LTO, alignment, Win32 large pages)
  and web search only for missing idea sources. No Linear/Notion/Slack/Docs posts (rule: no outside messages).
- New skills, committed under `skills/<name>/` on the branch they describe and mirrored into `.claude/skills/`:
  `forge-lock-port` (fresh lock copy from d4f4312, O3→monolithic hunk map, line-set proof, ON-node references, handoff layout),
  `forge-candidate-checks` (kit pc1/pc2 wrapper, cand_checks, CI sanitizer self-play, mate probe, RESULTS table).
  In Phase 2: `forge-speed-stack` (stack recipe, weight alignment, net-path PGO).
- Updates: forge-ltopgo-pgo (R13: C:\o13 work dir, tags, the kit compiles any new src/*.cpp, w21pt recipe), forge-pc-rules (R13
  rules: ≤ 2 threads, C: ≥ 30 GB, D:/F: ≥ 50 GB, scratch ≤ 20 GB, 10-min pushes, skills under `skills/`).

## Cadence and budget
Push about every 10 minutes (`git push -q -u origin <branch>`), with RESULTS.md + STATUS.md updated in each push; `[skip ci]` only
on doc-only pushes of branches without CI. No new phase until the planned items are pushed with their checks. When this block is done:
push a new short plan for the next items (P1 items 3-5: bnd68, packc28, eos49). If usage looks low: stop starting new work and write
`opus_r13/FINAL_REPORT.md`.

---
# Block 2 plan (written 2026-10-31 ~16:45 PC clock, after block 1's P1 items were READY and P2 steps 1/1a/1b were building)

Order = the prompt's order. Same pipeline and checks as block 1 (skills forge-lock-port, forge-candidate-checks).
1. **P1 item 3, bnd68** (NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=50 ContHist4Pct=45 EvalOnlyStore=1 EvalOnlyStoreMinDepth=2):
   port = diff of `packae2r_h256e12_src.zip` vs the lock source (only board.hpp/cpp + search.hpp/cpp differ; the
   h256e12 base has the lock's search code, its net differs). Proof: line set vs the zip's own packa/packe2r patches,
   plain OFF pins, ON live; kit v2.3 -Expose pc1/pc2; checks; CI ASan+UBSan; handoff `p1/bnd68`.
2. **P1 item 4, packc28**: `packc.patch` (applies with -F0 on the lock); gate 28 line from its RUN_INFO:
   AspFailHighReduce=1 AspFailHighMaxReduce=3 EvalSwingMult=24 EvalSwingMax=200. Same proof set; handoff `p1/packc28`.
3. **P1 item 5, eos49** (EvalOnlyStore=1 EvalOnlyStoreMinDepth=2): port = diff of `packe2r_h256e12_src.zip` vs the lock
   (search.hpp 4 lines, search.cpp 25 lines). Same proof set; handoff `p1/eos49`.
4. **P2 step 2, sparse L1 (find-nnz)**, if credits allow: read the stack's L1 (fc_0 / HalfKA layer()), write the nnz-chunk
   list + int8 dot over it behind `FORGE_SPARSE_L1` (default 0), bit-identical parity on the 12k FENs (embedded + FTP1
   net), bench pins, sanitizer, advisory ABBA.
If usage looks low at any point: stop starting new items, push, write `opus_r13/FINAL_REPORT.md` (Phase 8).
