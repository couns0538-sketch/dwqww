# HANDOFF — the second mechanism behind the cap's two counter-cases (unrun, complete lead)

A lead for whoever picks this up next. **Nothing here is a result.** It is a stated open question with the instrument
that would settle it, written so the next reader does not have to re-derive the setup.

## What is established (mine, with the evidence)

| fact | evidence |
|---|---|
| The cap is the sole cause of the move divergences (11 of 11 restored with it off) | 08-F37, `mechanism_variants.txt` |
| Turning it off reduces node count on **9 of 11** boards (3,356–14,040 nodes) | 08-F38, `instrument_cap.txt` |
| On **2 of 11** boards it goes the other way (+621, +10,981) | same table |
| The two counter-cases are **not** explained by the gate firing less often | 08-F39, `countercase_probe.txt` |

## The precise shape of the open question

The cap fires at a node when **the root has a lone king AND that node has a side with only its king** (patch lines
~1563–1574). Measured over the exact legal tree to depth 4, that condition holds at **100 % of nodes on all 11
boards** — counter-cases included. So the cap is doing work everywhere, and the two counter-cases cannot be explained
by it doing *less* work there.

**Therefore the cause is not in WHETHER the cap fires but in HOW its changed reductions propagate.** A reduction the
cap clamps changes which nodes get visited at that depth; a different visited set changes what the transposition
table, killers, histories and the aspiration window see; and any of those can raise the total node count even though
the clamp itself only ever *reduces* effort locally. The direction of the net effect is then board-specific — which is
exactly what 2-of-11 in the other direction looks like.

**This is a hypothesis shaped by the data, not a finding.** It is stated here so it can be killed rather than
inherited.

## The instrument that would settle it — and why it is not mine

**A build that prints per-depth reduction counts**, and the clamped-reduction count specifically: for each
`info depth` line, how many reductions were applied and how many were clamped by `bare_king_lmr_cap`. Two variants
(cap on / cap off) on the 11 boards would then show directly whether the counter-case boards have a different
clamped-reduction profile.

Why I did not run it:
- it needs a **source patch** to `src/search.cpp` (a counter and one extra `info string` line), i.e. a text patch in
  my own folder plus a scratch build — feasible, but it is engine-internals work, and
- my area is the clock. Area 7 (reading the search code) and area 3 (move generation, which built build variants for
  exactly this kind of question) both own this instrument natively.

**The instrument does not exist in my tool set**: every tool I have measures the engine from *outside* (UCI
messages, wall time, node counts, python-chess). Reduction counts are internal state and require the patch.

## What the next reader needs, concretely
1. The 11 boards are in `check_s03f13.txt` (the divergence table), and the two counter-cases are marked in
   `instrument_cap.txt` by a positive Δ.
2. Variant builds: `-DFORGE_FIX_BARE_KING_LMR_CAP=0` (cap off) and `=1` (shipped), everything else default, pins
   verified identical at 312,866 — so any node-count difference is attributable to the switch.
3. The measurement to make: per depth, `clamped_reductions / total_reductions`, on the 9 predicted boards versus the
   2 counter-cases. If the counter-cases show a much lower clamped-reduction share, the "propagation" account is
   supported; if they show the same share, the cause is elsewhere again and the lead needs re-aiming.
4. **Do not treat the hypothesis above as confirmed.** Two counter-cases out of eleven is a small sample, and I have
   already written one mechanism story tonight (08-W2) that a test destroyed.

## Why this handoff exists at all
Because the honest end state of my mechanism work is: **the cause of the move changes is identified (the cap), the
direction of its effect on search size is a strong tendency with two named exceptions, and the cause of those
exceptions is not known.** Writing that as a lead with an instrument is more useful than a half-run experiment, and
it is the difference between "we stopped" and "here is where to start".

## Show the current state again

    cd forge-combo29/swarm/08/pc20
    python3 mechanism_variants.py /tmp/mv.txt    # which switch causes the divergences
    python3 instrument_cap.py /tmp/ic.txt        # node-count direction, 9 vs 2
    python3 countercase_probe.py /tmp/cc.txt     # the gate fires 100% everywhere
