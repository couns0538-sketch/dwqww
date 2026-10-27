# S05fix — FMA checker v4: whole .text and whole-binary scan, computed fma_count — DONE (Linux CI recorded below)

Branch `opus-sol-S05fix` = AL1 base `d4f4312` + CI baseline `0d99f02` (`e41596a0`) + `ff2d48e6` (v4 checker, tests,
planted bug, per-branch CI) + the REPORT commit. No engine source change. Machine exclusive: no (Idle priority; objdump
runs only). Work and results by a sub-agent; this report text is its hand-back.

## Acceptance

| Item | Command | Result | Evidence |
|---|---|---|---|
| S05-1 whole .text, not only forge::nnue:: | `test_forge_sol_S05_fmacheck_v4.py` | an FMA in an unrelated function now FAILS (fma_count 1, nnue_scoped 0); v3's fixture passed it | `logs/v4_fixture_tests.log` |
| S05-1 computed fma_count | fixture with 4 fused ops in 2 functions | fma_count 4, nnue_scoped 1, each listed with section and symbol | same |
| S05-1 whole-binary count printed | `forge_sol_S05_fmacheck_v4.py <exe>` | first line `FMA_COUNT whole_text=N whole_binary=M nnue_scoped=K instructions=I nnue_contract=... status=...`, then JSON; FMA in `.init` counts in whole_binary | `logs/v4_*.out` |
| Fixture tests | `python -B test_forge_sol_S05_fmacheck_v4.py -v` | 33 OK (Sol's 27 with one expectation reversed by S05-1, + 6 new) | `logs/v4_fixture_tests.log` |
| AL1 lock exe (5d4df7f1) | v4, v3, `objdump -d \| grep -cE 'vfn?m(add\|sub)'` | v4 PASS: 0/0/0 over 282,302 instructions, NNUE contract PASS (mask-zero); v3 PASS; grep 0 | `logs/pc_checks.log` |
| h256_e12 lock exe (456743d9) | same | same as AL1 | `logs/pc_checks.log` |
| Planted bug | `make_fma_mutant.py` (std::fma in the LMR table setup) + `build_pc.sh` | grep 2; v4 FAIL whole_text=2 whole_binary=2 nnue_scoped=0 (forge::tune::refresh(), static initializer); Sol's v3 PASS with its literal "fma_count": 0 | `logs/v4_mutant_fma_outside_nnue.out`, `logs/v3_mutant_fma_outside_nnue.out` |
| Linux ELF (default + planted bug) | opus-sol-s05fix-ci 40517502825, opus-ci 40517502603 | see "Linux CI" below | — |

## What changed (v4 vs Sol's v3, unchanged copy in `sol_v3_unchanged/`)
- Scan every instruction of every section objdump disassembles (PE `.text`; ELF `.init .plt .text .fini`).
- `fma_count` (whole .text), `fma_count_whole_binary`, `fma_count_nnue_scoped`, per-section counts, first 50 hits.
- Exit 1 on any nonzero count, or (unless `--fma-only`) if v3's NNUE output contract fails (logic unchanged).
- Streams objdump output; `--disassembly FILE` for fixtures/replays (portable; v3's tests needed a POSIX objdump
  shim); mnemonics `v[4]f[n]m{add,sub}*` and `vf[c]maddc*`.

## Findings
- v3 only looked at forge::nnue:: and printed a literal 0: an std::fma in search's LMR table setup (2 FMAs) passed v3.
- Both PC lock exes are FMA-free across the whole .text (282,302 instructions); grep and v4 agree.

## Linux CI
Recorded by the main session after the hand-back (the runs were queued when the sub-agent finished): see the section
appended below when the runs complete.

## Left / UNVERIFIED
- Sol's S05 ctestwire patch (FORGE_BUILD_NNUE_VALIDATION float-parity targets) is not ported to AL1 in this job; wiring
  v4 into its `forge_sol_S05_fmacheck` ctest is the natural follow-up when S05 itself is ported.
