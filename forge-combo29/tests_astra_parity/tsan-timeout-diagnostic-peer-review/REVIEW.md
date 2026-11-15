# Independent review: two bounded 0018 diagnostic searches

READY: no blocking finding. Reviewed frozen diagnostic.cpp, control.mjs, audit.mjs and declaration; verified all21 frozen file hashes, all26 source pins, native/engine binaries, build flags and object/input pins. The case position files exactly equal the original full histories and FENs. The recorded offline self-test passed both legal-history checks and four completion cases. This reviewer ran no engine or native diagnostic and made no Git, source or root-state change.

The controller allows only case4 then case10, once each, with an exclusive lock. Each fresh process uses the original on/off configuration, Threads2,Hash16,OwnBookfalse,UseNNUEtrue,MultiPV1 and go depth9. Seven seconds cover setup; a separate absolute60-second response window begins immediately before sending go. Normal measured shutdown uses250ms. Each controller command wraps the native helper in timeout75seconds with2seconds kill grace and a78-second parent bound, well below8minutes.

Search output is collected in a dedicated vector before quit. The outcome is frozen before finish(250); shutdown output is retained in the full transcript but is never appended to that search-result vector. Timeout, missing bestmove, bound-only output, missing exactdepth9 or nodes, illegal returned move, invalid score or parser error cannot establish depth9 completion. Overall diagnostic success additionally requires no recorded error/diagnostic and a normal observed exit. A bestmove caused by quit therefore cannot convert a timeout to completion. Raw commands, responses, stderr, timing events and process status survive success or failure; an outer interruption cannot infer a missing final result.

This has zero soak credit and explicitly says warm_tt_reproduced=false. Fresh full-history replay reconstructs the board/history, not the old session's warm TT and search histories. Neither controller nor auditor changes the global stop or authorizes normal-soak continuation. The original findings remain unchanged. The auditor's exit0 means evidence can be summarized; the explicit diagnostic_success/searchCompletedBeforeQuit fields, diagnostics and process status determine the diagnostic outcome.

Pinned native: d0ecb06670e3c6f06aa9e86e456147372f51c09b78c28af30cf61d978a76b3a4.
Pinned controller:6cb405eaad3e245b7109af9bfd4c1682534bda07ac113421ba731e268c323f15.
Exact verification results are in PIN-VERIFICATION.txt.
