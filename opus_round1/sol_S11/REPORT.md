# S11 [Sol leftover] Node-exact speed pack: MaterialKeyTable — DONE (node-exact; speed eligibility not met)

Branch `opus-sol-S11` = `d4f4312` (AL1 s198 lock tree `294dbed` + baseline evidence + CI recipe) + `0d99f02`
cherry-picked (`ed951e8e`) + [S11] commits. Code `ad05f62b` (option, table, test) and `faff1c46` (keep
`material_key` inlined); tools/CI `86a5d560`; evidence `316b9c2e`, `5179b5ea` ([skip ci]). Every file and archive
size: `FILES.md`. No Elo or speed claim.

## 1. What was ported
- Sol's S11 work has exactly one prepared idea, the "material_key table-sum"
  (`forge_sol_S11_material_history_key_20261026.patch`, branch forge/sol-pack31-20261025 @17aa0cae).
  It is a history-lookup speedup. The material-correction key is a Horner polynomial (mod 2^64) in the ten piece
  counts, so it equals a constant plus ten independent per-slot terms. A constexpr table (10 x 65 words, 5200 B)
  gives the same 64-bit key with ten loads and adds instead of ten dependent multiply-adds and a final multiply.
- Sol prepared no make/unmake or SEE idea. His exclusions stand: picker/piece_type and history hoists were
  earlier speed packs, TT prefetch belongs to S13 and NNUE updates to S12. Nothing new was invented here.
- Sol's native work (L′/B 1M-position three-arm parity, results 3a409d62/e53edba0) used his dev-base refs. His
  open items (scalar observer, final parity, publication summary) are replaced on AL1 by: scalar-vs-AVX2 node
  identity on all refs, the CTest key test, and this report.
- Files changed:
  - `include/forge/material_key_table.hpp` (new; `alignas(64)` table, `matkey::table_key`);
  - `include/forge/search_options.hpp` and `src/search/options.inc` (new; `forge::options::material_key_table = false`);
  - `include/forge/search.hpp` (one include);
  - `src/search.cpp`: `material_key()` gets `if (options::material_key_table) [[unlikely]] return matkey::table_key(board);`
    in front of the unchanged Horner code, plus `[[gnu::always_inline]]`;
  - `src/uci.cpp`: `option name MaterialKeyTable type check default false`, accepts true/false;
  - `tests/material_key_tests.cpp` + CMake (CTest `forge_material_key_tests`).

## 2. Runtime UCI option, not a compile switch
- **Why.** The acceptance asks for NPS OFF vs ON in the same binary, which only a runtime option allows. A compile
  switch would leave the OFF binary identical to the lock, but its A/B compares two binaries whose layout differs
  by more than this effect.
- **Codegen cost** (`codegen_compare.sh`, lock exe vs OFF build):
  - `corrected_eval` 99 -> 108 instructions: one `cmpb $0x0,material_key_table(%rip)` / `jne` ahead of the Horner
    chain. Registers are re-allocated: the lock's chain shuffles through xmm1, the new one does not.
  - `update_correction` 81 -> 109.
  - `search` 2413 -> 2414: one xmm spill/reload pair around a call plus nop padding; its start moves 32 -> 16 mod 64.
  - `qsearch` 810 -> 807: one spill fewer plus padding.
  - Iterative-deepening driver 2119 -> 2120 (48 -> 32 mod 64).
  - Every other listed hot function is identical (MovePicker::next, TT probe/store, NNUE, make/unmake, SEE).
- **Bug found and fixed.** The first build (`ad05f62b`) let GCC emit `material_key` out of line and inline
  `corrected_eval` into search/qsearch, so the OFF path paid a call with spills. codegen_compare caught it,
  `[[gnu::always_inline]]` in `faff1c46` restores the lock's structure, and all evidence below was regenerated
  from `faff1c46`.

## 3. Acceptance

| # | line | result | command → raw output |
|---|---|---|---|
| 1 | scalar vs AVX2 node-exact on all refs | PASS | **PC:** `build_pc_scalar_nnue.sh` compiles nnue.cpp with `-U__AVX2__ -U__SSE__ -fno-tree-vectorize -fno-tree-slp-vectorize` plus a forced include that undefines MinGW's `_M_X64`/`_M_AMD64`. Without that include MinGW keeps the SSE path. Macro dump: `FORGE_NNUE_SSE 0`; forge::nnue:: has 0 packed float ops, 47 scalar `ss` ops, and one `vmovdqu8 %zmm0` zero store (lanes[16] init). That build and the normal exe, with `uci_check_opt.py --full` with and without `--set MaterialKeyTable=true` → 4× ALL OK. **Linux** (run 40478254153, g++-14, x86-64-v3; branch + scalar build, OFF and ON) → 4× ALL OK |
| 2 | ON nodes == OFF | PASS | **Refs**, OFF and ON, PC (AVX2 and scalar) and Linux: bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690. **CTest** `forge_material_key_tests`, 14/14 checks: count-domain proof on the 650 single-slot vectors (covers all 65^10 count vectors) and 100000 random vectors; 1,000,000 random-walk positions (33,598 with promoted pieces) where table key == polynomial key on 64 bits and the search's material index read through the real `corrected_eval` is equal OFF/ON; the 8 bench positions at d11 give equal nodes, score, move and PV OFF/ON (total 312866). **Mutations:** mutant 1 (one table word +1) fails the test 4/14 (150,440 boards) yet bench stays exact, because it only relabels correction slots. Mutant 2 (7 and 8 white pawns share a term) gives ON bench d11 314061 / d13 927796 / d16 3167021 (MISMATCH) with OFF exact |
| 3 | NPS OFF vs ON, same binary, 5 runs, median | DONE, no effect measurable on the PC | `nps_onoff.py exe 5 MaterialKeyTable 16 20`, ABBA order, nice 19, machine exclusive: no. Medians ON/OFF: d16 −1.67% wall / −0.96% CPU; d20 +1.20% / +1.52%. 95% CIs of the mean difference all contain 0 (d16 wall −2.80..+0.73, d20 wall −2.05..+2.13). Quiet runner, 10 runs: d16 +0.17% (CI −1.16..+1.74), d20 +1.69% (CI +0.62..+2.86). Nodes identical on every run |
| A1 | builds on the lock tree | PASS | PC recipe (`b/tools/build_pc.sh`), CMake (g++ 15.2), Linux CMake (g++-14) |
| A2 | OFF bench-exact AL1 (5 depths), perft5 | PASS | standard `opus_round1/ci/uci_check.py --full` → ALL OK (PC; Linux opus-ci release) |
| A3 | FMA 0 | PASS | 0 in the PC AVX2 and scalar exes and in the Linux builds |
| A4 | CTest + ASan/UBSan (CI) | PASS | Local ctest 14/15, only the 4 known forge_tests lines (`check_known_failures.py` PASS). opus-ci 40478253767: release, asan and tsan all success; known check PASS; no sanitizer report; TSan 0 reports. The new test passes in all (ASan 6.8 s) |
| A5 | UCI option default OFF | PASS | `option name MaterialKeyTable type check default false`; the test asserts it is off by default |
| A6 | IDEA_SOURCE | PASS | `IDEA_SOURCE.md` |
| A7 | ON node / NPS numbers, no Elo claim | PASS | above; no Elo claim |
| A8 | OFF build vs lock speed (hot code changed) | no slowdown | **PC**, `nps_ab.py lock s11 10 16 20`: d16 wall +0.44% (CI −0.37..+1.25), CPU +1.66%; d20 wall +1.94% (CI +0.14..+3.74), CPU +0.72%. **Quiet runner:** d16 +1.16% (CI −1.29..+3.62), d20 +0.46% (CI −0.74..+1.66) |
| S11 | speed eligibility: PC CI lower bound ≥ +2% at d16 AND d20 | NOT MET / UNVERIFIED | PC noise-dominated; runner lower bounds −1.2% (d16), +0.6% (d20). Advisory only |

CI runs: opus-ci 40478253767 (release, asan, tsan: all success) and opus-sol-s11-nps 40478254153 (success).

## 4. Left / UNVERIFIED
- Speed gain: UNVERIFIED. The machine was never exclusive, and the ≥ +2% rule is not met on the runner.
- Gate: none proposed for Elo. Options are folding it into S29's single speed-stack gate, or a non-regression
  SPRT [−3, 1] at 10+0.1 vs AL1 with MaterialKeyTable=true. QA picks the srand.
- No make/unmake or SEE ideas: Sol prepared none.
- Sol's 1M-record NNUE snapshot parity (accumulator bits) was not repeated on AL1. The patch does not touch
  NNUE; node identity of the scalar and AVX2 builds covers the search.
- The Linux scalar build shows 2 wide-register uses in forge::nnue:: (0 packed float ops). Not inspected further.
- The PC clock is about 9 h ahead of UTC, so PC log stamps are PC clock.
- The worktree has untracked `tools/__pycache__` and `tools/match/__pycache__` from Python ctest cases; they were
  never committed and are left in place (no deletes).
