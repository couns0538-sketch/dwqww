# Applying the score-by-depth lens to every row it was used on (S-C49)

`S-C47` classified all five outlier positions using depth, seldepth, nodes and the **final** score. `S-C48` then found
that for i=16 that was not enough — the final score hid the fact that S14 had reached the mate three iterations earlier
while PC20 was still returning evaluations. **A method that indicts one row has to be run against every row it was used
on**, so here is all five under the score-by-depth lens.

## All five, first moment each setting reports a mate

| i | node ratio | S14 first mate | PC20 first mate | final scores equal? | verdict under this lens |
|---|---|---|---|---|---|
| 16 | 18.37× | d9 `mate −4` (11,613) | **d12** `mate −3` (238,009) | yes | **later convergence** — PC20 found it 3 iterations later |
| 78 | 6.10× | d7 `mate 7` (10,075) | d7 `mate 5` (12,657) | no | **stronger, earlier** — PC20 already better at the same depth |
| 99 | 3.81× | d10 `mate −9` (2,626) | d10 **`mate −4`** (8,341) | yes | **earlier correctness** — PC20 right one iteration sooner |
| 72 | 3.49× | d8 `mate 6` (3,302) | d8 `mate 6` (6,714) | no | **stronger at the end, after losing the lead** — tied d8–d9, S14 ahead at d10 (`mate 5` vs `mate 6`), PC20 overtakes at d11 (`mate 4`) |
| 116 | 2.95× | d11 `mate 5` (8,744) | d11 `mate 4` (24,825) | no | **stronger at the same depth** — both find a mate at d11, PC20's is one move shorter |

## Which of my earlier verdicts change

| i | `S-C47` verdict | verdict now | changed? |
|---|---|---|---|
| 16 | "more verification of the same answer" | **later convergence**, PC20 slower to find the mate | **YES** — corrected in `S-C48` |
| 78 | stronger (shorter mate) | unchanged — and now with the extra detail that PC20 was already better at d7, the first depth either found a mate | confirmed, sharpened |
| 99 | "more verification of the same answer" | **earlier correctness**: S14 reported `mate −9` at d10 and only revised to `mate −4` at d11, while PC20 had `mate −4` from d10 | **YES** |
| 72 | stronger (shorter mate) | unchanged — but the path is not monotone: tied d8–d9, **S14 ahead at d10**, PC20 overtakes at d11 | confirmed, sharpened |
| 116 | stronger (shorter mate) | unchanged — one move shorter at the same depth, immediately | confirmed |

**Two of five verdicts change, and both were the ones I had called "more verification".** That is not a coincidence: the
phrase "same answer, more work" was my shorthand for "the final scores match", and the final score is exactly the
summary that hides *when* the answer arrived.

## The two corrections, stated plainly

**i=99 was not verification.** I wrote that PC20 "raised seldepth 21→26 at the SAME score — more verification of the
same answer". The trace shows PC20 reached the **correct** score one iteration before S14 did: at depth 10 S14 said
`mate −9` and PC20 said `mate −4`, and S14 only converged at depth 11. So PC20's extra nodes bought **earlier
correctness**, which is a real benefit of the same kind as i=78's shorter mate, not redundant checking.

**i=16 was the opposite**, as `S-C48` established: the same final score arrived *later* under PC20, with seldepth
climbing 17→21→26→34→51 while S14's saturated at 25.

So the five positions are not one phenomenon with five instances. **Two are PC20 finding the answer sooner or better
(78, 116), one is PC20 finding it sooner in a different sense (99 — correct earlier, same final), one is PC20 finding it
later (16), and one is PC20 finding it better only after trailing at d10 and overtaking at d11 (72).** The node ratio alone cannot tell
these apart, which is why the mean was misleading.

## The rule this adds to the record

`S-C47`'s rule was "the axes defining *the same search* must include what it concluded". `S-C48` refined it to include
**when** it concluded it. This page adds the part that cost me two wrong verdicts: **a summary axis that matches at the
end can conceal a difference in the middle, and "same answer, more work" is not a diagnosis — it is what the final
score looks like when you have not looked at the path.**

The cheap test that would have caught both: **for each position, find the first iteration where each setting reports
its final answer.** Two numbers per position, and they separate every case in the table above.

## What I am not claiming

* Not that these five generalise. They are the tail of a bimodal distribution on one FEN sample; the *classification
  method* generalises, the proportions do not.
* Not that later convergence is a defect. It is a cost with a mechanism (a quiescence regime that keeps extending). It
  becomes a defect only if someone can show the extension is wasted, which I have not.
* Not that "verification" was the wrong *word* for i=99 so much as the wrong *finding* — PC20 did more work and got a
  better-founded answer, but "better-founded" here means "correct sooner", not "checked more".
