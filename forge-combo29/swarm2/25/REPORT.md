# REPORT — seat 25, group 5, part 5

## 1. Seat and machine

| | |
|---|---|
| seat | **25** |
| group / part | **5 / 5** (the checker) |
| model | DeepSeek V4.1 Flash |
| machine | 4 cores, `nproc` = 4, Intel(R) Xeon(R) Processor, 1 thread per core, 4 cores per socket |
| compiler | g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0 |
| `-march=native` gives | `__AVX512F__ 1`, `__AVX512BW__ 1`, `__BMI2__ 1` |
| clang | Ubuntu clang version 18.1.3 (present, not used by this seat) |
| python-chess | 1.11.2 |

## 2. STEP 2 — builds and known numbers

**Patches: all clean, no line containing `offset`, `fuzz`, `FAILED`, `reject` or `malformed`.** Full patch
output is in `step2.txt`. Patch hashes all matched the brief:

```
d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a  pc_r15.patch
034814873e2ffce7010b7b065d79b5aa0a57419cbb75cc8bfc4ff22208278cea  a_speed.patch
20cca10770a32af8d9b7b26b9fd9544fefb67e592b35177f68788cfd73ab7574  e1.patch
3d2ce085a8b76478942d4e29d7a74512eb3ecd2d328d224e27f711a48e46cb30  stack.patch
```

**Checksum lists: 29 of 29 OK on r15d, 29 of 29 OK on kF**, zero non-OK lines (`sha256sum -c`).

Binaries:

```
da21c7efaa2fd850f008e7342bbd2314c1e38eeb817b9d0e9dfa38f5ca959130  bin_r15d
59f95a59ef9dc5eca379117254de013fad60013fbebdc668c3a4ce6a37ac4d0e  bin_kF
```

| check | expected | bin_r15d | bin_kF | verdict |
|---|---|---|---|---|
| no options, `bench 11` | 312866 | 312866 | 312866 | MATCH |
| no options, `bench 13` | 862329 | 862329 | 862329 | MATCH |
| no options, `go perft 5` | 4865609 | 4865609 | 4865609 | MATCH |
| PC20, `bench 11` | 278024 | 278024 | 278024 | MATCH |
| PC20, `bench 13` | 587276 | 587276 | 587276 | MATCH |

Two operational notes for whoever runs this next, both cost me time:
- **`bench N` must be sent on stdin.** Passed as argv it prints nothing and exits 0. A process fed
  `bench` and read with a "read until bestmove" loop **hangs forever**, because `bench` never emits
  `bestmove`. I lost about eight minutes to that before switching to a full scripted stdin read to EOF.
- **`go perft` prints `nodes 4865609`**, not a `Nodes searched:` line. A parser looking for the latter
  reports nothing and looks like a wrong perft.

The **net768** known numbers (bench 11 -> 882074, bench 13 -> 4275906) are for groups 1, 2, 3 and part 5
of group 4. Seat 25 is group 5 part 5, so they are outside my required set and **were not run**.

## 3. Group 5 known answers — the three ladders

The position `2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1`, `go depth 1..20`, each a fresh
search after `ucinewgame` + `isready`, on bin_r15d. **All 20 rows of all three ladders match the brief,
including every node count and every bestmove.** Raw: `ladder_S14.txt`, `ladder_B.txt`, `ladder_PC20.txt`.

| setting | first positive `mate` at | nodes there | depth-20 bestmove | depth-20 score | depth-20 nodes |
|---|---|---|---|---|---|
| S14 | depth **16** | **240,516** | `g3g6` | mate 2 | **241,262** |
| S14 + HistRework 2 | **never through 20** | n/a | `f6h5` | cp 836 | **774,832** |
| PC20 | **never through 20** | n/a | `f6h5` | cp 916 | **1,052,250** |

My three ladders reproduce the brief exactly. Because the brief's numbers are met, my part may proceed.

**The ladders do not show what a careless reader would take from them.** In the A ladder the score stays
centipawn through depth 15 and only at depth 16 does it become `mate 2`. So the P position is **not** a
case of a mate being reported and then hidden; it is a case of a mate that a fixed depth below 16 never
finds, in all three settings, and that S14 finds at 16 and the other two never find. **B and PC20 do not
lose a mate the default has; they fail to find a mate the default finds only at the last depth of the
ladder.**

## 4. The prediction, graded

Committed alone at 2026-11-18T15:35Z (`prediction.md`), after the three ladders and before any census run.

| predicted quantity | predicted range | measured | verdict |
|---|---|---|---|
| share of M that B does not find by depth 16 | 10 – 45 % | **0.0 %** (0 of 117) | **OUTSIDE — too low** |
| share of M that E does not find by depth 16 | 15 – 50 % | **0.9 %** (1 of 117) | **OUTSIDE — far too low** |
| share of M that B finds later than A | 0 – 15 % | **5.1 %** (6 of 117) | inside |
| share of M that E finds later than A | 0 – 15 % | **14.5 %** (17 of 117) | inside, just |

**Two of four are outside, both badly.** I also predicted M would be "most likely 90 or more"; M is **117 of
120**, so that was right. My error was the size of the HistRework 2 mate defect on real finish positions: I
expected a partial loss and the truth is essentially none.

## 5. Results

### 5.1 The census

120 positions: the first 40 games of `F1k.pgn` in file order whose final position is checkmate and which
have at least 8 plies, and from each the positions 3, 5 and 7 plies before the end. `positions.tsv`,
sha256 `faf85239c3e154817abe3182eefa19e10670f58d64a41e7ba14558dbdeb604bd`. Every position was checked to
have the winner to move; game 41 was hand-verified as Black mating in 2 with Black to move.

Settings: A = S14, B = S14 + HistRework 2, E = PC20, F = PC20 + HistRework 0. One search per position,
`go depth 16`, fresh `ucinewgame` + `isready` each time, bin_r15d throughout. Raw: `census_A.json`,
`census_B.json`, `census_E.json`, `census_F.json` (one record per position per setting, with the full
first-mate triple, last info line and bestmove).

**M = 117 of 120** positions where A's last score is a positive mate.

| setting | found by 16 of M | earlier than A | same depth | later than A | **not by 16** | finds a mate A does not |
|---|---|---|---|---|---|---|
| B = S14 + HistRework 2 | 117 / 117 | 9 | 102 | 6 | **0** | 0 |
| E = PC20 | 116 / 117 | 12 | 87 | 17 | **1** | 0 |
| F = PC20 + HistRework 0 | 117 / 117 | 13 | 85 | 19 | **0** | 0 |

The three positions where A itself reports no mate at depth 16 (games 45 back 5, 45 back 7, 59 back 7)
are not in M and are excluded from every share above.

**The single E failure** is game 59 back 5, `8/8/p7/8/2Q5/P7/3p2PK/3k4 w - - 10 53`: A finds `mate 4` at
depth 9, E ends at depth 16 on `cp 2011`, bestmove `h2g3`. B finds it at depth 10. So on this one position
PC20 loses a mate that is one ply deeper than the mate A finds.

### 5.2 The control that decides what the census means

This is the part I would keep if only one result survived, and it is **not** what the brief asked for. I
asked why B showed zero loss where the ladder showed total loss, and the answer is that **the corpus was
not sampling the class the rule can affect.**

`QuietExtinction` and its relatives act on **quiet** moves. A mating move that is a check or a capture is
not a quiet move, so a history-driven quiet rule cannot hide it. I therefore classified every census
position independently of the engine: for the position 3, 5 or 7 plies before the end, I enumerated every
first move that forces mate within exactly that many plies, and tagged each as check, capture, or quiet.
`quiet_oracle.json`. (Bounded exhaustive search, 3 s per position; 84 of 120 resolved, 36 timed out. The
timed-out ones are excluded from the table below and are **not** counted as "no mate".)

| the position's mating moves | n | B found | E found | F found |
|---|---|---|---|---|
| **every mating move is quiet** | **24** | **24 / 24** | 23 / 24 | 24 / 24 |
| some mating move is quiet | 33 | 33 / 33 | 33 / 33 | 33 / 33 |
| every mating move is a check or capture | 26 | 26 / 26 | 26 / 26 | 26 / 26 |
| no mating move found by the oracle | 1 | 0 / 1 | 0 / 1 | 0 / 1 |

**On the 24 positions where the ONLY way to mate is a quiet move, HistRework 2 found the mate 24 times out
of 24.** That is the class the rule is supposed to damage most and it is untouched. Examples where A and B
agree exactly, quiet mating move named from the oracle: game 43 `b8d8`, game 47 `f6f7`, game 58 `c4c2`,
game 59 `a3a4`, game 62 `b7b8q` (a quiet promotion), game 77 `f4e3`, game 79 `g5h5`.

**So the honest statement is not "HistRework 2 is safe".** It is that **a fixed depth 16 on real finish
positions does not expose the defect that the single P position exposes at depths 1 to 20**, even on the
quiet-only subset, and the two facts are both true. The rule is selective in a way neither the ladder nor
the census alone shows: it costs a mate on a position that needs 16 plies of search to resolve, and it
costs nothing on 117 real mates in 2 to 4 searched to depth 16.

### 5.3 What changed between settings, where nothing was lost

Score or mate-distance differed between A and B on 2 of 117 cells, A and E on 2, A and F on 1, even where
both found a mate. In the "found later" column E is the worst of the three at 17 cells (14.5 %), and E is
also the setting that loses one outright. F, which differs from E only by `HistRework 0` instead of 2, finds
every mate A finds and is the latest of all (19 later). **That ordering is the opposite of what the
HistRework value alone would predict**, and I do not have an explanation for it from these data.

## 6. What I did not do, and what I am not sure about

**Not done**
- **Seat 21 never pushed.** I checked at 15:29Z and again before starting the census: only seat 25 existed
  among `for-fable-and-opus/swarm2-*`. So the primary part-5 task — recount seat 21's committed raw output
  with my own parser, then run A and B on its first 30 positions — **was not possible.** I took the stated
  fallback in full: the three ladders, then the census on the next 40 checkmate games of `F1k.pgn` (games
  41 to 80). I did not read any other seat's code, because there was none.
- **The four non-mandatory settings checks.** No net768 run (outside my required set). No sanitiser build.
  No kF anything: the brief gives group 5 only bin_r15d, and I ran only bin_r15d. **Every number in this
  report is r15d.**
- **No timing.** Nothing here is a speed measurement, so the kF question is untouched by this seat.
- **The 36 oracle timeouts.** Excluded, not imputed. A few may have mating moves; the table's denominators
  are the 84 resolved positions only.

**Not sure about**
- **Whether the census's zero means the rule is safe or the corpus is easy.** I believe the second is the
  larger part: 115 of 120 positions have A reporting the mate by depth 10, and 6 by depth 1. A depth-16
  search on a mate in 2 has enormous slack, so the rule has to fail in a very particular way to show. **The
  P position is mate in 2 as well and still fails** — so "mate in 2 is easy" does not by itself explain it,
  and the difference between P and the census is unresolved. Something about P (a quiet, non-obvious,
  non-checking key move in a crowded position) is not captured by "the mating move is quiet", because 24
  corpus positions where every mating move is quiet still pass.
- **The one E loss could be noise.** It is one cell, and I did not re-run it with a fresh process to
  confirm reproducibility, so I would not build on it.
- **My quiet/check/capture labels come from python-chess, not from the engine**, and "quiet" there means
  not a check and not a capture. The engine's own definition may also exclude promotions or include other
  terms, so my class boundary is an approximation of the engine's.

## 7. The two commands the brief requires, pasted

Captured immediately before the report commit (`git status --short` is empty, i.e. the tree was clean).

```
$ git status --short
(no output)

$ ls -R forge-combo29/swarm2/25
forge-combo29/swarm2/25:
census_A.json
census_B.json
census_E.json
census_F.json
ladder_B.txt
ladder_PC20.txt
ladder_S14.txt
positions.tsv
prediction.md
quiet_oracle.json
REPORT.md
SEAT.txt
stamps.txt
step2.txt
```

Every file is text. No program, object file, net, book, PGN or archive of them is committed: the PGNs and
all four trees (`r15d`, `kF`, the sanitiser copy, and `forge-combo29`) live only in `~/w` and were never
added to the repository.

## 8. What I would tell the next seat to do differently

**Search the class, not the corpus.** The one valuable result here came from asking "is the mating move in
this corpus actually the kind of move the rule can touch", and the answer was that on 24 of 83 resolvable
positions it is exactly that kind of move, and the rule still never fails. **A zero on a corpus is only
evidence about a rule if the corpus reaches the rule's trigger**, and the cheapest way to establish that is
an independent oracle over the corpus positions, not more engine runs. My census had 120 rows and the
control that made it interpretable had 84, and the control was worth more than the census.

**A known answer that matches can still be misread.** All three ladders matched the brief exactly and it
would be easy to report "HistRework 2 hides a mate in 2" as the finding. The ladder shows a mate that no
setting below depth 16 finds and that two settings never find; that is a narrower and different claim, and
it is the one the numbers support.
