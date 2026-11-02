# Astra R10 results - UNPROVEN

Setup: isolated shallow clone/worktree created from f43a26aeed2448379fc2916b25f31ead8707b0ec. Original checkout/branches untouched. AGENTS review policy preserved with R10 scope.

Frozen lock: FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072.
Kit original MD5 verified:729FE7275C3C01D22C751CB751D5C9D2.
Bench T1 Hash16 depths11/13/16/20/22:312866/862329/3024920/12389307/34048354.
Perft5 start4865609 kiwipete193690690. UHO crew gates only.

| Milestone | Status | Next |
|---|---|---|
| M0 plan/worktree/review policy | PASS setup only | safety compatibility tests/review |
| Job1 native proof/timing | UNVERIFIED | recover inputs and build adapters |
| Job2 P4/P7 | NOT STARTED | recheck heads on entry |
| Job3 audit/replay | NOT STARTED | frozen inputs after Job2 |

Planning review: installed launcher rejects required C/F protected roots; only D floor implemented. Exact proof helper requires ON difference and T4 up front. Kit resets priority to BelowNormal. Branch-local compatibility work in progress before native jobs. No candidate accepted.
Ruling: use existing matching branch skills, not global C: installs; all writes remain D:a10. User milestone reviews override generic one-final-review skill advice.

M1: safety launcher preflight19/19 PASS (green-002), proof helper fixture14/14 PASS; these are helper tests, NOT engine proof. Original defects reproduced; failed/intermediate logs preserved. Safety launcher SHA842D6520058EB9F5C14D7426CA3BAD92F080AFB5F5684F1C43AB1A56FE38C21D. Proof runner SHA525201937C360E8EB0B438A4A03C77DD69866E7DB5FAAD40EFCE68DA8B34431F. Focused independent rechecks pending.

Build adapter review found PS5.1 module-path hazard, missing frozen source comparison, residual-child risk on timeout and missing failure receipt/fresh retry tags. Fixed each: WindowsPS module path/preflight PASS, complete R9 manifest binding, observed owned PID+creation-time cleanup, retained exception receipts/new suffix tags. Recheck pending before native launch. No C: config changes. First commit failed due missing local Git identity; set only R10 repo identity and successfully published028326f, verified remote. Input hashes match lock/r9/corpus exactly (job1/inputs.json).

M1 recheck closed: independent review approved launcher842D6520 and exact-proof52520193 changes. Build wrapper fixes plus final manifest declaration/process-exit race/post-run tool hash/cleanup receipt corrections reviewed; no compiler recipe defect. Native launches use full protected roots, Idle affinity12, no capture/disk errors. `.gitattributes` now preserves all R10 evidence/helper bytes on publication; original local bytes re-staged to prevent newline normalization invalidating recorded hashes.

M2 native build proof: pc1-a and pc2-a both PASS, exeSHA256775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284 (also equals recovered R9). All OFF/ON five pins and perft exact on both builds and their plain controls. Zero missing-profile warnings/vfmadd. Complete original kit outputs copied into job1/build-proof01; direct reviewed collector PASS. Generic proof helper's Werror witness contract is incompatible with exact kit: no flags invented/changed; original kit's fatal postcompile profile scan and raw artifacts remain authoritative. UCI Hash defaults32, but pinned bench code creates its own Searcher(16); T1 bench contract verified from source. Smoke/sanitizer explicitly set T1/Hash16.

M3 validation review found and fixed unbounded smoke allowance, potentially zero searched selfplay and incomplete output-drain acceptance. Three regression tests PASS; focused independent recheck approved validate_uci9CE866CB and run_checksB2741B59. Native T1 smoke OFF/ON PASS (12 legal moves each;500ms maximum for100ms requests). ASan+UBSan rerun PASS:8games/572legal plies per mode, zero reports; deliberate ASan and UBSan controls each detected. Auxiliary sanitizer recovered SHAa56762278935af93344680ba147a9076f63b52504e2495a686d7fe5f28a4a2aa with original R9 source/build provenance, not misrepresented as a fresh production build. T4 UNVERIFIED (host loaded). Exact raw-bit parity/negative control and timing still UNVERIFIED. Next: finish reviewed parity native run; timing only after parity PASS.

M4 native parity PASS and independent original-trace review PASS:12000 root FENs,20 exact components per row,0 OFF/ON differing rows. 684064 active ON evaluations,324032 moves,12000 nulls with fresh seed3771096103. Negative source changes exactly W2[0]575->4671 (serialized byte range393728..393729);3975 actual root mismatches vs good OFF. All42 good/negative source hashes and14 referenced artifact hashes independently verified. Full native evidence/source copies at job1/native-parity. Diagnostic binaries are not production candidates. Compiler attempt1 exited1 before compilation because cc1plus could not load DLL (0xC0000135); bounded before/after PATH probe confirmed cause. Child-only UCRT PATH fix,10 adapter tests PASS, new retry02 builds/runs exit0; failed outputs preserved. Checker14 tests PASS. Harness2B49E0D4; final adapter8AD3A883; checker08E088C8.

M5 timing readiness review PASS after fixing protocol snapshot/hash race and prerequisite-to-candidate binding. Current native host topology confirms CPUs2/3 same SMT core, compiler identity copy on D matches actual kit compiler.12 timing regression tests PASS. Protocol frozen BEFORE ANY timing at SHA256c83ccb17d428069be129eaf4f1b253dbf299bb6d77ad0353a5667fa82ccb3245 (job1/timing/protocol.json). Exact10 eligible A/A blocks precede10 ABBA; calibration absmedian<=0.5%,IQR<=1pp,eachblock within+/-2%;80attempts/phase,60min cap. Timing NOT STARTED at this checkpoint. Prerequisite declarations checked against original native evidence; T4 still UNVERIFIED and full gate readiness incomplete.

Evidence sealer helper15 fixture tests PASS and source reviewed; existing strict gate packer unchanged. Incomplete packs never claim gate readiness. No pack delivered yet. All strength UNPROVEN.
