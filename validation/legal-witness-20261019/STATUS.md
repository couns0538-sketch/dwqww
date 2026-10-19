# Legal witness: Linux correctness passed, timing/Windows pending

Candidate6.4.5 source/tests `82cd2c24062d07cbacbe5b722b6ec0b718981abd`,
on `forge/legal-witness-20261019`, preserves the tested6.4.4 parent and every
prior candidate. Accepted integration remains `9108d012`.

One exact legal nonpromotion quiet pawn push witnesses nonterminality; failure
uses the unchanged complete generation fallback. No search values, pruning,
move ordering, NNUE weights or float operation order change.

Both the unmodified6.4.4 control and actual candidate passed18,947 Boolean and
state-preservation comparisons:23curated positions,10,000frozen openings and
72deterministic legal walks. Oracles use the old full-generation algorithm and
make/unmake king safety; shared generation/attacks limit their independence.
Release8/8 and ASan/UBSan8/8 passed, including perft,UCI,ponder,TT,rule50 and
validation tooling. Six cold/warm1T cases and bench11 match parent exactly;
Linux node signature419798. Original logs, commands and source/build hashes
are in [Linux checkpoint](linux-validation-checkpoint.zip) and its manifest.

Kernel harness compiles and emitted indirect dispatch checks pass. Measurement
waits for all other jobs to finish. API-kernel timing has translation-unit/inlining
limits and cannot establish whole-engine NPS or Elo. Windows checks/packaging
are running from frozen82cd source. No strength games or new Elo estimate exist.
Keep failed attempts; finish bounded kernel and Windows gates before the next
candidate. Native equal-clock/Ryzen testing remains independently required.
