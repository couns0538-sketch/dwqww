# STATUS — portable-build audit

**State: complete.** All five measurements requested were run; the findings are in
`FINDINGS.md` beside this file, evidence in `evidence/`, scripts in `scripts/`.

## What was asked and what came back

| # | measurement | result |
|---|---|---|
| 1 | build at `-march=x86-64-v2` and `v3`, define `FORGE_PORTABLE` if it exists | **The path already exists** (CMake option, drops `SLIDER_PEXT` + `NNUE_ZMM`). Built at v2 and v3. **All 11 LOCK.md pins exact on both, plus perft 5.** |
| 2 | if a pin moves, say which and by how much, ISA path or compile-flag bug | **No pin moved.** None on any build, at any depth, net on or off. |
| 3 | timing vs native on 120 positions, ABBA, ratio + CI + direction share | **v2 = 1.1614 (+16.1%), CI 1.1572–1.1671, slower on 120/120. v3 = 1.0422 (+4.2%), CI 1.0372–1.0450, slower on 106/120.** Both slot-bias corrected; p ≤ 1.4e-5. |
| 4 | drawn-root bail identical on each build | **Identical on all 8 cases**, including the mate-in-one forfeit. Byte-identical, not merely equivalent. |
| 5 | portable in practice, and what does it cost | **Yes.** Correct at every level tested; costs +4.2% at v3 and +16.1% at v2. Cheapest safe portable config is v3 + PEXT at **+1.4%**. |

## The two results worth escalating

1. **`FORGE_PORTABLE=ON` is 2.8 points more expensive than it needs to be at v3.** It
   disables PEXT unconditionally, but `x86-64-v3` includes BMI2. Enabling PEXT at v3 gives
   **+1.43% instead of +4.22%**, with every pin still exact. One flag; not applied here
   because the owner's hardware should time it first.
2. **A lower `-march` with the switches left on does not compile** — three `#error`s, by
   design. Recorded because a silent miscompile is the failure mode this prevents.

## Things that were caught rather than reported

- **The A/A control is not null**: the same binary in both ABBA slots gives 0.9890. Every
  ratio here is from two arms in opposite order, and the correction is validated against a
  value the estimator cannot tune (agreement 0.43% or better on all seven pairs).
- **A vacuous bail fixture was rebuilt.** The first mate-in-one FEN was illegal; the engine
  silently kept the previous board and the row would have read as a pass. Caught by two
  different boards returning identical node counts.
- **A zero that was my own bug.** The first static ISA sweep reported `v3pext` as having no
  AVX and no PEXT; `objdump` had failed on a wrong path and the grep counted an empty file
  as zero. Re-run with an existence guard, it shows 1,024 `ymm` and 127 `pext`.
- **AVX-512 emulation results were discarded, not reported.** qemu 8.2's TCG reports
  `avx512f=0` for every CPU model including `max`, so the native build's SIGILL there is
  qemu's gap. The v2/v3 emulation results stand because AVX2/SSE2/BMI2 *are* emulated.

## Limits a reader should carry

- NPS is this machine's (Xeon, 4 cores), not the lock's `znver5`. Re-time §6 on the owner's
  hardware before changing the CMake default.
- Per-run CIs cover within-run sampling only. **Between-run drift is ~1.4%**, so the +1.4%
  and +2.3% rows are approximate. The +16% and +4% rows are not affected.
- No AVX-512 build was executed in a lower-ISA environment (no emulator can).
- No game-level or Elo claim: a 16% slowdown is a real cost at fixed time, but that was not
  measured.

## Reproduce

```bash
export LIBRARY_PATH=/usr/lib/gcc/x86_64-linux-gnu/13
git worktree add /tmp/wt/base 6b98f217
scripts/build_all.sh
scripts/check_pins.sh /tmp/build/native/forge    # gate
python3 scripts/identity.py && python3 scripts/bail.py
```
