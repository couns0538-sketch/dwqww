# Outside-production promotion-recapture prototype

The narrowly guarded fallback passes the bounded API gate. Production source16,
Git, the Board header/class definition, original core, and previous research
artifacts remain untouched. This is a prototype result, not a source17 switch.

The patch inserts one anonymous-namespace helper using public Board getters and
one dispatch before the ordinary threshold bounds. The source16 swap loop and
threshold logic remain byte-for-byte unchanged outside that insertion. No class
definition or header changed, so replacing only Board.cpp in a copied core does
not mix inconsistent Board definitions across translation units.

The guard requires a last-rank target and a live original pawn of the promoting
color geometrically attacking it after excluding the initial origin/captured
square. Initial king/castle handling is preserved. The rare helper retains the
source16 pin mask, LVA/lsb choices, ray updates, and terminal king-defense test,
adds promotion material plus the resulting queen victim value, and folds a
bounded 64-entry full gain stack without the old rare-path threshold shortcuts.

The immutable 316-case baseline and ten new research cases were frozen before
the only build/run attempt. Two original initial-illegal moves are excluded from
oracle claims and retained in the ordinary-path parity check.

- All 324 legal cases match frozen oracle values and 6,480 fixed-grid answers.
- All 30 adjacent-bracket answers on the ten new cases pass.
- All 314 non-guard full output rows are byte-identical to source16.
- Twelve rows enter the fallback; eight source16 exchange mismatches are fixed.
- Both mirrored threshold-zero false negatives now return +500, matching oracle.
- Both mirrored false positives now return -600, matching oracle.
- The old inherited -400 versus -1200 controls now correctly return -1200.
- Pinned-pawn +500 and promotion/king-recapture +300 controls stay correct.

The new driver prints the existing twenty thresholds, actual guard
classification, and adjacent brackets. Its source16 twenty-threshold prefix
matches the previously frozen actual output. The independent source audit found
no issue in stack arithmetic, pin/LVA behavior, the guard, king termination,
array bounds, or header/ODR consistency.

Only one Board object and one diagnostic driver object were compiled,
sequentially. Only Board.cpp.o differs in copied core members. The two finite
API invocations used 0.472786 seconds of a 30-second operational budget, with a
10-second cap each. Every phase exited zero; no retry, bench, match, or
additional engine invocation was run.

SOURCE-FREEZE.json, inputs/, attempt1/record.json, attempt1/comparison.json,
raw outputs, patch, exact Board sources, source/header TARs, objects, copied
cores, executable diagnostics, and drivers preserve the result. The previous
research capsule remains unchanged at SHA-256
9f2b0d81d053c433bd3640ad5f6cefb8cbd04e1f3bdf7f02ead244525e7963f3.

No runtime/NPS/Elo gain is claimed. LVA/lsb and optional-stop approximations
remain. Full engine/sanitizer/Windows gates and any integration decision belong
to a separately frozen candidate. The capsule manifest hashes every payload;
the archive verification receipt is outside the ZIP to avoid self-reference.
