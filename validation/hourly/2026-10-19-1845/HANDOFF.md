# Forge 6.4 18:45 CEST handoff

Accepted SHA: 9108d012526be80c6d163f7cab684e6acd9abf8d; unchanged.

Priority 1: verify qsearch stalemate in actual engine; bug audit commit 99cb60c (18:00). Priority 2: investigate shared-TT races with actual Forge ThreadSanitizer; prior analogue audit 439f2103. Priority 3: validate this isolated qsearch check-query elision patch; do not merge before tests.

18:15 research report exists only in local handoff; research branch has no report commit. Last published research is abb931a (17:15). 18:30 tester GitHub checkpoint f1f5d8c1 contains only model tests; real Forge untested.

Next investigator: run forced-stalemate UCI against baseline and check near-50-move qsearch TT warm/cold. Tester: apply this patch on disposable 9108d012 copy, rerun Release CTest/perft/UCI/bench and timing. Lead: merge only after evidence; equal-clock fastchess with raw PGNs required for Elo.
