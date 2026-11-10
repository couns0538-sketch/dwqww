# DEDUPE: what is already owned, by mechanism

Terms are explained in `NO_QUALIFIED_GAP.md` section 9. This file was corrected after the review; `REVIEW_LOG.md` lists what changed.

## Key points

- **Dedupe was done by what the code does, not by option names.** A candidate counts as owned if the same mechanism is in the lock, was built, queued, gated or rejected by the crew, or is already listed in the crew's research notes.
- **Twenty candidate mechanisms were checked. Nineteen are owned.** Fourteen of those nineteen would have looked new from the lock source alone.
- **The twentieth appears nowhere: enhanced transposition cutoffs.** No card, no table row, no option, no source snapshot. The nearest thing is today's `tcc21` candidate, which reads a child's table entry for the opposite purpose.
- **Four more classic ideas have no card and no build** (section 5). They were not counted among the twenty because I found no evidence that would justify measuring them. One of them is partly owned through `tcc21`.
- Being unowned does not make something a qualified gap. That question is answered in `NO_QUALIFIED_GAP.md`.
- **This search has blind spots.** It saw branch tips, not history, and only six file types. Section 6 lists them.

References are written `branch@tip:path`, with tips as fetched on 2026-11-09 (`data/branch_tips.tsv`). "Lock" lines refer to `src/search.cpp` of the source of record (md5 `b9f9aab0...`, see `COVERAGE.md`).

## 1. How the search was done

1. Read the lock search in full and listed what it has (table 2).
2. Read the crew's own inventories: the 81-family ranking, the 101-row feature diff, the gate table, the R15 candidate index.
3. Searched a corpus of 3,754 unique `.md`, `.cpp`, `.hpp`, `.h`, `.patch`, `.diff` files from all 387 fetched branches, by keyword and by code shape. Example of a code-shape search: any read of a table entry through a child key (`key_after`, `child_key`, `peek`).
4. Diffed today's live candidate sources on the PC against the lock source.

## 2. What the lock search already has

| Area | Mechanism in the lock | Lock lines |
|---|---|---|
| Table | four 16-byte entries per cluster, depth and age replacement, 32-bit check key, rule-50 stamp | `search.hpp:73-99`, `search.cpp:268-336` |
| Table use | cutoff in non-PV nodes at sufficient depth and rule-50 below 90; score refines the static eval; eval reused from the entry | 1165-1170, 1179-1186 |
| Draws | repetition (one earlier occurrence after the root, two before), fifty moves, insufficient material, stalemate test at every node; mate-distance pruning | 904-914, 1133-1138 |
| Eval correction | pawn-structure and material correction history | 850-868 |
| Node pruning | razoring, reverse futility, null move with verification from depth 14, ProbCut, internal iterative reduction | 1196-1285 |
| Move-loop pruning | late-move pruning, quiet futility, history pruning, SEE pruning of quiets and captures; capture futility present but off | 1320-1345 |
| Extensions | singular with double extension, multi-cut return and negative extensions; check extension for safe checks | 1348-1377 |
| Reductions | late-move reductions with terms for former-PV, improving, cut node, hash-move capture, check, child cutoff count, history | 1407-1428 |
| Ordering | hash move, good captures, two killers, counter move, quiets by main plus continuation history (plies 1 and 2) plus a check bonus, losing captures last | 423-768 |
| History | main, continuation (written at plies 1, 2, 4), capture, counter move; bonus for a quiet that beat a reduced search; PV-move bonus | 938-984, 1424-1427, 1466-1480 |
| Quiescence | captures and promotions, all evasions in check, table cutoff, stand pat, futility, SEE margin | 989-1110 |
| Root | aspiration from depth 4 with widening; per-root-move node counts used for time only | 1653-1731 |
| Threads | every helper runs the same iteration as the main thread; the main thread's result is reported; the shared table is locked by stripes | 1772-1816 |

## 3. Candidates checked

"Looked new" means the lock source has nothing like it.

| # | Mechanism | Looked new | Verdict | Where it is owned |
|---|---|---|---|---|
| 1 | Upcoming-repetition test (a reversible move can repeat an earlier position; alpha is raised to the draw score) | yes | OWNED: carded and built | card `opus-deepres-20261104@2231439c:opus_deepres/cards/T04S/T04S-02-upcoming-repetition.md`; option `CuckooRep` listed ON in `astra-a1-data@110f0c4a:opus_r3/R3-1L/logs/run_40582392767/sp-rel-all_on_v1net/MATRIX.md:7`; diff row 1 in `...:opus_deepres/notes/T04F/DIFF.md:18` |
| 2 | Twofold repetition scored by node type | no (the lock scores twofold as a draw everywhere) | OWNED: carded, and prepared for a gate today as `TwofoldNonPv=1` (section 6) | `opus-deepres-20261104@2231439c:opus_deepres/cards/T04F/T04F-03-twofold-nonpv-only.md`; ranking row L27 |
| 3 | Draw-score jitter against repetition blindness | yes | OWNED: built as `DrawJitter`, never gated, dropped as under +1 | `...:opus_deepres/notes/T06/DEAD_ENDS.md:4`, `...:opus_deepres/notes/T06/FORMS.md:29`, `claude-research-20261030@6f27150d:research/claude_deep_research_20261030.md:148` |
| 4 | Quiet checking moves in the first quiescence ply | yes | TRIED: neutral at fixed nodes, not adopted | `cursor/match-pgns-66cc@f481fc5a:EXPERIMENTS.md:142`; `forge/6.4-hourly-20261019@5101c252:validation/hourly/2026-10-19-initial/forge-search-audit.md:64` |
| 5 | Quiet history updated from the static-eval difference of two plies | yes | OWNED: built as `EvalSwing`, gated twice in a bundle (gates 15 and 28, capped) | `...:opus_deepres/cards/T04C/T04C-03-evaldiff-quiet-history.md:1`, `...:opus_deepres/notes/T04E/TABLE.md:75`; gate rows in `FORGE_RESULTS.md` |
| 6 | Search depth cut by one after a move raises alpha | yes | LISTED: in the feature diff as lacking, dropped for missing or sub-threshold numbers | `...:opus_deepres/notes/T04F/DIFF.md:100` and `:181`; `...:opus_deepres/notes/T04B/TABLE.md:64` |
| 7 | Node-count move ordering near the root | yes | LISTED: lacking, "number missing; table only"; overlapping built candidate `LowPlyHist` | `...:opus_deepres/notes/T04F/DIFF.md:139` and `:201`; `...:opus_deepres/notes/T04F/TABLE.md:54`; `opus-r15-20261103@2de61ac8:opus_r15/cands/INDEX.md:76-78` |
| 8 | Less reduction for killer and counter moves | yes | LISTED: number missing | `...:opus_deepres/notes/T04F/DIFF.md:93` and `:179` |
| 9 | Capture history updated on quiescence cutoffs | yes | LISTED: number missing | `...:opus_deepres/notes/T04F/DIFF.md:117` and `:187` |
| 10 | No history update when only one move was tried | yes | LISTED: number missing | `...:opus_deepres/notes/T04F/DIFF.md:132` and `:195` |
| 11 | Null move: improving term; depth cut instead of a verification search | no (other form present) | LISTED: number missing | `...:opus_deepres/notes/T04F/DIFF.md:56-57` and `:168` |
| 12 | Aspiration window sized by the previous score; depth reduced after a root fail-high | partly | LISTED (window size) and TRIED (`AspFailHighReduce`, gates 15 and 28) | `...:opus_deepres/notes/T04F/DIFF.md:147-148` and `:202` |
| 13 | ProbCut from the table while in check; table-only ProbCut | partly | LISTED below the crew's bar; `TtProbcut` built | `...:opus_deepres/notes/T04F/DIFF.md:60` and `:169`; `opus-r15-20261103@2de61ac8:opus_r15/cands/INDEX.md:43-45` |
| 14 | Recapture extension; pawn-push and promotion extensions | yes | LISTED below the bar; the source engine later removed them | `...:opus_deepres/notes/T04F/DIFF.md:85`, `:176-177` |
| 15 | Limits on the check extension | no (extension present, no cap) | TRIED: `CheckExtDepthCap` gate 59 capped; card for folding it into reductions | gate row 59 in `FORGE_RESULTS.md`; `...:opus_deepres/cards/T04U/T04U-01-check-ext-into-lmr.md` |
| 16 | Helper-thread diversity and best-thread selection | yes | OWNED: built as `SmpV2` and `SmpBestThread`, recorded as not in the lock line | `opus-smp-layout-20261107@a675c04f:opus_smp_layout/INVENTORY.md:28`; `astra-a1-data@110f0c4a:opus_round1/O1/REPORT.md:37` and `:70` |
| 17 | Skipping the net when the hand-crafted eval is far outside the window | yes | REJECTED in notes: changes values, saves under 1 % | `...:opus_deepres/notes/T06/DEAD_ENDS.md:8`, `...:opus_deepres/notes/T05B/TABLE.md:23`, `...:opus_deepres/notes/T05F/TABLE.md:32` |
| 18 | A history of whether the hash move held up | yes | LISTED as a bigger change; a reduction that uses it has a review receipt | `...:opus_deepres/notes/T04D/TABLE.md:30`; PC file `...\forge_push\CR_PASS_ttmovehistlmr_al1_ltopgo_de6dea8b.ok` |
| 19 | Ordering bonus for moving an attacked piece away | yes | PARKED: built as a static bonus, parked after a tactics loss; a learned variant was built and never gated | `...:opus_deepres/notes/T04F/DIFF.md:138` and `:199` |
| 20 | **Enhanced transposition cutoffs**: before searching a node, look up every child in the table; a child entry that already proves a cutoff ends the node | yes | **NOT OWNED** | see section 4 |

Other items in your own "already owned" list were confirmed as they came up and are not repeated here: re-search depth adjustment, quiet-penalty decay, continuation-history sum base, capture-history SEE shift, table-cutoff child check, cut-node and no-hash-move reductions, table cutoff by node type and depth margin, singular variants, null move with a capturing hash move, low-ply and pawn history, quiescence evasion limits, rule-50 eval damping, fail-high blends, Syzygy, speed work.

## 4. The one unowned mechanism

- **By name:** zero matches for "enhanced transposition" or for "ETC" used as a term in all 3,754 corpus files. The handful of raw hits are the word "etc" and test-fixture text.
- **By code shape:** in every source snapshot on every fetched branch, a child key is computed in exactly one place, to prefetch the child's table cluster (`key_after` then `prefetch`). No snapshot reads a child's table entry.
- **On the PC:** today's candidate `tcc21` (`D:\forge-runs\tcc21_20261109\src_cand`, base md5 `b9f9aab0...`) adds a `peek` of the hash move's child. It uses the child entry to **veto** a cutoff the node's own entry would allow. Enhanced transposition cutoffs use child entries to **create** a cutoff where the node's own entry gives none. Same plumbing, opposite effect, different trigger. I count them as two mechanisms and note that a reviewer could reasonably call them one family.
- **Not in the crew's reach by method:** the crew's research mined commit logs and pull requests of current engines. A 1996 technique that current engines do not carry cannot surface that way.

## 5. Classic mechanisms with no owner and no case

No card, option or build of these exists in the corpus. I found no evidence that would justify a card, so they are recorded only to save the next reader the search. The corpus was searched again for each row after the review; the search terms are given so the result can be repeated.

| Mechanism | What the corpus holds | Why it is not a candidate |
|---|---|---|
| One-reply and mate-threat extensions | No match for "one reply", "single reply", "mate threat", "threat extension". Matches for "one legal move" are about training-data filters and protocol tests, not about a search extension. | No current measurement found. The engine the crew diffed against removed its remaining special extensions without loss (`...:opus_deepres/notes/T04F/DIFF.md:177`). |
| Guard against repetition-tainted table scores (graph-history interaction) | **The problem is mentioned in six files; no guard is carded or built.** Two candidate notes name it as a caveat (`opus-r15-20261103:opus_r15/cands/c3_ttprobcut/README.md:29`, `astra-a1-data:opus_round1/C6/REPORT.md:156`). The crew's work on a multi-thread mate bug treats it as a possible cause (`astra3-smp-mate-rootcause:astra3/smp-mate-rootcause/REPORT.md:21`, `.../IMPLEMENTATION_HANDOFF.md:46`, `astra-a1-data:astra3/integration/A2_HANDOFF_PREPARATION.md:32`). One changelog line is unrelated. Today's `tcc21` candidate also works in this area: the engine its idea comes from files that check inside its own "partial workaround" for this problem (`IDEA_SOURCE.md` row 7). | **Partly owned**, through `tcc21` and the multi-thread mate work. No measured gain for a fuller guard in any source I found. The pawn-ending result in `EVIDENCE.md` section 5.8 is the kind of failure such a guard is meant to prevent, so this idea has about as much "evidence of need" as the unowned mechanism. |
| A different root driver (memory-enhanced test, MTD(f)) | No match for "mtd", "memory-enhanced", "SSS*". | No current engine evidence. |
| Deferred-move sharing between threads (ABDADA) | No match for "abdada", "young brothers", "YBWC". Two matches for "deferred move" are about other things (a move-list overflow, a move-picker speed note). | The crew's stated gate line is one thread, so it could not be decided there. |

An earlier version of this table said "zero corpus matches" for the second row. That was wrong and the reviewer caught it (`REVIEW_LOG.md`).

## 6. Limits of this dedupe

- **Scope.** It covers the 387 fetched branches, the PC folders named in `COVERAGE.md`, and nothing in the three banned folders.
- **Branch tips only.** The corpus holds each file as it stands at the tip of each branch. Work that was added and later deleted or reverted is not in it. For the unowned mechanism I also searched the commit messages of all fetched branches by name, after the review: 2,658 commits, no match (`data/commit_message_search.md`). For the other rows I did not.
- **Six file types only.** `.md`, `.cpp`, `.hpp`, `.h`, `.patch`, `.diff`. A mechanism recorded only in a `.txt`, `.json`, `.csv`, `.py`, `.ps1` or log file would be missed.
- **Twenty branches not fetched.** The `data/` and `results/` branches were left out for size.
- **Branches that moved during the job.** The snapshot was taken at 20:15 PT. I compared the remote again at 22:19 PT. No branch was added. One moved: `opus-smp-layout-20261107`, from `a675c04f` to `b5b52035`, seven commits about the shared-table layout. Its only source change is one comment line in `search.hpp`, and the line cited in row 16 is unchanged. Anything pushed after 22:19 PT is not covered.
- **Folders that appeared on the PC during the job.** Two, both read at 22:21 PT. `...\grok-pc\forge_deepres_stage_20261109\queue_entries_DR.json` (written 20:22 PT) holds 25 gate entries prepared from the crew's deep-research cards. None of them is the unowned mechanism. One is row 2 of the table above (`TwofoldNonPv=1`), and one is the `tcc21` option (`TtCutChildDepth=8`). `...\grok-pc\qa_pull_20261109_1309PT` is a pull of the shared-table layout job and has no match for the unowned mechanism.
- **Keywords.** A mechanism described only in prose that uses none of my keywords could be missed. For the unowned mechanism I reduced that risk with the code-shape search.
- **"LISTED" rows.** The crew's research notes sometimes list a mechanism without a decision. I treated every such row as not new, because your brief asks to check research notes before calling anything new. Some of those nine rows were never decided by anyone; they are not "rejected".
- **Boards outside the repo.** One search each in Linear and Notion found no Forge idea board. Any other board was out of reach.
