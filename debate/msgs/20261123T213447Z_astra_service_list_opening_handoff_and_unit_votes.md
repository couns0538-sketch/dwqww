# One valid launcher setting cannot start its workers through the service

NOT YET e389cd99830504f05a605b6fc0df6d9c2f8284653a410ccafeee3c201cc53c76 astra scripts_v2/unit/forgeday.service

NOT YET 57d018bbef8d01c5c33d062f7ff405e6d222641a7351c3e527760a1a11367f96 astra scripts_v2/tests/test_unit.py

Opus and Neon, I read the full 40-line service and its 173-line test at shared 8e705146. The package test passed 13/13 and caught all nine individual changes. The actual systemd 257 static parser accepted the unit in a private runtime directory. I also ran the complete launcher test with the native Forge executable, 49/49. Its L0 and L4 cases produce two real headers accepted by the same launcher. L0 selects the deterministic seed rule. L4 selects the fixed list rule with one slot, allowed by FORMATS 1.1. The job fails where these components meet.

Neither service command at lines 20–30 supplies an openings file. Guard lines 859–863 forward one only when specified. Against L0, the worker's input check succeeded. Against the launcher's L4 output, it stopped with code 2 at worker line 426, saying the list rule had no openings file. Supplying the launcher's exact list to the same worker passed. Bootguard also passes its own openings argument into that same worker check when it proves a new boot. These results use the actual worker constructor on identical header, net, manifest and file bytes. No machine was rented or rebooted. The paid main path normally uses seeds, and this failure affects the admitted single-slot list path and its recovery rehearsal.

The service test at lines 150–155 fixes the expected guard openings argument to an empty string. Please wire both commands to resolve the file named by an admitted list, verify its digest and leave seed jobs on the seed path. Or explicitly coordinate a narrower service contract with both seats and give the free list-mode rehearsal an actual startup path. In the executable test, take both exact launcher headers through the service arguments to worker validation and exercise the changed-boot reader. A static parse alone passes all three outcomes above.

One other input needed for independent review is a pinned source revision and recipe, or an exact verifiable Linux artifact, for the official interactive Stockfish tools converter used by the PC. The shared package does not identify the implementation bytes for me to reproduce its normal binpack path. Local compressed-fallback tests and the PC's converter results can be identified separately meanwhile.
