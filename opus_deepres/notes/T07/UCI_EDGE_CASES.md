# T07 UCI time edge cases to box-test on Forge (lock FD3A5190)
Status: COMPLETE (written from a read of the lock source only; nothing was run - every case is a test still to do)

Lock code read (read-only): `src/uci.cpp` go parser 65-110, go dispatch 287-380, ponderhit 411-420, stop 421;
`src/search.cpp` time allocation 1249-1271, root pre-checks 1329-1346, soft-stop factors 1433-1456, hard stop
679-690 (polled every 1024 nodes at 774 / 885, every node when `nodes` is given); `include/forge/search.hpp` 19-41
(SearchLimits), 387-391 (ponderhit).

Formulas (sudden death / increment, defaults): available = max(1, time - MoveOverhead);
soft = available / TmSoftDivisor(22) + inc * TmIncrementPercent(75) / 100; hard = min(available * TmHardPercent(60) /
100, soft * TmHardSoftMultiple(5)); both clamped to [1, available]. movestogo: mtg = min(movestogo, 50);
soft = available / (mtg + 1) + inc * 3 / 4; hard = min(available * 4 / 5, soft * 4). movetime: hard = soft =
max(1, movetime - MoveOverhead), no stability factors (time_managed_ stays false). The soft limit is only checked
between iterations; the hard limit stops mid-iteration.

## Test hygiene (applies to every case)
- Book: with OwnBook on and game ply < Book Depth (30), any clocked or movetime `go` answers a book move at once
  (uci.cpp 325-345) and no time code runs. Every case starts with `setoption name OwnBook value false`.
- Positions: F1 = `position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1` (White to move),
  F2 = `position startpos moves e2e4` (Black to move).
- Timing: the budget starts when the `go` line is read (uci.cpp 157, 324) for finite clocked searches only. Measure
  "go sent -> bestmove read" in the driver; expect at most budget + ~5 ms on an idle core (Idle priority, CPUs per the
  PC rules). Stdin EOF ends the loop and stops the search, so the driver must keep stdin open until bestmove.
- Driver form used below: `S: <lines>` = lines sent after the hygiene lines; `E:` = expected lock behaviour;
  `R:` = recommendation where the lock behaviour looks wrong or risky.

## A. Only increments, only the other side's clock, missing own clock
1. `go winc 1000 binc 1000` (no wtime/btime). E: time_ms stays -1 (uci.cpp 99-102), no time management, search runs
   to depth 64 until `stop`. Test: S F1 + that line; assert no bestmove after 2 s; send `stop`; bestmove within 50 ms.
   R: a GUI never sends this in play; keep, but document that the engine needs `stop` here.
2. `go btime 5000 binc 100` with White to move (F1). E: same as 1 - the parser stores only the side to move's clock,
   so the opponent's fields are dropped and the search is untimed. Test: as 1.
3. `go wtime 5000 winc 100` with Black to move (F2). E: untimed, as 1. Test: as 1 (the mirror check).

## B. movestogo
4. `go wtime 10000 btime 10000 movestogo 1`. E: soft = 9990/2 = 4995, hard = min(7992, 19980) = 7992 ms; the
   soft-stop factors apply here too (factor >= 0.45). Test: S F1 + line; bestmove in [2.2 s, 8.0 s].
5. `go wtime 10000 movestogo 0`. E: clamped to 1 (uci.cpp 95) -> same budget as case 4 (up to 80 % of the clock).
   R: risky - the spec defines no movestogo 0; reading it as "absent" (sudden death: soft ~ 454 ms) is the safe
   choice. Test: S F1 + line; record the time; flag if > 1 s.
6. `go wtime 10000 movestogo -5` and `go wtime 10000 movestogo x`. E: both -> 1 (max(1, value), bad text reads 0),
   same as case 5. R: as case 5. Test: as 5.
7. `go wtime 10000 movestogo 200`. E: mtg capped at 50 -> soft = 9990/51 = 195 ms, hard = min(7992, 780) = 780 ms.
   Test: bestmove in [0.08 s, 0.8 s].
8. `go wtime 60000 winc 1000 movestogo 40` (cyclic + increment). E: soft = 59990/41 + 750 = 1463 + 750 = 2213,
   hard = min(47992, 8852) = 8852 ms. Test: bestmove in [1.0 s, 8.9 s].

## C. Tiny increments, very low remaining time, clock below Move Overhead
9. `go wtime 10000 winc 1`. E: soft = 454 ms (the 1 ms increment adds 0), hard = 2270 ms. Test: bestmove < 2.3 s.
10. `go wtime 60 winc 10`. E: available 50, soft = 2 + 7 = 9, hard = min(30, 45) = 30 ms. Test: bestmove < 40 ms.
11. `go wtime 30` (available 20 < 22). E: soft rounds to 0 -> hard = 1 ms. The root pre-check (search.cpp 1337) may
    find the 1 ms already spent and return the first legal move in generation order with no search. Test: run 20 times;
    assert a legal move every time and < 10 ms; count how often the move equals `go perft 1`'s first move.
    R: when the budget is gone before depth 1, prefer the TT move or a completed depth 1 over the first legal move.
12. `go wtime 5` and `go wtime 0` (clock below / at zero). E: available = 1 ms -> hard = 1 ms; as case 11.
    Test: as 11.
13. `setoption name Move Overhead value 1000` then `go wtime 500 winc 100`. E: available = 1 -> 1 ms move. Test: as 11.
14. `setoption name Move Overhead value -5` / `value 5000` / `value abc`. E: clamped to 0 / 1000 (uci.cpp 270-281);
    bad text prints `info string invalid value for option Move Overhead` and keeps the old value. Test: send each,
    then `go wtime 1000`; compare times (overhead 0 -> soft 45, hard 225 ms; 1000 -> 1 ms).

## D. Increment larger than base
15. `go wtime 100 winc 1000`. E: available 90; soft = 754 -> clamped 90; hard = min(54, 3770) = 54 ms, so hard <
    soft and the move takes ~54 ms. Test: bestmove in [40, 70] ms.
16. `go wtime 0 winc 1000` (pure increment, base already spent). E: 1 ms move (never banks the coming increment).
    Test: as 11. R: correct for increment-after-move clocks; keep.
17. `go wtime 500 winc 2000`. E: soft 1522 -> clamped 490, hard = min(294, 7610) = 294 ms. Test: bestmove in
    [0.25, 0.32] s; a follow-up `go wtime 2206 winc 2000` gets hard = min(1317, 7995) = 1317 ms.

## E. movetime / nodes / depth combinations
18. `go movetime 0` and `go movetime 5`. E: hard = max(1, mt - 10) = 1 ms; case-11 risk applies. Test: as 11.
19. `go movetime 1000 wtime 500`. E: movetime wins (search.cpp 1255 before 1258): 990 ms although only 500 ms are on
    the clock. R: cap movetime by the clock budget when both are given. Test: bestmove time; flag if > 500 ms.
20. `go movetime 1000 depth 3`. E: stops at depth 3 (well before 1 s). Test: last info depth = 3, time < 1 s.
21. `go movetime 300 nodes 100000000`. E: first limit wins (300 ms here); with `nodes` given, should_stop runs at every
    node (search.cpp 774, 885) and reads the clock each time a hard limit exists. Test: bestmove < 320 ms; note nps
    vs. plain `go movetime 300` (expected lower; record, not a failure).
22. `go nodes 20000 wtime 100000`. E: node limit first (total nodes over all threads). Test: final info nodes in
    [20000, 20000 + small overrun].
23. `go nodes 0`. E: immediate answer, first root candidate, depth 0 (search.cpp 1329-1333). Test: legal bestmove
    < 10 ms.
24. `go nodes -5` / `go nodes 18446744073709551616`. E: parse fails, nodes not set -> untimed depth-64 search (as
    case 1). R: reject with an info string or treat as 0. Test: as case 1.
25. `go depth 0` / `go depth -3` / `go depth 99` / `go depth abc`. E: clamped to 1 / 1 / 64 / 1. Test: last info
    depth 1, 1, (stop after 2 s), 1.
26. `go` (bare). E: depth 64, no clock; needs `stop`. Test: as case 1.
27. `go mate 0` and `go mate 40`. E: mate 0 = no mate limit (untimed, as case 1); 40 is clamped to 32 (depth 63).

## F. Negative, missing, non-numeric and overflowing fields
28. `go wtime -500 btime -500`. E: negative -> 0 (max(0, v)) -> 1 ms move (case 12). Test: as 11.
29. `go wtime` (value missing at end of line). E: reads 0 -> 1 ms move. Test: as 11.
30. `go wtime btime 1000` with White to move. E: `btime` is eaten as wtime's value -> 0 -> 1 ms move; with Black to
    move (F2) btime is never set -> untimed search (case 1). Test: run on F1 and F2.
31. `go wtime 99999999999`. E: from_chars overflows a 32-bit int -> 0 -> 1 ms move (uci.cpp 77-78). Clocks above
    2147483647 ms (24.8 days) collapse to an instant move. R: parse as 64-bit or saturate. Test: as 11; flag.
32. `go winc -50` / `go winc abc`. E: increment 0. Test: `go wtime 10000 winc -50` budget equals `go wtime 10000`.
33. `go movetime -100` / `go movetime 3000000000`. E: both -> 0 -> 1 ms move. R: as case 31. Test: as 11.

## G. Ponder, infinite, stop
34. `setoption name Ponder value true`, `go ponder wtime 10000 btime 10000`, wait 3 s, `ponderhit`. E: no time is
    charged while pondering; the soft/hard budget starts at ponderhit (search.hpp 387-391, search.cpp 660-666) with
    the clock values of the `go`. Test: bestmove arrives <= 2.3 s (hard) after ponderhit, never before it.
35. As 34 but `stop` instead of `ponderhit`. E: bestmove at once (search result). Test: < 50 ms after stop.
36. `go ponder depth 2` and wait 2 s. E: the search ends early but bestmove is held until `ponderhit` or `stop`
    (uci.cpp 358-362). Test: no bestmove before ponderhit; bestmove < 10 ms after it.
37. `ponderhit` with no ponder search active. E: ignored (uci.cpp 412). Test: no output, next `isready` -> readyok.
38. `go infinite wtime 1000`. E: infinite wins; bestmove only after `stop`. Test: as case 1.
39. `go wtime 10000` then `isready` mid-search. E: readyok at once, search continues (no stop). Test: readyok < 10 ms,
    bestmove still within budget.
40. `go wtime 10000` then `position ...` or `setoption ...` mid-search. E: both stop the search first (stop_search),
    a bestmove is printed for the old search. Test: exactly one bestmove before the next go's output.

Findings to hand to the crew (from reading, not yet confirmed by a run): cases 5/6 (movestogo 0 or bad -> last move of
a cycle, up to 80 % of the clock), 19 (movetime ignores the clock), 31/33 (overflow -> instant move), 11/12 (possible
unsearched first legal move at 1 ms budgets), 24 (bad nodes -> untimed search).
