# Next bounded search experiments

Initial read-only research against frozen 6.4.12 source
`8865666cc0ab4961cd507bae40ff6ce44e9319df`, 2026-10-20 UTC. A subsequently
authorized tiny Board diagnostic was compiled against the immutable existing
Release core; see the executed follow-up below. No production edits, engine/core
rebuilds, timing trials, games, Git mutations or network operations were
performed. The separate TT package remains frozen. Rankings
reflect source signal and bounded engineering cost; no Elo gain is measured.

## 1. Absolute pins in SEE recaptures

`src/board.cpp:836-890` derives `stm_attackers` geometrically, selects the least
valuable attacker and updates occupancy. There is no test that a non-king
recapture exposes its own king. This is a concrete tactical approximation
error, not evidence that Forge emits illegal moves. SEE controls capture
ordering (`src/search.cpp:352-355`) and qsearch/main pruning (`:814`, `:1054`).

Independent python-chess legality checks, preserved in `pinned-see-oracle.json`,
confirm the valid position
`4k3/4n3/8/3p4/8/8/8/3QR1K1 w - - 0 1`: Qd1xd5 is legal and wins a pawn
without any legal recapture on d5. Ne7xd5 is pseudo-legal but illegal because
Re1 pins Ne7 to Ke8. The current source recurrence predicts
`see_ge(Qxd5, 0)==false`: pawn100, queen900, swap800; geometric knight300
toggles result to0, produces swap-500 and terminates false. Removing Re1 is a
verified control where Ne7xd5 becomes legal. The initial source prediction was
then tested against the actual frozen core, as recorded immediately below.

**Executed follow-up:** `pinned-see-red/` preserves a12case public Board API
diagnostic, compiler/commands/deadlines, input hashes, untouched actual core and
driver bytes, stdout/stderr and independent legality oracle. Two mirrored
absolute-pin captures reproduce actual `see_ge(0)==false`, `static_exchange=-800`
although the legal exchange gains100 and has no legal recapture. Eight legal
controls agree at threshold0, including unpinned, along-pin and working king
recapture cases. Two initially illegal captures separately establish that SEE
does not validate its initial move; main/qsearch perform that legality check.
The diagnostic exits0, while the explicit expected regression assertion exits1
and its original failure is preserved. The verified392203byte archive contains
all25 original core/header/source/driver/evidence files; SHA256
`5cd5a9d6c39273f113f72d1603c28d8d044d3a56ed820b4d4a9ab573e535cdaa`.
This remains a demonstrated pruning false-negative risk, not an Elo result.

Candidate: exclude illegal pinned recapturers using current exchange occupancy
and king rays. Do not reject every pinned move: moves along the pin ray can
remain legal; a pinner can disappear and new pins can emerge during exchanges.
Tests must include diagonal/orthogonal pins, legal along-ray captures, removed
pinners, king recaptures, en passant and promotions. Avoid calling a complete
legal-move generator for every SEE attacker. Count affected actual pruning
decisions and cost before a fresh paired equal-time SPRT. A legal-capture
minimax oracle is useful for this bounded tactical corpus; generic SEE is
still a selective approximation and not expected to solve all chess tactics.

No existing applied pin-aware SEE patch was found in the inspected candidate
refs or commit subjects. `include/forge/bitboard.hpp:136` already supplies
`between()`. Reuse current Board occupancy/king-square helpers. This candidate
offers a more concrete starting point than retuning a historical neutral knob.

## 2. Make double-extension accounting follow the current path

`src/search.cpp:1069-1083` tests mutable `ss->double_extensions <= 6`; a double
extension sets it from the parent plus one, a nonpositive extension copies the
parent, and a single extension leaves the field unchanged. SearchStack slots
are reused across siblings/iterations and initialized only at full-search
setup (`:1321`). Thus the tested value can belong to another path. Symbolically,
parent count7 and a reused current slot0 can authorize count8; a single check
extension can also carry an unrelated previous sibling's count instead of the
parent's. This is source-grounded bookkeeping inconsistency, not a reproduced
crash or strength finding.

Candidate: capture the inherited path count in a local value; test that value
for double-extension eligibility and assign the current frame for every actual
child as inherited plus `(extension==2)`. Same-ply singular verification can
mutate frame fields, so use a stable local inherited value rather than relying
on the frame remaining unchanged. Preserve the existing threshold/margins and
change only accounting. Add a real-search trace/regression proving that each
child count equals the parent's path count plus its own double extension,
including sibling order, check extensions and excluded-move verification.
This changes the search tree, so require correctness, controlled node/cost
screens and fresh equal-time SPRT; lower depth or fewer nodes alone is no gain.

No prior applied patch for this field was found in the inspected refs/history.
The prior `SingularMargin=1` experiment is a different hypothesis and remained
inconclusive/not adopted; do not rerun it as an accounting fix.

## Existing work checked and excluded

- Newest `origin/forge/research-20261020-{0915,1015,1115}` all resolve to
  `356e863dbd86d2ce24b8ee9486d7406f1d525480`; they contain no newer distinct
  strength-research publication. The separate time-origin reconciliation is
  already assigned and is not a third experiment here.
- `origin/forge/research-20261020-0815`, commit
  `b0ed22d` / `validation/hourly/2026-10-20-0815/RESEARCH.md`, discusses the
  older clock origin, TT snapshots and rule-50 context. These are already
  repaired or being reconciled in the present lineage; no reuse as new work.
- `origin/forge/research-20261020-0515`, commit
  `761ae645cf1db4979b78357a6bd27752aafa0084`, reports TT, SMP node-budget
  characterization and stable root effort. `origin/investigator/hourly-20261020-0500-node-budget-audit`
  resolves to `d2d8dfe4fe9df20697f993bf44dea0f65e57ba39`; its actual patches
  `validation/hourly/2026-10-20-deadline/probe-deadline{,-tests}.patch` repair
  diagnostic deadlines, not the engine's node budget. No new applied engine
  improvement can be inferred from those branch names.
- `validation/release-6.0.0/EXPERIMENTS.md` already records neutral/inconclusive
  capture futility, fail-low continuation bonus, earlier ProbCut, smaller RFP,
  stronger LMR history and quiet-check trials. Preserve them and prioritize
  the two concrete source issues above. No NNUE retraining, duplicate solved
  TT/rule50/stalemate/lazy-check/root-effort/OwnBook work or speculative feature
  accumulation is proposed.
