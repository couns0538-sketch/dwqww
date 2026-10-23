# Final chosen-network native inference parity

Status: **PASS — native inference parity only.**

The final frozen H128 residual include `a52efa5f7864b04d0e8fceb3b14af4fc4970e0bb0a0a8706be0959b0bbb98df7` matched the shared Python trainer on 2048/2048 integer scores exactly; maximum integer error 0 cp, feature mismatches 0. HCE-only records and legal/filter flags matched; all three invalid-input controls were rejected.

Compiler, NNUE-object compilation, link and parity processes exited 0. The explicit chosen-network object preceded the immutable archive; its old nnue.cpp.o member is absent from the retained link map. All original source/header/tool/network inputs remained unchanged. Exact commands, streams, actual exits, source/object/executable hashes and the unchanged shared test output are preserved beside this report.

Final frozen chosen-network native inference parity only; no CTest, bench, training, search, Windows, speed, loss, Elo or acceptance conclusion.
