# Pin-aware SEE prototype — bounded API correctness only

Frozen parent source is `21538ec5416c909fc98a08688242a0b3b9710b25`
(6.4.14). Production source, Git, and original Release core were not changed.
The applied patch exists only in the exported
`/workspace/pinned-see-prototype-20261020/source/src/board.cpp` and is preserved
as `pinned-see.patch` and `candidate-board.cpp`.

Every non-king geometric recapturer is tested with its origin removed from the
current virtual occupancy. The exchange target stays occupied, permitting legal
captures along a pin ray. The existing own-king attack helper receives
`removed = ~occupancy | target`; this masks consumed original pieces and the
captured victim's ghost at the target. All same-value candidates are filtered
before the original least-value/least-square choice. The existing king branch,
initial promotions, en passant, recurrence, and early bounds are unchanged.
Initial move legality remains the caller's responsibility.

`prepare_prototype.py` compared all complete build-source files to source215,
exported them, copied the current Release archive, and compiled only Board.cpp
serially with the exact existing Release flags. `build-record.json` records the
original and candidate core member hashes: only `board.cpp.o` differs. Two tiny
diagnostics were linked against the original and copied candidate archives.
Both complete build-source exports are saved as tar files; historical release
and validation trees are outside those source exports.

The original 300-case corpus was fixed before the diagnostic run: original12,
32 mirrored authored controls, and the first256 legal captures from seeded
valid sparse positions. Four supplemental dynamic diagonal controls were then
added without changing any original input or expected result. Independent
python-chess1.11.2 legal-capture minimax preserves the complete exchange trees.
All302 legal initial moves agree with the candidate at20 thresholds and in
exact `static_exchange`; two initial-illegal captures separately agree on
legality and are excluded from SEE correctness assertions. Legal recapture
sets also agree. The baseline has8 exact oracle disagreements, all corrected.
No candidate mismatch or new/worse mismatch was found.

Exact authored assertions are runnable with `python3 assert_authored.py`;
`python3 assert_authored.py baseline` is an intentionally failing RED assertion
against the actual frozen215 baseline. Inputs, independent oracle, all raw
stdout/stderr, command return codes, flags, objects, cores and diagnostic
executables are preserved. One initial supplemental FEN incorrectly left the
nonparticipating black king already checked; the independent validity guard
rejected it before engine execution. Its original script/failure is retained;
only that king square was corrected (a7 to h7).

Representative exact expectations below apply to both colors. Every authored
legal case additionally asserts legality, its complete first legal recapture
set, exact exchange value, and every saved threshold.

| Control | Expected exchange | Baseline | Candidate |
|---|---:|---:|---:|
| Original orthogonal absolute pin | +100 | -800 | +100 |
| Diagonal absolute pin | +100 | -800 | +100 |
| Newly exposed orthogonal pin | -800 | -500 | -800 |
| Newly exposed diagonal pin | -800 | -300 | -800 |
| Ghost target rook removed | -300 | -300 | -300 |
| Ghost target bishop removed | -500 | -500 | -500 |
| Pinner leaves original square | -200 | -200 | -200 |
| Legal along orthogonal pin | -300 | -300 | -300 |
| Legal along diagonal pin | -500 | -500 | -500 |
| First knight pinned, second legal | -800 | -800 | -800 |
| Legal / protected king recapture | -800 / +100 | same | same |
| En passant, no / rook recapture | +100 / 0 | same | same |
| Capture promotion Q/R/B/N | +1300/+900/+700/+700 | same | same |
| Quiet promotion Q/R/B/N, rook recapture | -100 | same | same |

This is a prototype correctness screen. Per-attacker full king attack lookup
adds unmeasured cost; its performance and playing-strength effect remain the
largest practical risks. Full candidate Release/ASan/TSan/CTest and search gates
are still needed before integration. Original SEE least-value and recapture
promotion approximations remain; a bounded corpus is not universal minimax
proof. No performance trial, NPS claim, strength match or Elo claim was made.
Execution elapsed times are retained solely to account for the120second
engine-execution budget.
