# REPORT_deepseek5_job5 (deepseek5, 2026-11-16 UTC)

1. **What was asked**: the `go` line and the `position` line, blind — prediction committed first, then measurement of 76 lines × 10 repetitions with the answers held by you. **The answers: (1) H1–H5 all came out as required (H1 LIMIT, H2 RUNS, H3 CLOCK, H4 OTHER:no-bestmove with the swallowing wrapper, H5 OTHER:delayed-answer at 401.5 ms — the harness sees a delayed delivery); (2) the measured classes and the 25 prediction mismatches are listed below — the prediction file was committed alone (04:52:14Z) before any measurement; (3) ONE genuine FAULT: P1 — after an illegal token inside a `position … moves …` line the engine answers a move for the WRONG SIDE.** How sure: sure of P1 (10/10 repetitions, perft 29 on the held board, the bestmove illegal for the real side, cause read in the source); the class-label mismatches on the terminal roots (C3–C5) are label-vs-substance, not behavior.
2. Step 0: the exe of job 3, sha256 re-printed: `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` (same file as job 3: built 2026-11-15 20:43:17, 794,888 bytes; pins re-verified this job? — NOT re-run this job: the same file was pin-verified at job 3's step 0 (04:07:26Z stamps) and nothing rebuilt it; stated, not assumed fresh).
3. Table:

| step | done? | evidence | result |
|---|---|---|---|
| Step 1 prediction, own commit | done | tests_deepseek5_job5/prediction.txt, commit e62aaf6f6 at 04:52:14Z | 76 rows, pushed before any measurement |
| H1–H3 controls | done | control_H.txt | LIMIT / RUNS / CLOCK as required |
| H4 planted (swallow one bestmove) | done | control_H4.txt | OTHER:no-bestmove — the harness-fault signature, as required |
| H5 planted (hold bestmove 400 ms) | done | control_H5.txt | 401.53 ms → OTHER:delayed-answer — NOT AT_ONCE, as required |
| List A (31 lines × 10) | done | raw_A.txt (310 rows) | classes: see summary; 1 prediction miss worth naming (A31) |
| List C (5 × 10) | done | raw_C.txt (50 rows) | C1 searched (trap did NOT fire); C3/C4/C5 answered with **0 nodes** (terminal roots) |
| List B (31 × 10) | done | raw_B.txt (310 rows) | **B21/B27: `infinite` overrides the depth limit (RUNS)** — the finding of the list |
| List P (9 × 10) | done | raw_P.txt (90 rows) | **P1 = the fault**; P2/P3/P6/P7 refused the position and answered for the held board (consistent); P8/P9 accepted 1,200/12,000-ply histories (setup ≤ 0.1 ms) and then hit the threefold trap (0-node answers) |
| Step 4 (lists under ASan) | not done | — | the 50-minute stop fell first |

**Per-list class counts** (majority class per line; full per-repetition data in the raw files): A: CLOCK 3 (A01, A16, A29), AT_ONCE 11, LIMIT 9, RUNS 8; B: AT_ONCE 5, CLOCK 5, LIMIT 11, RUNS 6, OTHER:no-bestmove 1 (B08), OTHER:perft-no-bestmove 1 (B28), REFUSED 3 (B29–31); C: LIMIT 5 (of which C3/C4/C5 have 0 nodes = no search); P: LIMIT 9 (P2/P3/P6/P7 with the position REFUSED in their info strings).

**The 25 prediction mismatches, listed as demanded** — each with one line of why:
- A09, A19, A27 (AT_ONCE predicted, LIMIT measured): a failed/negative movetime did not stop the engine instantly; it ran a real (tiny) search to depth ≥ 2. My "immediate" reading of the clamp was wrong.
- A25, B06, B18 (RUNS predicted, LIMIT/CLOCK measured): the movestogo-1 plan does NOT hand the whole remaining budget to one move — the searches ended inside the harness window (~1.2 s or less). My ~1.9 s estimate came from assuming no reserve.
- A31 (AT_ONCE predicted, RUNS measured): parse_clock_ms SATURATES the overflowing movetime (int64-max), it does not zero it — the search runs past 1.5 s. My parenthetical alternative was the truth.
- B01 (CLOCK predicted, AT_ONCE measured): the ponder search finished inside its ~166 ms plan BEFORE my 300 ms ponderhit — ponderhit arrived after bestmove. My timing model of the plan was right; my class rule keyed on the depth field, which stayed ≤ 1 for this fast plan. Measurement artifact of my class boundaries, not an engine surprise.
- B02 (RUNS predicted, AT_ONCE measured): `go mate 1` resolved instantly (no mate to find → no unbounded hunt).
- B03 (RUNS predicted, LIMIT measured): `go mate 3` ended at a limit within the window.
- B05 (LIMIT predicted, CLOCK measured), B12/B13 (LIMIT predicted, CLOCK measured): class-boundary artifacts (my classifier calls a sub-600 ms deep search CLOCK even when a named movetime/node limit ended it).
- B14 (LIMIT predicted, AT_ONCE measured): a 1-node search answers at depth 1 — the class vocabulary's AT_ONCE/LIMIT boundary sits on the depth field, not on "did the named limit act". Label issue.
- **B21, B27 (LIMIT predicted, RUNS measured): `go depth 5 infinite` and `go infinite depth 3` search PAST their depth limits — the infinite flag removes the depth stop as well as the time stops. This is a real behavior fact I did not know, and a program that sends both would wait forever.**
- C1 (AT_ONCE predicted, LIMIT measured): **the root-repetition trap did NOT fire**: the position had occurred three times in its own move list, and the engine still ran a real depth-6 search. My prediction came from your earlier description of the trap; on THIS tree it did not reproduce in this form (see section 7).
- C3, C4, C5 (AT_ONCE predicted, LIMIT measured): substance agrees (the terminal roots answered with **0 nodes** — no search); the label differs because the terminal path still emits the asked depth. Label-vs-substance.
- P2, P3, P6, P7 (REFUSED predicted, LIMIT measured): the POSITION line was refused (`info string invalid FEN: …` — verbatim in the raw rows) but the GO then ran ON THE HELD BOARD and answered legally for it; my prediction conflated the position refusal with the go class. The held-board behavior is the same one P1's fault corrupts.
- B08 (OTHER predicted, OTHER measured — agreement; listed in the fault scan but NOT a fault: the line is not a `go` command at all and the engine rightly ignores it).

**The faults:**
- **P1 (10/10 repetitions)**: `position startpos moves e2e4 e7e5 e2e4` — the engine prints `info string illegal move e2e4`, keeps the position after 1.e4 e5 (perft 1 = 29 ✓), and then answers `g1f3` — a WHITE move on a BLACK-to-move position — illegal in the real game, 10 of 10. A runner that follows the documented apply-until-illegal behavior and then plays the answer would make an illegal move every time such a line occurs. **Cause, file:line**: src/uci.cpp, the position handler's move loop (the `while (input >> token)` loop right after the `info string illegal move` branch at src/uci.cpp:63): it applies every syntactically-valid token with `candidate.make_move(*move, undo)` — `parse_uci` checks only the token's SHAPE, not legality, so the illegal token is "applied", the side flips, and the search then runs for the wrong side. One sentence: an illegal token must be refused BEFORE make_move, as the loop's own first branch does for unparseable ones.
- Not faults, checked and cleared: B08 (not a go command; ignored — correct), B28 (perft is not a search; it printed `nodes 4865609` at the startpos ✓ the known answer), P5 (the engine REFUSED the illegal position — `info string invalid FEN: side that moved left its king in check` — and answered legally for the board it holds (perft 1 = 20, e2e4 legal there); my first fault scan flagged it because I checked legality against the refused position — my checker's error, corrected here).

## What I did NOT do
- Step 4 (lists B and P under the ASan exe): the stop fell first; the fault-class lines (P1 especially) have NOT been seen under sanitizers.
- A second engine process for any list (the job's one-process-per-list was followed; cross-process repetition of the P1 fault is untested).
- The H-controls at 10 repetitions (they ran once each; the H lines are harness checks, not engine behavior).

## What I am NOT sure about
- Whether P1's wrong-side answer extends to OTHER illegal-token shapes (a move that is well-formed but blocked, e.g. a king capture): my single P1 token was a pawn move to an occupied square; the mechanism (make_move without a legality check) predicts yes for every shape, but I tested one.
- Whether the C1 trap's absence means the trap is not in this tree at all, or its condition differs (the root-repetition rule may count only occurrences AFTER the root index — the root occurring at plies 0/4/8 of its own history may read differently inside the search than it does in my reading of your description).
- B01's class: whether a GUI that ponders and hits EARLY (before the plan ends) would see anything different — my ponderhit always came after the search had finished.

## A better way
- The class vocabulary strains on three edges I hit (the 0-node terminal answers labeled with their asked depth; the named-limit searches labeled CLOCK; the delayed-delivery case): one bit in the raw row — "did any search run (nodes > 0)" — would make the classes checkable from the data instead of from my thresholds. One field; no extra run.
- The P1 fault is cheapest to catch at the RUNNER level: a runner that replays the engine's answers with python-chess (as this harness does) turns "wrong-side bestmove" into an immediate, loud failure — I would make the replay check part of every game runner this queue uses (it is already in my job-15 runner's design).

## times: see stamps.txt
## Model
deepseek5 — DeepSeek (the model serving this cloud-agent run).
