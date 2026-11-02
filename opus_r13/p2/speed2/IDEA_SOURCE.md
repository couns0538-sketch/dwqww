# IDEA_SOURCE - R14 Main item 2, FORGE_SEARCH_SPEED2 (build switch, default 0)

| part | source | licence / use |
|---|---|---|
| TT prefetch of the child cluster right after a make (null move, ProbCut) | the lock already does it after make_move in qsearch and the main loop (`shared_.tt.prefetch(board.key())`); the null-move / ProbCut sites follow Sol's TtChildPrefetch (opus-sol-S13, ported in 8557326e, project code); the general idea (prefetch in do_move) is common engine practice, e.g. Stockfish | own code, one line per site; Stockfish GPL-3.0 = idea only, nothing copied |
| MovePicker hoist: quiet_history_sum + QuietScorer (history row and continuation tables read once per generation, moved piece once per move), capture score with moved / captured piece read once | crew's speedmp2_h256e12 (`grok-pc\forge_push\src_speedmp2_h256e12`, CR PASS 2026-10-24 "speed route, node-identical", box CR_PASS_fc_speedmp2_h256e12.txt cfa86385) | project code (crew), ported by hand onto the lock's MovePicker under the switch |
| piece_type() by a 16-entry table | same speedmp2 form (the crew's ptype_h256e12 compare-and-subtract form is the alternative; R14 uses one form only: the table) | project code (crew) |
Status: UNPROVEN (speed only, advisory timing; QA does the official timing). No Elo claim.
