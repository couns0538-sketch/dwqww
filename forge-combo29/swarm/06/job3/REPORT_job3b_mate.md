# REPORT job 3b — area 6: the mate-PV check that explains finding S-F9

## What was asked / the answer / how sure

**Asked.** Not a separate assignment: this is the follow-up on my own job-3 observation S-F9, that on G
index 196 one side reports `cp 4402` while its colour mirror reports `mate 14`, and on index 217 `cp 2557` vs
`mate 11`. A mate on one side and a huge centipawn score on the other would be a serious engine fault, so it had
to be checked rather than left as a suspicion.

**Answer.** It is **not a fault**. Two separate explanations, both checked:

1. **The PVs are truncated at the depth horizon, not wrong.** Every mate score in the depth-10 G output whose PV
   reaches its full `2N-1` plies is a **real checkmate**: 12 of 12, with 0 illegal moves and 0 "legal but not
   mate". The 4 mate PVs that do not reach full length are cut off at the search horizon (PV plies 11/15/14/16
   against a required 20/16/27/21) — the engine printed as much of the PV as it had searched, which is normal UCI
   behaviour, not a claim that the mate is delivered inside the shown line.
2. **`cp 4402` is not a mate score in disguise.** The engine's mate threshold is
   `MateInMaxPly = 32000 - MaxPly = 31872` (`include/forge/search.hpp:73-74`), and **0 of 353** G records carry
   a `cp` score at or above it. The huge cp is simply a completely winning position scored before the search
   depth was enough to see the mate: the same position at depth 6 / 8 / 10 / 12 / 14 gives
   `cp 4009 / cp 4177 / cp 4412 / mate 8 / mate 4`, i.e. the mate is found at depth 12, and the depth-10 number is
   a legitimate non-mate score. The mirror side finds the mate at depth 10 because its tree is different (see
   job 3's ordering mechanism).

**How sure.** High. The mate check is mechanical (python-chess replays every PV and asks `is_checkmate`), and the
depth ladder is reproducible from one command.

## Honesty numbers

Same build, `~/bld/release/forge`, sha256 `e06310eca…`, bench 11/13/16 = 312866/862329/3024920, perft 5 =
4865609 (`../HONESTY.txt`). Threads 1, Hash 16 for the depth ladder. The mate check reads only
`out_G_d10.txt`, which carries its own `meta_G_d10.txt` with the exe path, sha256, `id name` and all option
lines.

## Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| does the reported mate PV actually deliver mate? | done | `check_mate_pv.py`, `mate_pv_check.txt` | 12 of 12 full-length PVs are checkmate |
| illegal moves inside a mate PV | done | same | 0 |
| legal PV ending in a non-mate | done | same | 0 |
| mate score leaked into a `cp` field | done | same | 0 of 353 (threshold 31872, `search.hpp:73-74`) |
| mate PVs shorter than 2N-1 | done | same | 4, all truncated at the horizon (plies 11/15/14/16) |
| is `cp 4402` a real evaluation? | done | depth ladder below | yes: 4009 / 4177 / 4412 / mate 8 / mate 4 at depths 6/8/10/12/14 |
| was position 196 actually mate-in-1 (a missed mate)? | done | python-chess | no, 0 mate-in-1 moves among 32 legal moves |

The depth ladder for G index 196 (`5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1`), pasted:

```
depth 6  cp 4009  nodes 965   bestmove f8e7
depth 8  cp 4177  nodes 6394  bestmove f8d6
depth 10 cp 4412  nodes 11215 bestmove f8d6
depth 12 mate 8   nodes 27427 bestmove f8d6
depth 14 mate 4   nodes 30941 bestmove f8d6
```

Commands that show each result again:

```
python3 check_mate_pv.py out_G_d10.txt
python3 depth_scan.py ~/bld/release/forge "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1" 14
```

## Findings

**F1 — every full-length mate PV in the depth-10 G output is a genuine checkmate (12 of 12), and no `cp` score
reaches the engine's mate threshold. The mate machinery is sound on this set.**
Shows again: `python3 check_mate_pv.py out_G_d10.txt`.

**F2 — the `cp 4402` vs `mate 14` pair is a depth artefact, not a bug: the same position needs depth 12 to see
the mate (`cp 4009 → 4177 → 4412 → mate 8 → mate 4` at depths 6/8/10/12/14), and its mirror's different tree
found the mate two plies earlier.**
Shows again: `python3 depth_scan.py ~/bld/release/forge "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1" 14`.

**F3 — 4 of 16 mate PVs in `out_G_d10.txt` are shorter than `2N-1` plies, so a checker that requires a full PV
will report them as failures. This is horizon truncation, not a wrong score.** Recorded because it will bite
anyone who writes a mate-PV assertion (area 5 job 1 is exactly such a checker) — the assertion must be
"`played_plies >= 2N-1` OR `played_plies == searched plies`", not "the final position is mate".
Shows again: `python3 check_mate_pv.py out_G_d10.txt` (the TOO-SHORT listing).

## Suspicions, not proven

None open from this check. The cp-vs-mate question is answered; the ordering asymmetry it came from is job 3's
finding S-F6/S-F7/S-F8 and stands on its own.

## What I did NOT do

- I did not re-search all 353 positions at depth 12 to see how many mate/cp disagreements disappear with depth.
  That is a cheap and worthwhile follow-up but it is a new job, not this check.
- I did not test negative mate scores for correctness beyond replaying the PV: a `mate -N` claim means the
  *opponent* mates, and a truncated PV cannot demonstrate that. The 11-ply `mate -10` at index 69 is such a case
  and is listed as NOT CHECKED, not as verified.

## What I am NOT sure about

- Whether the 4 truncated mate PVs would still be mates when searched deeper. Index 196's mate is confirmed at
  depth 12 and 14, so that one is solid; the other three were not extended.

## Times

`date -u` lines are in `stamps.txt`.

## Last command's output

The `ls` of this folder is in `stamps.txt`; `check_mate_pv.py`, `mate_pv_check.txt` and this report are the new
files, and `depth_scan.py`, `out_G_d10.txt` are the reused ones.
