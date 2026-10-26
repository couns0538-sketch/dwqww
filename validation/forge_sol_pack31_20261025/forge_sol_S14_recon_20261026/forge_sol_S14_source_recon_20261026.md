# S14 read-only source recon — 2026-10-26

Recommendation: **no duplicate engine patch**. The supplied bases already have fixed MovePicker storage and an O(1) square mailbox. The remaining distinct work is a validation-only allocation/order oracle. No implementation was started for S14, and no compiler, engine, benchmark or match ran.

`MoveList` is a fixed 256-element array (`board.hpp:45–74`); the picker owns fixed scored/bad-capture/move-list/check-mask buffers. B retains its existing capacity256 bad-capture buffer/assertion; L/Lprime retain64. That known buffix difference must not be silently normalized. Board::piece_at (`board.hpp:145`) indexes squares_[64] (`:170`); moved_piece (`:161`) delegates to it. Global piece_type (`:199`) already runs in O(1) with a constant-modulo enum conversion, rather than scanning bitboards. Adding another mailbox or recoding the already-reviewed ptype arithmetic/table variants would duplicate prior work.

Fixed buffers alone are insufficient to prove no allocation. I inspected the called sort and selected scoring/generation/SEE/attack paths. MovePicker uses **std::sort**, not stable_sort. Installed GCC14's std::sort routes through in-place introsort, insertion sort and an in-place heap fallback with local Scored moves; selected Forge callees use fixed arrays and indexed reads. Worker history allocation and Board history-vector reserve happen during setup, outside picker construction/next. These are source facts, **not a native allocation-zero measurement** and not a guarantee about an uninspected Windows library.

|Base|Full search.cpp SHA256|MovePicker lines|Exact MovePicker-lines SHA256|
|---|---|---:|---|
|L|44680416e008f4ccc0ac7d95a1452ae3db34459f945ea3311dc456536fcb0e55|319–556|5b087d02ab3f5104026ef9adf15a48e776336ae9eb5b60ca27963dd814cf7b3d|
|Lprime|44680416e008f4ccc0ac7d95a1452ae3db34459f945ea3311dc456536fcb0e55|319–556|5b087d02ab3f5104026ef9adf15a48e776336ae9eb5b60ca27963dd814cf7b3d|
|B|8cf398b9ee92d5daeefa09be78665b4d84f5ee630cf7b50cd7eec6ef2d91c11e|319–559|81ed79d4aef4516a4bd8429bd543631acf6f15bbc47fad924be9636f0d255e15|

Common board.hpp SHA256: `5b42d3557730edc65f795a097e45d18a3cb621d56bdfa8b379773bb496204c77`. Complete exact per-base source hashes, relevant function/line-range hashes, installed-library source hashes and four historical CR-note hashes are in `forge_sol_S14_source_recon_20261026.json`.

The earlier CR-passed speedmp/mp2 work already covers scoring hoists and piece_type lookup; speedstack/ptype covers alternative type conversion. Their review status and historical timing prose do not mean those patches are applied to these supplied trees: the actual code still has the original piece_type modulo and no QuietScorer. Do not resubmit those ideas under an S14 name or treat old evidence as a new measurement.

A reusable actual-MovePicker oracle already exists in `validation/lazy-movepicker-20261019/differential-attempt1.zip` (archive SHA256 `2e78c6e9b85ffd085d61ce5020a5e711117db0ec3054f90681e67f545cb04a33`). Its `harness/picker_differential.cpp` has SHA256 `99b2a12b2bfccaf087ab270cdea64828c9064b70dffd0cf9874bd699d8703023`; archive and selected member hashes match the original receipt. It includes actual frozen search.cpp and seeds histories, TT moves, killers, countermoves, dynamic quiet skipping and parent-state restoration across six modes. Its historical60138 rows concern6.4.6/6.4.7, **not current h256 validation**. It hardcodes10000+23 cases and lacks scoped allocation observation.

The bounded next step is in `forge_sol_S14_validation_only_plan_20261026.json`: reuse/adapt that own-project diagnostic for20 fixed supplied FENs and64-pick prefixes; count only construction/next allocations; keep formatting, setup and make/unmake outside the window; add meaningful allocation/dump mutation controls and mailbox consistency checks. The proposed20 FENs are recorded for review, not tested. Native execution stays after S11–S13 and a root grant. If the existing goals validate, S14 contributes no new engine code to S29. If observation demonstrates an allocation, isolate its real cause before proposing a fix.

All native node/perft/CTest/allocation/speed/Elo conclusions for S14 remain **UNVERIFIED**. Selected source inputs were unchanged during this recon. No Git mutation or duplicate skill was created. Stop before tool/engine implementation until root reviews the source findings.
