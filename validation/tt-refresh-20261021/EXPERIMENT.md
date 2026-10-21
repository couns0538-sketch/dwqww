# Forge 6.4.23: refresh reused TT entry generations

Baseline source: `ff2e269c6058be84456e3b98344826d17b0056eb` (qualified Forge22).
Accepted integration remains `5101c2529d386b7c3a04ba9156a69ee34df6bb43`.
This isolated branch preserves all prior candidate changes, including the still
unaccepted correction-history experiment; no integration merge is authorized by
this record.

Hypothesis: occupied entries reused across root searches should remain recent
even when a TT cutoff returns without a subsequent store. Refresh only old hit
generation bits while holding the existing stripe or explicit exclusive lease,
before making the coherent snapshot. Keep every other field, opaque destination,
epoch, score eligibility and lifecycle requirement unchanged.

This deliberately changes replacement priority, age-only shallow store admission
and hashfull telemetry. It is a TT-policy strength ablation, not a correctness
repair or an exact-behavior speed optimization. Retaining deep old bounds or
frequently accessed shallow entries can help or hurt. The prior observer recorded
6461 old hits and3366 eligible cutoffs without stores, but did not demonstrate
later eviction benefit. Original evidence and the unapplied unconditional-write
proposal are preserved separately; this actual source writes only when old.

Four new permanent real-table groups preserve all eight existing groups. They
cover payload/flags and snapshots, handles and shallow admission, misses/zero tags,
replacement/hashfull/wrap, and guaranteed aged hits followed by concurrent
reader/writer/hashfull stress. The new regression linked to the unchanged original
22 core exits1 at the expected first old-hit policy assertion. This is an expected
policy contrast, not evidence that old policy is a correctness defect.

Candidate Release14, ASan/UBSan14, default unsuppressed TSan14 and eight active UCI
checks are required before strength testing. The first actual canonical bench
signature is unknown and will be frozen once with exact source/core/executable/raw
bindings. No parent search parity, NPS or Elo result is claimed. All failed attempts
must remain retained; no rerun may rescue a failed engine gate.

If native gates pass: fresh openings, timed operational A/A then serial paired
equal1+0.01 Fastchess versus22, T1/Hash32/OwnBookfalse/Ponderfalse/MoveOverhead10,
SPRT logistic[0,+10], alpha=beta=.05, cap512pairs. Freeze actual source, build,
runner, opening selection and acceptance rule before play. Any operational fault
invalidates acceptance; natural cap is inconclusive. No retry, resume or pooling.

Current status: implemented, expected parent policy contrast passed; first full
native validation passed42CTest/8active, TT12/PV56 each, independent1185checks and
root644originals/17parentsingles/77Git/138evidence rehash. First actual benchmark
captured292545nodes with an exclusive source/core/exe/raw freeze. All strength
evidence remains pending. Windows23 is not yet built.
Do not change the frozen22 hosted payload or accepted integration branch.
