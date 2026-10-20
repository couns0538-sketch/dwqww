# Legal witness: correctness passed; speed and strength inconclusive

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

Kernel compilation and emitted dispatch checks passed. All60 paired API-kernel
blocks completed with matching checksums, but preregistered AA noise failed:
CPU ratios0.736..1.444. No speed acceptance is made. The prepared pinned
whole-engine screen was NOT run because this prerequisite failed; no retry.
Original records are in [kernel checkpoint](kernel-attempt1.zip). The public-helper
reference has different translation-unit inlining opportunities; kernel ratios
cannot establish whole-engine NPS or Elo even with good calibration.

Seven Windows functional/signature checks passed under Wine from frozen82cd
source, including18,947 comparisons and351063bench nodes. [Windows ZIP](../../releases/forge-6.4.5-candidate-windows-zen5.zip):
SHA256 `336624514ae0c93f5ee5b35a5a34e3422b4d9ea6855cd04aeb22cdd03f08dd4f`.
Independent package review passed; native Windows/Ryzen tests remain pending.

Decision: retain as a correctness-tested isolated speed candidate, with performance
and strength inconclusive. Zero new match games; no Elo estimate. Next experiment:
reuse the reviewed upstream qsearch query deferral in another isolated branch.
