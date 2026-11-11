# JOB D - evidence matrix (what the repository already shows, read 2026-11-11)

Sources: `opus-nnue-int8-vnni-20261106` @ `e57f8f61` (`opus_nnue_int8_vnni/STATUS.md`, `BENCH.md`, `logs/`),
`opus-30h-20261103` @ `32bb47cb` (`opus_30h/FINAL_REPORT.md`, `a/RESULTS.md`, `kit25/README.md`),
`fable52-search-gap-20261109` @ `56a76b15` (`fable_search_gap/data/gate_table_summary.md`),
lock `lock/combo29-20261110` @ `16833ecc` (`forge-combo29/LOCK.md`, `windows_build/`).
Nothing below was re-measured for this table; it is a reading of those files.

## Matrix

| Build | Previous verdict | Control that was run | What the PGO workload covered | Unresolved question | Reopened here |
|---|---|---|---|---|---|
| **Lock combo29** `forge_clang_combo29_trial_w6.exe` (clang 23.1.5 ThinLTO + IR PGO) | Bit-exact speed lock, +10.19 % NPS vs trial_w6, no Elo claim | 12000/12000 FENs vs trial_w6, ten bench pins, perft, T2-4 soak | Workload v1 = `bench 11/13/16`, default options = float residual net ON. The path the lock runs is the path that was profiled. | None | No. Used as reference only. |
| **INT8/VNNI gate** `forge_nnue_int8_vnni_gate_81741f2b.exe` (GCC 15.2 LTO+PGO, kit v2.3 `lp_v1`, parent trial_w6) | "UNPROVEN, no speed claim". ON ran at about 0.50x OFF. No SPRT was queued. | OFF = all lock pins; identity build byte-equal to trial_w6; kernel == scalar on 203,724 positions; eval diff vs float on 12,001 roots: max 29 cp, mean 3.21 cp | Workload v1 with the option OFF only. **The INT8 code never ran during training.** The branch's own `BENCH.md` states this and shows a plain -O3 build at about 0.97x. | Speed of the INT8 path when it is the profiled path; and the same on the current lock (combo29, clang). | **Yes - the reported defect, confirmed from the candidate's own report.** |
| **v2 gate exe kit v2.3** `df1f140b` | v2 path 0.710x the lock (CI 0.680-0.741) on the same tree | lock net as v2 file = lock pins | Workload v1, `EvalFileV2` empty. **v2 path cold.** | Superseded inside the same job by kit v2.4 / v2.5. | No (already corrected by its authors). |
| **v2 gate exe kit v2.5** `v2p3` `ff856ba8` / `v2p4` `a2a560cb` (GCC LTO+PGO, `-PartialTraining`, workload v2n, older lock FD3A5190) | v2 path about 1.07x (CI 0.987-1.152, advisory, one shared CPU). In play the v2p4 exe with the lock's own net scored 47.0 % (-20.9 +/- 18.5) vs the lock exe. | lock net as KB1/KB4/KB8 replicas = lock pins to d22; negative controls differ; lockstep 5 games identical | Workload v2n = v1, then the same benches with the lock net as **KB4**/OB8 replicas. The v2 code was profiled, but not with a KB8 net and not on combo29/clang. | Is a v2 KB8 exe built with the current lock's recipe and profiled on the KB8 net as fast as the lock? The -20.9 Elo control was never explained by a quiet speed measurement. | **Yes - not the cold-path defect, but the profile did not match the candidate layout and the base is no longer the lock.** |
| **KB8 U8** soup `o30_gpu_soupU8r3r5r10r12r14.nnue2` sha256 `dcf07a65...` (residual, KB8 rank4x2, H256, OB8) on v2p4 | Sanity 400 games 51.00 % (+7.0 +/- 19.7). Later gate rows `UO30U8` 2528 games +16.50 **H1**, confirm `UO30U8c` 4000 games +3.04 **CAP** (gate table row with `option.EvalFileV2=...o30_gp...`). | Package checks (parity x3, OFF pins, ON benches twice equal); v2p4 control above | As the kit v2.5 row. The gate exe named in that later row is not identified in the files read here. | Speed of U8 on a correctly profiled combo29 build. Strength is a gate matter and stays open. | **Yes, speed and build only.** |
| **KB8 run 5** `o30_gpu_kb8short_r5.nnue2` sha256 `27ea0a39...` (residual, same layout) on v2p4 | Sanity pooled 520 games 51.44 % (+10.0 +/- 16.1). No gate row found. | As U8 | As the kit v2.5 row | As U8 | **Yes, speed and build only.** |
| Standalone nets (`EvalFileHalfKA`, 1024-wide; and the H512 standalone path of `fable-nnue-arch`) | Gate rows NPTW4S5/S6 about -96 to -124 Elo; fable-nnue-arch reports NPS only | not read in detail | not established from the files read | Whether those exes were profiled on their own path | **Not reopened here**: not one of the three named candidates and its engine source is not on the lead branches. Listed so the gap is visible. |

## Correction and additions (2026-11-11, follow-up; read from `C:\Users\Administrator\grok-pc\forge_push\FORGE_RESULTS.csv`)

The first version of this matrix was written from a truncated summary table. The gate table itself says:

| Gate row | Candidate exe | Base it played | Games | Elo | Verdict |
|---|---|---|---|---|---|
| `UO30U8` (U8) | `forge_ltopgo_x_o30v2p4_a2a560cb.exe` | `base_AL1_s198_ltopgo_x_FD3A5190` (the v2p4 exe's own parent) | 2528 | +16.50 | H1, SPRT [0,10] |
| `UO30R5` (run 5) | same v2p4 exe | same FD3A5190 base | 2568 | +16.11 | H1, SPRT [0,10] |
| `UO30U8c` (U8 confirm) | same v2p4 exe | `base_AL1_s198_trial_w6_4181A589` (a newer, faster speed lock) | 4000 | +3.04 | cap, no decision |
| `NPT104-*`, `NPTS3-*`, `NPTW4S4-*` (stand-alone 1024 nets) | `forge_ltopgo_x_r10fix1_halfka_9e5cb644.exe` | FD3A5190 | 248-288 each | -86 to -116 | H0 |
| `NPTW4S5-*`, `NPTW4S6-FIN` (stand-alone 1024 nets) | same r10fix1 exe | `base_combo29_clang_E1284F7F` | 242-286 each | -96 to -124 | H0 |

- **Run 5 does have a gate row** (+16.11, H1). The "no gate row found" in the matrix above is wrong.
- **The candidate exe was never rebuilt when the base moved.** In the confirm gate the v2p4 exe (built on the FD3A5190-era source) played trial_w6. Measured here against the combo29 lock on identical trees: v2p4 with the s198 replica 0.7375, trial_w6 0.9123. So in that confirm gate the candidate ran the same tree about 19 % slower than the base it was compared with, and still read +3.
- **The stand-alone nets were gated on one exe built by the LTO+PGO kit from the R10 HalfKA source.** That exe is 14 % slower on the HalfKA path than a plain build of the same source (same net, same tree), and its own float path is 0.766 of the combo29 lock it was later compared with. See REPORT.md, follow-up section.

None of this turns a speed ratio into Elo. It says which earlier strength readings compared exes that were not built alike.

## What this does and does not invalidate

- The INT8 "0.5x" speed reading is invalid as a statement about the INT8 kernel; its arithmetic checks are unaffected by the profile.
- The opus-30h authors did find and fix the cold v2 path (kit v2.4, v2.5). Their KB-layout identity controls stand. What is missing is a quiet, paired speed measurement on the current lock with a profile from the candidate's own net layout.
- The U8 gate rows (H1 then CAP) are strength results from the gate; this job does not revisit them and cannot turn NPS into Elo.

## Controls available per path

| Path | Can it express s198 + HCE exactly? | Control used in this job |
|---|---|---|
| old residual float (source-built) | yes, it is the lock source | node-identical benches, 12k exact match vs diagnostic reference |
| INT8/VNNI | no (lossy quantization of the same net, HCE unchanged) | s198 through the INT8 path: error statistics vs diagnostic reference; kernel vs scalar int8 reference |
| v2 residual KB8 | yes (s198 written as KB8/OB8 replicas) | node-identical benches, 12k exact match vs diagnostic reference |
| v2 residual KB8 with U8 / run 5 | different function | not comparable to s198; replica control on the same exe |
| standalone (no HCE) | **no** | exact s198 control unavailable; only same-net reference checks would apply |
