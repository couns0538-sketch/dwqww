DRAFT of the block to append to STATUS.md when the 12-hour window closes (2026-11-17T10:19Z).
Kept here so the wording cannot drift; the live block is appended to STATUS.md at the close.

## <date -u at close> FINAL

seat 17 | area 7 (reading the code) + the PC path (softnodes, node tiers, match clock) | Threads 1 | branch for-fable-and-opus/swarm-17

THE DELIVERABLE IS THE DOCUMENT SET, not a list of rows. Read in this order:

1. forge-combo29/swarm/17/FINDINGS_TABLE.md
   Every finding and every negative, each with its build (base 6b98f217 or PC r15), its settings
   (none / S14 / PC20), Threads 1, and whether a GUI can reach it. Supports the decision of what to fix next,
   ranked by what the owner can actually hit rather than by what is technically wrong.
2. forge-combo29/swarm/17/NOTE_moves_path_hazard.md
   The per-move hazard: `info string illegal move` -> `readyok` -> a bestmove for a board the caller never
   asked for. Supports the decision of whether the engine should refuse harder, and gives a GUI author the one
   rule that makes it safe today (treat that line as fatal for the game).
3. forge-combo29/swarm/17/NOTE_select_readline_artifact.md
   The Python harness artefact that fabricates an unbounded run. Supports the decision of how to read engine
   output in any future harness, so a measurement is not a false hang.

Supporting evidence in the same folder: REPORT_job1.md, REPORT_job2.md, REPORT_job3.md, PC_BUILD.txt,
HONESTY.txt, and the raw job folders (job1/, pc/) that every table row points at.

State of my own finds at the close: S-F1 and S-F8 (bestmove 0000 / zero-node reports on a no-legal-match
`searchmoves` root) are OPEN and still present on the PC build; low exposure because the match program and
self-play never send `searchmoves`. S-F2 withdrawn by me. S-C11 and S-C12 withdrawn per FABLE_TO_swarm_6.
Everything else on the PC path came back clean, with the 30-game clock test and the 180-line legality sweep
as the two strongest "it works" results.
