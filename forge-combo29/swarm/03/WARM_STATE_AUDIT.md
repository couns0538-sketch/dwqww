# WARM-STATE AUDIT — seat 03, after seat 10's report

Seat 10 reports: two identical unrestricted searches in ONE process give 56,720 then 4,951 then 4,516 nodes, while
three separate processes give 56,720 each; `ucinewgame` restores cold, `Clear Hash` does not (40,569, a third value).
I reproduced it exactly before checking my own work (`job0/warm_state.py`, section E).

## Does it touch any number I published?

**No.** Every published number in this folder comes from `go perft d`, never from a depth search. My harnesses do
run many positions per process (500 per process in job 1), so the question "is perft warm-state dependent?" had to
be measured, not argued. `job0/warm_state.py` measures it on one mid-game position:

```
A perft 4 x10 in one process
  values: [1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595]
  distinct: [1110595]  STABLE
B perft 4, then ucinewgame, then perft 4
  values: [1110595, 1110595]  STABLE
C perft 4, then Clear Hash, then perft 4
  values: [1110595, 1110595]  STABLE
D perft 4 x10 in ten separate processes
  values: [1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595, 1110595]  STABLE
E CONTROL go depth 12 x3 in one process
  values: [56720, 4951, 4516]  VARIES
```

So on this build: perft gives the identical count warm, cold, after `ucinewgame`, and after `Clear Hash`; and the
same harness DOES detect the depth-search warm effect (control E), which is what makes the perft stability a
measurement rather than a harness that cannot see anything.

Raw transcripts: `job0/warm_state.{a,b,c,d0..d9,e}.raw`.

## What in my folder was measured with several searches in one process

| result | process model | warm-state risk | label |
|---|---|---|---|
| job1 perft 1..4, 5,000 R positions | 10 processes x 500 positions, perft only | none (perft stable, measured above); each position starts from `position fen` | **cold-equivalent, valid** |
| job2 perft 1..4, 314 special positions | 4 processes x ~100 positions, perft only | none | **cold-equivalent, valid** |
| job3 perft 1..5, 230 positions | 5 processes x 50 positions, perft only | none | **cold-equivalent, valid** |
| job1b perft 1..4, 5,000 positions (SEED 311) | 10 processes x 500, perft only | none | **cold-equivalent, valid** |
| check13 perft 1..4, seat 13's 5,000 | my harness, perft only | none | **cold-equivalent, valid** |
| honesty pins: `bench 11/13/16` | one process each, `ucinewgame` before | a `bench` run does its own internal sweep; the pins are node counts, not timings, and all three match the brief's pinned values in both harnesses | **valid (matches the pin)** |
| `honesty.sh` perft 5 | one process, after `ucinewgame` | none | valid |
| the two `go depth 12` runs I used **only** to demonstrate seat 19's quit fault | one process each, single search | n/a — the point was the fabricated answer | not a measurement |

## Was `Clear Hash` ever used as a baseline by me?

No. Grep of my whole folder for `Clear Hash` before this audit: only the mention in this file and the `warm_state.py`
test. I have never set it, and never used it as a "cold" baseline.

## One thing worth telling the others

Section C above shows `Clear Hash` leaving perft at 1,110,595 — identical to cold — so on this build `Clear Hash`
does not disturb perft at all, while seat 10 is right that it does not restore the cold *search* state. Both are
consistent: perft touches no hash. My perft tables are therefore safe even if a `Clear Hash` had been in the loop;
the depth-search tables in other seats' areas are the ones that need the seat-10 rule.
