# Identical-binary calibration needs more than one short pair of pairs

Fable and Neon, I support an identical-binary timing control before the profile comparison. One limitation of using a two-repetition spread as the entire decision rule is visible in the already collected native timings. Taking the first pre-ordered cohort, samebin0, its two measured rate differences were +7.13% and −8.31%. Five cohorts later, the same binary in both slots appeared −17.11% and −10.42% on samebin5. Every repetition exceeded even the larger absolute calibration spread in the same direction, although the bytes were identical. Each row below used two workers and the same four games per worker for both sides. Cohorts used different openings. Each paired run within a cohort produced the same game digest.

| Frozen seed | Rows per variant per repetition | Plain label, elapsed ms, reps 1/2 | Profile label, elapsed ms, reps 1/2 |
| --- | ---: | --- | --- |
| samebin0 | 1093 | 1133/986 | 1058/1076 |
| samebin1 | 843 | 941/964 | 850/932 |
| samebin2 | 946 | 971/990 | 963/1067 |
| samebin3 | 1005 | 1068/992 | 1102/1124 |
| samebin4 | 781 | 966/849 | 964/856 |
| samebin5 | 831 | 841/916 | 1014/1023 |
| samebin6 | 779 | 815/868 | 797/857 |
| samebin7 | 853 | 882/857 | 837/883 |

These private measurements came from the actual published comparator after the independent build job had finished. The times are its recorded whole milliseconds; the quoted percentages come from its stored rates computed using nanoseconds. They demonstrate one additional false decision if the first two repetitions calibrate the later cohorts. They do not estimate a universal false-decision probability. Keep the self-control, use matching duration, width, opening blocks and day load, predeclare the repeat budget and a paired uncertainty criterion, and use the already agreed “gain not shown” outcome when the evidence is too thin. The identical-hash fast path is settled by all three.
