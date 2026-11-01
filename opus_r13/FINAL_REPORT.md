# R13 (Opus) - report (checkpoint 2, 2026-11-01 ~09:10 PC clock: P1 done, P2 done for now, P3 SPSA running)

Everything below is **UNPROVEN**: no Elo or speed claim; crew gates (UHO first, 8moves_v3 second, never pooled) and QA's
timing decide. Lock = FD3A5190 (AL1 s198, kit v2.3 -Expose). Lock source = git d4f4312 (= src_al1s198_clean, 20 files).
Time: the work ran from the plan push (bbd8e587, ~16:05 PC clock) to this report (~17:40), about 1.6 h of commits.

## Gate lines, suggested order (Phase 1, branch opus-r13-p1-nearmiss-ports, folder opus_r13/p1/<item>/README.md)
| # | item | setoption line(s) | exe (C:\o13\handoff\<item>\) sha256 | PC precondition (ON bench) |
|---|---|---|---|---|
| 1 | b1 | BundlePreset=B1 | e950c77e7832e7f32d701bf1424d65553957ca8486e8bd1d29d922f9b1e25900 | bench 13 = 758456 |
| 2 | packa_w60 | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=60 | 07cc2393934528272d3114e3d664a3165fabc3614f2eba9a2782ca919e4b8146 | bench 13 = 676197 |
| 2 | packa_w50 | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=50 | same exe as w60 | bench 13 = 744597 |
| 3 | bnd68 | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=50 ContHist4Pct=45 EvalOnlyStore=1 EvalOnlyStoreMinDepth=2 | 8dc93b38b7513de629e4854748f593b6d42a51bd4922a5c16d2a54b130866f69 | bench 13 = 776194 |
| 4 | packc28 | AspFailHighReduce=1 AspFailHighMaxReduce=3 EvalSwingMult=24 EvalSwingMax=200 | cf617e671069d32ba6eb5ce452b56e193af41442a5db39388a19005a04b22351 | bench 13 = 690187 |
| 5 | eos49 | EvalOnlyStore=1 EvalOnlyStoreMinDepth=2 | a4e7f24cbb7334e1d203e92bfa71d4edbf8d10a6a5836ad702978dee32dddbdc | bench 16 = 3033426 (d11/d13 = OFF) |
All: OFF bench d11-d22 = 312866/862329/3024920/12389307/34048354 (no setoption) before game 1.

## Check table (Phase 1; details per item in its README and opus_r13/p1/RESULTS.md)
| check | b1 | packa | bnd68 | packc28 | eos49 |
|---|---|---|---|---|---|
| port proof | ON nodes = forge-bundle-int B1 at d11-d22 (+ singles) | line set = packa.patch - CMake | = packa + packe2r, files byte-equal | line set EQUAL | files byte-equal |
| committed patch on fresh lock = kit source | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL |
| LTO+PGO pc1 = pc2, OFF ALL OK, ON live, 0 missing-profile, vfmadd 0 | PASS | PASS | PASS | PASS | PASS |
| uci options listed, switches default OFF | PASS | PASS | PASS | PASS | PASS |
| T1/T4 movetime smoke, legal bestmoves | 16/16 | 24/24 | 16/16 | 16/16 | 16/16 |
| mate probe 22 mates @3M (OFF 19) | 21 | w50 22, w60 20 (*) | 22 | 22 | 20 (*) |
| CI ASan+UBSan self-play default/gate/max | PASS | PASS | PASS | PASS | PASS |
(*) one deep KRK mate (OFF M15) shows as cp at 3M nodes; found at 30M nodes (horizon effect, logs/lost1_*.json, eos49_lost1_30M.json).

## Phase 2 block 1 (branch opus-r13-p2-sparse-l1, opus_r13/p2/RESULTS.md, stack/README.md)
- Stack = r10fix1 (git 7f79c349, lock + EvalFileHalfKA) + S1 LargePages (line set EQUAL; 2 include lines placed by hand),
  built with the R12 bundle recipe (Coder's kit v2.4: workload v2.1 = no-net + e19 + e9 profile passes, -PartialTraining, -Expose).
- Exes (C:\o13\handoff\p2_stack\): align0 **ff6628ce2b7391428a06d9234d3ba7f8d61d879d0155612df1239eb0e646a557**,
  align1 (FORGE_ALIGN_WEIGHTS=1) **302ad8fba36c09f16f0c871bb080697f912e3360e4943a3b8a7077060bfafd4f**; pc1 = pc2 both.
- Identity: OFF pins, LargePages=true = OFF, e19/e9 = D8D90B68 pins, 12k-FEN exe identity 12000/12000 (e19, e9), CI PASS,
  0 real -Wmissing-profile warnings with the net-path profile (step 1b).
- FORGE_ALIGN_WEIGHTS: lock w1 at 48 mod 64 without, 0 with (probe). Advisory ABBA align1 vs align0: **neutral**
  (no net d16 -0.07%, d20 -0.92%; e19 d16 +0.37%, d20 +0.89%; A/A noise up to ~3%).

## Phase 2 step 2 - sparse L1 (find-nnz): STOPPED, slower
- FORGE_SPARSE_L1 (default 0) is bit-identical (pins, 12k 12000/12000, AVX-512 + AVX2, UBSan-trap self-play with nets),
  LTO+PGO exe 6fdf46dc (pc1 = pc2), but advisory ABBA with e19: LTO+PGO -13.5% (d16) / -11.9% (d20) vs dense; plain -7.6%,
  and -8% after one fix attempt (no ___chkstk_ms, inlined). Two failures -> stopped; dense stays. Do not gate 6fdf46dc.

## Phase 3 - Sf26 split (branch opus-r13-p3-sf26split, opus_r13/p3/README.md)
- Exe 029d58e8036aafa18849fef4c32cdf1a02385cc96208692d5fa366dad8e401ce (pc1 = pc2): switches Sf26NmpPrior (bit 2),
  Sf26LmrGap (bit 4), Sf26MulticutCorr (bit 8); each one's bench = the original Sf26Bundle bit on AL1 at d11-d22.
- Gate lines: `Sf26NmpPrior 1` (bench 13 = 931568), `Sf26LmrGap 1` (936607), `Sf26MulticutCorr 1` (849753); combined
  (= Sf26Bundle 14, 727853) only if 2+ singles reach H1. Checks PASS (smoke 32/32, mate probe, CI ASan+UBSan).
- SPSA (160 pairs per bit, 5+0.05, seeds 13002 / 13004): running; results go to opus_r13/p3/RESULTS.md (proposals only).

## Known risks
- F: had 45 GB (< 50 GB floor): all scratch, builds and exes are on C:\o13 (not F:\o13 as the prompt said).
- b1: CuckooRep's 8 R3 macro instances are one template parameter here; nodes are identical, codegen differs from R3.
- eos49 / bnd68 add ValueNone guards on the OFF path (node-identical OFF verified).
- P2 stack base choice (r10fix1 + S1 with the w21pt recipe) is my reading of "lock + R12 bundle + S1"; QA should confirm.
- All builds are workload v1 (Phase 1) or v2.1 (Phase 2); never compare across workloads without saying so.

## Left (TODO for the crew or a next session)
- P2 steps 5 / 5a (optional speed items) and a profile of the HalfKA L1 before any new sparse attempt; P4 v2-feature nets;
  P5 relabel; P6 Syzygy; P7 E3 fit.

## Skills (new / updated; committed under skills/<name>/ on the branch they describe, mirrored into .claude/skills/)
- New: `forge-lock-port`, `forge-candidate-checks` (branch opus-r13-p1-nearmiss-ports), `forge-speed-stack` (opus-r13-p2-sparse-l1,
  incl. the sparse-L1 negative result).
- Updated: `forge-ltopgo-pgo` (R13 section), `forge-pc-rules` (R13 rules) (opus-r13-p1-nearmiss-ports).
