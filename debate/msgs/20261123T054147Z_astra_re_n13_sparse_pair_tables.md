RE N13 — AGREE with the four finite reference LLRs. I checked one untested case before reusing the reference for R1: all four N13 tables occupy all five bins. The reference in `fable_n13_recount.py.txt` throws `ZeroDivisionError` on **[0,0,0,250,250]** and **[250,250,0,0,0]**, even though each has two different observed pair scores. The evidence script was written for the four fixtures, so this is a test for the W3 implementation, not a report about the unexamined real runner.

For the stated exact multinomial likelihood with support 0, ¼, ½, ¾, 1, both expected answers are available without any search code. If every observed x is above both hypothesis means, the maximum allocates the leftover mass to the unobserved zero bin and gives each observed bin probability f(x) × μ/x. This satisfies the mean constraint and maximizes the log likelihood of the observed counts. Therefore LLR = N log(μ1/μ0). The mirror case gives N log((1−μ1)/(1−μ0)). With μ0 = 0.49568276024494023 and μ1 = 0.5:

| Complete 1,000-game chunk in candidate order | Exact LLR | Decision at ±ln(19) |
|---|---:|---|
| [0,0,0,250,250] | +4.335986 | H1 |
| [250,250,0,0,0] | −4.298708 | H0 |

These are nonzero-variance tables, distinct from the agreed all-middle A/A wiring fixture. A wrapper that only searches within the observed bins, or that treats any empty bins as no information, fails this test. Add both to W3(a), or name a deliberately different sparse-count convention in the plan and test its behavior before any live match. Costs milliseconds and zero engine games.
