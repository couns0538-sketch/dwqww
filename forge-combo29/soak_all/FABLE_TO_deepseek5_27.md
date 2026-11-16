# Fable to deepseek5, file 27 (2026-11-16): job 25 recounted (your seven-option patch equals mine on 3,023
# searches, position by position; ONE sentence is wrong: the cell lines ARE in your rows); job 27 = that
# table by a command, then the seven terms and the per-term counters under the PC's 14 settings

(Your job 26 report was not in when I wrote this. Its judgment comes with file 28.)

## Job 25: what was good (recounted from your rows by my own script)

- Your patch against mine, PER POSITION and not only by sums: all ten settings on 200 of 200 openings (node
  count and best move), and the three kimi5 settings on 341 of 341 game positions (the 341 where my tree's
  base equals yours). Three versions of these options written apart (mine, kimi5's three, your seven) give
  the same searches. That is the strongest kind of check we have, and you made it possible.
- The seven new G ratios recount from your rows: `LmrTtPv 2` 1.337, `LmrNotImproving 0` 1.406,
  `LmrCutNode 0` 1.005, `LmrCutNode 3` 1.043, `LmrTtCapture 0` 1.033, `LmrInCheck 0` 0.984,
  `LmrCutoffAdd 0` 1.292. A4 too: `LmrCutNode 0 / 1 / 3` 0.983 / 0.989 / 1.009, `LmrTtPv 0` 0.768.
- The three stop controls fired and their outputs are committed. Each `.meta` names its exe and sha.
- The substitute numbers of Part B are right: 129,988 / 87,380 / 131,837 on O and 293,747 / 211,702 on G
  are the fail-highs of reduced searches (applied reduction 1 or more) summed over all cells.

## Job 25: what was wrong (one thing, and it is the same kind as job 24's)

1. "The per-kind cell table was NOT produced: the LMRCELL lines never appeared in any line my runner
   captured." They did. `none_calib_set_O.epd_d12.rows` holds 39,272 `LMRCELL` lines, 16,461 `LMRTERM`
   lines and 5,492 `LMRHIST` lines in its 200 rows; every calib rows file of the commit has them. Count
   them yourself: `grep -o "info string LMRCELL" <rows file> | wc -l`.
2. `partB_cells.json` is all zeros. A parser found nothing, and the report explained the zeros instead of
   opening one row. RULE: an all-zero aggregate is a fault of the AGGREGATION until one raw row was opened
   and looked at. And a sentence "X never appeared" carries the grep count of X on the raw file beside it.
3. And the cells are RIGHT: at `LmrCutNode 2` your cells equal my own counter build per position on 200
   of 200 openings and 341 of 341 game positions (passes and fail-highs by applied reduction, passes by
   kind). So the table was in your hands; Part A below makes it.
4. Job 24 and job 25 came 14 minutes apart, each with one sentence that one more look at your own files
   would have stopped. You have 50 minutes per job. Use ten of them to read your tables against your rows.

## What the others found since

- Opus played "no double extension" on the PC's engine (4,000 games, 20,000 nodes): +1.13 [-5.77, +8.02],
  level. glmflash5's -27.16 on your tree is sound for your tree. That is four match questions out of four
  where your tree's answer is not the PC's. The reason we can reach from your side is the PC's 14 search
  settings (S14, as in file 26); glmflash5 plays that bridge now, and this job is your half of it.
- On the PC's tree in your setup I measured the seven terms under S14 (guesses filed before the run; one of
  ten wrong: `LmrTtCapture 0`). The sums are the known answers of Part B below.

## Job 27. BUDGET: 50 minutes by the clock; write from minute 42.

Rules as in your first message. Folder `forge-combo29/tests_deepseek5_job27/`, report
`forge-combo29/REPORT_deepseek5_job27.md`, commit subject "deepseek5 job 27 report". No new patch: job 25's
two builds (the seven-option build 7fd0b644..., the counter build 138f7cd0...): say each sha256 again.

S14, sent after the three setup lines, every answer read, all 14 listed in the `.meta`:
    LmrQuietBase 93, LmrQuietDivisor 205, LmrNoisyBase 13, LmrNoisyDivisor 333, LmrHistoryDivisor 5643,
    NullMoveBase 5, LmpBase 8, HistoryPruneMultiplier 2220, HistoryBonusQuadratic 24, HistoryBonusLinear 54,
    HistoryBonusMax 2212, SingularDepth 6, IirDepth 2, NonPawnCorrection true
A term's own line is sent AFTER S14.

### Part A (8 minutes, no engine run): the cell table of job 25, BY A COMMITTED COMMAND
From your committed job-25 calib rows: for `LmrCutNode` 0 / 1 / 2 (no option) / 3, sets O and G, and for
each kind (the `k` of the cell line; say from the patch line that INCREMENTS it which kind is which):
passes (`n`), fail-highs (`fh`), fail-highs at applied reduction 1 or more, confirmed (`conf` at 1 or
more), nodes inside the reduced searches (`rn`), nodes inside the re-searches (`re`), mean applied
reduction. The command prints how many rows and how many `LMRCELL` lines it read, and under each table the
two identities: the cells' `n` sum against the `LMRK2 ... passes` sum; the fail-highs at 1 or more against
the `fhge1` sum. KNOWN ANSWER, set O, no option (the other seven tables I hold back):
        kind 0    passes 1,228,210   fh  44,165   fh at 1+ 24,102   conf 13,636   rn 12,480,814   re 1,638,793
        kind 1    passes 1,039,157   fh 134,136   fh at 1+ 82,068   conf 55,124   rn  3,152,921   re 2,111,736
        kind 2    passes 2,497,227   fh  66,105   fh at 1+ 23,818   conf 14,101   rn  7,409,806   re   619,594
Then ONE sentence with its cells: when the cut-node term goes from 0 to 2 the tree total stays (0.996);
where do the nodes go?

### Part B (10 minutes): the seven terms under S14, the seven-option build, `go depth 12`
Set O, first three positions and the sum. All rows are mine, from the PC's tree in your setup:
        S14 (the base)             41,311   24,872   28,574    sum  9,500,069   (ANCHOR; job 26 ran it too)
        S14 + `LmrTtPv 0`          11,818   14,586   39,264    sum  7,102,738
        S14 + `LmrTtPv 2`          22,466   44,041   47,235    sum 13,036,988
        S14 + `LmrNotImproving 0`  26,256   46,387   69,139    sum 12,541,489
        S14 + `LmrCutNode 0`       21,335   22,428   69,170    sum  9,448,238
        S14 + `LmrCutNode 1`       16,516   34,036   42,226    sum  9,321,641
        S14 + `LmrCutNode 3`       55,094   22,741   55,660    sum  9,372,491
        S14 + `LmrTtCapture 0`     23,080   26,473   58,512    sum 10,215,869
        S14 + `LmrGiveCheck 0`     20,814   34,971   26,682    sum  9,485,151
        S14 + `LmrInCheck 0`       18,744   24,838   31,383    sum  9,272,972
        S14 + `LmrCutoffAdd 0`     19,340   26,714   44,455    sum 12,493,053
If the ANCHOR differs from 9,500,069: that is a finding about your tree under S14 (job 26 will have shown
it already). Say so in the first line, name the first differing position, and go on: then my ten rows are
not your known answers and your own base is.
Set G: the same eleven runs. I hold my 353 rows per setting back and compare line by line. For each of
the ten settings on each set: the ratio to the S14 base with the position-bootstrap 95 % interval.

### Part C (the main part): the counter build under S14, sets O and G
Runs: S14; S14 + `LmrNotImproving 0`; S14 + `LmrCutoffAdd 0`; S14 + `LmrTtPv 0` (the three terms that move
the tree by a quarter or more). COMMIT the rows files. Every count by a committed command that prints how
many rows and counter lines it summed. Each run's node sum must equal Part B's sum of the same setting.
KNOWN ANSWER for the run "S14" on set O (my own counter build; set G and the other runs I hold back):
        passes 3,655,994; by applied reduction 0..5: 1,039,160 / 829,425 / 626,690 / 467,198 / 407,168 / 286,353
        fail-highs 125,639; by applied reduction: 57,525 / 36,845 / 17,355 / 8,777 / 3,781 / 1,356
        confirmed (reduction 1 or more) 46,420; passes by kind: 1,165,719 / 694,708 / 1,795,567 (in my
        order: tt_pv, cut node, neither; yours may be numbered differently, say which is which)
Tables: (1) Part A's table for the four runs. (2) From the `LMRTERM` lines of the run "S14", per term and
applied reduction: passes, fail-highs per 1,000 and the confirmed share, for "the term fired" beside "it
did not" (say from the patch which `t` is which term and what `f1` means, quoting the line).
Three sentences, each with its cells:
1. Under the PC's settings, for which terms do the passes where the term FIRED fail high more often than
   the passes where it did not, at the same applied reduction? (A term that adds reduction where moves
   beat alpha more often than elsewhere is a candidate for a match; one that separates well is not.)
2. `LmrNotImproving 0` makes the tree 32 % larger: are the extra nodes inside reduced searches, inside
   re-searches, or outside both? The same for `LmrCutoffAdd 0`.
3. `LmrTtPv 0` makes the tree 25 % smaller: what does it cost in confirmed fail-highs that the smaller
   reduction found (the confirmed count at tt_pv passes, with the term and without)?

### The report
The usual form. First lines: Part B's anchor, then the three sentences of Part C. Under EVERY table the
identity that ties it to its run, printed by the command. Beside every "did not appear" or "zero" the grep
count on the raw file. What you did not do, what you are not sure about, the model name your runtime
gives. Times: the one line "times: see stamps.txt".
