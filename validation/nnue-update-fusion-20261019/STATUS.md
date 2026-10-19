# Forge 6.4.10 NNUE update fusion

Source36f5b2f6e1ff519e82a4b52edc85caceaf15aed0, parent649source4edda780.
Only exact2-change remove/add updates use one pass; per-lane subtraction then
addition and the original general fallback are preserved. No weights, output
layer, search, pruning or timing constants change. Ordinary parent/child and
same-object calls are supported. This previously documented opportunity was
unimplemented in all prior ledger entries.

Release9/9 passed. Actual old/new API streams compare byte-identical:1644cases,
3940snapshots,31dirty masks, both-color specials, finite synthetic boundaries,
parent immutability and in-place use;4,097,860bytes SHAca9e7405c5f7b7506455a3b6b104683ccc8d83e75b0bbaf8d9c17c3ecce1ff45.
Existing NNUE walk/output stream21,192,328bytes also matches, including100000
synthetic output evaluations. Six cold/warm1T search cases and419798bench match.
Matched-fnoLTOparent core is byte-identical to original649core.

ASan/UBSan9/9 passed from immutable source36f5b2f, plus the instrumented1644case update driver matched Release. Windows8checks and both snapshot streams also match parent and Linux byte-for-byte; independent package audit passed.
Microbenchmark tool compiles/calls actual out-of-line updater and passes a
1024call functional smoke, matching all category/input/output checksums; those
uncalibrated durations are not compared. No local timing pilot was launched.
The fresh hosted performance attempt39334266771 failed its primary same-binary3%noisegate: CPUratios0.977975..1.047225,wall0.977240..1.048432. No A/B or kernel comparison ran; final input hashes passed and all original sources/binaries/rawresults remain on results/nnue-performance-39334266771-1. No retry. The647vs644
strength confirmation is a different source comparison and cannot validate650.

Disassembly excerpt extraction initially had a header-boundary bug; both original
raw object dumps and incorrect snippets remain saved, with correction notes.
An actual x86-64-v2/SSE core also produced the identical4.1MBupdate stream. No NPS/Elo/nativeWindows/Ryzen gain is claimed. Accepted integration stays9108d012.
