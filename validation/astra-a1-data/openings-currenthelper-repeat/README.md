# Current-helper replay of the min-25 opening book

One generation was run with the current helper ddf8713016863512ffd6227c5b3f623d53a87e9964f0bbb8c94c146525d58ff3 and unchanged generator f2e25096f4c2a018ced4f731e01999d9700b42a2f1836ae8ba63b137749d43b7. The full settings were copied from ../openings-unbalanced-25/standard-one/settings.json: count64, seed20261030, nodes1024, Hash1MB, 6–16plies, every selected position within±150cp, final absolute score25–150cp, maximum2000attempts, orthodox R8 move format. This was one helper on CPU0 at nice19 while the separate full filter remained active; no performance comparison is intended.

Start: 2026-10-30T04:28:56.795623+00:00. End: 2026-10-30T04:29:01.543335+00:00. Exit0. Wall 4.745527s; owned-child CPU 4.583203s. Probe and generator hashes were unchanged after the run.

The current run accepted64positions from338attempts, with32White and32Black advantages, mean final absolute score67.578125cp and selected maximum148cp. Book, settings and generation statistics are byte-identical to the historical min-25 run with helper ad2fa25e384d71fc30bf5c22108da0336675d93a21fd9b11604964acb771c498. Book SHA256:7237efd96cb0b9b60a0717679d867e5ce04eddd2d46e56234cef77820066ee81.

Metadata is NOT byte-identical: each of64records has a different probe_binary_sha256 reflecting the actual binary used. A recursive comparison checked every field without exclusions and found exactly those64provenance differences, with no move/FEN/score/depth/node/trajectory difference. The complete field-by-field differences and both file hashes remain in outer_logs/comparison/comparison.json. This does not assert general equivalence of the two helpers. Native Windows R8 execution remains UNVERIFIED and no Elo claim is made.

current_generation/ is a complete unchanged copy of the newly sealed generator output, including original native IPC. Original command, outer stdout/stderr/exit receipt, exact settings and comparison script are separate under outer_logs/. Both historical and current output seals/manifests were verified; no old artifact was edited. SHA256SUMS.txt covers all evidence files except itself. The original /tmp directories remain intact.

IDEA_SOURCE: user current-helper attribution requirement and exact same-repository generator/probe protocol.
