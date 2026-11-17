# Final report — forge-combo29 audit

Two documents, both rendered from the swarm run of 2026-11-16T22:20Z → 2026-11-17T10:08Z.

- **`forge-findings.md`** — the report. Opens with the decisions table and the gate caveat; §1–§5b and
  §8–§10 are about the engine, §6 and §7 are about how to measure it.
- **`test-matrix.md`** — the same run enumerated. 137 rows: 31 areas tested and correct, 33 tested and
  wrong, 16 conditional or partial, 21 never tested with the reason for each, and 36 instruments in this
  audit that reported something false, with what caught each one.

Engine under audit: `forge-combo29` at commit `6b98f217`. Build `e06310ec…`, `/usr/bin/g++` 13.3.0,
`-DFORGE_MARCH=x86-64-v4`, Release, `Threads 1` unless a row says otherwise.

**Read the "pins matched" caveat before trusting any green result.** The four `bench` pins are a valid
instrument and an invalid certificate: 6 of 9 real behaviour changes pass a green 4/4, including
`Threads` and the drawn-root bail. Pin agreement means *invisible to this instrument*, never *safe*.

Read `test-matrix.md` first if you want a checklist; read `forge-findings.md` first if you want the
reasoning. Where they disagree the findings document is the authority, and it should not happen — both
were generated from the same tally.

## What this run found, in one line each

- **Do not ship** the NNUE weight-column prefetch (8.1–9.8% slower, four measurements).
- **Ship both drawn-root patches, for a narrower reason than first claimed** — they fix the reporting, and
  on 2,457 real drawn roots they change the move in **0**.
- **Keep `Threads 1`**, keep the default `Hash`, leave `AspirationDelta` at 18, and do not enable
  `SoundMatePruning` below fixed depth 10, `AspCappedReopen`, `AspArmLate` or `QuietExtinction`.
- **Verify every mate label independently**: 26.1% to 37.1% of verifiable labels are wrong.
- **Do not rely on this engine to convert a won endgame** — the score collapses to `cp 0` at halfmove 90.
