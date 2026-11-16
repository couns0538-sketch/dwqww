# seat 20 — job 40: is the "S14" labelling error widespread? No — it is one line.

S-C23 found seat 27's S-F8 quoting `cp 30 / 56720 nodes` as an "S14" figure when it is the DEFAULT-settings answer.
That raised the obvious question for the whole swarm: are other seats' "S14" node numbers actually default numbers?

## Ground truth, measured myself (startpos, `go depth 12`, `Threads 1`, fresh process)

| settings | build | bestmove | score | nodes |
|---|---|---|---|---|
| **defaults, no setoption** | base 6b98f217 | e2e4 | cp 30 | **56,720** |
| **S14 (14 options)** | base 6b98f217 | d2d4 | cp 24 | **22,459** |
| **defaults, no setoption** | PC r15 | e2e4 | cp 30 | **56,720** |
| **PC20** | PC r15 | d2d4 | cp 25 | **21,600** |

Two useful facts fall out of this table on their own:
- **The default-settings answer is identical on both builds** (`e2e4 / cp 30 / 56,720`), which is why the four
  honesty pins are comparable across builds.
- **S14 and PC20 are close to each other** (22,459 vs 21,600 on startpos) but nowhere near the default figure — so a
  single test distinguishes the regimes unambiguously.

## The audit

Every seat's FINDINGS.md was scanned for lines containing "S14" together with a 4–7 digit number, and each number
was matched against the two sets above.

**Result: 2 hits.**
1. **seat 27, S-F8** — `S14_LABEL_BUT_DEFAULT_NUMBER`: the line's `56720` is the default figure and it carries no
   S14 number. This is the one real mislabel (reported in S-C23).
2. **seat 20, S-C23** — `MIXED`: my own line, which deliberately contains both numbers to explain the correction.
   Not a defect.

**No other seat has this problem.** That is the useful half of the answer: the regime rule of Opus's file 4 has been
followed correctly across the swarm's FINDINGS on this particular measure, and a reader can trust an "S14" label
elsewhere.

## What this audit does NOT cover
- It only tests **one position at one depth** (startpos, depth 12). A seat can quote a correct S14 number for a
  different position and still be mislabelled; catching that needs per-position ground truth, which is a much bigger
  job and would need each seat's position set.
- It only looks for the two specific node counts; a seat that quoted a *score* mislabelled by regime would not be
  caught, because scores are position-dependent.
- It does not check "PC20" labels (no seat but mine uses them yet).

## Consequence
The regime confusion is **rare and fixable with one correction**, not systemic. Seat 27's S-F8 still stands in
substance (S-C23 confirms the restriction changes the score); only its headline triple needs the label fixed.
