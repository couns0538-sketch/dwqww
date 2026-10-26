# Forge S06 development report — 2026-10-26

Implemented the ordered handoff's offline gate miner and triage tool. No engine
source, network, search, evaluation, accepted lock or running training changed.
Accepted h256_e12 remains code `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792`
with explicit net SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`
(MD5 `6d22f612c855e17c62d396d32da99ea4`). Tool work continues from preserved
S27 `fbe6bb61b2da1913ad6916b6d0192f39c06143c5`, with intermediate S06 checkpoint
`5fe0d6fc37abdf5856d12d0aea6f9f91fc3bb40a` on `forge/sol-pack31-20261025`.

The tool reports candidate W/D/L, six pair categories and five bins, approximate
LLR for explicit hypotheses, descriptive Elo/95% uncertainty, observed TL/crash,
opening/explicit-phase splits, and CSV triage. Raw records and inputs survive
faults. Metadata pools remain separate. Engine patches/diffstat: **none**.

| Check | Verdict | Evidence / limit |
|---|---|---|
| Full final offline suite | PASS | 76 tests; root validation and independent review |
| Independent review | PASS | 30 original/adaptive checks; 200 Decimal statistics cross-checks |
| Final source/test stability | PASS | All 9 executed source/test/driver digests equal before/after validation |
| Standalone flat delivery | PASS | All76 tests with PYTHONPATH empty; source/test hashes unchanged |
| G95 supplied counts | PASS | +0.231624 ±8.529388; approximate nElo LLR -0.561985 |
| G100r supplied counts | PASS | +10.889880 ±8.379770; approximate nElo LLR 2.219838 |
| G119 supplied counts | PASS | +9.498939 ±8.841725; approximate nElo LLR 1.727094 (target1.72 within.01) |
| Newer supplied CSV | PASS | UTF-8 BOM; all35 rows parsed; no pooled rows or verified acceptance |
| Historical original178 parser replay | PASS | W66/D44/L68;89 pairs; bins[1,10,68,10,0]; PGN/log agree |
| Historical timeout parser replay | PASS | Expected exit1/BLOCKED, original Candidate timeout1 retained |
| G104 actual paired likelihood | UNVERIFIED | Actual paired counts/raw gate evidence missing |
| Current gate raw PGNs/logs, legality, confirm/lock | UNVERIFIED | None supplied/observed; no live PC audit |
| Engine bench/perft/FMA/CTest/sanitizers | UNVERIFIED this job | Not rerun: no engine modification or executable launched |
| NPS / new match / Elo gain / native Windows | UNVERIFIED | No speed measurement, new games or adoption claim |

All three count cases use the supplied paired Gaussian nElo approximation, not
an exact arbitrary-profile Fastchess likelihood. Estimates and fixed 95%
normal/delta halfwidths are arithmetic checks on supplied counts, not newly
measured gains. Zero variance and boundaries are explicit nulls; no fabricated
uncertainty, W/D/L or PGNs. Wald decisions never authorize acceptance.

The supplied 13:35 CSV supersedes older missing-count notes: G104 W/D/L is
130/497/71 at698 games. Its reported LLR2.95 cannot be independently reproduced
without the actual pair profile. The explicitly **synthetic illustration**
[9,33,203,98,6] gives +29.438009 ±13.220604 (delta method; transformed-score
interval [16.253466,42.707721]) and Gaussian LLR3.045415. It is not the actual
G104 profile and does not verify the reported2.95. No force-fit was performed.
The same CSV historically reports G120 H1 at928 games W184/D623/L121, conc7;
this is source-reported metadata, not a current live/confirm/lock conclusion.
It is not pooled with G119 conc5 or other seeds/concurrency.

The historical178-game run is existing 2026-10-19 evidence, originally H0 at a
fixed10,000-node protocol. S06 only reparses its unchanged PGN/console; zero new
games were played. Its old outcome/estimated strength does not transfer to the
current lock. The original timeout replay validates rejection and does not
identify or fix that forfeit's cause.

Preserved failed approaches include statistics fixture/setup corrections,
initial missing-feature REDs, non-normal termination handling, malformed FEN,
run identity and variation-comment faults, decreasing/overwritten snapshots,
malformed result/fault/player lines, and CLI status propagation. The complete
raw log history and available prior source versions are in the reversible
archive. Superseded 73-test validation is not claimed as final76 coverage.
The old cumulative-log test fixture ended its first match before appending a
second summary; it was corrected to one live cumulative match and gained an
explicit PARSED assertion. Existing failures were not hidden by filenames.

All code is original and idea sources are listed in the README. Existing recovery,
tool-routing, validation and TDD skills were reused. No duplicate skill or global
installation was made. No callable optional CodeRabbit/skill-creator connector
was available; native Python and an independent reviewer provided the evidence.

Next: follow the saved resume order with S33 (+S48), then S07. Recover their exact
spec/input hashes and existing status first; do not reopen completed S02/S03/
S28/S04/S05/S25/S27/S06 or infer an accepted engine change from tooling work.
Disk remains tight; no large build/training job is pending. All owned subprocesses
for this cycle are closed. No background continuation is claimed.
