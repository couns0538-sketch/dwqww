# Draft bounded hosted Linux pilot

Prepared outside the checkout. No workflow, API, network, build, engine, or user-repository action has been performed. A disposable local Git repository reproduced and verified the preservation-command fix. Root review and the final candidate source freeze are mandatory before use.

Install mappings after review:

- `forge-hosted-strength.yml` -> `.github/workflows/forge-hosted-strength.yml`
- `run_hosted.py`, `protocol.json`, `openings/`, `provenance/` -> `.github/hosted-strength/` with the same relative paths.

Candidate is frozen at2c0c7efa49023d8e3f49de3f5596f333a3f01202 in both workflow and protocol; root must confirm all source gates and review before launch. Change the pending status only after that review. Baseline is Forge6.4.4 source816423b1ddac23a00244449deef59dba736055a9. The workflow rejects an unresolved/mismatched SHA. Push trigger matches only `forge/hosted-strength-*`; results branches do not trigger a new run. One attempt only. No retries or fallback authentication/infrastructure.

Workflow: Ubuntu24.04, hard24-minute job cap, 4-minute build/test step bound, identical GCC14 Release flags for both sources, full CTest, pinned native Fastchess60d7a7a, then one-CPU calibration followed by fixed-node AA readiness and one capped equal-clock SPRT. Builds finish before timing. A failed timing gate permits no games. Any interruption, incomplete/abnormal PGN, dirty log, changed input or failed independent audit prevents acceptance.

Calibration is a new prospective host-specific test: two excluded baseline fresh-process warmups and three baseline/baseline bench11 pairs. It does not inherit a pass from the failed cloud host. All commands must produce419798 nodes. Both high-resolution processCPU and externalwall must pass frozen median[.95,1.05] and every-ratio[.85,1.15] gates within30seconds. No candidate-vs-baseline performance test is run.

The unchanged match runner uses one thread, Hash32, OwnBookfalse, restarton, overhead10 and serial color-swapped pairs. Its CLI does not explicitly set Ponderfalse: the wrapper captures both UCI handshakes and requires their advertised defaultfalse. Fixed-node AA uses its existing smoke-only maxmoves200 guard. The strength SPRT has no maxmoves/adjudication, uses tc2+0.02, and is capped at500pairs or16minutes. The first48pairs are a prefix of this same test, with no screening decision/reset. Runtime order is the unchanged runner's deterministic seed permutation, recorded in `provenance/runtime-order.json`; it differs from the initial corpus-selection order.

The wrapper does not trust run_match.py's known final-LLR parser weakness. It independently requires complete normal PGNs, exact opening prefix, matching native pentanomial counts, and uses windows_validate.audit_likelihood(...,cap=500), including final finite LLR, unique native decision and independent GLR boundary crossing. A time-capped attempt is inconclusive; original records are not trimmed or pooled. Artifact upload and a fresh result-branch push are attempted with always(); a platform hard cancellation can prevent these cleanup steps, so they cannot be guaranteed after runner loss.

Opening provenance:4 AA plus500 SPRT positions, disjoint and unique; all retain corpus EP='-'. Excluded5973 canonical historical positions from29files including portable AA/pilot/SPRT and workspace validation selections. 949 eligible unique corpus positions remained before selecting504. Full source/exclusion hashes and selection method are in `provenance/`.

The sixteen-minute SPRT is likely to end inconclusive. An H1 boundary concerns this opponent/control and does not prove a +5 Elo gain. Results are native hosted Linux evidence only, with no native Windows/Ryzen claim.

Final preparation checks: original orphan preservation command reproduced exit128; fixed --ignore-unmatch command exits0 and commits only hosted-results. Evidence is in provenance/git-preservation-smoke/{result.json,commands.json,commands/}. Preserve the throwaway-repo locally, but EXCLUDE that nested repository when staging/copying the package into Git. The package checksum manifest excludes throwaway-repo.

Wrapper captures host context before/after, checkpoints AA success before SPRT, and polls every0.5seconds for non-normal PGN terminations or console/log warnings/errors. Detection stops the owned group and makes the attempt failed/inconclusive without a reset. Workflow records source-commit/exported-file maps, engine/library hashes and LastTest logs. GCC14 fallback installation is bounded inside the existing4-minute build step.
