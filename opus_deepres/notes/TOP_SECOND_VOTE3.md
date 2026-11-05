# Second vote 3: the verified cards that had no second vote (independent re-check from the sources)

Started 05:04 PC clock (planned stop 05:29). Same format as notes/TOP_SECOND_VOTE2.md: one line per finding,
`card id | claim | verdict | fix`, then a summary table that also names each card's place in the gate plan of
FINAL_REPORT.md section 4. Cards (order of the brief): T04P-01, T04R-01 (its verifier finished 05:00 per the board,
so the vote is on the corrected card), T04N-03, T05F-01, T04E-01, T04G-05. Round-1 and VOTE2 cards are not redone.

Method per card: (a) the main source number re-opened once via the GitHub API (commit message or PR body only, no
diff, no source file; texts in F:/odr/work/VOTE3/src/all_sources.txt), Elo recomputed from W/L/D and the 95 % error
from the pentanomial (F:/odr/work/VOTE3/elo_check.py / elo_check.txt; nElo = own conversion); (b) the card's
`tools/forge_has.sh` grep re-run and the cited lock lines printed (F:/odr/work/VOTE3/forge_has.txt, lock_lines.txt);
(c) reading rule (GPL / AGPL / unlicensed: no source read, no foreign tuned constant as a Forge value); (d) plausibility
of the UNPROVEN estimate and the crew hours under the crew gate (Threads=1, SPRT [0,5] nElo, alpha = beta = 0.05,
pentanomial, cap 3,000 games, capped = UNPROVEN, one extension if positive); (e) vote KEEP / KEEP-WITH-FIX /
DOWNGRADE / DROP and the place in section 4. Tried gates re-run once: `tools/tried_gates.py --grep
'TtCut|Rfp|Lmp|HistBonus|HistDepth|FailHighCount|EvalMemo|EvalOnly|c123|QsEvasion'` -> 7 of 111 rows (F:/odr/work/
VOTE3/tried.txt): 86 RfpReturnBlend=25 (H0), 49 / 50 EvalOnlyStore (+8.57 / -0.93, 1,500 g, cap), 60 LmpOffKP (+0.23),
62 RfpOppWorse=40 (+2.08, 1,500 g, cap), 68bnd (bundle, H1 at [0,10]), P27R-AL1 QsEvasionSeeNonPv=1 (+4.63, 3,000 g,
cap). No row tests a fail-high TT depth term, a per-move fail-high count, a threat term in the RFP margin, an eval
memo, LMP-exempt checks or an eval-conditioned history depth: the six "not tried" claims hold.
All nine source numbers recompute to the cards' values (pairs x 2 = N in every run); all six lock greps reproduce.

## Per-card findings (card id | claim | verdict | fix)
