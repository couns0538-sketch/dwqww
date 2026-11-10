# Qualification rule for the one unowned candidate

Written and committed 2026-11-09 about 20:56 PT, after the 24-position runs were read and **before** the 95-position run (`etc_probe_wide.tsv`) was read. It fixes how that run decides the verdict.

The candidate is enhanced transposition cutoffs at expected cut nodes. The measurement is the replica harness `tools/etc_probe` (not the lock search).

The candidate is **selected** only if all of the following hold on the 95-position set for rule `cut6` or rule `cut8`:

1. **Controls.** The counting run has the same node count as the plain run in every position, and the plain run repeated has the same node count in every position.
2. **Agreement.** At nodes where a child entry would cut, the plain search also fails high in at least 99 % of cases.
3. **Clear node saving.** The 95 % range of the geometric-mean node ratio (cutoff taken versus plain), over all positions, lies entirely below 1.00.
4. **Not paid for by lookups.** Either the first-order net (savable share minus lookup cost) is positive in the middlegame group, or the overall time ratio is below 1 by more than twice the A/A time deviation.
5. **Not an endgame-only artefact of two or three positions.** The middlegame group's geometric-mean node ratio is at or below 1.00.

If any item fails, the verdict is **NO QUALIFIED GAP**, with the failed item named as the blocker.

Even if all items pass, the result stays a replica measurement. The first step of any later work is the same count inside the real lock search.
