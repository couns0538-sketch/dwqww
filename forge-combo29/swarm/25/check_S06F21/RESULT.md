# S-C3 — independent confirmation of seat 06's S-F21 (colour-mirror asymmetry rate)

## What was claimed (seat 06, S-F21)
On the G set (353 positions), depth 10, S14, the bestmove differs from the colour-mirror's bestmove for
**101 of 353** positions (28.6%, CI 24.1-33.5) and the scores differ for **94.6%**.

## My result (harness written from the claim, not copied)
| measurement | seat 06 | mine |
|---|---|---|
| bestmove not the mirror | 101/353 = 28.6% | **101/353 = 28.6%** |
| score not equal | 94.6% | **334/353 = 94.6%** |
| CI on the bestmove rate | 24.1-33.5% | 23.9-33.3% |

Exact agreement on both counts, on my own build with my own harness, with the mirror computed by
python-chess `board.mirror()`. Evidence: `check_G_full.txt`.

## Why the comparison is trustworthy
- Protocol: UCI, Threads 1, Hash 16, all 14 S14 options, OwnBook false, `ucinewgame` + `isready` before every
  `go`, a fresh process per search. `ucinewgame` was verified COLD on this build
  (`../audit/warm_cold_audit.txt`: three fresh processes 18407 each, and ucinewgame in one process 18407 x3).
- **Planted control (Opus Rule 1):** the same comparison, run against a 180-degree ROTATED board instead of
  the colour mirror, is flagged as different 5 of 5 times. So the harness can see a difference and a "0
  differences" or a low rate could not be an artefact of blindness.
- A first run on 60 positions gave 23.3% (CI 12.6-34.0), which already overlapped seat 06's interval; the
  full 353 then matched exactly.

## What I did NOT do
- Did not investigate the CAUSE (seat 06 spent S-F14/S-F17/S-F20/S-C1 ruling out tie-break, aspiration window,
  accumulated root alpha and the colour-absolute history index; I have no cause to offer).
- Did not test the R-set rates (19.5% / 21.5%) that S-F21 reports beside the G figure.
