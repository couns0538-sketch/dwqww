# Rule50 context: implementation checkpoint, not validated

Forge6.4.4 is isolated on forge/rule50-context-20261019. It preserves the prior
clock, terminal, underpromotion, SIMD and coherent-TT changes. The accepted
development branch remains unchanged at9108d012.

The actual6.4.3 library reproduced the forward near-limit error and both reverse
score-context paths. The original five-failure regression, legal zeroing/mate
controls, independent python-chess oracle, original commands/source/library/
binary hashes, raw outputs, insufficient one-line proposal and reviewed context
proposal are in investigation-before-integration.zip. Its adjacent JSON is the
member/hash manifest. Earlier mutable preparation metadata was not fully
versioned; PROVENANCE-HISTORY.md records that limitation. Original per-run raw
results and command files were retained.

The context implementation and regression targets are now applied but have not
been compiled or run. Independent static review is pending. The previous TT
candidate's tests do not validate this new source. Source changes are separate
from the frozen6.4.3 performance experiment. Next: compile fresh Release, run all
seven CTest suites, diagnose any failures, run sanitizer/context tuple/lifecycle
checks, measure appropriate fixed-work behavior/performance and preserve the
decision. No equal-clock Elo or Stockfish gain is claimed.

## Completed candidate validation

Source816423b1ddac23a00244449deef59dba736055a9 now passes all seven Release
and all seven ASan/UBSan CTest suites. TSan passes all eight TT groups, the
actual-Worker rule50 regressions, and eleven legality-checked UCI lifecycle
searches. Independent static review found no actionable issue. The exact current
regression source compiled against frozen6.4.3 headers/library fails seven
assertions, including both reverse paths, and passes here. That control is
separate from the earlier five-failure test whose reverse cases were diagnostics.

Cold/warm one-thread search outputs match the6.4.3 parent outside intentionally
changed rule50 fixtures. Both Linux bench11 signatures are419798; both Windows
signatures are351063. These are behavior checks, not speed gains.

Windows core, TT8, rule50, UCI and ponder checks passed under Wine, with unchanged
inputs and emitted SIMD/no-fusion checks. Two independent audits authenticate
source, tested binaries, runtime logs and packaged bytes. The standalone Zen5
ZIP is releases/forge-6.4.4-candidate-windows-zen5.zip, SHA256
d4fc94a529b1b0be89a37adb229433aade6923c8453a565fcf0b06e280171439.

The complete Linux logs/control/parity/provenance are in
linux-validation-checkpoint.zip (SHA256ffa23aab8e312361b68acc8e2bb869e4d4a36fba44c242c47e5b7fe0bdaa7dd5).
Windows original evidence is under windows/. Earlier approaches remain intact.
The inherited whole-engine speed gate is inconclusive after the independent
same-binary A/A audit, archived separately; do not claim Elo or promote the
accepted branch without sufficient further evidence. Next experiment is the
prepared legal-witness path with complete fallback and differential oracles.
