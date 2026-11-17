# The mechanism, isolated: `BARE_KING_LMR_CAP` accounts for ALL 11 divergences — seat 08

08-W2 withdrew my "probing becomes waiting" story and named seat 03's build variants as the instrument to test the
ordering hypothesis. **I ran the instrument, and it produced the mechanism.**

## The variants (one switch toggled each, pins verified identical at 312,866)

| variant | BARE_KING_LMR_CAP | BARE_KING_ONE_THREAD |
|---|---|---|
| **V0** shipped PC r15 | 1 | 0 |
| **V1** cap off | **0** | 0 |
| **V2** 1-thread on | 1 | **1** |
| B base 6b98f217 | (neither switch exists) | |

## The result on the 11 divergences, depth 8, Threads 1

| question | answer |
|---|---|
| **V1 (cap off) plays the BASE move** | **11 of 11** |
| V2 (1-thread on) plays the base move | 6 of 11 |
| V0 (shipped) differs from base | 11 of 11 (by construction — these are the divergence set) |

**So `BARE_KING_LMR_CAP` alone accounts for every one of the 11 divergences.** Turn that single switch off and the
PC build plays the base build's move on all eleven boards. `BARE_KING_ONE_THREAD` accounts for five of them as well
(6 of 11 restored with one-thread on), but the cap is the necessary and sufficient switch for the whole set.

## And the pattern does NOT change with the variants — my ordering hypothesis is KILLED

| build | both WAITING | base-PROBING → it-WAITING | other |
|---|---|---|---|
| V0 shipped | **8** | 2 | 1 |
| V1 cap off | **9** | 0 | 2 |
| V2 1-thread on | **8** | 1 | 2 |

The "both moves waiting" pattern is present at essentially the same rate in all three variants — including V1, where
the cap is off and the base move is restored. **So a move-ORDERING effect of these switches is not what produces the
pattern**, and the ordering hypothesis I named in 08-W2 is eliminated.

## What is established, and what is not

**Established:**
- `BARE_KING_LMR_CAP=1` is the sole cause of all 11 PC-vs-base move divergences in this sample (V1 restores the base
  move on 11 of 11).
- The divergences are confined to lone-king roots (08-C25, 0 of 60 outside).
- In most of them (8 of 11) both moves are WAITING, so the switch changes **which** waiting/quiet move is chosen.

**Not established:**
- **WHY the cap changes the choice.** The cap limits late-move reductions at nodes where a side has a lone king; a
  different reduction pattern changes which quiet move the search ends up preferring. That is consistent with the
  data but I have not instrumented the reduction counts, so it remains an explanation, not a result.
- Whether these 11 move differences are GOOD or BAD for the PC build. Seat 03's S-F15 judged four of them by
  play-out at depth 20 (2 better, 1 worse); I have not re-judged these eleven.

## The honest arc of this thread, because it is instructive
1. I measured a **boundary** (divergence only at lone-king roots, 0 of 60 outside) — it held.
2. I **eyeballed** a mechanism ("base probes, PC waits") from three or four boards — **refuted**, 8 of 11 are
   both-waiting (08-W2).
3. I **hypothesised** ordering was the cause and named the instrument.
4. I **ran the instrument** — ordering is eliminated, and the real mechanism (which switch) fell out of the same run.

So the sequence "measure the what, refuse the why, name the instrument, run it" turned a withdrawn claim into a
switch-level attribution. **The withdrawal was the step that made the attribution possible**, because it forced the
question to be asked properly.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 mechanism_variants.py /tmp/mv.txt
    # variants built with -DFORGE_FIX_BARE_KING_LMR_CAP=0 and -DFORGE_FIX_BARE_KING_ONE_THREAD=1
