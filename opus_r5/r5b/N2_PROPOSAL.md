# N2 proposal (R5B): O2 + NOZERO + SPEEDSTACK in one node-exact build — UNPROVEN, no Elo claim

Branch `opus-r5b-speed` (base `forge-bundle-int` b7c1772). Details and every log: `REPORT.md` (M1-M4). Gate spec as
data: `n2_gate_spec.json` (same content as the table at the end).

## Candidate and opponent (PC lock recipe, `-march=znver5`)

| role | exe (F:\opus_scratch\r5\r5b\exe) | sha256 | flags on top of the recipe |
|---|---|---|---|
| candidate N2 | `forge_r5b_n2_z5_b2983d07.exe` | `1823fe614065211d50ff2fad36860dcd7ccadb35a3b3fbd78c68ad4f32f27ca4` | `-DFORGE_NNUE_O2=1 -DFORGE_NOZERO_MOVE_BUFFERS=1 -DFORGE_SPEEDSTACK=1` |
| opponent OFF | `forge_r5b_off_z5_m1fix.exe` | `ca5b9331b8fe9132cac958bc7687f2d872aa60e997fde6eb5bd8b9508c6f1858` | none (code = b7c1772 OFF; only the PE timestamp/checksum bytes differ) |
| alternative pair (job-spec flags `-march=x86-64-v3 -mtune=znver5`) | `forge_r5b_n2_v3_b2983d07.exe` vs `forge_r5b_off_v3_m1fix.exe` | `faac168d92a18f7a2eb2164655c5907d75fe26fc91cd0f0ae7589c913041aee5` / `241368e87d4ed9f4b247c840e0d18b42d8028b5543d7710d2b3b728f0e1350cc` | same |

Recipe (both exes of a pair): MSYS2 ucrt64 g++ 15.2, `-std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256
-ffp-contract=off -fno-fast-math -march=znver5 -pthread -static`, built by `opus_r5/r5b/tools/build_r5b.sh`
(RECIPE=znver5). Engine tree: commit b2983d07 (the M1 fix). Later commits add only a test-only macro, tools and
reports: N2 rebuilt from the final branch head is byte-identical to this exe apart from the PE timestamp/checksum fields (REPORT.md
"Final checks"). Why znver5: it is the PC lock exe's recipe (lock archive `2_build/BUILD.md` "Windows", `build_pc.sh`,
used for the R3 gate exes); the job spec's v3 flags give the alternative pair (identical evidence below).

## What changed in O2 (M1) — exactly

On `-march=znver5` the O2 AVX2 kernels were compiled out: `src/nnue.cpp` selected them only under
`FORGE_NNUE_AVX2 && !defined(__AVX512F__)`, and znver5 defines `__AVX512F__`, so a PC O2 build ran the portable
accumulator loops (proven from the binary: same 16-zmm refresh loop as OFF, no ymm kernel; `logs/m1_kernel_audit_b7c1772.log`).
Fix in the guard, commit b2983d07, every line under `#if FORGE_NNUE_O2`:
- new `FORGE_NNUE_KERNEL_AVX512` (= `FORGE_NNUE_AVX2 && defined(__AVX512F__)`) with a 512-bit `Vec` (`__m512`,
  `_mm512_load_ps / _store_ps / _add_ps / _sub_ps`) for the existing kernel templates (fused quiet / capture /
  castling update kernels, register-blocked refresh with 8 vectors = 128 floats per block);
- `forge::nnue::kernel_name()` and, at `uci`, `info string nnue kernel: accumulator avx512, output avx2` (O2 builds
  only; OFF output is unchanged);
- the parity test's kernel label.
Node-exact: each lane sees the same float operations in the same order as the portable loop and the AVX2 kernel
(no FMA, no reassociation). Bit parity vs AL1 s198 (`tests/nnue_parity_tests.cpp`, 1,303,743 positions): AVX-512,
AVX2 and forced-scalar builds PASS with the same digest `f807d80cbabc1d59`. Speed: on this PC the 512-bit kernel is
not measurably faster than the portable loops it replaces (both about 0 vs OFF at d20; REPORT.md M3 passes 1-2).

## Identity (Threads 1, Hash 16, OwnBook false; lock `2_build/uci_check.py --full`)

| exe | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|
| N2 znver5 (candidate) | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK |
| OFF znver5 (opponent) | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK |
| N2 v3, OFF v3 | same | same | same | 0 | ALL OK |

## NPS: N2 vs OFF, CPU-time NPS, % with 95 % CI (paired t on log ratios)

| where | d16 | d20 | A/A floor d16 / d20 | +2 % lower-bound rule |
|---|---|---|---|---|
| PC, znver5 pair, pass 3 (fresh file copy per slot, 20 pairs, core 14, PC 91 % busy) | **+2.05 [+1.30, +2.80]** | **+1.91 [+1.47, +2.36]** | -0.67 [-1.98, +0.65] / -0.89 [-1.73, -0.03] | not met |
| PC, v3 pair, pass 1 (12 pairs, core 12) | +2.32 [+1.66, +2.99] | +2.02 [+1.36, +2.69] | -0.01 [-0.85, +0.85] / +0.12 [-0.52, +0.76] | not met |
| quiet GitHub runners, x86-64-v3, pooled over 6 runners (CI method) | **+4.76 [+3.83, +5.69]** | **+4.84 [+4.41, +5.27]** | +0.01 / +0.17 | **met** |
| quiet runners with AVX-512, x86-64-v4 (512-bit kernels), pooled over 2 | +4.86 [+4.08, +5.65] | +5.40 [+3.81, +7.02] | -0.05 / +0.39 | met |
| the one Zen 5 runner (EPYC 9V45), v3 / v4 | +0.28 [-4.72, +5.54] / +3.80 [+2.40, +5.23] | +1.68 [+0.31, +3.06] / +4.79 [+1.64, +8.02] | noisy (spread 28 %) | not met |

Verdict: **N2 is a real speed-up everywhere it was measured (about +2 % on this Zen 5 PC, about +5 % on Zen 3 and
Intel runners). It meets the +2 % lower-bound rule on the quiet runners, the rule's proxy (forge-engine-verify), and
does not meet it on the loaded Zen 5 PC**, where the 95 % lower bounds are +1.30 / +1.47. PC caveat: per-file speed
offsets (ASLR base / page placement) moved PC rows by up to +-2.8 % in passes 1-2 even for byte-identical files; pass 3
samples them with a fresh copy per slot, and a re-linked OFF (pure layout change) stayed within the floor
(-0.80 / -0.14). Single switches on the PC: O2 about 0, NOZERO and SPEEDSTACK about +1 % each.

## Non-regression evidence (M4)

- (a) node-exact with real searches: `go depth 18` on 50 self-play positions, N2 znver5 vs OFF znver5: 50/50 identical
  bestmove, node count, score and pv (64.8 M nodes).
- (b) smoke: 200 games N2 vs OFF at 5+0.05, Threads 1: PASS, 0 illegal, 0 crashes, 0 time losses, 0 missing bestmoves,
  0 restarts; go/stop stress 50/50 with 0 problems.
- (c) uninitialised reads (NOZERO): N2 with the move buffers poisoned (0xFE, 0x5A) on every construction keeps the
  identity (ALL OK); CI `opus-r5b-n2` green: valgrind memcheck of OFF and N2 (0 errors), the poison identities,
  N2 ASan+UBSan and TSan with CTest and the known-failure check, N2 x86-64-v4 release + ASan on an AVX-512 runner.
  (`-ftrivial-auto-var-init=pattern` keeps the identity too, but on g++ 15 it does not reach these class members, so
  it is not counted as a NOZERO test.)

## Proposed gate (we do not run it; the queue owner fills srand and openings start)

| field | value |
|---|---|
| id / tag suggestion | R5B-N2 / `gateR5B_n2_vs_off_z5` |
| candidate | `forge_r5b_n2_z5_b2983d07.exe` (suggested install name `forge_r5b_n2.exe`), sha256 `1823fe61...27ca4`, no options |
| opponent | `forge_r5b_off_z5_m1fix.exe` (suggested install name `forge_r5b_off.exe`), sha256 `ca5b9331...1858`, no options |
| both sides | `option.Threads=1 option.Hash=16 option.OwnBook=false` |
| TC | **10+0.1** (speed shows most at short TC) |
| SPRT | **non-regression: elo0 = -10, elo1 = 0** (nElo), alpha = beta = 0.05, model normalized |
| cap_games | **3000** (int); wall time to the cap at concurrency 8: at most about 3.4 h (2 x (10 + 65 x 0.1) s per game) |
| srand / openings start | **blank / blank** |
| book | `C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn`, pgn, order random (as R5A) |
| prebench d11 / d13 / d16 / d20 / d22 | cand_on = cand_off = 312866 / 862329 / 3024920 / 12389307 / 34048354 (node-exact) |
| check at start | the candidate prints `info string nnue kernel: accumulator avx512, output avx2` at `uci`; the opponent prints no such line |
| pass means | N2 is not weaker than OFF by 10 nElo or more; together with the NPS rows it is the basis to ship N2 as the build recipe of later bundles |
