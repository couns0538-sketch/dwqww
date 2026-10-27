# S05fix — FMA checker v4: whole .text scan, computed fma_count, whole-binary count

Tool only (Python 3.10+, standard library, GNU objdump). Branch `opus-sol-S05fix` = AL1 base `d4f4312` + CI
baseline `0d99f02` + this folder + a per-branch workflow; no engine source change.

Sol's v3 checker (`forge_sol_S05_fmacheck_v3_20261025.py`, 17aa0cae; unchanged copy in `sol_v3_unchanged/`)
searched for fused multiply-adds only inside `forge::nnue::` symbol bodies and printed `"fma_count": 0` as a
literal. `forge_sol_S05_fmacheck_v4.py` fixes S05-1:

- scans every instruction of every section `objdump -d` disassembles (PE: `.text`; ELF: `.init .plt .text .fini`),
  every function, not only `forge::nnue::`;
- computes `fma_count` (= whole `.text`), `fma_count_whole_binary`, `fma_count_nnue_scoped`, per-section counts and
  lists the first 50 fused instructions with section and symbol;
- prints `FMA_COUNT whole_text=N whole_binary=M nnue_scoped=K instructions=I nnue_contract=... status=...` and one
  JSON line; exit 1 if any count is nonzero, or (unless `--fma-only`) if v3's NNUE output contract fails;
- streams objdump output (no whole-listing copy in memory); `--disassembly FILE` reads a saved listing (fixtures,
  replays); `--objdump PATH` picks the objdump; `--fma-only` counts a stripped or non-NNUE binary.
Counted mnemonics: `v[4]f[n]m{add,sub}*` (FMA3/FMA4/AVX-512, incl. fmaddsub/fmsubadd) and `vf[c]maddc*`.
The v3 NNUE output-contract logic (256-bit min/mul/add plus max or proven masked zero clamp) is unchanged.

## Run

```sh
PATH=/c/msys64/ucrt64/bin:$PATH python -B forge_sol_S05_fmacheck_v4.py <forge.exe>   # PC (MinGW objdump)
python -B test_forge_sol_S05_fmacheck_v4.py -v                                      # 33 fixture tests
python -B make_fma_mutant.py <COPY of the source tree>                              # planted bug (copy only)
bash ci_s05fix.sh ci_out                                                            # Linux CI (ELF), see below
```

`.github/workflows/opus-sol-s05fix-ci.yml` runs `ci_s05fix.sh` on every code push: the default Linux build must pass
v4 with zero counts; the planted `std::fma` (outside `forge::nnue::`) must fail v4 while v3 passes it; fixture tests.

## Files

- `forge_sol_S05_fmacheck_v4.py`, `test_forge_sol_S05_fmacheck_v4.py` (Sol's 27 v3 fixtures, one expectation
  reversed by S05-1, + 6 new tests), `make_fma_mutant.py`, `ci_s05fix.sh`.
- `sol_v3_unchanged/` — Sol's v3 checker and fixture runner, byte-identical (sha256 e7ba90e5..., 152f0d77...).
- `logs/` — PC runs (lock exes, planted-bug exe, v3 vs v4), fixture tests, CI artifacts.
