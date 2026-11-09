# opus_syzygy_gaps - evidenced gaps in the P6 Syzygy integration

Status lives in `STATUS.md`, the gap list in `GAP_LEDGER.md`, pins and identity in `BENCH.md`. All strength claims are UNPROVEN:
no games were played by this job, and nothing here says anything about Elo. Every ON path is a SEARCH CHANGE (or a report
change, where stated) and needs QA's own SPRT after Code Review.

## Parent and patches
- Actual parent: lock source `d4f43124` (exe FD3A5190) + `opus_r13/p6/syzygy_port.patch` md5 4342d24f = kit exe 150374ff, the exe of
  P6's gate lines. This is not trial_w6: trial_w6 is the same source + six node-identical speed switches.
- `patches/syzygy_gaps_after_p6.patch`: this job's change on the P6 tree. All code is behind three macros, default off.
- `patches/syzygy_port_and_gaps_after_w6.patch`: P6 port + this job's change on the trial_w6 source, where applicable (see BENCH.md).
- The reader is the own P6 reader, untouched. Fathom and python-chess are test oracles only (IDEA_SOURCE.md).

## Switches
Macros are compile-time, default 0: with all three at 0 the preprocessed source is the parent's and the kit exe is byte-identical to
it. With a macro at 1 a `tune::` int appears (default 0), advertised under `-Expose` like every search option. Existing option
names (`SyzygyPath`, `SyzygyProbeDepth`, `Syzygy50MoveRule`) are unchanged. All switches act only while tables are loaded.

| option (macro) | value | mechanism | kind of change |
|---|---|---|---|
| `SyzygyTbBounds` (FORGE_SYZYGY_TB_BOUNDS) | bit 1 | a TB loss stops forward pruning at a node, in the main search and in qsearch, as a mate loss does | search |
| | bit 2 | a TB-band null-move score is replaced by beta, as a mate score is | search |
| | bit 4 | TB-band best scores do not update correction history, as mate scores do not | search + eval |
| `SyzygyRootExact` (FORGE_SYZYGY_ROOT_EXACT) | 1 | root report: a win with exact dtz + counter = 100 is shown as a win; WDL-only ranks above counter 0 show the search score | report only |
| `SyzygyRule50` (FORGE_SYZYGY_RULE50) | bit 1 | a stored TB score that cannot be completed before move 100 at the current clock is not used | search (warm table only) |
| | bit 2 | changing `Syzygy50MoveRule` clears the hash while tables are loaded | option handling |

## Semantics
**WDL.** From the side to move: -2 loss, -1 blessed loss, 0 draw, 1 cursed win, 2 win. A WDL value assumes counter 0. Inside the
search it is read only right after a capture or pawn move, without castling rights, never at the root, never in a singular search.

**Cursed wins and blessed losses.** With `Syzygy50MoveRule` true they are draws for the search: exact score +-2 (`TbCursed`). With
false they are wins and losses. At a root they show +-2 unless a mate is found.

**Distance.** DTZ in plies from the side to move. Some tables store moves: then the true distance is |dtz| or |dtz| + 1 and the
reader sets `rounded`. A move's value at the root is its DTZ counted from the root position. A zeroing move has 1 (win), 101 (cursed win),
0, -101 (blessed loss) or -1 (loss). A mate counts as 1.

**Root ranks and the 50-move boundary.** Let c be the root counter, d the move's distance.
- Win, d + c <= 99: certain, rank 2000 (all equal, or 2000 - d if a position repeated since the last zeroing move).
- Win, d + c >= 100: rank 1000 - (d + c). At exactly 100 the zeroing move is the hundredth half-move, so an exact d still wins and a
  rounded d is undecided between win and cursed win. The move set is the same with every switch. `SyzygyRootExact` only corrects the
  report for the exact case. Deviation noted: the common rank convention leaves sum 100 at the same rank, and so does this job; only the
  report differs, using the `rounded` flag the reader already has.
- Loss, d + c >= 101: rank -1000 + (d + c), a 50-move draw is in reach. Otherwise rank -2000.
- Only the best-ranked moves are searched, inside a given `searchmoves` list (if the list excludes them all it is kept as given).

**Claim and automatic draws.** The engine does not model claims. As in the lock, 100 half-moves without a zeroing move are a draw in the
search unless the hundredth half-move mates, and the root reports a draw at counter >= 100. FIDE's automatic 75-move and fivefold rules are
not modelled separately: they lie beyond the draws the engine already assumes. The tablebase's own 50-move logic is the same claim
assumption.

**Repetition.** At the root a move into a third occurrence counts as a draw (distance 0), and a root whose line already repeated a
position ranks wins by distance. Inside the search any repetition after the root is a draw, as in the lock. Tablebase values do not know the
game history: that is why probes run only at counter 0 (no repetition is possible there) and why a root is ranked with the game history.

**Score bands and the TT.** Mate scores: |s| >= 31872, unchanged. TB band: 31743 <= |s| <= 31871, TbWin = 31871; a TB win found at ply p
scores TbWin - p and is reported as `cp`, never as a mate. While tables are loaded a TB-band score is stored as the distance from its node, like a
mate score. Without tables that range holds ordinary scores, stored unchanged. Bound direction: interior wins are lower bounds, losses upper
bounds, draws exact.

**Missing, corrupt, unsupported.** Missing folder, no tables: off. A file with a table name that fails validation is rejected at load and
counted. Probes return "no result" for castling rights, too many pieces, or a missing or inconsistent table: the search goes on without
them. Root: DTZ first, then WDL if a DTZ probe fails, unranked if a WDL probe fails. Body corruption that still parses is a limit of the
format without the checksum check: see the fixture notes in GAP_LEDGER.md.

## Test tools (`tools/`)
| tool | purpose |
|---|---|
| `env.ps1`, `pinned.ps1` | Idle + mask 0xF000, job TEMP; every job runs under them |
| `plain_build.ps1`, `kit_build.ps1` | plain build; kit v2.3 LTO+PGO, token for token as the speed job's `lp_v1` |
| `uci_tb.py`, `pins.py` | FEN runner over UCI (fails closed on pin or invalid FEN); bench and perft pins |
| `gen_fens.py`, `gen_clock_fixture.py`, `gen_warm_fixtures.py` | fixtures |
| `oracle_chess.py`, `fathom_root.c` | independent expected values |
| `tb_root.cpp`, `root_check.py` | root path: kept moves and report against the oracle |
| `make_instr.py`, `tb_claims.cpp`, `claims_build_run.sh` | test-only instrumented tree: every TB-band claim at a node against the full tables |
| `false_claims.py`, `move_quality.py` | root claims and move result against the oracle |
| `warm_claims.py` | warm-table fixtures for the rule-50 handling |
