# Forge S33 development report — 2026-10-26

Completed the finite-cap advisory planner. Accepted h256_e12 remains unchanged:
source1ab50b2dd64d9b2f752f7f1285f6968cad2fd792 plus explicit net
74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b.
No engine patch, new match, speed acceptance or Elo-gain claim.

|Check|Verdict|Evidence|
|---|---|---|
|Model/API/CLI tests|PASS|23 tests; output collision and dependency tampering regressions retained|
|S48 dependency tests|PASS|16 tests, including small synthetic API smoke|
|G95/G100r/G119 count-only fixtures|PASS|QA Gaussian nElo LLRs -0.561985/2.219838/1.727094 within.02|
|Six predeclared validation cells|PASS|20,000 trials each; maximum probability difference0.0078305 <.03|
|Complete required grid|PASS|630 cells,20,000 evaluations each; all seeds/layouts retained|
|Full-grid analytic agreement|PASS|Max0.0130866; zero cells above.03|
|Original terminal evidence audit|PASS|90 groups,1.8million paths,12.6million protocol terminal records recounted|
|Finite-cap/LLR mathematics review|PASS|Independent eigen-series, finite differences, LLR and all630 analytic checks|
|Numerical successor binding|PASS|24 functions/constants/RNG AST identical; old six-cell source/receipts retained|
|True+9.5 G119 cap-most-likely check|PASS|P(cap)=0.8177, P(H1)=0.1823 under [0,10]nElo/1500|
|Actual G104 paired likelihood|UNVERIFIED|Actual paired profile missing; no inferred counts accepted|
|Actual conc7/8 operating characteristics|UNVERIFIED|No actual profiles supplied; no pooling or substitution|
|Engine/runtime/Elo/PC acceptance|UNVERIFIED this job|Zero engine games or source changes|

The published table contains15 true logistic-Elo values (-5..30 by2.5), six
separate profiles and seven requested protocols. Three profiles use supplied
conc5 counts; three use independent-game draw-ratio models. Bounds are nElo,
not logistic Elo. Seven protocols share each group's modeled paths;12.6million
cell evaluations are not12.6million independent paths or played games.

Both worker processes closed exit0. All90 raw terminal archives and summaries
passed a separate forensic audit, including seeds/layouts, exact probabilities,
mean/median games, SE/Wilson intervals and1,890 conditional bias sets. No
non-finite terminal estimate occurred. The full-grid maximum analytic difference
is at G119/true-2.5/[0,10]/3000. This validates the stated approximate model's
agreement, not arbitrary native Fastchess likelihood or error guarantees.

The original six-cell run used b04af9f source. Shipped planner
008819d5387cdd5ac5d512bb2ebafd09f141aafc9b6904cba2f73a8373634d03 adds
safe NEW-output handling and hash-pinned dependency lookup. Exact numerical AST
equivalence was independently verified; those120,000 trials were not rerun or
reselected. The complete grid executed the shipped008819d source directly.
S48 dependency SHA21713b327007b0cda450200e172f6affb27cd65ac10e26ed8680d9447669d855.

G104's actual paired counts remain absent. The explicitly synthetic example
[0,44,219,75,11] gives approximate LLR2.948544 at698 games and [0,10]nElo,
illustrating a possible LLR; it is not the observed profile and does not reproduce
all reported W/D/L/Elo/CI. The earlier S06 example [9,33,203,98,6] matches its
W/D/L and rounded Elo/CI but gives approximate LLR3.045415. Neither validates
the native2.95 or justifies replacing missing evidence.

Three separate one-page ADVICE documents discuss net, search and speed designs.
No live gate or stopping rule was changed. Narrower hypotheses are not
automatically more decisive at a fixed cap; the complete table preserves every
cell rather than selecting favorable forecasts. Same input/seed/layout/version
replays deterministic model output; execution wall times and UTC are provenance.

All initial REDs, negative controls, source versions, corrected API/layout/CLI
failures and original validation results are preserved. The existing project
strength-validation skill was extended with an explicit producer-schema receipt
and checked prepare-before-mutate sequence after a cache-preflight field error.
Before SHA f874b2e3546ce8124eff95dcfa99685f25a710139bb836a27d4b01b1df78f6c2;
after81e78395d3dc0e9a4c77d27540eb5e845473982ad794fb8200c58172e0d75c24.
Three baseline field errors and corrected real-producer controls are recorded.
This is a local reference/workflow proof, not a new/global skill installation
or fresh-agent pressure-test claim. No duplicate skill was created.

S48 is the paired add-on; continue S07, S26 and the full saved54-job queue.
S07 native checks are running independently after the modeled CPU jobs closed.
This report does not imply the remaining job pack is complete.
