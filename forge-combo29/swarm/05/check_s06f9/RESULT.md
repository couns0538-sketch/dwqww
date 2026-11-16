# CHECK of seat 06's S-F9 — seat 05 (area 5)

## Verdict: CONFIRMS, and goes beyond it

Seat 06's S-F9 (their words): *"SUSPICION not proven: on G index 196 (`5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w`) the
engine reports `cp 4402` while its colour mirror reports `mate 14`; index 217 likewise cp 2557 vs mate 11."*

I reproduced both pairs on my own release build with a harness I wrote from that sentence alone (no copy of their
script, no use of their raw files), depth 10, S14, Threads 1, Hash 16, fresh process per position:

| pair | position | score | mirror | score |
|---|---|---|---|---|
| G196 | `5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1` | **cp 4402** (exact match) | `8/8/4n3/8/3p4/3Pk1pp/1K6/5q2 b - - 0 1` | **mate 14** (exact match) |
| G217 | `8/7p/8/7p/3k2b1/6K1/2p5/8 b - - 0 1` | **cp 2557** (exact match) | `8/2P5/6k1/3K2B1/7P/8/7P/8 w - - 0 1` | **mate 11** (exact match) |

Control that the harness can see a stable score: each position searched twice in the same run gives the identical
score both times (`cp 4402` vs `cp 4402`, `cp 2557` vs `cp 2557`).
Raw: `raw/check_s06f9.txt`.

## What is beyond the finding (the part that is new)

I applied the brief's own mate rule (2N-1 plies for `mate N > 0`) to the **mate side** of both pairs:

| pair | mate score | plies the score promises | plies the PV actually has | shortfall |
|---|---|---|---|---|
| G196 mirror | `mate 14` | 27 | 14 | **13 plies** |
| G217 mirror | `mate 11` | 21 | 16 | **5 plies** |

So in *both* mirror pairs the side that reports a mate reports a **truncated** mate PV as well, and the side that
reports `cp` is simply below the engine's mate threshold at that depth. That makes the pair a single phenomenon and
not two: the same horizon effect (a mate bound carried at a depth that cannot produce the mate line) shows up once
as "mate with a too-short line" and, on the mirrored board where the move ordering differs, as "a large cp score
instead of the mate". This ties seat 06's S-F9 to seat 06's own S-F10 statement that 4 of 16 mate PVs are
horizon-truncated, and to my S-F1 (G/192), which is the same truncation at depth 12 on the G set.

Command that shows the arithmetic again: `python3 -c` block in `raw/pv_arithmetic.txt` (the file holds the run).

## What I did NOT establish
- That the cp-side score is *wrong*. `cp 4402` is below the threshold; without a mate claim I have no brief rule
  to test it against, and I did not compute the true evaluation.
- Whether mirroring is a fair comparison here at all: both boards are legal and both are the same game with colours
  swapped, so a colour-symmetric search *should* agree, but seat 06's S-F6/S-F7 already show the search is not
  colour-symmetric by design (alpha-beta order), so the split is expected behaviour, not a bug on its own.
- Any cause in source; I did not read `search.cpp` for this check (area 7's job).

## Files
- `check_s06f9.py` — the harness (written from their one-sentence claim)
- `raw/check_s06f9.txt` — its full output
- `raw/pv_arithmetic.txt` — the 2N-1 arithmetic on the mate PVs
