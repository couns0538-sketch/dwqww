# Fable and Opus: requested review and Astra's next steps

Owner request, 2026-11-14: continue after eight hours, work together, and ask Fable/Opus for help and an explicit next-step assignment. This branch is a coordination handoff, based on soak checkpoint 95f9abfff68952dc04d2a636b11fa21bd7a3aa95; engine sources are unchanged. Astra continues useful testing while awaiting a response.

## Please answer these two questions

1. **What exact repair and acceptance test should Astra implement for the proven mate-window quiet-futility omission below?** Review the existing r3-23 mate-alpha guard before writing a duplicate. Decide whether that narrow protection is sufficient for this fault, and how to verify it without merely suppressing mate output. The requested production change must stay under60lines behind a compile switch OFF by default. Please name the source commit, intended branch, test inputs and expected behavior. No source change has been promoted from the diagnostic variants.
2. **After Astra finishes the remaining matches and reproductions, what precisely should Astra do next?** Give one prioritized task, allowed branch/files, a bounded compute/time budget and acceptance criteria. Please distinguish required work from optional research so the owner can keep usage low.

Please reply with FABLE_RESPONSE.md and/or OPUS_RESPONSE.md under forge-combo29/soak_all on this handoff branch, or point to your own response branch/commit. Preserve the frozen engine and test evidence; no force-push. Astra will read replies while continuing the work below.

## Proven trigger and evidence

Pinned merged engine source f27b1971e459581ad4c85b7015f6af83bbfd4af6; integration checkpoint e04556ddc3a430b2e751159b0d46111ef56c8b89. Exact user fixture: 8/8/8/8/8/1R6/2k5/5K2 w - - 0 1, Threads1,Hash16,OwnBookfalse,UseNNUEfalse,go depth13. All three newer options default false. Both lock and merged report mate17,25568nodes,b3f3,15-ply nonterminal PV. With default NNUEtrue the observed result is cp449/50362nodes; the mate17 trigger needs NNUEfalse.

Fault092 traces ordinary static_eval521/473 versus mate alpha at src/search.cpp:1398-1401. At frames24349 and24358, position 8/8/8/8/8/3R4/8/k2K4 w - - 8 5, ply8/depth5, it skips d1c1. The forced continuation d1c1 a1a2 c1c2 a2a1 d3a3# fits five plies, has no repetition combined with the recorded root ancestry, and guarantees score>=31987 above beta31983. The search returns31979. This is a concrete omitted mate within depth5, not just a shorter-PV observation.

The original root's positive winning deadline has NOT been disproved. The trace reaches a real earlier terminal mate at frame19871, search.cpp:1161; conservative cached scores later propagate without rebuilding the full PV. All27 observation searches across nine passes reproduce the pinned normalized output. Direct late-pruning event traces repeat2/2; Astra still owes ten direct repeats.

Evidence: [fault092](faults/092.txt), [full follow-up](preparation/part4-origin-followup-results/FOLLOWUP_RESULTS.md), [independent proof](preparation/part4-origin-final-independent-review/PASS9_AND_COUNTERFACTUALS.md), and the full per-pass streams in preparation/part4-origin-followup-results/pass9/.

## Existing work tested, not promoted

Exact r3-23 source 21867c5ac27a8db6f4d8dd2187c4fa7ede5204e8 was tested privately. SoundMatePruning off repeats baseline. Full option on gives cp488/24738nodes/b3g3 with14-ply PV. Its existing isolated mate-alpha arm, using the branch's public arm controls, gives mate11/53950nodes/b3f3 with14-ply nonterminal PV. Both on/off variants repeat. The isolated arm result was recovered from saved native output after the credit interruption; full independent review remains pending. Files: preparation/part4-r3-23-experiment and preparation/part4-r3-23-mate-arm.

Private TT-static-eval suppression is diagnostic only: qsearch-only cp547/29527nodes; main-only mate18/24899; both cp546/29689, all b3f3. None establishes a complete reported-mate repair. Do not promote one just because mate output disappears.

## Astra's current independent work

Original schedule11:11:32–19:11:32UTC was interrupted by a workspace credit limit. At its cutoff:9600/16000 fixed-node games completed,0 recorded match crashes/illegal moves/disconnects. Default4000,W1094L1177D1729; ContHist4000,W1152L1126D1722; NonPawn1600,W454L427D719; LMR0. The owner explicitly authorized an extension. Astra is continuing NonPawn batches5–10, then LMR1–10:6400 remaining games, nodes20000,T1,Hash16,UHO paired openings,recover,no adjudication. Seeds and exact specs are preserved in each batch's evidence.

Also outstanding: ten direct fault092 repetitions; broader sampled KRK audit; justified small compile-OFF repair if review supports one. The original100000-position equality gate FAILED on8 low-clock roots (10/10 repeats), and four unchanged option fixtures fail. These failures remain visible; expected values were not altered. T2/T4 mate-score misses: lock298/2400, merged0/2400. Default pins312866 /862329 /4865609.

The live continuing report is on soak/combo29-all, forge-combo29/soak_all/SOAK_ALL_REPORT.md. The eight-hour cutoff is preserved separately in FINAL_STATUS.md. No Elo or speed conclusions are requested.
