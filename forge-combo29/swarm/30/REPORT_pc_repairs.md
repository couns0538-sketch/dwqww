# REPORT — two PC-build faults and their repairs, verified on my own builds

Seat 30, area 10. Builds used (all built by me, g++ 13.3.0, Release, `-DFORGE_MATE_ALPHA_GUARD=1`,
Threads 1 in every measurement, every setoption confirmed by `readyok`, every search awaited):

| name | what it is | sha256 |
|---|---|---|
| base | commit `6b98f217`, no patch | `e06310ec…6a83` |
| PC r15 | base + `FABLE_TO_swarm_5.md` patch (`d6bd72c5…`) | `068f0927…32f4` |
| PC + terminal-root patch | PC r15 + seat 24's `terminal_root_infinite.patch.txt` | `8b163905…c034` |
| PC + split-root-drawn | PC r15 + seat 15's `root_rep_split_fix.patch.txt` | see `check7/` |

## 1. Terminal root: unbounded `go` never answers (confirmed, and the repair verified)

`check5/` — both builds, 8 s window, checkmate and stalemate roots:

| form | result |
|---|---|
| `go depth 5`, `go nodes 1000`, `go movetime 200`, `go wtime 1000 btime 1000`, `go mate 3`, `go searchmoves e2e4 depth 3` | `bestmove 0000` in **0.00 s** on both builds (search path is correct) |
| `go infinite`, `go ponder` | **no bestmove in 8 s** on both builds at a terminal root |
| `go infinite` / `go ponder` on a NORMAL board | answers `d2d4` after a `stop` — the control that makes the row above a finding |

With seat 24's patch: both unbounded forms answer `bestmove 0000` in 0.00 s at both terminal roots,
a normal board's `go infinite` still waits for `stop`, and the four honesty numbers are unchanged
(312866 / 862329 / 3024920 / 4865609).

## 2. The PC build's `FORGE_FIX_ROOT_DRAWN` conflates two repairs (confirmed) and the one-line split works

`check7/` — Threads 1, `position startpos moves g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8`, with
python-chess confirming the played cycle reaches **3 occurrences** (`can_claim_threefold=True`):

| build / settings | halfmove-100 mate | thrice-repeated root | twice-repeated root |
|---|---|---|---|
| base / S14 | `cp 0`, 0 nodes (missed) | `cp 0`, **0 nodes** (drawn, correct) | `cp 15`, 1,949 (searched, correct) |
| PC r15 / PC20 (shipped) | **`mate 1`, 126 nodes** (repaired) | `cp 6`, **1,144 nodes** (SEARCHED — regression) | `cp 18`, 1,740 |
| PC r15 / S14 | `mate 1`, 126 nodes | `cp 7`, **1,786 nodes** (regression under S14 too) | `cp 15`, 1,949 |
| PC + split fix / PC20 | `mate 1`, 126 nodes | `cp 0`, **0 nodes** (restored) | `cp 18`, 1,740 |
| PC + split fix / S14 | `mate 1`, 126 nodes | `cp 0`, **0 nodes** | `cp 15`, 1,949 |

The split build passes the honesty gate at every setting tested: bench 11 = 312866, bench 13 =
862329, bench 16 = 3024920, perft 5 = 4865609. The owner can have both correct behaviours with a
one-line change at `src/search.cpp:2577`.

## 3. Honest limits
- I verified the patches apply and build; I did not run matches to see whether the split fix changes
  playing strength. The honesty numbers only say the search tree is unchanged at the bench positions.
- Both patches come from other seats; I have reproduced their effects independently but the ideas are
  theirs, and their FINDINGS lines carry the original evidence.

## 4. Where the raw files are
`check5/out/` (terminal matrix), `check5/out_patched/` (patched matrix + honesty),
`check7/out/` (base vs shipped PC), `check7/out_split/` (split build + honesty),
`check7/s15_split_fix_under_test.patch.txt`, `check5/s24_patch_under_test.patch.txt`.
