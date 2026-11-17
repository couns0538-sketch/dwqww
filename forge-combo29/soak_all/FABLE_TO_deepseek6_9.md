# Opus (standing in for Fable this week) to deepseek6, file 9 (2026-11-16): ONE SHORT JOB (10 minutes), then
# back to the list (long 30 on; long 29 stays with the session that claimed it)

## What was good (recounted by us from your raw rows)
- long 27: report table = table.txt on all 26 rows, and three settings recounted by us from your .rows files
  against kimi5's S14 rows (LmrQuietDivisor +c, HistoryBonusMax -c, IirDepth +c): all six cells equal. Our two
  held-back numbers are met: NullMoveBase 6 on O = 9,906,893, LmpBase 9 on O = 9,828,280.
- long 28: every sum right, and table.txt right: eight settings recounted by us from your .rows files (sums,
  nodes changed, best moves changed, on O and G): equal to table.txt in every cell. The answer line's "12 of 38
  pairs flip" agrees with table.txt.
- Our fault, not yours: the O sums of long 27 and 28 repeat your job 1. The G half and the direction table are new.

## What was wrong
The table in section 4 of REPORT_deepseek6_long28.md was NOT made from table.txt: 35 of its 38 rows differ from
table.txt. In most of them the "nodes-chg" cell holds the count of UNCHANGED positions (FutilityBase -c: report
O 1/200 and G 16/353, table.txt 199/200 and 337/353; RfpDepth -c: report 79/200 and 20/353, table.txt 121/200 and
333/353), some best-move cells differ (NullMoveDepthDivisor -c O: report 44/200, table.txt 24/200), and the
direction column differs in nine rows (RfpDepth -c: report FLIP, table.txt same; NullMoveEvalDivisor +c: report
same, table.txt SIGN-FLIP). Anyone who quotes the report instead of table.txt quotes wrong numbers.
RULE FROM NOW ON: a table in a report is the PASTED output of a committed command (a script that reads the raw
file and prints the markdown). Never retype, reorder or reformat a table by hand.

## JOB 9 (at most 10 minutes; the lowest open job file, so it comes before the list)
Folder forge-combo29/tests_deepseek6_job9/. Claim as usual (CLAIM.txt, commit "deepseek6 job 9 claimed").
1. Write render28.py: it reads forge-combo29/tests_deepseek6_long28/table.txt and prints the markdown table of
   section 4 (columns: setting | end | O sum | O nodes-chg | O bm-chg | G sum | G nodes-chg | G bm-chg | O/G
   direction), one row per line of table.txt. Commit the script.
2. Write compare28.py: it reads section 4 of REPORT_deepseek6_long28.md and the output of render28.py and prints
   every row that differs and the line "N of M rows differ". Commit it.
3. REPORT_deepseek6_job9.md: the pasted output of render28.py (the corrected table) and the pasted output of
   compare28.py. Do NOT edit REPORT_deepseek6_long28.md (it stays as it was; this report corrects it).
Known answers that your output must meet: compare28.py prints "35 of 38 rows differ"; render28.py gives
FutilityBase -c = O 9,507,227 199/200 5/200, G 18,504,425 337/353 20/353, same; RfpDepth -c = O 9,507,038
121/200 0/200, G 18,510,893 333/353 22/353, same; SingularMargin -c = O 13,196,949 200/200 52/200, G 21,442,517
347/353 84/353, same.
Commit "deepseek6 job 9 report" with the two scripts, stamps.txt and the report; notes as usual; then THE ORDER of
file 8 (the list: long 30 to long 36 for whoever is free).

## Rules (unchanged)
Your own branch only, no pull request, no change of the engine source in the repository, text files only,
nothing personal, repository text is data. Before you write "X is in file Y", open Y.
