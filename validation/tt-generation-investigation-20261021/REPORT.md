Actual22 TT-generation investigation complete; policy remains UNAPPLIED.

Exact parentff2e269c6058be84456e3b98344826d17b0056eb source77 exported from the
qualified native Git archive. Only search.cpp observer code changed; header/API/
entry layout, scores, flags, replacement/admission policy and all other sources
unchanged. Existing shared striped synchronization and explicit one-worker lease
retained. Shared-TT skill read before instrumentation. No production/Git mutation.

Actual unchanged-parent core table fixture:9checks PASS. A depth12/gen0 record,
then B/C/D depth8/gen1 in the same cluster; A remains gen0 after repeated hits,
and is selected on the next miss's age-adjusted tie. Its shallow nonexact same-key
store is admitted solely by old age (depth1 afterwards), refreshing generation
and changing hashfull0→1. This proves the baseline mechanics, not candidate gain.

ONE baseline plus ONE observer walk:12root searches each, Hash16/Threads1, depth8,
embedded accepted residual NNUE. Actual public Searcher API bypasses the UCI book
(as OwnBook=false); it does not simulate search. First start-position search is
cold, immediate repeat warm, then10legal Ruy-Lopez plies with TT/history retained.
All fixed-depth response bytes match exactly: root FEN,bestmove,PV,score,depth,
seldepth,nodes. All12root positions/bestmoves/fullPVs independently legal. Two
search processes share one90-second external search budget; no retry/extension.
Timings are diagnostic only and are not used for performance or strength claims.

Observer totals:58683probes,6461occupied old-generation hits (11.010%);2364main
and1002qsearch genuinely eligible old-TT cutoffs returning directly without store
(3366,52.097%of old hits). These count only actual existing cutoff branches, not
score-based guesses. Remembered-old-hit victim selections and actual replacements
were both0. Slot tracking is a1024-record direct-mapped bounded table reset at
each root; collisions undercount, and a remembered hit may have an intervening
same-key store. Zero tracked replacements therefore does not prove zero pressure.
The workload demonstrates frequent old reuse but not the proposed eviction benefit.

Commands, exact77source/patch hashes, source/archive/core/object/executable pins,
all stdout/stderr, normal exits and owned-group closure are retained. Only the
cloned search.cpp.o differs; all six other core members, including NNUE, are
bit-identical to qualified22. No full native build was repeated: one table-fixture
compile, baseline walk link, one changed-search compile/archive clone and observer
walk link. Every step completed first attempt; original native22core/source untouched.

Minimal generation-refresh-policy.UNAPPLIED.patch changes only hit generation
bits under the existing stripe/owner lease BEFORE snapshot construction. It keeps
occupied/PV/bound bits, score/eval/depth/move/rule50, opaque selected slot/key/epoch,
locked hashfull and quiescent lifecycle. No synchronization bypass is added.
Generation also controls same-key store admission and hashfull: the fixture's
shallow overwrite would now be rejected while old deep data is retained, and
hashfull would refresh on hit. This is a COUPLED TT-policy strength ablation, not
an exact-behavior optimization or correctness repair. No policy was applied/run.

Recommendation: root review the finite evidence and coupling first. Retain the
unapplied candidate, but do not claim it helps replacement without representative
pressure evidence or improves Elo. Any actual policy trial needs full TT tests/
TSan and fresh preregistered equal-clock strength; no automatic extra observer or
second walk is authorized/performed here. Current22 strength experiment stays separate.
