# Independent RED review: singular verification loses caller PV metadata

**Verdict: RED is supported. No substantive blocker found to a separately authorized, minimal GREEN experiment. This review does not accept the production change or establish an Elo gain.**

Frozen source: `2e151d019bc58dff2ab4e76e99ef99516af8d222`.
Authoritative RED receipt: `../red-attempt1/result.json`, SHA-256 `75b75b5054aa5c34e366005f70c9b27ea82e59abc04b73a1c3a80574d2f2ea7e`.

## Causal source review

The main search computes its local `pv_node` from the search window and assigns `ss->tt_pv = pv_node || (tt_hit && tte.pv())`. Singular verification calls the same search routine on the **same `SearchStack*` frame**, with a null window. That recursive entry can replace the outer frame's true `tt_pv` with false when its TT entry is non-PV. Existing cleanup restores `double_extensions` and `excluded_move`, but not this flag.

The caller subsequently uses `ss->tt_pv` to decide LMR eligibility and to reduce the reduction by one for PV context, and stores that flag in the final TT entry. Losing it can therefore affect future move selection and search context. The caller's separate local `pv_node` remains true; this evidence does not show that the outer main PVS boolean itself becomes false.

The proposed production patch saves this flag immediately before the same-frame call and restores it immediately after, before the `aborted_` return and before subsequent singular-extension or cutoff branches. These are exactly two added statements. This is a narrow correction of caller metadata, consistent with the surrounding cleanup. It should be tested as a behavior-changing correctness candidate with full qualification and paired equal-time strength testing.

## What the saved execution demonstrates

The actual Worker probe links Forge's real core and invokes the existing friend access to the real search. Its seeded TT fixture reports one singular call and one loss for PV caller/non-PV TT; PV TT control reports one call/no loss; no-hit and null-window TT-cutoff controls report zero singular calls/no loss. The seeded TT score is an artificial controlled fixture, rather than an independently proven search bound. The natural witness supplies the complementary real-search evidence.

The original natural bench stderr contains eight summaries totaling **716 singular verifications and 25 losses**. Every loss is caller-PV true, before true, after false. All 25 counted losses are emitted; no summary approaches the diagnostic limit of 64 rows (maximum 11). Raw/static evaluation and `in_check` are unchanged at these observed points. The baseline and observer build both report **321,912 nodes** for this finite `bench 11` workload with OwnBook explicitly disabled. Equal aggregate node totals support this limited comparison; they do not prove identical complete traces or establish a timing result.

Independent python-chess replay validates all **27 recorded FENs, selected moves, and resulting boards** (25 natural, two probe). Both recorded `in_check` values match the original FEN. They describe the caller before making the selected move, not check status after that move. The first natural witness can be constructed legally from the initial position by `e2e4 e7e5 g1f3`, followed by the recorded legal `d7d6`. That reconstructed path is not a claim about unrecorded engine ancestry.

`current_move` changes in 24 natural rows. The caller unconditionally assigns the selected move, moved piece and continuation pointer before making the child move, so these observations do not justify broadening this patch to restore those fields. Other shared search state and intentional history updates are outside this narrowly demonstrated flag defect.

## Independent provenance checks

`review_evidence.py` ran 60 static checks successfully. It reads files and parses archives; it executes no engine, compiler, CMake, Git command, or patch process.

- The original TAR contains 76 source inputs with the recorded hashes. All actual diagnostic inputs match their source manifest; only `src/search.cpp` differs, with the other 75 exact.
- Applying the observer unified diff **in memory** reproduces the actual diagnostic search source exactly. The proposed production diff adds only flag save/restore. The GREEN diagnostic diff is exactly this observer source plus those two statements; this is source review, not a GREEN runtime conclusion.
- Parsing both actual static archives shows the same seven members. Six nonsearch objects, including Board, evaluation and NNUE, have identical bytes; only search differs. Original member hashes match the published audit.
- All six original command groups' stdin/stdout/stderr match the RED receipt. Original return codes are expected: the deliberately failing RED Worker probe returns 1, all other commands return 0. Each group records empty live ownership sets after completion. This verifies saved cleanup facts, not a new inspection of historical processes.
- Frozen inputs, original engine/core artifacts and actual Worker probe binary retain their receipt hashes.
- The first outer invocation stopped before any engine/compiler spawn because `variants_sha256` remained `REQUIRED`. Comparing immutable clearances finds only its resolved hash and an explicit metadata-correction record. The second outer invocation is the first actual RED engine phase. The preserved pre-spawn failure is not a failed engine run rescued by a retry.

## Limits and next gate

Diagnostic counters, stream formatting and FEN formatting do not write search/board data, but introduce execution time, allocations and I/O. This review does not prove universal observer transparency, SMP behavior, sanitizer cleanliness, restored-frame correctness in all paths, or performance improvement. Natural traces instrument selected fields, not every search-frame field. Node totals alone are not Elo evidence. No match result or positive strength claim is made.

Proceed only under separate authorization with the minimal production patch and permanent regression coverage, then full native and Windows qualification as appropriate. Use a predefined paired equal-time match/SPRT protocol to measure playing strength; record a correct fix separately from any eventual Elo acceptance.

Review outputs were written only under `validation/pv-metadata-20261021/independent-red-review/`. No production source, existing evidence, branch or Git index was modified by this review.
