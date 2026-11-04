# Synthetic identity-ambiguity proof

Recorded: 2026-11-03 14:56:05 Vienna. Helper, tests and proof artifacts are frozen
for independent review. No production rows were copied and no writer was edited.

This is a counterexample under the inspected serialization/dedup rules and legal
synthetic game histories. Score zero is an admitted fixture value. The specified
initial seen state is synthetic; its prior production origin is not asserted.
Unknown historical engine choices/configuration and real shard provenance are
not reconstructed. A PASS here is not production separation or training clearance.

Verified construction: X and Y share the ten-ply opening prefix, then use their
different four-ply knight cycles. Every move is legal. Both games stop at the
actual third occurrence at ply 18, consistent with the inspected writer's rule,
and have White result 0.5. Each buffers eight quiet noncheck records at plies 10..17.
The initial seen set contains four unwanted keys; the first-four-field key of A
and B is excluded. All six fixture keys have distinct 128-bit digests.

H1 writes Y and emits A/B with IDs Y/Y, dropping 6 of 8 rows. H2 writes X then Y
and emits exactly the same full bytes with IDs X/Y, dropping 14 of 16 rows. Both
final seen states are equal with 6 keys. Initial/final hash sets stay in RAM and
are not serialized. Assigning A to train and B to val gives zero overlap on
six-field, four-field and board+side keys, each with 2/2 valid keys and 100% fill.
The move b1c3 takes A to B with exact full-FEN and clock consistency.

Thus this observation can correspond to one original game or two. Legal
continuity and zero key overlap cannot universally reconstruct original IDs
under these rules. No leakage claim about any particular real shard follows.

Validation and generation:

- RED identity-ambiguity-red01: 7 failed in 0.09 seconds, expected missing helper.
  CPU 3 admitted at 0%, Idle, one CPU.
- GREEN identity-ambiguity-green01: 7 passed in 0.09 seconds. Independent oracle
  replay, exact bytes/IDs, full-state one-ply witness, coverage and hashes passed.
  Empty initial seen state fails the equal-output claim; illegal Qh5 is refused.
  CPU 3 admitted at 14%, Idle, one CPU.
- identity-ambiguity-command.ps1 -Phase proof01 exited 0 and generated the new
  proof bundle. CPU 0 admitted at 5%, Idle, one CPU. No native child was started.
- Source writer MD5 was rechecked read-only with Get-FileHash and matched
  0a7f225ae89ace5830b8840f17ada9d6. No writer module or database was imported/opened.
- The short test/generation slot was released to the parent and proof reviewer.
  Independent review is pending; no accepted-candidate claim is made here.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\r14_identity_ambiguity.py | 0b95e213be4941cc98a67a8f3a7cfa43 |
| D:\a14\tests\test_r14_identity_ambiguity.py | e0e805d1f983495ecbc72221f7c7d08b |
| D:\a14\sep\identity-ambiguity\PROOF.json | 50e901e03627d4618fe6853890e2922b |
| D:\a14\sep\identity-ambiguity\README.md | 2fe1ceb6fbd645eddd0095018860dd2d |
| D:\a14\sep\identity-ambiguity\H1.synthetic.txt | b1af6b6639edd55f9eab8eb3cbd6d505 |
| D:\a14\sep\identity-ambiguity\H2.synthetic.txt | b1af6b6639edd55f9eab8eb3cbd6d505 |
| D:\a14\sep\identity-ambiguity\MANIFEST.json | 0451c24a9ab8c18a183f7c59f5afeb95 |
| D:\a14\evidence\test_logs\r14\identity-ambiguity-command.ps1 | 69673554529d0e3364c3f797169fe829 |
| D:\a14\evidence\test_logs\r14\identity-ambiguity-red01\output.log | 0ad827e4ffdc98a5bdf9763e26dd8d57 |
| D:\a14\evidence\test_logs\r14\identity-ambiguity-green01\output.log | 4fbe7004d31424baee615034d6da921e |

No commits were made by this task.
