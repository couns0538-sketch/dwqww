# FINDINGS - seat 17 (area 7, reading the code for faults)

One line per finding, only ever added. A check of another seat's finding is its own line.

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-F1 | 7 | `go depth N searchmoves <name with no legal root move>` answers `bestmove 0000` on a position that HAS legal moves (startpos: 20 legal, 0000 returned) - UCI defines 0000 as "no legal move exists", so a GUI reads it as an illegal move | `forge-combo29/swarm/17/job1/finding_searchmoves.py` (run: `cd forge-combo29/swarm/17/job1 && python3 finding_searchmoves.py /agent/repos/base/forge-combo29/build/forge sm`) | NEW |
| S-F2 | 7 | WITHDRAWN - my stated SOURCE for S-F1 was wrong. I claimed `src/search.cpp:2640` reads `front()` of an empty MoveList; it does not, because every empty-`root_candidates` path returns at the early block on line 2253. The OBSERVABLE S-F1 (`bestmove 0000` with 20 legal moves) stands and is still mine; the mechanism I gave for it does not | refuted by my own marker test, `forge-combo29/swarm/17/job1/reach_check/flow.json` (`EARLY_PATH cand=0 ... legal=20` and no `PAST_EARLY` for every searchmoves case) | WITHDRAWN (source only) |

## Harness correction (swarm broadcast, seat 19 finding 19-F12), recorded by seat 17 on 2026-11-16T21:34Z

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-C0 | CONFIRMS 19-F12 | A pipelined `go depth 12` + immediate `quit` answers `bestmove a2a3` with 0 `info` lines, while the same search read to `bestmove` answers `e2e4` at 56,720 nodes; my harness gets the 56,720-node answer, so my results are from a harness of the second kind | `forge-combo29/swarm/17/job1/harness_check.py` (run: `cd forge-combo29/swarm/17/job1 && python3 harness_check.py /agent/repos/base/forge-combo29/build/forge harness_ok`) | CONFIRMS |

### Which of my own recorded results were affected
- INVALID and RE-RUN: `proof_runner.py` pipelined its command list including `quit`, so its first
  "real build, 0 sanitizer lines" run measured a search that never ran (the planted faults were
  unaffected - their hooks fire before the search). The runner now reads to `bestmove`, and the proof
  was re-run at 2026-11-16T21:34Z: real search reaches depth 6 / 1703 nodes / 0 sanitizer lines;
  planted heap over-read 2 lines; planted signed overflow 1 line. Files replaced in `job1/proof/`.
- NOT AFFECTED: `run_asan.py` / `run_asan.sh` always read stdout until `bestmove` before writing
  `quit`; a raw log (`job1/asan_G_1_12/one_1.log`) ends at depth 14 with 131,575 nodes and an `e2e4`-class
  answer, not `a2a3` with 0 nodes.
- NOT AFFECTED: `finding_searchmoves.py` (S-F1/S-F2) uses the same read-to-bestmove driver and its
  `bestmove 0000` answers are accompanied by `info depth 1..5` lines.

## Measurement-integrity audit (seat 19 warning), recorded by seat 17 on 2026-11-16T21:37Z

| id | area | one sentence | file with the exact command | state |
|---|---|---|---|---|
| S-C0b | CONFIRMS 19-F12 (measurement rule) | my own checker had the same defect class: `harness_check.py` defaulted a missing `nodes` field to 0, so an unmeasured run printed "nodes=0" like a measured zero; it now prints `None` and every claim is asserted to rest on lines the engine actually printed | `forge-combo29/swarm/17/job1/harness_check.py` (run: `cd forge-combo29/swarm/17/job1 && python3 harness_check.py /agent/repos/base/forge-combo29/build/forge harness_ok`) | CONFIRMS |

### What changed, and the proof each guard fails when it should
- `run_asan.py`: refuses an exe with no sanitizer symbols (else "0 sanitizer lines" would mean nothing);
  counts `not_measured` (missing bestmove / missing info depth / missing node count) separately from clean
  results; exits non-zero when nothing was measured. Guard shown failing:
  `python3 run_asan.py <release exe> G.epd 1 2 8 /tmp/guard1` -> `FATAL: ... has no __asan_/__ubsan_/__tsan_ symbols`.
- `proof_runner.py`: each case now asserts the evidence it exists to show (real search: >=1 info depth line
  AND a node count; planted cases: >= expected sanitizer lines). Guard shown failing: pointing the planted case
  at an unplanted build gives `FATAL: case planted_heap_overread proves nothing: expected >= 2 sanitizer line(s), saw 0`.
- `harness_check.py`: an empty log raises `FATAL: ... no bestmove line; no info depth line ...`.
- Re-run after the fix (evidence in `job1/proof/` and `job1/harness_ok/`): real search 6 depth lines,
  1703 nodes, 0 sanitizer lines; planted heap over-read 2 lines; planted signed overflow 1 line.

## Correction of my own S-F2 (2026-11-16T21:42Z), after reading seat 07's 07-R1

Seat 07's 07-R1 says my S-F2 source claim is wrong; it is, and I checked it myself rather than
taking it on trust. Scratch copy of 6b98f217 with marker prints (`/tmp/reach17`, not committed):
- `go depth 5 searchmoves e7e5` on startpos: `EARLY_PATH cand=0 drawn=0 legal=20`, and NO `PAST_EARLY`.
- `go depth 5 searchmoves zzzz`: same.
- `go depth 5 searchmoves e2e4`: no `EARLY_PATH`, `PAST_EARLY cand=1`.
- `go depth 6` startpos: `PAST_EARLY cand=20`.
- checkmated root: `EARLY_PATH cand=0 ... legal=0`.
So the empty-candidate case always leaves through line 2253; line 2640 never sees an empty list.
My first marker attempt was worthless (I instrumented a statement guarded by `is_none()`, so it
could not fire even on the normal path and proved nothing) - replaced by the control-flow markers
above. The observable S-F1 answer stays: `bestmove 0000` is returned while `legal=20`.
| S-C1 | CONFIRMS 07-R1 | seat 07 is right that search.cpp:2640 is not an empty-container read; my own marker test shows every empty-root_candidates search leaves at the 2253 early block (`EARLY_PATH cand=0 drawn=0 legal=20`, no `PAST_EARLY`) | `forge-combo29/swarm/17/job1/reach_check/flow.json` | CONFIRMS |
| S-C2 | CONFIRMS 07-F1 | reproduced on my build with my own driver: the five info lines are literally `score cp 0 nodes 0 nps 0 hashfull 0 time 0 pv` (empty pv) and the answer is `bestmove 0000`, while python-chess says the root has 20 legal moves; 07's extra claim (unsearched roots presented as a 0-node draw) is exactly what the raw lines show | `forge-combo29/swarm/17/job1/reach_check/case07f1.log` (driver: job1/uci_driver.py) | CONFIRMS |
| S-C3 | 07-F1 vs my S-F1 | note, not a refutation: S-F1 and 07-F1 describe the same engine behaviour from two seats. 07-F1 adds the `score cp 0 nodes 0` presentation and the `restricted_root_empty` plumbing detail; my S-F1 is the `bestmove 0000`-on-a-live-position statement. Neither supersedes the other | both command files | OVERLAP |
| S-C4 | CONFIRMS 27-F2 | exact threshold reproduced on my build at startpos: `go nodes` 1/5/10/20/25 answer `bestmove a2a3` with ZERO info depth lines; 26 answers `d2d4` with `info depth 1 ... nodes 26 ... pv d2d4`; the boundary is 26 as seat 27 said (not a range) | `forge-combo29/swarm/17/job1/check27/nodes.json` + `job1/check27/nodes_*.log` | CONFIRMS |
| S-C5 | CONFIRMS 27-F4, weaker rate | same effect, my numbers: on 8 G positions at depth 10 (S14 not applied), a fresh process vs the same process after `setoption name Clear Hash` gives the same bestmove for 7 and a DIFFERENT bestmove for 1 (index 7: `g5h5` fresh vs `g5h6` after Clear Hash). So the histories do survive Clear Hash as 27-F4 says; my changed-rate is 1/8, not their 9/20, because my sample, depth and position set differ | `forge-combo29/swarm/17/job1/check27clear/clear_hash.json` | CONFIRMS (rate differs) |
| S-C6 | CONFIRMS 27-F4 (baseline corrected after seat 10's rule) | `setoption name Clear Hash` between two searches changes the depth-10 node count in 20/20 G positions and the bestmove in 1/20, while `hashfull` drops to 0, so the TT is emptied and the surviving difference is attributable to the histories. CORRECTION: my first version of this line called the fresh process the baseline, which conflates two effects - seat 10 is right that a repeated search in one process already drifts (10/10 positions: 23448 -> 5067). The claim that survives is narrower and I keep only that: after Clear Hash the residual drift is not the TT, because the TT was emptied | `forge-combo29/swarm/17/job1/seat10/cold_warm_clear.json` (cold / warm / clearhash columns), `job1/check27clear/` | CONFIRMS (re-labelled) |
| S-F3 | 7 | NOT a fault, recorded because it protects the honesty numbers: `bench 13` returns nodes 862329 identically after 0, 1, 2 and 5 preceding depth-6 searches in the same process, so the history drift of 27-F4 / my S-C6 does NOT contaminate the pinned node counts - `bench` resets that state itself. Any harness that compares bench pins across runs is therefore safe from this particular drift | `forge-combo29/swarm/17/job1/bench_repeat/bench_after.json` | NEGATIVE |
| S-F4 | 7 | Methodological trap, not an engine fault: `OwnBook` defaults to TRUE, so any clock or time-management measurement that starts from the initial position is answered by the book in ~0 ms with no `info depth` line. My own first clock run measured nothing this way (5 "results" with 0 depth lines). With `setoption name OwnBook value false` the same searches scale as expected: wtime 1000 -> 55 ms / depth 14, 10000 -> 374 ms / depth 18, 100000 -> 5234 ms / depth 25 | `forge-combo29/swarm/17/job1/clock/clock.json` (0 depth lines, book on) vs `clock/clock_nobook.json` (book off) | NEW (method) |
| S-F5 | 7 | NOT a fault, checked and clean: the one unchecked multiply in the clock plan (`clock_plan.hpp`, `hard = min(available*4/5, soft*4)`) does not overflow under ASan+UBSan even at `wtime 9223372036854775807 movestogo 1`; the search simply runs its (huge) budget with 22 depth lines and no `runtime error` line | `forge-combo29/swarm/17/job1/clock/clock_extreme_nobook.json` | NEGATIVE |
| S-F6 | 7 | NOT a fault, deep-search stack safety on record: under ASan+UBSan, `go nodes 2000000` reaching seldepth 64 in two positions and seldepth 48 on startpos produced 0 sanitizer lines; the two `bestmove 0000` answers in that batch are correct terminal roots (verified with python-chess: one is checkmate, one is STALEMATE with 0 legal moves), i.e. the known case, not a fault | `forge-combo29/swarm/17/job1/maxply/maxply2.json` | NEGATIVE |
| S-F7 | 7 | NOT a fault, history arithmetic at its advertised extremes: every history/LMR/move-ordering tunable set to its advertised max and then its min, 5 G positions each at depth 12 under ASan+UBSan, gave 0 sanitizer lines. The tunables demonstrably took effect (same positions: max set 6,380-29,330 nodes; min set 91,404-567,342 nodes, a 40x spread), so this is a real stress of `apply_history`, `history_bonus` and the reduction tables, not a run with the options ignored | `forge-combo29/swarm/17/job1/job2/hist_extremes.json` | NEGATIVE |
| S-C7 | CONFIRMS (known item, Opus FABLE_TO_swarm_1) | the known "a root restricted by searchmoves searches a different, mostly smaller tree" is quantified on my build: on one G position with ALL legal moves listed in searchmoves, nodes are 1451 vs 2986 (d8), 5763 vs 11342 (d10), 29306 vs 50704 (d12) - the restricted tree is about HALF the unrestricted tree at every depth, while the bestmove is identical. So it is a real effort distortion, not just a different tree | `forge-combo29/swarm/17/job1/job2/allmoves_parity.json` | CONFIRMS known |

## Warm/cold correction after seat 10's rule (2026-11-16T21:52Z)

Seat 10 states: two identical unrestricted searches in ONE process drift (56,720 -> 4,951 -> 4,516),
three separate processes do not, `ucinewgame` restores cold, `Clear Hash` does NOT. I reproduced all four
parts exactly (`seat10/one_proc.log`, `seat10/proc_*.log`, `seat10/newgame.log`, `seat10/clearhash.log`:
56720 / 56720 / 56720 / 40569).

Which of my results this affects:
- S-C5 (Clear Hash bestmove change 1/8) and S-C6 above: both compared a fresh process with a post-Clear-Hash
  search, i.e. a cold run against a warm run PLUS a TT clear. The comparison is confounded and is now
  labelled as such. What is still solid: `hashfull` goes to 0 after Clear Hash, so the TT really is emptied,
  and the drift that remains cannot be the TT.
- S-F3 (bench 13 = 862329 after 0/1/2/5 prior searches) is NOT affected: it used one process deliberately
  and found the pin unchanged, and `bench` is its own cold-ish path; the result stands as measured.
- Every ASan sweep is single-search-per-process by construction (`run_asan.py` launches one engine per
  position), so no ASan node count in this job was measured warm.
- S-C7 (restricted vs unrestricted, 24 halves) compared two separate processes per depth, so it is cold on
  both sides; it is a tree-size comparison anyway, not a repeated-search drift claim.

Rule I now follow: a cold baseline is a fresh process or `ucinewgame`, never `Clear Hash`, and a warm
comparison is labelled warm.
| S-C8 | CONFIRMS 10 (warm/cold rule) | reproduced all four parts on my build: one process 3 identical searches = 56720 / 4951 / 4516; three processes = 56720 three times; `ucinewgame` between = 56720 / 56720; `Clear Hash` between = 56720 / 40569. Also separated the two effects on 10 G positions: warm repeat differs from cold in 10/10, and Clear Hash differs again from warm in 10/10 | `forge-combo29/swarm/17/job1/seat10/` | CONFIRMS |
| S-F8 | 7 | NOT a new fault, bounded and recorded: `searchmoves` with no legal match combined with other limits. `go nodes 1000 searchmoves e7e5` and `go movetime 100 searchmoves e7e5` both emit 64 `info depth` lines (depth 1..64) ALL with `nodes 0`, i.e. the depth limiter is not reached by a node or movetime budget because no search happens - the terminal-root loop runs to max_depth. `go depth 5 searchmoves e2e4 e2e4 e2e4` de-duplicates correctly and answers `e2e4`. `searchmoves e7e8q` (a promotion that cannot exist here) answers 0000. 0 sanitizer lines in all of them | `forge-combo29/swarm/17/job1/job2/sm_nodes.log`, `sm_movetime.log`, `sm_dup.log`, `sm_promo.log` | NEGATIVE / detail for 07-F1 |
| S-F9 | 7 | NOT a fault, TT resize verified: `Hash` 1/8/32/512/2048 MB changes only the pressure, not the answer - hashfull 440 / 58 / 10 / 0 / 0 and nodes 53652 then 52591 four times, bestmove identical; 18 ASan+UBSan searches with Hash set to min, max and toggled between searches all clean (0 sanitizer lines). The epoch/slot guards in `store_body` do their job | `forge-combo29/swarm/17/job1/job3/hash_sizes.json`, `job3/hash_resize.json` | NEGATIVE |
| S-F10 | 7 | My own method lapse, recorded per the honesty rule: I first measured Hash sizes by PIPELINING `quit` into the search and got `None` for all five sizes - the 19-F12 fabricated-answer trap. Re-run with the read-to-bestmove driver the same five sizes measured properly. Any harness I report from now on is the driver one | `forge-combo29/swarm/17/job1/job3/hashsize_1.log .. hashsize_2048.log` | NOTE |

## S-F8 follow-up: is the no-legal-match searchmoves root unbounded on the clock? NO. (2026-11-16T22:00Z)

Asked to confirm the unbounded part on the clock. I could not confirm it, and the honest answer is that my
own first attempt said the opposite of the truth, so both are recorded.

1. My FIRST harness (`job2/unbounded_check.py`, select()-based polling on a buffered text pipe) reported that
   `go movetime 100 searchmoves e7e5` ran 20.0 s with no bestmove, and that TWO CONTROLS did the same
   (`go wtime 1000 btime 1000 searchmoves e2e4`, and `go wtime 1000 btime 1000` with no searchmoves at all).
   Controls failing is the tell: a correct control cannot take 20 s at a 1 s clock, so the measurement was
   faulty, not the engine.
2. Re-measured with the blocking read-to-bestmove driver (`uci_driver.run_one`), and then a THIRD time with a
   plain shell pipe and no Python at all:
   | go line | bestmove | wall |
   |---|---|---|
   | `go movetime 100 searchmoves e7e5` | `bestmove 0000` | 19 ms |
   | `go wtime 1000 btime 1000 searchmoves e7e5` | `bestmove 0000` | 18 ms |
   | `go movetime 100 searchmoves e2e4` (control) | `bestmove e2e4` | 91 ms |
   | `go wtime 1000 btime 1000 searchmoves e2e4` (control) | `bestmove e2e4` | 36 ms |
   | `go wtime 1000 btime 1000` (control) | `bestmove e2e4` | 67 ms |

Conclusion, stated plainly: with no legal match for `searchmoves`, the engine returns `bestmove 0000` on its
own in about 18-19 ms, well inside any time limit. It does NOT hang and it is NOT unbounded, and it does not
need `stop`. What IS true from S-F8 is narrower: the 64 `info depth` lines are emitted with `nodes 0` and
`time 0`, i.e. it reports a completed search of 64 depths that was never searched - a false report, not a
long one. The `time 0` / `nodes 0` in every line is the misleading part, not the wall time.
Evidence: `forge-combo29/swarm/17/job1/job2/unbounded/recheck.json` and `recheck_*.log`;
the faulty first attempt is kept beside it as `unbounded/unbounded.json` so the error is visible.
| S-F11 | 7 | Root cause of my faulty S-F8 first attempt, recorded so no other seat repeats it: `select()` on a text-mode `subprocess` pipe fires when BYTES arrive, but the following `readline()` on that buffered text stream then blocks waiting for a complete line. A diagnostic read of `uciok` this way took 5.03 s and returned exactly 1 line instead of finishing in milliseconds. Any timing harness must either read with a blocking `readline()` per expected answer (what `uci_driver.py` does) or use non-buffered binary reads; mixing `select` with `readline` invents timeouts | `forge-combo29/swarm/17/job1/job2/unbounded/unbounded.json` (faulty) vs `unbounded/recheck.json` (correct) | NEW (method) |
| S-C9 | CONFIRMS 21-F2 (the readyok part) | reproduced on my build: after a REFUSED `position fen` the engine prints `info string invalid FEN: invalid FEN fields` and then still answers the following `isready` with `readyok` (raw line order: readyok / readyok / "invalid FEN" / readyok / nodes 29). So a GUI that syncs on readyok cannot tell that the position was refused and that the OLD position is still loaded. I did NOT reproduce their "wrong side" wording as a separate claim - on my run the kept position is simply the previous one (29 = after e2e4 e7e5, and 20 from a bare startpos), which is the known item | `forge-combo29/swarm/17/job1/check21/c9_readyok_after_refusal.txt` | CONFIRMS |
| S-C10 | CONFIRMS 21-F8 | `position fen 4k3/8/8/8/8/8/8/4K3 w - - 0 0` (fullmove 0) is REFUSED by Forge (`invalid FEN fields`) while python-chess accepts it and says the position has 5 legal moves; because the refusal keeps the old board, `go perft 1` then answers 20 (startpos) instead of 5 | `forge-combo29/swarm/17/job1/check21/c10_fullmove0.txt` | CONFIRMS |
| S-C11 | CONFIRMS 21-F9 (sharply) | reproduced with a clean boundary: one board with a mate in 1 for White (`6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - <hm> 1`). At halfmove 0 and 99 all three limits (`go depth 5`, `go nodes 1000`, `go movetime 50`) answer `a1a8` scored `mate 1`. At halfmove 100 and 150 all three answer `f2f3` scored `cp 0 nodes 0` - the mate in 1 is MISSED. The boundary is exactly at 100, and it is search-limit-blind (all three `go` forms) as 21-F9 says. python-chess confirms a1a8 is mate | `forge-combo29/swarm/17/job1/check21f9/f9.json` | CONFIRMS |
| S-C12 | CONFIRMS + severity of 21-F9 | severity, checked rather than assumed: (a) python-chess VALIDATES the halfmove-100 mate-in-1 FEN (is_valid True, status 0, 20 legal moves, mate a1a8 available), so the engine can be handed it by any GUI, book tool or file; (b) in a real game the fifty-move rule is a CLAIM, not automatic, so a counter >= 100 with a mate available is reachable whenever neither side claimed; (c) this engine models no claim at all - search.cpp:2251 treats `halfmove_clock() >= 100` as a drawn root and search.cpp:1302 does the same inside the tree - so it adjudicates a draw the rules do not require and never searches; (d) the raw log at halfmove 100 shows depth 1..5 all `nodes 0` with an EMPTY pv, i.e. no search was performed | `forge-combo29/swarm/17/job1/check21f9/f9.json`, `check21f9/hm100_5.log`, `check21f9/severity.txt` | CONFIRMS (severity assessed) |

## Threads audit (swarm rule, after seat 04's measurement), seat 17, 2026-11-16T22:22Z

Rule now in force: any score reported must be from Threads 1 unless the job is about threading.
Seat 04 measured the PC build at Threads 4, depth 12, PC20: four fresh runs on ONE position gave
+2576 / mate 13 / mate 18 / mate 16, nodes 5.0M-31.4M; Threads 1 gave +2207 four times with identical
nodes 75,311. Move stable, scores not.

My audit:
- I set Threads above 1 in EXACTLY ONE place: the `threads4` set of the job1 MultiPV sweep,
  `job1/mpv/mpv.json` (6 records). Those records contain NO score, and I never cited any of them in
  FINDINGS or a report, so no recorded claim of mine rests on a multi-threaded score.
  Their NODE COUNTS are provisional (not reproducible above Threads 1) - flagged here.
- Every other measurement I have reported used the default, which the exe's own `uci` list states as
  `option name Threads type spin default 1`. My ASan runner (`run_asan.py`) never sends a Threads
  option at all (`grep -c Threads` = 0), so every ASan sweep, every honesty line, the PC20 PC-build
  check, and the S-F1/S-F8/S-C9..S-C12 checks are Threads 1.
- Finding lines from here state "Threads 1" explicitly, plus build (base or PC r15) and settings
  (none / S14 / PC20).

## PC r15 re-run of my finds and checks (2026-11-16T22:22Z) — every line Threads 1

Build: PC r15 (base 6b98f217 + FABLE_TO_swarm_5.patch, sha256 d6bd72c531f785f4..., built with
-DFORGE_MATE_ALPHA_GUARD=1). Settings: PC20 (S14 + CuckooRep/HistRework 2/TtPruneV2/CorrHistV2/
MateAlphaGuard/OwnBook false). Threads 1, Hash 16. Comparison column is the base tree under S14.

| my id | base tree (S14, Threads 1) | PC r15 (PC20, Threads 1) | verdict |
|---|---|---|---|
| S-F1 (`bestmove 0000` on a live 20-move position) | 0000, 5 zero-node depth lines | **0000, 5 zero-node depth lines** | **STILL PRESENT on the PC build** |
| S-F8 (no-match `searchmoves` prints depth lines of `nodes 0`) | 64 lines, nodes 0 | 64 lines, nodes 0 | STILL PRESENT |
| S-C10 (`fullmove 0` refused, old board kept) | refused, plays old board | refused, plays old board | STILL PRESENT |
| S-C11 (halfmove 100 misses a mate in 1) | `f2f3`, `cp 0 nodes 0` | **`a1a8`, `score mate 1`, nodes 84/105** | **REPAIRED on the PC build** (FORGE_FIX_ROOT_DRAWN) |

So of my own finds, S-F1 and S-F8 are live defects on the engine the owner actually plays, and the
missed-mate I confirmed for seat 21 is fixed there. Evidence: `pc/recheck/S-F1_pc20.log`,
`S-F8_pc20.log`, `S-C11_pc20.log`, `S-C11_base.log`, `S-C10_*`, summary `pc/recheck/recheck.json`.

## Answer to the two follow-up questions (2026-11-16T22:36Z) — all Threads 1

### Q2: does the PC's FORGE_FIX_ROOT_DRAWN also cover the counter-resetting PAWN-move mate?

YES, on the decisive board. A pawn move resets the fifty-move counter, so a pawn-move mate is the strongest
test: the position after it cannot be a fifty-move draw at all.

Decisive board `r7/1P6/8/8/8/8/8/k1K5 w - - <hm> 1`, only mate `b7a8q` (capture-promotion, SAN `bxa8=Q#`).
Measured: the engine's own generation order puts `b7b8q` FIRST and `b7a8q` fifth, so the base tree's
"play the first legal move" fallback plays the WRONG move here:

| build / settings | hm | bestmove | last score | max nodes | mate found |
|---|---|---|---|---|---|
| base 6b98f217 / S14 | 100 | `b7b8q` | `cp 0 nodes 0` | 0 | **NO** |
| base 6b98f217 / S14 | 99 | `b7a8q` | `mate 1` | 60 | yes |
| PC r15 / PC20 | 100 | `b7a8q` | `mate 1` | 60 | **YES** |
| PC r15 / PC20 | 99 | `b7a8q` | `mate 1` | 60 | yes |

So the PC's fix covers the pawn-move case too, on a board where the base tree demonstrably fails. Note the
first three promotion-mate boards I built (`8/P7/...`) were NOT decisive: there `a7a8q` happens to be the
engine's first generated move, so the base tree plays the right move by luck with a 0-node score. I say that
because a luck-passing case would have been a false "repaired" verdict.
Evidence: `pc/pawn_check/decisive.json`, `pc/pawn_search/decisive_pawn_mate.json`,
`pc/pawn_search/engine_order_check.json` (the luck cases, listed so they are not reused as evidence).

### Q1: are S-F1's five zero-node lines the same defect as 19-F12's aborted-search fabrication?

NO — two separate defects, proven with markers in a scratch copy of the PC r15 tree (`/tmp/pathprobe`,
never committed). PC r15 has only ONE textual `result.best_move.is_none()` catch-all (line 3017, the one
19-F28 names); the other same-shaped fallback is the root-drawn early-return block. I marked both and ran
six cases (Threads 1, no setoption):

| case | marker that fired | bestmove |
|---|---|---|
| `go depth 5 searchmoves e7e5` (S-F1) | `PATH_EARLY_ROOTDRAWN count=0` | `0000` |
| S-F1 Black to move | `PATH_EARLY_ROOTDRAWN count=0` | `0000` |
| `go nodes 1000 searchmoves e7e5` (S-F8) | `PATH_EARLY_ROOTDRAWN count=0` | `0000` |
| `go depth 5` normal | neither | `c2c4` |
| halfmove 100 mate (S-C11) | neither | `a1a8` (repaired, searched) |
| K+N vs K (insufficient) | `PATH_EARLY_ROOTDRAWN count=8` | `g1e2` (correct: all moves draw) |

So:
- 19-F28's catch-all at `src/search.cpp:3017` **never fires** in any of my six cases. Seat 19's finding is
  about a search ABORTED before an iteration completes (quit/EOF mid-search); mine is a root that is
  adjudicated terminal BEFORE any search starts.
- S-F1 is the early block, and it explains the `0000`: with `searchmoves` matching nothing,
  `root_candidates` is EMPTY, so `count=0`, the guarded `if (!root_candidates.empty())` skips the
  assignment, `result.best_move` stays `Move::none()`, and UCI prints `0000`. It is not a fabricated
  bestmove at all - it is an empty one, which is exactly why my earlier claim that this block could read
  `front()` of an empty list was wrong.
- Both are "no search ran, yet a complete depth-by-depth report was emitted"; that shared symptom is why
  they looked like one defect. Different guards, different lines, different fixes.

Consequence for the owner: repairing 19-F12 does NOT repair S-F1, and vice versa. This one is still live
on the PC build (measured above).
Evidence: `pc/pathprobe/paths.json`, `pc/pathprobe/*.log`.

## CORRECTION after FABLE_TO_swarm_6 (2026-11-16T22:40Z): my S-C11 and S-C12 are NOT defects

File 6 rule: a draw by repetition or by the fifty-move rule scored 0 is NOT a defect (the owner's match
program ends the game at the third occurrence and at the 100th half-move). A `cp 0` at a high counter is a
defect ONLY when a forced mate exists that ends no later than the 100th half-move, i.e. only when
`2N - 1 <= 100 - counter`, with both numbers reported.

Applying that to my own boards (Threads 1, base tree + S14, `go depth 20`):
| board | counter | half-moves left | mate needs (2N-1) | inequality holds | engine | verdict |
|---|---|---|---|---|---|---|
| `6k1/5ppp/8/8/8/8/5PPP/R5K1 w` | 98 | 2 | 1 | YES | `a1a8`, `mate 1`, 420 nodes | correct |
| same | 99 | 1 | 1 | YES | `a1a8`, `mate 1`, 420 nodes | correct |
| same | 100 | 0 | 1 | **NO** | `f2f3`, `cp 0`, 0 nodes | **CORRECT behaviour** |

So the base tree already gets the boundary exactly right: it finds the mate while the counter still allows
it, and scores 0 only when no half-move remains. **S-C11 (and S-C12, its severity note) are therefore
WITHDRAWN as defects** — at counter 100 with a mate in 1, `cp 0` is the right answer, because the move that
would mate is the 101st half-move and the game is already drawn under the match program's rule. My severity
essay argued the FIDE-claim angle; file 6 states the owner's rule and it governs.

What survives, and it is smaller: the base tree reports `cp 0` at `nodes 0` with a **depth-by-depth report
for a search that never ran** (S-F8's shape), which is a reporting issue, not a wrong move. The PC r15 build
searches those roots anyway and answers `mate 1` with 420 nodes - also not a defect, just a different
(stronger) choice on a position the match program would already have ended.

The pawn-promotion board `r7/1P6/8/8/8/8/8/k1K5 w` at counter 100 is the same story: the base tree answers
`b7b8q` / `cp 0`, which is correct, and PC r15 answers `b7a8q` / `mate 1`. Neither is a defect. My earlier
"mate MISSED / REPAIRED" framing for that board is WITHDRAWN for the same reason.
Evidence: `pc/file6/inequality.json`, `pc/file6/boundary.json`.

## NEW AREA (file 6): `go softnodes N` on the PC build — deterministic but overshoots up to 2.06x

Build PC r15, settings PC20, Threads 1, Hash 16. Fresh process per run, 3 runs per cell, read to `bestmove`
(never a pipelined quit — 19-F12; my first attempt at this measured `nodes 0` on every cell for exactly that
reason and is thrown away, not reported).

| position | softnodes | last depth | nodes reported | overshoot | ratio | 3 runs identical | depth sequence complete |
|---|---|---|---|---|---|---|---|
| G1 `1r6/2k2pp1/...` | 2000 | 7 | 2671 | +671 | 1.34x | YES | yes |
| G2 `r3r1k1/...` | 2000 | 8 | 3312 | +1312 | 1.66x | YES | yes |
| G3 `6k1/p4r1p/...` | 2000 | 7 | 2314 | +314 | 1.16x | YES | yes |
| G1 | 20000 | 12 | 31779 | +11779 | 1.59x | YES | yes |
| G2 | 20000 | 11 | 21089 | +1089 | 1.05x | YES | yes |
| G3 | 20000 | 10 | 24052 | +4052 | 1.20x | YES | yes |
| G1 | 50000 | 13 | 52904 | +2904 | 1.06x | YES | yes |
| G2 | 50000 | 13 | 79187 | +29187 | 1.58x | YES | yes |
| G3 | 50000 | 11 | 50818 | +818 | 1.02x | YES | yes |
| G1 | 250000 | 17 | 288912 | +38912 | 1.16x | YES | yes |
| G2 | 250000 | 18 | **514117** | +264117 | **2.06x** | YES | yes |
| G3 | 250000 | 17 | 348824 | +98824 | 1.40x | YES | yes |

Answers:
- **Deterministic run to run: YES.** 12 of 12 cells gave 3 identical runs (`distinct_runs` = 1 everywhere),
  comparing depth, nodes, score, seldepth and the full PV. So `go softnodes` is reproducible at Threads 1,
  which means a self-play game replayed with the same inputs repeats.
- **Stops at a finished depth: YES.** Every cell's `info depth` sequence is 1,2,3,...,D with no gap
  (`depth_sequence_complete` true everywhere), so the search stops at the end of an iteration rather than
  abandoning one. That is what the softnodes contract says it should do.
- **How far past N: up to 2.06x, and the factor does not shrink with N.** 1.02x-1.66x at N=2000-50000 and
  1.16x-2.06x at N=250000. The overshoot is the cost of finishing the iteration in progress, so it is bounded
  by ONE iteration's node count, which grows with depth. The worst cell here is G2 at 250000: 514,117 nodes
  for a 250,000 budget.
- **GUI-reachable: YES, and it is the owner's own self-play path.** `go softnodes 2000` is what the PC sends
  for self-play (file 6), so a 1.16x-1.66x overshoot at that budget is on the production path: a 2000-node
  target can cost up to ~3,312 nodes. Whether that matters is a design question (an iteration must finish to
  be reportable), not a fault - the engine reports the true count in `info string softnodes nodes <N>`.

Evidence: `pc/softnodes/softnodes.json`, `pc/softnodes/*.log`.

## NEW ROW for FINDINGS_TABLE: does the bestmove change across the match path's three budgets?

Question (from the coordinator, implied by the softnodes overshoot): if the budget changes the move, the
match path's 20000 / 50000 / 250000 are different players at the same position.
Setup: 10 positions from set G, PC r15, PC20, Threads 1, Hash 16, fresh process per (position, budget),
read to `bestmove`. Deliberately small: an independent check of another seat's 100-position run.

Result: **9 of 10 positions give the SAME bestmove at all three budgets; 1 of 10 changes.**

| position | fen | 20000 | 50000 | 250000 |
|---|---|---|---|---|
| 6 | `2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b - - 0 1` | `c8c3` | `d6e6` | `d6e6` |

Scores on that position rose cp 7 -> cp 16 -> cp 37 with the budget, i.e. the 20000 answer was not a
deeper-search correction of the same plan but a different move that a slightly longer search abandons.

So: the budgets ARE mostly the same player (9/10 here), and the exception is a real one - a position where
a 2.5x larger budget changes the move. That is ordinary search behaviour, not a fault, but it means a match
run at 20000 and one at 250000 are not strictly the same opponent.

GUI-reachable: **YES - these are exactly the budgets the owner's matches send.**
Evidence: `pc/budget_move/budget_move.json`, `pc/budget_move/p*_*.log`.

## Mid-search `setoption` to an extreme — 26 cases, all clean, plus one real protocol observation

Setup: PC r15 ASan+UBSan build, PC20, Threads 1, 13 switches set to their worst value *during* a running
search (`go infinite` at 300 ms and `go nodes 2000000` at 200 ms), then `isready`, then `stop`.
Covered: HistRework 3 / 9, Hash 1 / 2048, Threads 256, CuckooRep on, TtPruneV2 on, CorrHistV2 on and off,
LmrQuietBase 300, HistoryBonusMax 10000, SingularDepth 20, MultiPV 8, DrawJitter 8.

Result: **26 of 26 cases gave a legal `bestmove`, answered `readyok`, and produced 0 sanitizer lines.**
`HistRework 9` correctly answers `info string invalid value for option HistRework` and is clamped (its node
counts match HistRework 3 exactly). `Threads 256` set mid-search is the worst case asked for and it survived.

**Real observation (not a defect): a mid-search `setoption` publishes `bestmove` BEFORE `readyok`.**
In 12 of 12 measured cases the engine emitted `bestmove b6b5` and only then `readyok`. A GUI that sends
`setoption` during a search and waits for `readyok` will therefore receive the truncated search's move
first. That is harmless for a GUI that reads to bestmove, but it means `readyok` is not a marker for
"the move has been emitted" in this flow. GUI-reachable: **only if a GUI changes an option mid-search**,
which the owner's match program and self-play never do.

### My own harness bug #4, recorded because it faked 12 hangs
My first version of this test waited for `readyok` with a predicate that CONSUMED lines, so the earlier
`bestmove` was swallowed; `stop` then found no bestmove and the script reported a HANG. All 12 cases were
false hangs - the logs contained `bestmove b6b5` and 22 `readyok` lines each. The pattern that gave it away:
12 of 12 failing, including cases that had passed an hour earlier, and a control comparison against a known
good log. Fix: keep every line consumed while waiting and inspect it for `bestmove` before declaring a hang.
This is the same class as S-F11 (a harness artefact that fabricates a hang) and belongs with it.
Evidence: `pc/midsetopt/` (15 cases), `pc/midsetopt3/midsetopt3.json` (12 cases after the fix);
the false-hang run is kept as `pc/midsetopt2/` so the error stays visible.

## Depth effect or selection effect? — DEPTH, established with an identical-nodes proof

Question: on position 6 (`2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b - - 0 1`) the move changes from
`c8c3` at `go nodes 20000` to `d6e6` at 50000/250000. Is the small budget's move genuinely worse, or is it
just shallower? A selection effect (the budget changes which move the search picks at equal depth) would be
the more interesting finding.

Measured (PC r15, PC20, Threads 1, Hash 16, fresh process per line):

| command | move | depth reached | nodes | score |
|---|---|---|---|---|
| `go depth 6` | `h8f8` | 6 | 2,305 | cp 34 |
| `go depth 7` | `d6e6` | 7 | 4,562 | cp 68 |
| **`go depth 8`** | **`c8c3`** | 8 | **13,628** | **cp 7** |
| `go depth 9` | `f5h6` | 9 | 31,897 | cp -30 |
| `go depth 10` | `d6e6` | 10 | 45,673 | cp 16 |
| **`go nodes 20000`** | **`c8c3`** | 8 | **13,628** | **cp 7** |
| `go nodes 50000` | `d6e6` | 10 | 45,673 | cp 16 |

**It is purely a DEPTH effect, and I can prove it rather than argue it: `go nodes 20000` is identical to
`go depth 8` in move, in nodes (13,628 both) and in score (cp 7 both), and `go nodes 50000` is identical to
`go depth 10` (45,673 nodes, cp 16).** The node budget is simply a depth selector on this position: it stops
after the last depth it can afford, which is exactly what `softnodes` was designed to do. There is no
selection effect to report.

Two further facts worth having, because they show why "the small budget's move is worse" is a bad reading:
- The move is **not monotone in depth at all**: 6 -> `h8f8`, 7 -> `d6e6`, 8 -> `c8c3`, 9 -> `f5h6`,
  10 -> `d6e6`. Every depth changes its mind. So "the 20000 answer is the worse one" is an accident of which
  depth that budget lands on, not a property of small budgets.
- An independent fixed-depth yardstick (`go depth 14` on the position after each move, negated) ranks
  `d6e6` +33, `f5h6` 0, `c8c3` -103, `h8f8` -142. I state plainly that this yardstick is itself a shallow
  search, so it ranks moves by one more search's opinion, not by truth; it is consistent with the engine's
  own deeper preference for `d6e6` but it is not independent ground truth.

GUI-reachable: **YES** — these are the match path's own budgets. The actionable statement for the owner is
that a 20000-node move on this position is a depth-8 move, and a 250000-node move is a depth-15 move, so the
two match tiers are playing at materially different depths here; they are the "same player" only in 9 of 10
positions I sampled.
Evidence: `pc/selection/depth_split.json`, `pc/selection/selection.json`, `pc/selection/*.log`.
