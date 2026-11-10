# IDEA_SOURCE: where each idea in this folder comes from

Terms are explained in `NO_QUALIFIED_GAP.md` section 9.

Rule followed: GPL and AGPL engines are ideas only. No code, constant, table or weight was copied from any engine. Everything under `tools/` is original work for this job. The harness `tools/etc_probe/etc_probe.cpp` links unmodified Forge lock sources (Couns's own code) and contains no third-party code.

## Sources read for the candidate mechanism (enhanced transposition cutoffs)

| # | Source | URL or revision | Date | Licence | What it actually supports | Quality |
|---|---|---|---|---|---|---|
| 1 | Plaat, Schaeffer, Pijls, de Bruin, "Exploiting Graph Properties of Game Trees", Proc. AAAI-96, pages 234-239 | https://cdn.aaai.org/AAAI/1996/AAAI96-035.pdf | 1996-08 | conference paper, copyright AAAI; ideas only | Defines the mechanism: before searching an interior node, look up all successors in the transposition table and take a cutoff that one of them already proves. States "For chess, ETC improves search efficiency by 28%". The chess program was Phoenix; figure 6 covers depths 2 to 9. | Primary. Read as search-tool excerpts of the PDF, not the full text. The 28 % figure is for a 1996 fixed-depth search without today's reductions. |
| 2 | Same authors, "Nearly Optimal Minimax Tree Search?", Technical Report TR 94-19, University of Alberta | https://arxiv.org/abs/1404.1518 (arXiv:1404.1518v1) | 1994-12 (arXiv copy 2014-04-05) | arXiv non-exclusive distribution licence; ideas only | Earlier description of the same mechanism. Section 4.1, as quoted by source 6: doing it at all interior nodes is too expensive for chess and checkers; doing it at nodes more than 2 ply from the leaves keeps most of the benefit; a variant that reorders moves from child entries "failed to yield a tangible improvement". | Primary. Section 4.1 wording seen through source 6 and through search excerpts. |
| 3 | Plaat, "Research Re: search & re-search", PhD thesis, Erasmus University Rotterdam | https://arxiv.org/abs/2403.13705 (v1) | 1996-06-20 (arXiv copy 2024) | arXiv licence; ideas only | Summary claim: the mechanism "reduces the search tree size for checkers and chess between 20%-30%, while incurring only a small computational overhead". | Primary. Excerpt only. |
| 4 | Schaeffer, Plaat, "New Advances in Alpha-Beta Searching", Proc. 24th ACM Computer Science Conference | https://liacs.leidenuniv.nl/~plaata1/papers/acm-final.pdf | 1996-02 | conference paper; ideas only | Plain-language description; no additional numbers used here. | Primary. Excerpt only. |
| 5 | TalkChess thread "Enhanced Transposition Cutoff" | https://www.talkchess.com/viewtopic.php?t=13005 (posts p=110838, 110865, 110868, 111779, 111790) | 2007-04-10 to 2007-04-14 | forum posts; ideas only | Practitioner reports, not controlled tests: one author saw "about 1% less nodes"; another keeps it "only at expected cut nodes" with at least 4 plies left and reports a minor gain; another reports a loss in a fast engine; another notes that internal iterative deepening already visits every child. | Secondary. Statements by engine authors, no data attached. |
| 6 | Chessprogramming wiki, "Enhanced Transposition Cutoff" | https://www.chessprogramming.org/Enhanced_Transposition_Cutoff | page fetched 2026-11-09 (cache dated 2026-07-13) | wiki text, CC BY-SA; ideas only | Says the technique "should not be applied at shallow depths", and that one well-known engine carried it in version 1.5 and dropped it from 2.0 because tests showed it hurt strength. | Secondary. The claim about that engine is not backed by a linked test; treat as UNVERIFIED. |
| 7 | Stockfish `src/search.cpp` on master | https://github.com/official-stockfish/Stockfish/blob/master/src/search.cpp (no revision pinned) | seen 2026-11-09 | GPL-3.0; ideas only, nothing copied | Seen only as search-tool excerpts (page copy dated 2026-11-07). The file confirms a table cutoff by looking at the entry after the hash move, which is the mechanism behind the crew's `tcc21` candidate. That check sits inside the block the authors introduce with the comment "Partial workaround for the graph history interaction problem". So the source engine files it with its guard against repetition-tainted table scores. I found no sign of enhanced transposition cutoffs in those excerpts. | UNVERIFIED as a citation (no pinned revision, excerpts only). Used only as context for `DEDUPE.md` rows 20 and section 5. |

**What I looked for and did not find:** any controlled test (SPRT or fixed-game match) of this mechanism in a current engine. Three searches on 2026-11-09 returned none. Absence of a published test is not evidence that it fails.

## Internal sources (Couns's own repo and PC)

| Source | Reference | Used for |
|---|---|---|
| Forge lock source of record | `D:\forge-qa\pack_combo29_20261108\pc_payload\source_snapshot` (hashes in `data/lock_source_hashes.tsv`) | all code references; linked unmodified by the harness |
| Crew deep-research notes | `opus-deepres-20261104@2231439c:opus_deepres/` | dedupe; crew gate rules and power arithmetic quoted in `EVIDENCE.md` |
| Crew candidate index | `opus-r15-20261103@2de61ac8:opus_r15/cands/INDEX.md` | dedupe |
| Crew pinned runner | `opus-r13-p1-nearmiss-ports@759acc6d:opus_r13/tools/run_pinned.py` | the idea of pinning the launching process so children inherit; my launcher is separate code and uses Idle instead of BelowNormal |
| Crew research method and gate request format | `astra-crew-skills-20261101@27752e05:plugins/forge-cpp-lab/skills/cpp-chess-engineering/references/research.md`, `.../gate-handover-pack/references/request-format.md` | structure of the evidence chain and field names of the gate proposal |
| Gate verdict table and logs | `C:\Users\Administrator\grok-pc\forge_push\FORGE_RESULTS.csv`, `D:\grok-pc-data\forge_push\gate*` | failure analysis |

## Position sets

- `tools/etc_probe/positions.epd` and `positions_deep.epd`: positions 1 to 8 are the eight positions of the engine's own `bench` command (`src/uci.cpp` lines 383-392 of the lock source). The rest are four widely published move-generator test positions and simple endgame set-ups typed for this job. No external file was downloaded.
- `tools/etc_probe/positions_wide.epd`: generated by the harness itself from the list above by playing its own best moves forward. No engine match was played.
- `tools/etc_probe/positions_supp.epd`: 48 opening positions taken at a fixed stride from `C:\Users\Administrator\grok-pc\coder-fuzz\UHO_Lichess_4852_v1.epd`, an opening collection already on the PC (read only), each played forward by the harness. The file is a list of positions, not engine code. **I did not check its origin or licence.** The 48 base positions are in the repo as plain position strings. If that is unwanted, delete the file; `data/SUPPLEMENT_RULE.md` says how to rebuild it.
