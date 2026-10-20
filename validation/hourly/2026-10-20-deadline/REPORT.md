# Forge 6.4 — timeout diagnostic deadline correction (2026-10-20 UTC)

Checked branch head before work: 2fc649effb6d2f09f4fdf63b44d59283fe26b616. No active owned engine/fastchess process found in this worker namespace; saved lease reports inactive.

The TT verification-tag candidate's first strength attempt remains **failed, not resumable**: six complete games/three paired openings, one Candidate timeout, and no native SPRT H0/H1 decision. No new native games, no speed measurements, no verified Elo gain. The original metadata-bearing match archive remains blocked from public upload pending authorization.

The previously saved (separate) bounded warm UCI diagnostic misclassifies some responses when the Python consumer is delayed: its timeout started at dequeue rather than before go dispatch, it judged delivery using dequeue rather than reader timestamps, and it could treat exited child plus an undrained stdout pipe as completed absence of bestmove. This cycle reproduced three controlled regressions (old diagnostic: two errors and one failed assertion), corrected all three without modifying chess engine source, and ran **11/11 synthetic diagnostic tests successfully**. An additional **8/8 mocked warm/cold trials** completed; all eight mock JSONL journals matched their SHA-256 summaries. The change is only to diagnostic quality; it does not diagnose the original native Candidate timeout.

Complete stage-0 through stage-3 diagnostic source, test scripts, the patch, pre-fix and post-fix output, synthetic raw UCI journals, SHA256SUMS and VERIFY.py are retained in the conversation artifact `forge64_cycle3_deadline_evidence_20261020.zip` (SHA256 `c82add3a7589d53cf323417688d6ec47aab771be2aa5241e442d2c6fb4c3d986`). This GitHub report does not claim the ZIP is uploaded to the repository.

Next: recover hash-frozen engine binaries and first-attempt raw evidence on an authorized host; acquire exclusive CPUs, measure warmed timing and scheduling, and only then preregister a replacement native SPRT. Keep all previous failure records and the six original games separate.
