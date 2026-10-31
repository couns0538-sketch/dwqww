---
name: forge-ltopgo-pgo
description: Build, verify and time Forge LTO+PGO exes on the PC with QA's kit (v2.3 frozen workload v1; v2.4 from Opus R12 adds workload v2 = net path + Threads=2, -PartialTraining, -CheckOptPins) - where the kit, sources and exes live, the binding pc1 = pc2 exe sha256 rule, the identity checks (OFF pins, net pins vs plain D8D90B68, 12k FEN exe identity), the palindromic ABBA speed method with A/A copies, CPU-pair etiquette (trainer 0x000F, gates 0xFFF0, QA frees a pair), and the pitfalls (bench ignores Threads, go is stopped by the next UCI line, -File cannot pass arrays, nondeterministic SMP profiles). Use for any LTO+PGO / PGO profile / build-mode speed question, a new candidate build with the kit, or a gate that needs an LP exe.
---

# Forge LTO+PGO builds (kit v2.3 / v2.4, R12 2026-10-30)

Rules first: [[forge-pc-rules]]. Speed method background: [[forge-engine-verify]] section 5. HalfKA facts:
[[forge-halfka-parity-test]].

## Where things are
- QA's kit v2.3 (read-only): `C:\Users\Administrator\grok-pc\forge_push\qa_ltopgo_al1_stage\kit_v23\` (build_ltopgo.ps1
  md5 729fe727, README, FROZEN_WORKLOAD.md, workload\, tools\lp_check.py). QA's v2.3 builds: `...\bin\ltopgo_v23x\<tag>\`
  (SUMMARY.txt has both exe sha256s; `src_copy\` holds the exes). Candidate sources: `...\cands\<name>\`.
- Kit v2.4 (R12): branch `opus-r12-pgo-net`, `opus_r12/kit_v24/` (v2.3 + workload v2 + switches), tools in `opus_r12/tools/`.
- Exes in `grok-pc\forge_push\bin`: lock LP FD3A5190 = `forge_ltopgo_x_al1s198_v23.exe` (AL1 s198, v1, -Expose);
  r10fix1 HalfKA LP 9E5CB644 = `forge_ltopgo_x_r10fix1_halfka_9e5cb644.exe` (v1); its plain twin D8D90B68 =
  `forge_plain_z5_r10fix1_halfka_d8d90b68.exe`. Nets: `r11_e19_final_bf1e347c.nnue`, `r11_e9_best_5380f866.nnue`.
- Source of 9E5CB644/D8D90B68 = git 7f79c349 (r10fix1), byte-identical to `cands\r10fix1\forge_r10fix1_src` (23 files).

## The kit in one paragraph
plain build (lock g++ line, one call) -> instrumented `-flto=1 -fprofile-generate -fprofile-update=single` -> training
-> use build `-fprofile-use -fprofile-correction -Wmissing-profile` (+ `-Wl,--no-insert-timestamp` on the link) ->
checks (0 missing-profile warnings, vfmadd 0, LTO IR in every object) -> lp_check identity plain vs LTO+PGO (OFF with
pins, then each -CheckOpt). **Binding: two clean builds (tags ..._pc1, ..._pc2) must give the same forge_ltopgo exe
sha256.** gcda manifests are record only (value profiles hold addresses/timings). A build takes ~1 min + identity.
- Params: `-Expose` (QA's gate builds use it), `-Affinity` (default 0x3), `-Work` (use F:\opus_scratch\..., never D:).
- Several `-CheckOpt` values need `powershell -Command "& build_ltopgo.ps1 ... -CheckOpt 'a','b'; exit $LASTEXITCODE"`;
  with `-File` the array arrives as one string.

## Workloads
- v1 (frozen): `uci, isready, bench 11, bench 13, bench 16, isready, quit`, no setoption. Never runs the HalfKA net path
  and never runs Threads >= 2 code -> both are compiled as never executed (cold, size-optimized). QA measured the v1
  HalfKA LP exe 12.1-12.4% SLOWER than plain with a net loaded (5-6% faster without a net).
- v2 (R12): v1 + the same benches with EvalFileHalfKA = e19 and = e9 + per block 8 `go nodes 200000` at Threads=2.
  `bench` ignores Threads (own one-thread `Searcher(16)`, exclusive TT lease), so SMP code only runs under `go`.
  A `go` is aborted by the next UCI line -> v2 needs `tools/train_driver.py` (waits for bestmove/readyok, checks net
  sha256 + 'EvalFileHalfKA loaded', exit code 0 so the .gcda get written).
- **Measured (R12): v2 does NOT reproduce.** Two clean v2 builds: 8f162985 vs 18503c4d (v2 + partial training:
  63ae405f vs ee5c8bea), 12 / 23 hot functions differ (`opus_r12/tools/exe_func_diff.py A.exe B.exe`). Timing-dependent
  Threads=2 counts land in search/qsearch/eval. The pc1 = pc2 rule and an SMP profile cannot both hold.
- **v2t1** (= v2 without the Threads=2 part: bench no net / e19 / e9, sha256 dca15f66) reproduces byte for byte:
  e06e0348 (pc1 = pc2), with -PartialTraining 436ed8e1 (pc1 = pc2). Use `-Workload v2t1` for gated net builds.
- `-PartialTraining` (GCC >= 10, MSYS2 g++ 15.2.0 here): functions never executed in training get normal -O3 instead of
  size optimization; never-executed blocks inside executed functions stay cold.

## Identity before any speed number
OFF: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft 4865609/193690690. With nets (plain D8D90B68
counts): e19 373062/831975/4115992/17885060/37006232, e9 287095/693432/2816047/12332089/25323515 (pass them as
-CheckOptPins). 12k exe-level identity: `r12_fens12k.py` (`go depth 2` per FEN with the net, all exes must agree; the
LP exe has no eval command, the net-level parity 12000/12000 vs nnue-pytorch is R11's / QA's halfka_tool result).

## Speed method (r12_speed.py)
Fresh process per run, BelowNormal, pinned to ONE logical CPU of the freed pair (sibling idle), Threads 1 Hash 16
OwnBook false [+ net], `bench 16` / `bench 20`; engine nps (wall) and bench-window CPU time. Palindromic blocks
E1..Ek Ek..E1 (k = 2 is ABBA) keep every pair of exes balanced against linear drift; >= 7 blocks + 3 A/A blocks against
a byte copy (per-file effects, R5B). Report median gain and the bootstrap (10000, seeded) one-sided 95% lower bound.

## CPU pair etiquette (R12)
Trainer holds 0x000F (Idle), gates 0xFFF0 (BelowNormal), self-play 3-CPU masks inside 4-15 (Idle), QA runs checks on
0x0003 at BelowNormal. Profiling and timing only on a pair QA frees: either QA narrows the trainer mask (e.g. 0xF->0xC,
as in QA's speed4) - `r12_build_chain.py` / `r12_speed.py` then see it free by themselves - or QA says "use 0/1" and
the tools run with `--pair 0x3 --ignore-idle`. Never on a gate's CPUs. Free RAM >= 4 GB.

## R12 results (2026-10-30, CPU 0, e9_best, 7 palindromic blocks, engine nps; opus_r12/REPORT.md)
- Kept: **v2t1 + -PartialTraining = 436ed8e1** (pc1 = pc2): net +7.2% d16 / +7.3% d20 vs plain D8D90B68 (95% LB +3.2 /
  +6.2), +22% vs v1-LP 9E5CB644; no net -0.04% / -0.81% vs lock LP FD3A5190 (inside A/A noise).
- v2t1 without partial training (e06e0348): net +4.2 / +5.6% vs D8D90B68 but -2.8 / -3.2% vs FD3A5190 with no net.
- 9E5CB644 vs D8D90B68 reproduced QA: -12.7% / -12.6%. A net-path profile turns the LP penalty into a gain.
- Per-file timing offsets are real here: an exe vs its own byte copy measured -3.0% (d16); single X-vs-Y comparisons
  of different files carry that much placement noise. For a close call use several fresh copies per variant
  (`tools/r12_pooled.py`; prepared, not run in R12).
- A waiting runner cannot be stopped (no kill, TaskStop leaves it running): to neutralise one, rename the exes it will
  start (`*.exe.parked`) - it exits with FileNotFoundError at its first run (R12 did this for the copies runner).
- 12k exe-level identity (`r12_fens12k.py`, go depth 2 on fens_12k): 36,000 searches in ~8 s per net.

## R13 (2026-10-31, Opus; tools on branch opus-r13-p1-nearmiss-ports `opus_r13/tools/`)
- Wrapper `kit_build.sh <scratch repo> <tag> 'N=V' ...`: pc_gate, fresh clean export per side, kit v2.3 `-Work C:\o13\w
  -Affinity 0xC -Expose` + pins + one -CheckOpt per gate line (passed via `powershell -Command "& kit ... -CheckOpt 'a','b'"`),
  then pc1 = pc2 sha256. ~3 min per build with 2 CheckOpts on CPUs 2-3 while a conc-8 gate + self-play run.
- F: was 45 GB (< the 50 GB floor of the R13 rules): work dirs and handoff exes on C:\o13. Short tags (`pka`, `b1k`) keep
  the .gcda paths short.
- The kit compiles every `src/*.cpp` (S1 LargePages adds src/large_pages.cpp; no kit change needed). New headers / .inc
  files are free. Lock source = git d4f4312 (see [[forge-lock-port]]).
- Results: packa (NonPawnCorr/PawnHist) exe 07cc2393 (pc1 = pc2, OFF ALL OK, 0 missing-profile). Checks: [[forge-candidate-checks]].
