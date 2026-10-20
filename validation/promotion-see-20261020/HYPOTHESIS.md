# Forge6.4.17 promotion-recapture SEE

Baseline source553caef144ae2e1b696ba35d7a0eb1a50a03fde9, preserving all16/15
and newer accepted integration356e863 work. This experiment changes only SEE
handling of exchanges where a later pawn capture may promote. No network,
evaluation weights, search parameters, TT or time-control changes.

Legacy SEE uses the pawn's100value after a recapture on its last rank and
omits the800promotion gain. Its threshold shortcuts can reject a sound queen
capture at0(-100 versus legal exchange+500) or accept a losing knight capture
(+200 versus-600). The frozen legal same-target exchange trees establish these
specific errors, not universal minimax correctness of an LVA approximation.

Use one rare guard before those shortcuts: last-rank target, nonking initial
mover, live geometrically attacking pawn of that rank's promoting color,
excluding initial consumed origins. The rare path preserves16pin masks,
LVA/lsb order, x-rays and terminal king test, accounts for queen-promotion
material and the following queen victim, then folds a64entry full gain stack.
The ordinary16body remains byte-identical. No Board header or class changes.

Actual baseline API research and reviewed prototype precede this application.
All324legal oracle cases/6480grid answers/30adjacent brackets pass;314non-guard
rows including2initial-illegal controls are byte-identical. Twelve cases enter
the guard, eight baseline value mismatches corrected. Two illegal initial
moves are excluded from oracle assertions. Immutable research/prototype capsules
and root byte-verification are in ../see-recapture-promotion-20261020/.

Permanent tests add five positions mirrored across colors to the existing23
cases. They verify exact exchange, zero/adjacent threshold answers and unchanged
FEN/key. Compiling these tests against frozen16core produces16expected failed
assertions; the same test object linked with reviewed prototype core passes.
Raw commands/outputs remain in native/permanent-{red,green}-attempt1/.

Next gates: frozen complete Release/ASan+UBSan/TSan builds and nine existing
CTest suites, actual targeted API against final core, Windows package checks,
controlled performance only where calibration permits, and a fresh equal-clock
SPRT if source/readiness gates pass. No source17full-gate or Elo claim yet.

Source16's original TSan batch remains FAILED8/9 due to initial15suciokdeadline.
One observed diagnostic did not reproduce it; cause remains unresolved. A new17
full-batch PASS would be new source coverage, not repair/proof about16's stall.
The unlaunched16strength package stays blocked and is not modified or retried.
