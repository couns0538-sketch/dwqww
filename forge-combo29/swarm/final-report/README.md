# Final report — forge-combo29 audit

Two documents, both rendered from the swarm run of 2026-11-16T22:20Z → 2026-11-17T10:08Z.

- **`forge-findings.md`** — the report. Opens with the decisions table and the gate caveat; §1–§5b and
  §8–§10 are about the engine, §6 and §7 are about how to measure it.
- **`test-matrix.md`** — the same run enumerated. 118 rows: what works, what fails, what is conditional,
  what was never tested and why, and 35 instruments that reported something false.

Engine under audit: `forge-combo29` at commit `6b98f217`. Build `e06310ec…`, `/usr/bin/g++` 13.3.0,
`-DFORGE_MARCH=x86-64-v4`, Release, `Threads 1` unless a row says otherwise.

Read `test-matrix.md` first if you want a checklist; read `forge-findings.md` first if you want the
reasoning. Where they disagree the findings document is the authority, and it should not happen — both
were generated from the same tally.
