# opus_syzygy_gaps - evidenced gaps in the P6 Syzygy integration

Status lives in `STATUS.md`, the gap list in `GAP_LEDGER.md`, pins and identity in `BENCH.md`. All strength claims are UNPROVEN:
no games were played by this job, and nothing here says anything about Elo. Every ON path is a SEARCH CHANGE (or a report
change, where stated) and needs QA's own SPRT after Code Review.

## Parent and patches
- Actual parent: lock source `d4f43124` (exe FD3A5190) + `opus_r13/p6/syzygy_port.patch` md5 4342d24f = kit exe 150374ff, the exe of
  P6's gate lines. This is not trial_w6: trial_w6 is the same source + six node-identical speed switches.
- `patches/syzygy_gaps_after_p6.patch`: this job's change on the P6 tree. All code is behind three macros, default off.
- `patches/syzygy_port_and_gaps_after_w6.patch`: P6 port + this job's change on the trial_w6 source, as one patch. Every check of that line passes (BENCH.md, trial_w6 line).
- The reader is the own P6 reader, untouched. Fathom and python-chess are test oracles only (IDEA_SOURCE.md).

## Switches
Macros are compile-time, default 0: with all three at 0 the preprocessed source is the parent's and the kit exe is byte-identical to
it. With a macro at 1 a `tune::` int appears (default 0), advertised under `-Expose` like every search option. Existing option
names (`SyzygyPath`, `SyzygyProbeDepth`, `Syzygy50MoveRule`) are unchanged. All switches act only while tables are loaded. Without tables nothing changes
with any value.

| option (macro) | value | mechanism | kind of change |
|---|---|---|---|
| `SyzygyTbBounds` (FORGE_SYZYGY_TB_BOUNDS) | bit 1 | a TB loss stops shallow pruning at a node, as a mate loss does. Without it a fail-soft TB loss with moves left unsearched is stored as an upper bound and reaches parents and the TT as a false TB win | search |
| | bit 2 | TB-band best scores do not update correction history, as mate scores do not | search + eval |
| | bit 4 | a null move that fails high with a TB-band score returns beta, as with a mate score: in a zugzwang passing wins and moving does not, so a null move proves no TB result | search |
| `SyzygyRootExact` (FORGE_SYZYGY_ROOT_EXACT) | bit 1 | root report: an exact dtz + counter = 100 win shows as a win; with WDL-only ranks and the 50-move rule on, above counter 0 the search score is shown, at counter 0 the root's own WDL | report only: same nodes, same moves |
| | bit 2 | root move set at the boundary: moves with dtz + counter = 100 are resolved by a budgeted walk (below), so a rounded move that really draws is not mixed with moves that lose. A root left undecided reports the search score, also without bit 1 | search (root move set, rare) |
| `SyzygyRule50` (FORGE_SYZYGY_RULE50) | bit 1, read side | with the rule on, a stored TB or mate score that cannot be completed before move 100 at the current clock is not used, and a stored probe result (distance 0) is used at clock 0 only | search: mostly with a warm table, rarely inside one search as well (same position at another clock) |
| | bit 1, store side | with the rule on, the TB loss distance of a non-root main-search node covers every searched move that ends in a mate. A loser prefers any TB loss to any mate, so without this the distance can understate the longest line, and the read side above would pass a score that is too late (R2 finding 2). Not at a root and not in qsearch: see `GAP_LEDGER.md`, Limits | search |
| | bit 2 | changing `Syzygy50MoveRule` clears the hash while tables are loaded | option handling |

`SyzygyTbBounds=7 SyzygyRootExact=3 SyzygyRule50=3` is the full set the suite ran on. `BENCH.md` has the per-bit numbers. Bits work alone, but they close the gaps only together where the ledger names two: `SyzygyRootExact=1` alone keeps the false TB losses of G5, `SyzygyRootExact=2` alone shows exact wins as +2 (first 1000 boundary rows: 28 and 13 wrong reports, 0 with 3), and `SyzygyTbBounds` bit 4 only matters with bit 1 (`zz2roots`).

## Semantics
**WDL.** From the side to move: -2 loss, -1 blessed loss, 0 draw, 1 cursed win, 2 win. A WDL value assumes counter 0. Inside the
search it is read only right after a capture or pawn move, without castling rights, never at the root, never in a singular search.

**Cursed wins and blessed losses.** With `Syzygy50MoveRule` true they are draws for the search: exact score +-2 (`TbCursed`), and a root shows +-2 unless a mate is found. With
false they are wins and losses, and a root shows a TB win or loss.

**Distance.** DTZ in plies from the side to move. Some tables store moves: then the true distance is |dtz| or |dtz| + 1 and the
reader sets `rounded`. A move's value at the root is its DTZ counted from the root position. A zeroing move has 1 (win), 101 (cursed win),
0, -101 (blessed loss) or -1 (loss). A mate counts as 1.

**Root ranks and the 50-move boundary.** Let c be the root counter, d the move's distance.
- Win, d + c <= 99: certain, rank 2000 (all equal, or 2000 - d if a position repeated since the last zeroing move).
- Win, d + c >= 101: rank 1000 - (d + c), shown as a cursed win.
- Loss, d + c >= 101: rank -1000 + (d + c), a 50-move draw is in reach. Loss, d + c <= 99: rank -2000.
- Exactly d + c = 100: the zeroing move is the hundredth half-move. An exact d wins or loses. A rounded d may be 101, which draws. The parent ranks all such wins 900 and all such
  losses -2000, so it can keep a move that loses next to one that draws (review R1, finding 1). With `SyzygyRootExact` bit 2 a rounded move is resolved by a walk: a table distance decides a
  reply unless it is itself rounded and exactly on the boundary; only those lines are followed, WDL after a zeroing move, repetition not modelled. The leading moves are walked in rounds with a growing
  cap per move (64, 256, then the rest), the memo kept across rounds, and the walk stops at the first proof. At most FORGE_SYZYGY_BOUNDARY_BUDGET (1000) moves per root, about 35 ms at worst on this PC. Result
  ranks: win 901, draw 899 or -899, loss -2000. If the budget runs out, or a table the walk needs is missing: 900 or -900, the root keeps those moves (a possibly drawing move goes before a sure loss)
  and reports the search score, because nothing is proved.
- Only the best-ranked moves are searched, inside a given `searchmoves` list (if the list excludes them all it is kept as given).
- Deviation noted: the common rank convention leaves sum 100 at one rank and reports it as a win. This job resolves or reports it as undecided, using the `rounded` flag the reader already has, checked by a
  solver that does not use that flag (`tools/oracle_exact.py`).
- With only WDL tables for some root move the ranks cannot see the counter. The move filter stays (limit: it may keep a move that is a 50-move draw at this clock); the report is handled by `SyzygyRootExact` bit 1.

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
them. Root: DTZ first, then WDL if a DTZ probe fails, unranked if a WDL probe fails. A DTZ file alone is not used. Body damage that still parses can give wrong values, because the file checksums are not
verified: the fixture only asks that the reader neither crashes nor reads out of range (GAP_LEDGER.md, Limits).

## Test tools (`tools/`)
| tool | purpose |
|---|---|
| `env.ps1`, `pinned.ps1` | Idle + mask 0xF000, job TEMP; every job runs under them |
| `plain_build.ps1`, `kit_build.ps1`, `preprocess_diff.ps1` | plain build; kit v2.3 LTO+PGO, token for token as the speed job's `lp_v1`; preprocessed source compare |
| `sanitize_builds.ps1`, `run_san.ps1`, `run_flip_asan.ps1` | g++ UBSan trap and MSVC ASan builds and runs, heap copies of the tables under ASan |
| `uci_tb.py`, `pins.py`, `identity_runs.ps1`, `compare_runs.py`, `identity_compare.sh`, `warm_identity.py` | FEN runner over UCI (fails closed on pin or invalid FEN); pins; node identity cold and warm |
| `gen_*.py`, `zz_scan.cpp`, `table_identity.ps1` | fixtures (clock, boundary, special, underpromotion, warm, two zugzwang sets, boundary roots with a missing child table), mutual zugzwang scan, table hashes |
| `oracle_chess.py`, `fathom_root.c`, `oracle_exact.py` | independent expected values: python-chess, Fathom, DTZ-free boundary solver |
| `tb_root.cpp`, `root_check.py`, `root_move_check.py`, `exact_check.py` | root path and engine moves against the oracles |
| `make_instr.py`, `tb_claims.cpp`, `claims_build_run.sh` | test-only instrumented tree: every TB-band claim at a node against the full tables, cold and warm |
| `false_claims.py`, `move_quality.py`, `mate_pv_check.py` | root claims and move result against the oracle, mate PV replay |
| `warm_claims.py`, `warm_move_check.py`, `playout_check.py`, `uci_misc_checks.py`, `run_partial.sh`, `gen_partial_tables.py` | warm-table fixtures and the moves played there; lines against an oracle opponent; searchmoves, castling, protocol, Threads soak; partial and damaged table sets |
| `qual_all.sh`, `special2.sh`, `run_v6.sh` | the whole suite for one exe + options |
| `final_chain.sh`, `final_freeze.sh`, `repro_from_pack.sh` | everything for a frozen head; the freeze proof (patch, preprocess, Build A, Build B pc1 = pc2, pins, identity cold and warm, per-option bench); a tree rebuilt from the pack alone |
| `after_w6.sh`, `after_w6_compare.sh`, `w6_arm_check.py` | the trial_w6 line, each check fail-closed; its compares from finished row files; changed lines against the speed conditionals |
| `exact_full.sh`, `und_check.py`, `exact_partial.py` | boundary runs against all exact oracle rows; bad rows on decided or undecided roots, with the parent as control; what resolved moves alone prove on rows the solver did not finish |
| `uci_churn.py`, `run_churn.sh`, `gen_warm_pred_fixture.py`, `run_pred.sh`, `info_runs.sh` | random option and table changes between searches; a root's entry read inside a later search; per-bit information |
| `gen_warm_read_fixture.py`, `mutants_read_side.sh`, `mutate_one.py`, `read_subset.sh` | rows where a read-side rule of `SyzygyRule50` bit 1 decides, with the mutants they must catch; `read_subset.sh` runs one built exe on the first rows only |
| `collect_logs.sh`, `make_manifests.sh` | compact logs into `logs/`; MD5 and SHA256 manifests of the pack |
