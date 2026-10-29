# A1 advertised-option contract test

Prepared for the merged R3 integration contract. Native execution is pending the lead's GO after the R5A merge. This file is a test specification, not an assertion that the current engine passes.

```bash
python3 astra3/integration/tests_pending/option_contract_tests.py \
  /absolute/path/to/forge --hidden 256 \
  --output-root /absolute/path/to/new-or-existing-evidence-root
```

Each invocation creates a unique child evidence directory and preserves original `stdin.bin`, `stdout.bin`, and `stderr.bin` per child process. Streams are binary, kept separate, and hashed; the JSON result is an interpretation, not a reconstructed engine log. Reader/decode errors, a changing executable hash, missing responses, unexpected exits, duplicate advertisements and duplicate active fields fail. The tested executable's hash and the reused Python reader/writer/driver hashes are recorded. The driver never edits engine files or existing evidence and never stops another process. `quit` and a bounded emergency kill apply only to its own child.

The existing `tools/uci_regression.py::Engine` supplies protocol deadline waits. A small subclass adds binary stream capture. The exact repository `tools/nnue/forge_nnue_v2.py` writer and reader generate/check zero-weight residual, standalone, threat-input and pawn-pair-input `.fnn2` fixtures at the specified build width. The test does not guess a network format or substitute another engine's code. These are synthetic activation fixtures, not candidate networks. A path with spaces is intentional.

## Dynamic advertisement coverage

Every actual advertisement is classified. Fresh processes test each ordinary spin/check option at a legal nondefault value, require its exact name/value in one `info string active:` line on a one-node restricted search, then reset it and require no active line. Missing integrated `SmpV2`, `TmSoftHardClamp` or `SingularV2` fails. The test does not hard-code the total number of advertised tunables: newly advertised ordinary options are automatically covered, while an unknown string/combo/button fails classification.

The explicit whitelist is narrow and uses exact names:

- `Hash`, `Threads`: resource controls; the probe uses Hash 16 and Threads 1.
- `Move Overhead`, `Ponder`: protocol/time-control capability settings outside the active-search-options contract.
- `OwnBook`, `Book File`, `Book Depth`, `Book Variety`: opening-book controls; book lookup is disabled for search probes.
- `Clear Hash`: stateless button with no nondefault persistent value.
- `Profile`, `DebugSearchDelayMs`: optional instrumentation/test scheduling, not active search changes.
- `BundlePreset`: a macro, checked separately against the exact expanded option settings for OFF/B1/B2/B3/B4/N1. Literal `BundlePreset=...` is not required in the active line. An added preset fails until its expected expansion is specified.

`NNUEFile`, bucket settings, feature settings and `PureNnue` receive compatible `.fnn2` fixtures. Their dependency options are set before `isready`, matching the engine's documented fail-closed loader. The expected active line includes those explicit dependencies. Returning the whole dependency group to defaults must remove the line.

`SyzygyPath` is not a blanket whitelist entry. Its nondefault path is deliberately absent: the test requires a zero-table diagnostic and either omission from the active line or a `(failed)` marker. **Successful real table loading remains UNVERIFIED**, because no tablebase files are supplied. An absent NNUE file must fail closed with the existing exit code 2 and an explicit error; it must never appear successfully active or silently search fallback. `(failed)` suffixes are accepted with or without a separating space.

## Preset/diagnostic coverage

- Every advertised preset expands correctly and preserves independent SmpV2/TmSoftHardClamp flags. N1 then OFF returns all preset-owned fields to defaults.
- Exactly seven owned fields may report `override <name> after preset`: CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2, SingularV2. Changed owned values report once; no-op, invalid, and post-OFF changes do not.
- Resource controls and all dynamically discovered non-owned ordinary options never report an owned override. Buttons/unknown names do not either.
- A no-op TtPruneV2=true retains its B1 attribution; a real false→true change clears it.
- A valid preset produces the CorrMargins/TtPruneV2 warning after its acknowledgement (and must respond without deadlock). Invalid presets and N1 refused under CorrExt emit no combination warning and leave the expanded search state unchanged.

## Limits

This is native protocol and settings evidence. One-node restricted searches establish reachability and diagnostics; they do not establish algorithmic strength, numerical evaluation correctness, perft, exact benchmark identity, SMP race freedom or speed. Those are separate integration qualifications. Build-time options absent from the tested executable are not exercised; if a build advertises them, the ordinary echo test requires them to activate truthfully. This script does not read or write live gate state and runs no matches.

IDEA_SOURCE: Forge R3 A1 / Code Review findings in the user-supplied 2026-10-28 handoff; Forge's existing Engine protocol driver and FORGENN2 schema/writer. No external engine implementation or tuned constants.
