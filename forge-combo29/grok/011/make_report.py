#!/usr/bin/env python3
"""Build REPORT.md and RESULT.txt from the raw files in this folder."""
import re
from pathlib import Path

here = Path(__file__).resolve().parent


def read(name):
    return (here / name).read_text()


def elo_games(name):
    text = read(name)
    elo = re.search(r"Elo: ([-\d.]+) \+/- ([\d.]+)", text)
    games = re.search(r"Games: (\d+)", text)
    return elo.group(1), elo.group(2), games.group(1), text


elo, err, games, match_text = elo_games("match_summary.txt")
on = read("compare_on_O.txt")
differ = re.search(r"differ (\d+) of (\d+)", on).group(1)
result = (
    f"seat=011 idea=11 id=S25 option=IdeaS25 exists=no applies=yes "
    f"off_identical=yes on_differs={differ} of 200 sanitizer=clean "
    f"elo={elo} err={err} games={games} partner=061 partner_verdict=CONFIRMS\n"
)
(here / "RESULT.txt").write_text(result)

parts = []
parts.append(
    """# Seat 011, idea 11, S25

Idea S25 keeps the root search full-width until a score has landed inside the window, then arms the narrow window, and it does not treat a re-search that is still outside the window as finished for the soft time stop.
I built UCI check `IdeaS25` (default false) and spin `IdeaS25_Resolved` (default 1, range 1 to 64).
Off, the narrow window still starts at depth 4. On, depth 1 stays full-width and the window arms after `IdeaS25_Resolved` in-window root scores (default 1, so depth 2).

EXISTS: no. The plain root loop in `forge-combo29/src/search.cpp` sets the narrow window with `depth >= 4`. That is a fixed depth, not a count of scores that landed inside the bounds.

## Honesty numbers

Exe B, no setoption, from `HONESTY_B.txt` (written by `write_honesty_b.py`):

```
"""
)
parts.append(read("HONESTY_B.txt").rstrip())
parts.append(
    """
```

Exe P, no setoption, from `evidence.py`:

```
"""
)
ev = read("evidence.txt")
# HONESTY_P block through the line before OFF_O
start = ev.index("HONESTY_P\n")
end = ev.index("OFF_O\n")
parts.append(ev[start:end].rstrip())
parts.append(
    """
```

Baseline sums, S14, Threads 1, Hash 16, from `BASELINE_B.txt`:

```
"""
)
parts.append(read("BASELINE_B.txt").rstrip())
parts.append(
    """
```

## Steps

```
step | status | evidence | result
STEP 1 seat | done | SEAT.txt stamps.txt | seat 011 idea 11
STEP 2 builds and baseline | done | HONESTY_B.txt BASELINE_B.txt | honesty match, O 9500069, G 18466239
STEP 3 idea | done | idea.patch.txt evidence.txt match_summary.txt | off identical, on differs, match played
STEP 4 partner 061 | done | partner_compare_off.txt partner_compare_on.txt partner_match_summary.txt | CONFIRMS
STEP 5 report | done | REPORT.md RESULT.txt | this file
```

## Proofs

(1) Honesty with no setoption. Exe P matches exe B: bench 11 nodes 312866, bench 13 nodes 862329, bench 16 nodes 3024920, perft 5 nodes 4865609. See the honesty block above and `honesty_P_*.txt`.

(2) S14 and `IdeaS25` false. From `compare_off_O.txt` and `compare_off_G.txt`:

```
"""
)
parts.append(read("compare_off_O.txt").rstrip())
parts.append("\n")
parts.append(read("compare_off_G.txt").rstrip())
parts.append(
    """
```

(3) S14 and `IdeaS25` true, O depth 12. From `compare_on_O.txt`:

```
"""
)
parts.append(read("compare_on_O.txt").rstrip())
parts.append(
    """
```

179 of 200 positions differ from exe B, so the new path runs. The sum is 9619908. `prediction.txt` said 9700000, wrong outside 8000000 to 12500000. The measured sum is inside that range.

(4) `uci` lists the new options. From `uci_P.txt`:

```
option name IdeaS25 type check default false
option name IdeaS25_Resolved type spin default 1 min 1 max 64
```

(5) AddressSanitizer and UndefinedBehaviorSanitizer build `/tmp/forge-A/forge`. `asan_G100_d10.meta` records `nm_asan 35`. `asan_G100_d10.txt` has 0 AddressSanitizer error lines (first 100 of G, depth 10, switch true). The scratch engine, one heap read past the end of a 4-int vector on the FEN in `scratch.fen`, run with the same `search_set.py`, reports one line in `asan_scratch.txt`: `ERROR: AddressSanitizer: heap-buffer-overflow`.

`git apply --check` of `idea.patch.txt` on the base worktree exited 0 when the patch was written.

## Match

Exe P switch true versus exe P switch false, S14, Threads 1, Hash 16, 20000 nodes, openings O then G, both colours. `extract_match.py` on `match_on_off.txt`:

```
"""
)
parts.append(match_text.rstrip())
parts.append(
    """
```

1106 games are in `match_on_off.pgn`. Elo -4.08 +/- 10.02. The point estimate is inside the prediction range (-30 to +40). The interval is not entirely below 0, and the point estimate is not below -20, so I did not open a second bug hunt. `prediction.txt` guessed +3.

## Partner

Partner is seat 061 (same idea, next seat with a branch). Seat 111 had no branch. `git apply --check` of their `idea.patch.txt` on a clean base worktree:

```
"""
)
parts.append(read("partner_apply.txt").rstrip())
parts.append(
    """
```

Their build, my `honesty_harness.py` and `search_set.py`. Switch false versus my exe B O rows (`partner_compare_off.txt`):

```
"""
)
parts.append(read("partner_compare_off.txt").rstrip())
parts.append(
    """
```

Switch true versus the nodes I parsed from their `O_p_on_d12.txt` (`partner_compare_on.txt`):

```
"""
)
parts.append(read("partner_compare_on.txt").rstrip())
parts.append(
    """
```

Switch true versus exe B (`partner_compare_on_vs_B.txt`):

```
"""
)
parts.append(read("partner_compare_on_vs_B.txt").rstrip())
parts.append(
    """
```

Their proof table says O on sum 9619908 and 179 positions differ from B. My run of their patch matches both, position by position against their log. Honesty on their binary matched 312866, 862329, 3024920, and 4865609.

Their own match claim (1106 games, Elo -4.08 +/- 10.02) was not replayed. The required partner match is 300 of my R openings, both colours, their switch. `extract_match.py` on `partner_match.txt`:

```
"""
)
parts.append(read("partner_match_summary.txt").rstrip())
parts.append(
    """
```

Verdict: CONFIRMS. The patch applies, honesty holds, switch false matches exe B on every O position, and switch true matches their O rows on every position.

## Suspicions, not proven

Their published 1106-game score line, including the pentanomial, is the same text as mine. Their on-search nodes also match my on-search nodes on all 200 positions. Equivalent arming plus the same opening order can produce the same games. I did not prove a copy, and I did not prove the games were played independently.

## What I did NOT do

I did not measure the soft-time hold on a clock. Depth and node searches leave that path idle.
I did not rebuild their sanitizer or their scratch bug. I read their probe log and ran my own.
I did not replay their 1106-game match.
The minute-60 fetch of `handoff/fable-opus-combo29-all-20261114` had no `FABLE_TO_grok_<N>.md`. Seat 111 had no branch.
I did not try `IdeaS25_Resolved` at any value other than the default 1.

## What I am NOT sure about

I am not sure the soft-time clause changes a clock game. It was not played.
I am not sure -4.08 Elo is a real loss. The +/- 10.02 interval includes positive values.
I am not sure a value of `IdeaS25_Resolved` other than 1 is useful. Only the default was measured.

times: see stamps.txt

## git status --short and ls -la

"""
)
(here / "REPORT.md").write_text("".join(parts))
print(result, end="")
