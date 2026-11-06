# Forge speed job (6 h, PC clock 08:38 -> 14:38; FINAL_REPORT by 14:08) - plan

## Context
Couns's crew voted A > B > C (D only if time). Elo gates take hours to days; a change that searches the same nodes
and only runs faster can lock on a bench-signature match + an ABBA nps win (as LTO+PGO did). This job builds that
lock path as tools (A), uses it on bit-exact hot-path changes (B), and adds gate wall-time tooling (C). Inputs reused,
not redone: deep research `opus-deepres-20261104` @2231439c (`FINAL_REPORT.md`, `notes/T05/SPEED_LIST.md`,
`notes/SPEC_SPEED.md` S1-S4 specs + review, cards T05*, `cards/T12/T12-03-bench-fuzz-checklist.md`).

## Facts found in orientation (they shape the plan)
- Lock exe `C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_v23.exe` sha256 fd3a5190... (checked).
  Source `...\qa_ltopgo_al1_stage\src_al1s198_clean` (= git d4f4312). Kit v2.3 `...\kit_v23\build_ltopgo.ps1`: flags
  `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread`,
  `-flto=1 -fuse-linker-plugin`, `-fprofile-update=single`, use `-fprofile-correction -Wmissing-profile`,
  `-Wl,--no-insert-timestamp`; FD3A5190 is the `-Expose` build; frozen workload v1 = `bench 11/13/16`, no setoption.
- **The lock's net is embedded (nnue_weights.inc) and ON by default** (`UseNNUE` default true). So the lock's v1
  profile already runs the net path; the ~12 % "net loaded" loss was the HalfKA (EvalFileHalfKA) builds, not this lock.
  "Net-off" = `setoption name UseNNUE value false` (pins 375354/907205/2448617/13573040/24506465). The workload
  comparison still runs as asked; I expect a small effect, and the report will say so.
- Lock pins net-on: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354; perft 5 startpos 4865609,
  kiwipete 193690690. Bench prints `bench depth D nodes N time T nps X` (own Searcher(16), ignores Hash/Threads).
- Lock net is 768->256 float SCReLU, no L1 layer: VNNI / vpdpbusd / find-nnz / sparse L1 apply only to the HalfKA path
  (not in the lock) -> Job B NNUE work = the AVX-512 output kernel and the accumulator path only (SPEED_LIST #5, #1).
- 12k FEN set: `F:\opus_scratch\r10\parity\fens_12k.txt` (12,000 lines, placement-only FENs, LF, md5 078b6c2e...).
- Sanitizers: MSYS2 g++ 15.2 has no ASan runtime; `C:\Program Files\LLVM\bin\clang++.exe` 18.1.8 (MSVC target) has
  ASan + UBSan runtimes, VS BuildTools 18 + SDK 10.0.26100 exist -> level 4 via clang++ under vcvars64.
- BOLT: not installed; ELF-only per its README (deep research) -> the "one try" is a recorded check, no build.
- PC now: C: 94 GB, D: 50.9 GB, **F: 59.6 GB free** (8 GB scratch would leave ~51.6: every tool gates on F: >= 50 GB
  + planned write; target <= 4 GB used). RAM 16 GB free. Load 75 % (crew on 4-15); CPUs 0-3 at 2-11 %.
- **The live NNUE trainer + its supervisor have mask 0xF (CPUs 0-3) at Idle.** My session process ([name withheld].exe pid
  11464) is Idle + 0x3, so every tool child inherits CPUs 0-1 / Idle. [name withheld] and [name withheld] Bot run on all CPUs.

## Ground rules as I will apply them
- CPU: builds, identity checks, workers' work: mask 0x3 (CPUs 0-1), Idle. Timing: CPU 2 only (mask 0x4,
  BelowNormal), CPU 3 kept free of my own work (it is CPU 2's SMT sibling). Nothing ever on CPUs 4-15 or the GPU.
  Every script sets affinity + class on itself first (children inherit), checks the result, and fails closed.
  ABBA runs are serialised by a named mutex (one timing run at a time). The trainer is never touched.
- Disk: scratch only `F:\ospd\` (wt, src, builds, packs, abba, ref, logs); gate F: >= 50 GB + write, C: >= 30 GB,
  `F:\ospd` <= 8 GB. Nothing written to D: except the one-line `WORKER_BOARD.md` appends the owner's [name withheld].md
  requires of every worker. D:\o30, C:\o30g, D:\a14 untouched (disclosure: one read-only `find` during orientation
  listed three tool paths under D:\o30\wt before I caught it; noted in the report).
- Git: partial + sparse clone `F:\ospd\wt` (sparse `/opus_speed/ /skills/`), branch `opus-speed-20261105` fresh from
  origin/main (upstream unset), commits as couns0538-sketch, **no vendor/model names and no co-author trailer** (brief
  ban; same as deep research), push `git push -q -u origin opus-speed-20261105` about every 15 min; never main / other
  branches / force. Licences: own code; ideas from GPL sources only via PR text already carded; MIT sources credited.
- Engine changes: build switches `FORGE_SPD_*` (default 0, `#if` with the lock text verbatim under `#else`), so the
  switch-0 kit build must equal FD3A5190 byte for byte. Speed claims only from my ABBA CSVs; everything else UNPROVEN.
- Workers (<= 3 at once): Agent tool, `subagent_type: fable` + `model: fable` (definition pins [name withheld]-fable-5-1,
  effort max) or `subagent_type: opus-max` + `model: opus` (definition pins effort max); no retry, no fallback, briefed
  with the forge-subagent-brief template + these rules; each reads/appends the worker board.

## Job A (vote 1) - speed-only lock path (me; ~08:55-11:45)
Tools in `opus_speed/tools/` (PowerShell 5.1 .ps1, dot-sourced shared `uci_lib.ps1`, no nested `powershell -Command`):
1. `build_variants.ps1 -SrcDir -Tag -Variants a,b,.. [-Define N=V] [-Expose] [-Twice]` - re-implements the kit's
   command lines token for token (self-test: variant `lp_v1` on the lock source must give FD3A5190 byte for byte),
   plus variants: `o3` (plain lock line), `lto`, `pgo` (no LTO), `lp_v1` (lock recipe), flags on lp: `-march=znver4`,
   `-fno-plt`, `-fno-semantic-interposition`, `-falign-functions=64`, `-fprofile-partial-training`, `-fipa-pta`,
   `-flto-partition=one` (+ `-fno-stack-protector` if g++ enables SSP by default); workloads on lp: `wNoNet`
   (UseNNUE false + bench), `wNet` (= v1), `wNet12k` (v1 + `go depth` on a fens12k sample), `wMixed` (short
   `go nodes` searches on ~300 full-FEN game positions from a finished gate PGN, warm TT within a game); `go`
   workloads use a driver that waits for `bestmove` (a `go` is aborted by the next line). BOLT: one recorded check.
   Per exe: sha256/md5, flags, g++ version, workload sha256, gcda count, 0 missing-profile, vfmadd 0; `-Twice` = pc1/pc2.
2. `bitexact_check.ps1 -Cand exe [-Ref lockexe] [-SanSrc dir -Define ..] [-Quick]` - PASS/FAIL per line, stops at the
   first FAIL: L1 bench d11/13/16/20/22 net on + net off (ref must equal pins); L2 perft 5 startpos + kiwipete; L3
   bestmove + nodes (+ score, depth) per FEN at `go depth 13` with `ucinewgame` per FEN on the 12k set (same 2-way
   chunking for ref and cand on CPUs 0/1; ref results cached by exe sha256; `-Quick` = first 2,000 FENs); L4 clang
   ASan+UBSan build of the source (+defines) with `-ffp-contract=off`, bench d16 nodes = pin and no sanitizer report
   (fallback if the source does not build under clang: g++ `-fsanitize=undefined -fsanitize-trap`, ASan marked N/A).
3. `abba.ps1 -A exe -B exe [-Core 2 -Depth 16 -Rounds 10 -Cooldown 3]` - A B B A per round, >= 10 rounds, fresh
   process per run at BelowNormal pinned to one CPU, net loaded (checks `UseNNUE ... default true` in `uci`), engine's
   own bench nps; fresh byte copies of both exes per round (+ one untimed warm-up) because R12/BH-8 measured 3-5 %
   per-file bias on this PC; nodes must stay constant per exe. CSV: round, order, exe, md5, depth, nodes, ms, nps,
   core, timestamp. 5-line summary: median ratio, 95 % Student-t interval of per-round log ratios (bootstrap median CI
   as a second line), A/A band from the session's lock-vs-lock CSV, WIN only if low end > 1.000 and median >= +1.0 %,
   load on CPUs 2-3 and total.
4. `speed_pack.ps1 -SrcDir -Name [-Variant lp_v1] [-Define ..]` - pc1+pc2 build (equal sha256) -> bench signature (net
   on + off) -> bitexact_check (full) -> abba vs lock -> `F:\ospd\packs\<name>\` (exe, md5, signature, bitexact.log,
   abba CSV + summary, build logs, g++ version, flags) + `opus_speed/candidates/<name>.md` filled from it.
Tests: (1) lock-vs-lock pack: lp_v1 of the lock source = FD3A5190, identical signatures, A/A inside the noise band;
(2) one search constant changed -> bitexact_check FAIL at L1; (3) all variants screened (L1-L2 + ABBA vs lock, losers
recorded), the best one(s) get a full pack whatever the ratio; workload winner also needs pc1 = pc2 (a `go`
workload may not reproduce - then it cannot be a lock candidate, reported). A new workload would mean a new kit
version for every later gate side: listed as a CR/QA item.

## Job B (vote 2) - bit-exact hot-path changes (2 workers code, I time; ~09:10-13:15)
Each change: own source copy `F:\ospd\src\<name>` = lock bytes + patch (`opus_speed/patches/<name>.patch`), switch
default 0; worker: plain build ON + pins quick check, then `bitexact_check -Quick` -> (me) `abba` vs lock on CPU 2;
winners get the full check. One change per commit, losers recorded with their CSVs.
- Worker B1 (opus-max): S4 `FORGE_SPD_TT_NOTLS` (TT probe/store without the emulated-TLS lease check, SPEC_SPEED S4,
  +2-4 % UNPROVEN), TT bucket / cache-line alignment check, TT prefetch placement (prefetch earlier, own R7 idea).
- Worker B2 (fable): S1 `FORGE_SPD_NO_ZERO_MOVELISTS` (steps 1-2 first, quiets-only mode after), S3
  `FORGE_SPD_MATKEY_FAST` (a), NNUE AVX-512 output kernel (16 lanes, same lane order, no FMA), S7 branch-free
  pick_best, S2 PEXT slider mode 1 if time.
- Order of timing follows the brief (NNUE, movegen, TT, MovePicker/SEE) as patches arrive.
- Stack only winners -> stacked source: switch-0 build = FD3A5190, full bitexact ON, ABBA stack vs lock (net loaded).
- Deliberate failure: pick_best tie-break `>` -> `>=` (move order) must FAIL bitexact_check, so ABBA never starts.

## Job C (vote 3) - gate wall time (worker C, fable; ~09:00-12:30, CPU-light)
Python tools in `opus_speed/jobc/` (read-only venv python `-I -B`, Idle, 0x3), read-only on gate folders,
FORGE_RESULTS.csv and PGNs; patches/scripts only, the running queue and its config untouched; crew vote unchanged.
Tools: pentanomial LLR replay (fastchess 1.8.2 GSPRT, reusing gate_summary.py's formula) with verdict check; LLR
projection (expected games to decision / chance to decide before the cap - planning only, never a stop rule);
queue throughput report (games/h per gate, idle gaps); opening-book load timing (on a copy); adjudication audit;
pre-gate screen (bench pins, perft, UCI smoke, WAC subset if present, tiny smoke match on CPUs 0-1); concurrency
plan for the queue's own cores (math only). Tests: same verdict as recorded on >= 5 finished gates; truncated and
corrupt PGN -> error exit, no verdict.

## Job D - only if A-C are done: loader/export profiling plan, read-only, no GPU.

## Outputs, cadence, stop
- `opus_speed/STATUS.md` (one line per job), `RESUME.md` (next step, open builds, scratch paths), `FINAL_REPORT.md`
  (tools + usage, candidates ranked by measured nps gain with bit-exact status, losers, what QA times first, skills),
  `candidates/<name>.md` per candidate; skills `skills/forge-speed-lock-path/SKILL.md` (Job A pipeline + protocol +
  pitfalls) and `skills/forge-gate-walltime/SKILL.md` (Job C), optional user-scope copies on C:.
- Times in Vienna time (PC clock = PT + 9 h = CET today; checked against a GitHub Date header at start), `date` read
  before every written time. Memory file `opus-speed-status.md` + MEMORY.md pointer.
- Timeline: 08:55 setup + spawn C/B1/B2 -> 10:30 Job A tools + tests -> 11:45 variants + packs -> 13:15 Job B stack
  -> 13:15-13:45 own 30-min bug hunt (re-run tests, re-read diffs, NOT independent) -> 14:08 FINAL_REPORT pushed ->
  stop by 14:38 (or earlier at ~85 % usage: report, commit, push, stop).

## Verification (end to end)
- Kit self-test: `build_variants lp_v1` on the lock source -> sha256 fd3a5190...; switch-0 builds of every patched tree
  and of the final stack -> same sha256.
- Lock-vs-lock pack: identical signatures, A/A ratio inside its interval; mutant (search constant) -> FAIL at L1;
  move-order mutant -> FAIL before ABBA; each candidate: pc1 = pc2, full L1-L4 PASS, ABBA CSV + md5 in its .md.
- Job C: replay table = recorded verdicts on >= 5 gates; corrupt / truncated PGN -> nonzero exit.
- Final: re-run bitexact_check + one ABBA of the kept stack vs the lock after the bug hunt; disk/CPU rules re-checked
  (no own process outside CPUs 0-3, F: >= 50 GB).

Follow-up 2026-11-05 19:43-19:47 PC clock (start tip 00d19e56): the 4 CR SHOULD leftovers only. Live lock = trial_w6
4181A589.... No timing, and no retune / lock of KING_LINES or bundles a-d. Record: `CR_SHOULD_W8.md`.
Follow-up 2026-11-05 19:5x-20:07 PC clock (start tip 38559f1b): leftover jobs 1 (default lock = trial_w6), 2 (warm_identity
refusal test), 3a-3c (CR NITs). The same limits applied. Record: `CR_SHOULD_W8.md`.
