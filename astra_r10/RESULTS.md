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
