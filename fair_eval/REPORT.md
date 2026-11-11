# JOB D - Fair evaluation-candidate builds - REPORT

Branch `fable/fair-eval-builds-20261111`, cut from lock `lock/combo29-20261110` @ `16833ecc03b425586f91f4c8834dea8807bf4c22`.
Measured 2026-11-11 on grok-pc (Ryzen 7 9850X3D, 8 cores / 16 logical CPUs). All paths are under `fair_eval/` unless they start with `forge-combo29/`.

## What the evidence settled

1. **The reported defect is real for INT8/VNNI and is now reproduced and removed.** An INT8 exe whose profile was recorded with the option off runs at **0.487x** the lock; the same source profiled on its own path runs at **0.984x** (0.994x in a second run at depth 22). The profile shows why: zero entries in the INT8 functions in the first build, 2.8 million in the second.
2. **KB8 U8 and KB8 run 5 did not have that defect, but the v2 path has a real cost.** With the profile recorded on the v2 KB8 path, the lock's own net written as a KB8 file searches the identical tree at **0.927x** the lock. Removing the cold-code hints does not change that.
3. **Every arithmetic control passed.** The source-built control and the v2 KB8 replica match the diagnostic reference on 12,000 of 12,000 positions. INT8 is lossy by design and lies inside the bounds fixed before the run.
4. **Nothing here measures playing strength.** NPS is not converted to Elo anywhere.

## Result table (one row per build)

NPS ratio = candidate / original lock exe, `bench 20`, 16 paired comparisons, one pinned core (protocol below). "Same tree" means both arms reported 12,389,307 nodes on every run.

| Build | Evaluation path, net | PGO workload and coverage proof (entry counts from its own profile) | NPS vs lock (95 % CI) | Bit-exact vs s198 + HCE | Previous verdict | New verdict |
|---|---|---|---|---|---|---|
| `lock_ref` | original lock exe, s198 embedded | historical v1; not rebuilt | 0.9986 (0.9964-1.0008) against itself = noise floor | reference | bit-exact speed lock | unchanged; all ten pins and perft 5 reproduced here |
| `base_resid` | old residual float, s198 | frozen v1; `nnue::evaluate` 2,530,181, `nnue::update` 3,100,891 | **1.0000** (0.9982-1.0018), same tree | **yes**: ten pins + perft equal; diag twin 12,000 / 12,000, max error 0 | none (new control) | the build pipeline reproduces the lock's speed and arithmetic |
| `int8` | INT8/VNNI on by default, s198 quantized | v1 with `NnueInt8Vnni 1`; `int8_l1_sum` 2,832,503, `update_int8` 3,412,421, `refresh_int8` 24 | **0.9838** (0.9810-0.9867), different tree (11,638,305 nodes) | **no** (lossy): exact 1,269 / 12,000, max 29 cp, mean 3.207 cp; inside the pre-registered bounds | "UNPROVEN, ON about 0.5x" | fair exe exists; the 0.5x was the profile, not the kernel. Strength open. |
| `int8_cold` | same source, default off, run with the option on | v1 as-is (option off); `int8_l1_sum`, `update_int8`, `refresh_int8` all **0** | **0.4874** (0.4864-0.4885), same tree as `int8` | as `int8` | - | the earlier defect, reproduced on combo29/clang |
| `v2kb8_lockrep` | v2 residual KB8, s198 as KB8/OB8 replicas | v1 with `EvalFileV2` = replica; `static_evaluate_v2` 2,530,205, `v2::update` 5,898,903; compiled-in `nnue::evaluate` and `nnue::update` **0** | **0.9266** (0.9245-0.9286), same tree | **yes**: ten pins + perft equal; 12,000 / 12,000, max error 0 | "v2 path about 1.0x (advisory)" on an older lock | the v2 KB8 path costs about 7 % NPS on the current lock with a correct profile |
| `v2kb8_lockrep_hot` | as above with `FORGE_NNUE_V2_HOT=1` | same workload; same counts | 0.9290 (0.9245-0.9335), same tree | yes: 12,000 / 12,000 | - | the cold-section / noinline / unlikely hints are not the cause |
| `v2kb8_U8` | v2 residual KB8, soup U8 | v1 with `EvalFileV2` = U8; `static_evaluate_v2` 2,469,154, `v2::update` 5,729,039; compiled-in 0 | **0.8081** (0.8067-0.8095), different tree (11,412,889 nodes) | **not comparable** (different function); SIMD = scalar kernel on 12,000 / 12,000 | sanity 51.0 % of 400; gate H1 then CAP | correctly profiled exe exists. Like-for-like path cost is the replica row; the rest is this net's tree. Strength open. |
| `v2kb8_r5` | v2 residual KB8, run 5 | v1 with `EvalFileV2` = run 5; `static_evaluate_v2` 2,724,498, `v2::update` 6,316,046; compiled-in 0 | **0.9136** (0.9119-0.9153), different tree (16,735,664 nodes) | **not comparable**; SIMD = scalar kernel on 12,000 / 12,000 | sanity 51.4 % of 520; no gate row found | as U8. Strength open. |
| standalone net path | - | - | - | exact control **unavailable** | - | not built: all three candidate nets carry the residual flag (file headers checked) |

Earlier affected exes under the same protocol (8 pairs each), for scale only. They sit on older, slower locks, so their ratio mixes base and path:

| Earlier exe | Option | NPS vs combo29 lock (95 % CI) | Read |
|---|---|---|---|
| INT8 gate `81741f2b` (GCC, trial_w6 base, cold profile) | off | 0.9123 (0.9104-0.9141), same tree | the trial_w6 base |
| | `NnueInt8Vnni 1` | 0.4633 (0.4625-0.4641) | on / off = 0.508, the earlier report's 0.5x |
| v2 gate `v2p4` `a2a560cb` (GCC kit v2.5, older lock) | off | 0.7919 (0.7907-0.7931), same tree | its base |
| | `EvalFileV2` = replica | 0.7375 (0.7354-0.7397), same tree | v2 / off = 0.931, the same path cost as measured above |
| | `EvalFileV2` = U8 | 0.6457 (0.6432-0.6483) | U8 / replica = 0.876 (0.872 in the new builds) |

## Per-evaluation microbenchmark (isolates inference cost from the search tree)

`evalbench` on the diag twins, the 12,000 FENs, 100 repetitions, 8 pairs, same pinned core. Value = nanoseconds per static evaluation; ratio = candidate / old residual twin, so below 1 is cheaper. "root" = full refresh + evaluate; "repeat" = evaluate again on a valid accumulator.

| Twin | root cost ratio (95 % CI) | repeat cost ratio (95 % CI) |
|---|---|---|
| old residual vs itself | 1.0022 (0.9973-1.0071), 505 ns | 1.0003 (0.9983-1.0023), 118 ns |
| INT8 | **0.7395** (0.7318-0.7472) | **0.8661** (0.8625-0.8698) |
| v2 KB8, replica | 1.2079 (1.2060-1.2098) | 1.0446 (1.0413-1.0480) |
| v2 KB8, U8 | 1.1944 (1.1920-1.1969) | 1.0312 (1.0291-1.0333) |
| v2 KB8, run 5 | 1.2055 (1.1994-1.2116) | 1.0293 (1.0256-1.0329) |

- U8, run 5 and the replica cost the same per evaluation (within 1.5 %). U8's lower NPS at `bench 20` therefore comes from its search tree, not from slower inference.
- INT8 is cheaper per evaluation than the float kernel, yet its NPS is 1.6 % lower. The microbenchmark does not exercise incremental accumulator updates, and its tree differs, so this job does not explain that gap.

## Arithmetic controls on the 12k FEN set

FEN set: `opus_speed/data/fens_12k_v2.txt` of `opus-nnue-int8-vnni-20261106` (12,000 six-field FENs, md5 `e7dbf2c8151188c03ef52054557a531e`). The sibling `fens_12k.txt` is placement-only and its README says it is not for engine runs.

**Reference.** The lock exe has no static-evaluation command, so no evaluation was queried from it. The reference is `base_resid_diag`: the branch tree with only `FORGE_FAIR_DIAG=1`, built by the lock recipe. It is called the *diagnostic reference* throughout, not the lock. Its link to the shipped exe:
- the pinned source passes the lock manifest (20 / 20 files), and with every JOB D switch at 0 all eight units preprocess identically to it (`results/pp_identity_macro0.txt`);
- same net (s198 md5 `22b4b9e2...`);
- all ten bench pins and perft 5 equal the original exe's own output (`results/pins/`, `results/lock_ref/`);
- a second diagnostic exe built with a different compiler and no LTO or PGO (GCC 15.2 plain -O3) gives the same 12,000 evaluations.

Remaining gap: the shipped exe is a different binary, and agreement through ten bench searches plus 12,000 positions is finite evidence, not a proof for all inputs.

| Comparison (total static eval, cp) | Exact | Max abs error | Mean abs error | Notes |
|---|---|---|---|---|
| GCC plain diag vs diagnostic reference | 12,000 / 12,000 | 0 | 0 | evaluation does not depend on compiler or PGO on this set |
| INT8 build with the option off vs reference | 12,000 / 12,000 | 0 | 0 | the float path is untouched in an INT8 build |
| v2 KB8 replica (as ported, hot, and scalar kernel) vs reference | 12,000 / 12,000 each | 0 | 0 | s198 + HCE expressed exactly |
| **INT8 vs reference** | 1,269 / 12,000 | **29** | **3.207** | signed mean +1.032; 20 cp or more on 10 positions (0.083 %); 64 sign flips; hand-crafted term equal on all 12,000 |
| INT8 PGO twin vs plain INT8 build | 12,000 / 12,000 | 0 | 0 | integer path is build-independent |
| U8: SIMD twin vs scalar-kernel build | 12,000 / 12,000 | 0 | 0 | same-architecture control |
| run 5: SIMD twin vs scalar-kernel build | 12,000 / 12,000 | 0 | 0 | same-architecture control |

INT8 error distribution (|error| in cp: positions): 0: 1,269; 1-2: 4,506; 3-4: 3,209; 5-9: 2,651; 10-19: 355; 20-49: 10; 50 or more: 0.
Three worst positions (reference / INT8): `7Q/1p1k4/2p5/6P1/4P3/2P5/5PK1/8 b - - 0 69` -1917 / -1888; `3R4/1pk3p1/2b2p1p/8/3Q4/P6P/1P3PP1/6K1 b - - 4 35` -2209 / -2184; `8/4k3/8/8/1P3R1P/5BP1/5P2/6K1 b - h3 0 53` -2135 / -2113. All ten are in `results/evals/int8__vs__diag_ref.json`.

**INT8 acceptance (fixed in the approved plan before the run): PASS.** VNNI kernel equals the scalar int8 reference on 12,000 / 12,000; max 29 (bound 50); mean 3.207 (bound 5.0); signed mean +1.032 (bound 2.5); 0.083 % at 20 cp or more (bound 0.5 %). The bounds were chosen knowing the INT8 job's own figures on its older parent, and the result reproduces those figures exactly. They are a regression bound, not a strength statement.

U8 and run 5 differ from s198 by design (mean 17.7 cp and 14.7 cp on this set); that is a description, not an error.

**Standalone.** A standalone net cannot express s198 + HCE, so no exact s198 control exists for that path; dropping the hand-crafted term, padding or distilling would be a different function. None of the three candidates is standalone, so no standalone exe was built.

## Timing protocol (fixed before the first measurement)

- Every run is a fresh process: `uci`, Threads 1, Hash 16, OwnBook false, the arm's options, `isready`, `bench 20`, `quit`. `bench` builds its own 16 MB searcher per call, so node counts do not depend on earlier commands.
- Value = nodes x 1000 / time from the engine's own bench line.
- Engine pinned to logical CPU 8 at High priority before it reads any input; driver on CPUs 0-1; no build or other job work during timing.
- One untimed warm-up run per arm, then 16 slots. Slot order alternates A B, B A. **One pair = the two runs of one slot; ratio = candidate / lock.**
- Reported: geometric mean, 95 % Student-t interval on the log ratios; median, min, max, SD and every raw sample are in `results/abba/<arm>/`.
- Same-evaluation arms were run with `--same-nodes`: every run of both arms reported 12,389,307 nodes.

| Arm | Median | Min | Max | SD | Elapsed |
|---|---|---|---|---|---|
| lock vs lock | 0.9993 | 0.9909 | 1.0058 | 0.0041 | 132 s |
| `base_resid` | 1.0007 | 0.9912 | 1.0047 | 0.0033 | 132 s |
| `int8` | 0.9836 | 0.9736 | 0.9974 | 0.0054 | 130 s |
| `int8_cold` | 0.4876 | 0.4841 | 0.4908 | 0.0020 | 193 s |
| `v2kb8_lockrep` | 0.9261 | 0.9218 | 0.9392 | 0.0039 | 138 s |
| `v2kb8_lockrep_hot` | 0.9296 | 0.9081 | 0.9511 | 0.0084 | 138 s |
| `v2kb8_U8` | 0.8087 | 0.8029 | 0.8120 | 0.0027 | 142 s |
| `v2kb8_r5` | 0.9140 | 0.9066 | 0.9186 | 0.0032 | 163 s |

For INT8, U8 and run 5 the evaluation differs, so the search tree differs and NPS reflects the tree as well as the code. The replica row and the microbenchmark are the like-for-like numbers.

### Robustness check (added after the protocol runs; not part of the pre-registered protocol)

The two central arms again at `bench 22` on logical CPU 12, 8 pairs each (`results/abba_robust/`):

| Arm | NPS vs lock (95 % CI) | Median | Min | Max | Nodes lock / candidate |
|---|---|---|---|---|---|
| `int8` | 0.9944 (0.9929-0.9959) | 0.9945 | 0.9919 | 0.9967 | 34,048,354 / 27,267,033 |
| `v2kb8_lockrep` | 0.9237 (0.9215-0.9258) | 0.9232 | 0.9207 | 0.9295 | 34,048,354 / 34,048,354 |

The v2 KB8 cost is the same on another core and depth (0.927, 0.924). The INT8 ratio moves with the tree (0.984 at depth 20, 0.994 at depth 22), which is why it is quoted as "within about 2 % of the lock" and not as one number.

## How each build was made

`build_fair.ps1 -Config <id>` runs four stages with the lock's compiler and flags (clang 23.1.5 llvm-mingw-20261104, sha256 `d05fee2c...`; flags token for token from `forge-combo29/windows_build/build.log`, including `-Werror=profile-instr-unprofiled -Werror=profile-instr-out-of-date` in the use stage):

1. instrumented ThinLTO build (`-fprofile-instr-generate`);
2. training on `bench 11 / 13 / 16` with that configuration's `setoption` lines; node counts are checked against the expected ones;
3. coverage proof read from the merged profile (`tools/profile_coverage.py`);
4. rebuild with `-fprofile-instr-use` from that profile only, then the workload again on the final exe.

The work folder is named by a sha256 over source files, defines, flags, compiler, workload text and net, so a profile cannot be reused by a different configuration. Each build took 11-13 s on 16 CPUs.

Source switches in `forge-combo29/` (all default 0): `FORGE_NNUE_INT8_VNNI`, `FORGE_NNUE_INT8_DEFAULT`, `FORGE_NNUE_V2`, `FORGE_NNUE_V2_HOT`, `FORGE_FAIR_DIAG`.
- INT8: `patches/int8_vnni_after_w6.patch` (md5 `9a2ad0b4...`), applied with no fuzz.
- v2: `patches/v2root_fe0da8d_9037f2a.patch` (md5 `926ada2c...`), the diff of `D:\o30\repos\v2root` up to commit `9037f2a3`, whose three changed sources hash-match the `v2p4` gate source. One UCI hunk was re-placed by hand. The published branch carries only the first port patch.
- `tools/apply_switch_guards.py` added the guards and the diagnostic commands.

The ports are confirmed by node counts: `int8` gives 326976 / 760289 / 3282449 / 11638305 / 27267033 at depths 11-22 and the two nets give 356115 / 952259 / 2514975 (U8) and 294850 / 679834 / 3128255 (run 5), exactly what the earlier jobs recorded.

## Identities

| Item | md5 | sha256 (first 16) |
|---|---|---|
| lock exe `forge-combo29/windows/forge_clang_combo29_trial_w6.exe` | `c0051c99695f48bf93272d96fe7548c3` | `e1284f7fc492c8fe` |
| s198 `forge-combo29/src/nnue_weights.inc` | `22b4b9e2c61b37c0450f13a3a92c19b3` | `a7ebcf3a319675f3` |
| INT8 weights `forge-combo29/src/nnue_int8_weights.inc` | `25982cc2c656b94d8728390ea97c703c` | - |
| replica net `lock_s198_rank4x2_ob8.nnue2` (written here by `tools/o30_v2net.py from-lock --kb-map rank4x2 --ob 8`) | `ccacfefbc393d0475c9b98202c5daf3e` | `8559fdfab2073754` |
| U8 `o30_gpu_soupU8r3r5r10r12r14.nnue2` | `5529d6b09c49b31647b746450a03c9bd` | `dcf07a65aee585ac` |
| run 5 `o30_gpu_kb8short_r5.nnue2` | `9cf175aae2364f1e2a7129132d4a95f2` | `27ea0a39c26977a9` |
| `base_resid` | `b794beb419d3140354ff8b10f452b5d0` | `8db5d2daa82bf926` |
| `base_resid_diag` (diagnostic reference) | `5c6b472da5f9f28b89ee4ef0050634e4` | `4d77eca114ae5000` |
| `int8` | `09b80085063b1949a23f6077a3b9f4b7` | `0d5b2db07cf0268c` |
| `int8_cold` | `a192f1ef57326f50349bb5e4d7aa705c` | `086645a17b86ed27` |
| `int8_diag` | `f24dd95f2d83596c1e4cb51c2a947992` | `eb70258b72ef076d` |
| `v2kb8_lockrep` | `d8f28f69766617ffb8fb49133b99338f` | `2cc7356822e7ff5d` |
| `v2kb8_lockrep_diag` | `e68e01826b41c552e766c44348891e82` | `fd241561d543d7dd` |
| `v2kb8_lockrep_hot` | `79241f439061ea364d9ba7aa7da28b78` | `7afb690d087db766` |
| `v2kb8_lockrep_hot_diag` | `10d94de28a2d29882084a0360af96e7c` | `3ebc7205e08ca80c` |
| `v2kb8_U8` | `e306ef17f16231af61aefa44e4f5b7cc` | `6fb2e1c56f1c8b23` |
| `v2kb8_U8_diag` | `320d5e381af11203e8b2dfba3cc2e184` | `b15a8eadbb5a151d` |
| `v2kb8_r5` | `a87c5df1bb9d564a6f7e9ecc92a7fd2a` | `320dd3d642a4c38e` |
| `v2kb8_r5_diag` | `d474dc551b6dcba7d8ade14304757123` | `86c91df3ffae3a18` |
| plain GCC diag `diag_ref_gcc_plain.exe` | `42fd7e4ccdbab9365e81475c5bb0de53` | - |
| plain clang `v2_scalar_diag_plain.exe` (`FORGE_NNUE_V2_SCALAR=1`) | `11602d8db0f6a0bc854472e6769f4207` | - |
| plain clang `int8_diag_plain.exe` | `34b5ac777c4315d547f9947c7b94db1d` | - |
| earlier INT8 gate exe (read only, `D:\opus_5h\int8_vnni\pack\`) | `e2da1a1f917adc64c17dbde78079853d` | `81741f2b0f5ae1be` |
| earlier v2 gate exe `v2p4` (read only, `D:\o30\w\v2p4_pc1\src_copy\`) | `81b5168760c7e17c954134b5957a3957` | `a2a560cb4b6a2c11` |

Exes, profiles and nets are not in the repository. They are at `D:\forge_jobs_20261111\fairD\_work\` (`builds\<config>_<identity>\forge_fair_<config>.exe`, `nets\`, `plain\`). Full hashes, flags, workload and coverage for each build are in `results/builds/<config>_<identity>/RECEIPT.json`.

## Reproduction

```
git clone https://github.com/couns0538-sketch/dwqww && cd dwqww
git config core.autocrlf false && git checkout fable/fair-eval-builds-20261111
# nets into _work\nets (file names and sha256 in fair_eval\configs.json); the replica:
python -I -B fair_eval/tools/o30_v2net.py from-lock forge-combo29/src/nnue_weights.inc _work/nets/lock_s198_rank4x2_ob8.nnue2 --kb-map rank4x2 --ob 8
pwsh -NoProfile -File fair_eval\build_fair.ps1 -Config int8            # any id of configs.json; add -Diag for the twin
bash fair_eval/tools/pp_identity.sh <pinned lock tree> forge-combo29   # macro-0 identity
bash fair_eval/tools/run_pins.sh <exe> <out.txt> ["setoption ..."]     # ten pins + perft
bash fair_eval/tools/run_evalfens.sh <diag exe> <fens> <out.tsv> ["setoption ..."]
python fair_eval/tools/eval_compare.py --ref REF.tsv --cand CAND.tsv --fens FENS --name N --out OUT.json
python fair_eval/tools/abba_fair.py --name N --out NEW_DIR --a <lock exe> --b <exe> [--b-opt "setoption ..."] [--same-nodes]
python fair_eval/tools/abba_fair.py --name N --out NEW_DIR --a <resid diag exe> --b <diag exe> --evalbench <fens> --reps 100 --slots 8
```

Raw results: `results/abba/` (every timing sample), `results/evals/` (comparison JSON, two compressed dumps, sha256 of all twelve dumps), `results/builds/`, `results/pins/`, `results/lock_ref/`. Earlier evidence is read in `EVIDENCE_MATRIX.md`.

## Limitations

- **Strength is not established** for any candidate. The U8 gate rows (H1, then CAP) and the missing gate for run 5 and INT8 are untouched.
- Timing is one machine, one core, one depth, Threads 1. Whole-machine load samples of one second, taken before and after each arm, ranged from 1 % to 18 % (processes that are not this job's; each sample is in `results/abba/<arm>/load.txt`). The lock-vs-lock interval (0.9964-1.0008) is the measured noise floor.
- NPS of a different-evaluation candidate is tied to the bench positions; U8 and run 5 differ by 10 points on the same code.
- The microbenchmark runs on diag twins, not on the timed exes, and does not cover incremental updates.
- The 12k comparison is against a diagnostic reference, not the shipped exe (gap stated above), and covers that set only.
- Builds are not byte-reproducible. A second `int8` build in a new folder gave the same identity, node counts and coverage but a different profile hash and exe md5 (`results/builds_repro/`).
- INT8 and the v2 path were not tested above Threads 1, and no sanitizer was run.
- Why the v2 KB8 path costs 7 % was not investigated. The lock's compiled-in net uses a 512-bit kernel and the v2 header offers AVX2, SSE and scalar kernels; whether that is the cause is not shown here.
- The standalone nets seen in the gate table (`EvalFileHalfKA`) were not examined: their engine source is not on the lead branches.
- The job finished well inside the time allowance because each build takes about 12 s; the remaining time was not padded.
