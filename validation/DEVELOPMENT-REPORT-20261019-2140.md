# Forge development report — 2026-10-19

Accepted integration remains **9108d012526be80c6d163f7cab684e6acd9abf8d**.
Latest isolated correctness candidate: **6.4.8**, source
**7125b3379a850de34041d42529cf95993607f93c**, published on
forge/root-effort-20261019. No accepted equal-clock Elo gain or Stockfish superiority.

| Candidate | Implementation | Verified result |
|---|---|---|
|6.4.5 /82cd2c2|Exact legal pawn witness before unchanged full fallback|Parent and candidate18947Boolean checks; exact parent search parity|
|6.4.6 /4e15dea|Defer pure qsearch gives_check until its use guard|Actual checked-evasion regressions and exact parent parity|
|6.4.7 /2c0c7ef|Initialize direct-check masks at quiet/evasion generation|60138actual ordered-picker rows,9590268bytes exactly match parent|
|6.4.8 /7125b337|Key cumulative root effort by full Move identity|All28actual-iteration counters match independent child-event sums; c3d5correct601instead of1355mixednodes|

All four preserve accepted residual NNUE weights and previous candidate repairs.
Each passed **Release8/8 and ASan/UBSan8/8**, including core/perft,TT8,rule50,
18947legal queries,UCI,ponder and support tooling. Each passed seven Windows
Wine checks and independent artifact audit. Root648audit52/52; offline648bundle
43/43. GCC14.2 and LLVM-MinGWClang23.1.3 compiled completeC++20engines.

**Benchmark:** exact cold/warm1T parent signatures and bench11 nodes remain
419798Linux/351063Windows. **NPS difference is unverified.** Old full-engine and
fresh pinned-kernel AA controls failed on the shared Xeon host; no repeated A/B
claim. A separate hosted EPYC7763 benchmark AA passed, but candidate throughput
was not measured in that protocol. Counts/fewer calculations are not Elo proof.

**Actual timed match:** hosted run39325939081 compares647with644source816423b,
identicalGCC14generic-v3 builds,Threads1,Hash32,OwnBookfalse,restarton,2+0.02,
serial paired fresh openings; logisticSPRT[0,+5],alpha/beta.05. Both timing AA
controls and8normal readiness games passed. The16min cap interrupted game148.
Original PGN has147normal completedgames:62wins,43draws,42losses;73complete
pairs plus orphanround74. All20018matchplies and1048readinessplies replayed
legally with independentpython-chess. Strict whole-PGN acceptance fails.

Last native144game snapshot:60wins,42draws,42losses; **+43.66±28.69Elo**,
printedLLR0.79(independent0.789742). This is an earlier descriptive estimate,
not the final147recordestimate or an accepted gain. Complete73pair descriptive
GLR0.815077 is inside±2.944439; no H0/H1. Two stop/quit warnings at deadline
shutdown and missing final input rehash prevent a clean-completion claim. Actual
hosted executable bytes were not archived; recorded source/build/binary hashes
are consistent. All59originalsnapshotfiles match resultscommit
1e9361d0e35a17c0d63a90d9431a6bb875d0817d. No PGN was trimmed/reconstructed/resumed.

**Decisions:** retain all four correctness-tested candidates.647is promising but
SPRT-inconclusive;648has no strength games and no demonstrated actual changed
stop/Elo. No candidate is merged into accepted9108. Failed fixture/control/
packaging attempts and corrected false-positive package checks remain preserved.

**Deliverables:** [648WindowsZen5ZIP](../releases/forge-6.4.8-candidate-windows-zen5.zip),
SHA2564b4de385808f5a383aa60de6bfc09cf48c02e5d23c191624540026cdac95b55e;
[648offlineWindowsvalidator](../releases/forge-6.4.8-windows-validation-bundle.zip),
SHA256253f33c129c0f5d4301354f755e03e876c7a76c6da18e13307facaceba7b4e73.
Extract the latter and run run-validation.cmd; nativeAA/pilot/SPRT remain pending.
It compares648against the exact original6.4ZIP, a separate question from647vs644.

Source/evidence: [root648](root-effort-20261019/STATUS.md),
[hostedoriginals/audit](hosted-strength-20261019/STATUS.md),
[76-recordledger](EXPERIMENTS.json), [currentbaseline](../docs/CURRENT_BASELINE.md).
Next: longer preregistered647confirmation with fresh openings and enough complete-
pair headroom, then separate648time/strength and actualRyzen validation. Retain
real small gains and inconclusive promising work; preserve training infrastructure.
