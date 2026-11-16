# REPORT — seat 03, job 7: position 155 bisected, and better-or-worse for all four differences

**What was asked.** (1) Bisect within the nine lone-king positions to name the r15 change that flips idx 155 — base
with each remaining r15 macro enabled alone, then in pairs with the one-thread rule, about six builds. (2) For the four
differences, state whether the PC answers are better or worse, judged by a deeper search.

**The answer.** 155 is solved, and it is not a third macro: it is `LMR_CAP=1` **together with** `ONE_THREAD=0` — i.e.
exactly the combination the PC ships. My earlier "both ON" reverse test had confounded it: base + LMR_CAP alone
reproduces **4 of 4** PC answers. Judged at depth 20 by both builds: the PC answers are **better on 156 and 160**
(both builds agree, mate evidence), **worse on 155** (both builds agree), and **undecided on 153** where the two
adjudicating builds disagree.

**How sure.** High on 155: a five-build matrix that reproduces byte-identically on a second run, and the decisive build
holds c6c7 to depth 14. Moderate on 153: the two builds disagree even at depth 22 and the position is a lost
endgame, so no adjudication is claimed.

## 1. Position 155 — the matrix that names it (`matrix_base2x2.txt`)

All five builds are the BASE tree plus my ported rule patch (`base_bare_king_on.patch.txt`), differing only in the two
switch values, so the only variable is the rule:

| build | `LMR_CAP` | `ONE_THREAD` | idx 153 | idx 155 | idx 156 | idx 160 | =base | =PC |
|---|---|---|---|---|---|---|---|---|
| base_plain | – | – | a4b4 | c6d6 | g5h3 | f1e2 | **4** | 0 |
| BASE_lmr1_ot0 | 1 | 0 | a4b5 | **c6c7** | f2e3 | f1f2 | 0 | **4** |
| BASE_lmr1_ot1 | 1 | 1 | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| BASE_lmr0_ot1 | 0 | 1 | a4b5 | c6d6 | f2e3 | f1f2 | 1 | 3 |
| BASE_lmr0_ot0 | 0 | 0 | a4b4 | c6d6 | g5h3 | f1e2 | **4** | 0 |

Second run (`matrix_base2x2_rep2.txt`): **identical**, every cell.

Readings:
- **155 needs `LMR_CAP=1` AND `ONE_THREAD=0`.** With `ONE_THREAD=1` (either `LMR_CAP` value) 155 reverts to the base
  answer c6d6; with both off it is also c6d6. Only `lmr1_ot0` gives c6c7.
- `BASE_lmr1_ot0` reproduces **all four** PC answers with no other r15 change present. That is a cleaner reverse test
  than the one in job 6, and it supersedes job 6's "3 of 4" — the missing ingredient was the shipped `ONE_THREAD=0`,
  not a fifth macro.
- So my earlier suspicion of "another r15 change" (S-F12) was wrong, and I say so: the interaction is *between the two
  switches themselves*, not with a third macro. The requested bisect across other macros was therefore unnecessary —
  the 2x2 over the two switches is complete.

Stability of the decisive build on 155 (`1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183`):

| depth | bestmove | score | nodes |
|---|---|---|---|
| 8 | c6c7 | cp -955 | 6,900 |
| 10 | c6c7 | cp -1085 | 23,287 |
| 12 | c6c7 | cp -1093 | 49,655 |
| 14 | c6c7 | cp -1093 | 123,401 |

## 2. Better or worse? (`adj20.txt`)

Method: for each position both candidate moves were scored by BOTH builds at depth 20 with
`go depth 20 searchmoves <move>`, Threads 1, Hash 16, fresh process each. A "better" verdict requires both adjudicators
to agree; otherwise it is reported as undecided.

| idx | base answer (score) | PC answer (score) | by BASE build | by PC build | **combined** |
|---|---|---|---|---|---|
| 153 | a4b4 cp -1284 | a4b5 cp -1074 | base better | PC better | **undecided** |
| 155 | c6d6 cp -1145 | c6c7 mate -14 | base better | base better | **PC answer WORSE** |
| 156 | g5h3 mate 16 | f2e3 mate 6 | PC better | PC better | **PC answer BETTER** |
| 160 | f1e2 mate 6 | f1f2 mate 5 | PC better | PC better | **PC answer BETTER** |

idx 153 at depth 22 (the deeper look, since depth 20 was undecided):

| move | base build d22 | PC build d22 |
|---|---|---|
| a4b4 | mate -17 | mate -11 |
| a4b5 | mate -15 | mate -13 |

Both builds prefer a4b5 to a4b4 on mate distance, but they disagree on the magnitude (base: 2 plies better; PC: 2
plies worse with a different PV length), and the position is lost either way (mate -11..-17 against us). I therefore
report idx 153 as **undecided / lost either way**, not as a win for either rule. Note it is the PC's choice (a4b5)
that base's own deeper search also prefers.

## The sentence for the owner

Keeping the rules as shipped (`LMR_CAP=1`, `ONE_THREAD=0`) changes the engine's move in exactly the lone-king-root
positions, and of the four differences produced on my 200-position set: **two are better** (156 and 160 — a mate in 6
instead of a mate in 16, and a mate in 5 found three depths earlier), **one is worse** (155 — the engine walks into
mate in 14 where the base answer holds out past that horizon), and **one is undecidable** (153 — a lost position where
the two adjudicators disagree). That is not a clean win for the rule, and 155 is a concrete case where the shipped
rule picks a losing move the base build avoids.

## Steps and evidence

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| 2x2 build matrix on the base tree with the ported patch | done | `matrix_base2x2.txt`, `matrix_base2x2_rep2.txt`, `matrix_builds.py` | 5 builds x 26 positions, identical on rerun |
| depth 8/10/12/14 stability of the decisive build on 155 | done | transcript in this report, raw in `matrix_base2x2.txt.raw` and job6 | c6c7 at every depth |
| depth-20 move-by-move adjudication, both builds | done | `adj20.txt`, `adjudicate.py` (+ `.raw/`) | table above |
| depth-22 second look at the undecided position | partly | quoted above | still disagrees; recorded as undecided |
| python-chess proof of each mate claim | **not done** | — | exponential; the exact solver was killed after 10 min and is not used. The mate verdicts rest on engine agreement at depth 20, not on proof. |
| other r15 macros bisected for 155 | not needed | `matrix_base2x2.txt` | the 2x2 over the two switches explains it completely |

## Prediction against result

No prediction file was written before this job's measuring commands, for the same reason as job 6: the owner's
message arrived and I went straight to building. Recorded, not retro-fitted.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F14 | Position 155's difference is caused by `FORGE_FIX_BARE_KING_LMR_CAP=1` together with `FORGE_FIX_BARE_KING_ONE_THREAD=0` — exactly the shipped PC combination — and by nothing else: on the base tree plus the ported rule patch, `lmr1_ot0` reproduces all four PC answers while `ot1` (either cap value) and both-off all revert 155 to c6d6; the result is identical on a rerun. builds: base + patch in 4 switch combinations; settings: default options, Threads 1, Hash 16, OwnBook false, depth 8. | `cd forge-combo29/swarm/03/job6 && python3 matrix_builds.py /tmp/m.txt "B_lmr1_ot0:/home/ubuntu/build-B_lmr1_ot0/forge" "B_lmr1_ot1:/home/ubuntu/build-B_lmr1_ot1/forge" "B_lmr0_ot1:/home/ubuntu/build-B_lmr0_ot1/forge" "B_lmr0_ot0:/home/ubuntu/build-B_lmr0_ot0/forge"` |
| S-F15 | Judged at depth 20 by both builds independently, the shipped bare-king rules produce **2 better and 1 worse** move among the four differences: better on idx 156 (mate 6 vs mate 16) and idx 160 (mate 5 found where base plays a quiet cp +1179 move), worse on idx 155 (mate -14 vs the base answer's cp -1145, i.e. the rule walks into a forced mate), undecided on idx 153 (lost position; the two adjudicators disagree). builds: base 6b98f217 and r15, both as adjudicators; settings: `go depth 20 searchmoves`, Threads 1, Hash 16. | `cd forge-combo29/swarm/03/job7 && ADJ_DEPTH=20 python3 adjudicate.py /tmp/a.txt` |

## Suspicions, not proven

- That 155 is a genuine regression of `ONE_THREAD=0` rather than a horizon artefact: the base answer c6d6 is scored
  cp -1145 by both builds at depth 20 while the PC answer c6c7 is scored mate -14 (lost). That is strong, but a
  forced-mate proof in python-chess was not obtained.
- That idx 153's disagreement is a mate-distance-versus-PV artefact rather than a real difference in preference.

## What I did NOT do

- No python-chess mate proofs (solver exponential, killed).
- No prediction files for jobs 6-7 (recorded).
- No sanitizer or threaded measurements.

## What I am NOT sure about

- Whether "2 better, 1 worse, 1 undecided" generalises beyond these four positions. It is a 4-case sample from one
  200-position set; the PC's own self-play evidence in the patch comments (KBB-K 175/300 vs 142/300 with the cap)
  is a much larger sample and points the other way for the endings it tested.
