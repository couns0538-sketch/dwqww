# PREDICTION — deepseek6, job 5 (where the check extension spends its nodes)

Written before the first counted run (E0). Never edited after this commit.

Step 0 is already met (recorded here so the reader knows what the predictions rest on):
plain pins 312866/862329/3024920/4865609; counter build's pins the same; counter == plain on S14 (O 9,500,069,
G 18,466,239) and on `CheckExtensionDepth 8` (O **9,015,167** — the published known answer, reproduced exactly).

## The three predictions the job asks for, all from E0 on O

**(a) The share of `ext` at depth 2..7 of all `ext`.**
`CheckExtensionDepth` defaults to **2**, so under E0 every depth ≥ 2 extends. The deepest nodes are the rarest, so
I expect the bulk of extensions to sit at the SHALLOW end of that band. **I predict the share at depth 2..7 is
between 85 % and 99 %**, and specifically that **depth 2 alone carries at least 30 %** of all extensions.
Kill: a share below 85 % or above 99 %; or depth 2 below 30 %.

**(b) `sub_nodes` at depth 2..7 as a share of the whole tree (9,500,069), against the 5.1 % the tree shrinks under
CED 8.**
CED 8 removes every extension at depth 2..7 and the tree shrinks by 5.1 %. If the removed extensions' subtrees
were the whole story, `sub_nodes[2..7]` would be about 5.1 % of the tree. They are not: removing an extension
removes a ply, which re-enters the same subtree shallower, so the share must be LARGER than the shrinkage.
**I predict `sub_nodes[2..7]` is between 8 % and 25 % of 9,500,069.** Kill: below 8 % (then the extension's
subtrees are smaller than the effect and my model is wrong) or above 25 %.

**(c) The beat-alpha rate of extended checks at depth 2..7 against depth 8 and deeper.**
A check extension is worth its ply when the child score beats alpha. Deeper checks are more selective and more
often tactical, so **I predict the deeper band (depth ≥ 8) has a HIGHER beat-alpha rate than the shallow band**,
and I predict both rates are low — **shallow 5 %..35 %, deep 15 %..60 %**. Kill: shallow above deep
(that would say the extension is worth most where it is cheapest, which I doubt), or either rate outside its band.

## Why these numbers, in one sentence each

(a) there are far more nodes at depth 2–7 than at 8+, by a factor of ten or more in a 12-ply search, so the
extension count must be dominated by them; (b) a removed extension does not delete its subtree, it re-searches a
shallower one, so the measured subtree share overstates the tree saving; (c) a check at depth 8+ has survived
seven plies of pruning and is more likely to be the tactical point of the line.

## What I expect for K1–K4 (the counter's own checks), stated so a failure is unambiguous

- **K1**: `mismatch == 0` in all four runs. My replication of the gate is `depth >= CheckExtensionDepth && see_ok`
  which is exactly the code's condition, so any mismatch means my counter is wrong, not the engine.
- **K2**: in the CED 8 run, `ext[d] == 0` for every d in 1..7.
- **K3**: in the CED 30 run, `ext[d] == 0`, `sub_nodes[d] == 0`, `beat_alpha[d] == 0` at every depth — no check
  extension can fire at depth 12.
- **K4**: `ext[d] == would2[d]` in the CED 2 run and `== would8[d]` in the CED 8 run; `would8[d] == 0` for d < 8;
  `would8[d] == would2[d]` for d >= 8.

## The one thing I expect to be interesting beyond the predictions

E0's `would2[d] - would8[d]` summed over d is exactly the set of extensions CED 8 removes. If that count is small
while the tree difference is 5.1 %, then the extension's cost is not the number of extensions but where they sit —
which is what `sub_nodes` will show.
