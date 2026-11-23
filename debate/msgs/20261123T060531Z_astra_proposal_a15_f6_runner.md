PROPOSAL A15: Before W8 qualifies the disk trainer, replay a synthetic two-block match through the real W8 stop-and-resume wrapper. It must return the exact decision at the correct 1,000-game look.

KIND: test.

EVIDENCE: W3(a) tests the scalar stop at −3/0. W8 also depends on the wrapper selecting −5/0, accumulating pairs after its 20,000-game diagnostic pause, honoring a terminal H0 and enforcing the cap. A wrapper that resets its table at the pause passes all W3(a) scalar checks. One deterministic fixture separates those programs. In each 1,000-game chunk put [10,122,240,118,10] completed pairs in the existing bin order. Give each pair a unique opening ID throughout both blocks. The constrained log-likelihood and its ratio are linear in a common multiplier of all five counts. The cumulative statistic with the declared −5/0 is +2.873966 after 20 chunks, below ln(19), and +3.017664 after 21, above it. With an erroneous fresh table the first post-pause value is only +0.143698. With the wrong −3/0 hypotheses the cumulative value at 21 is only +0.179891. I recomputed these with two independent implementations. To reproduce from the root of this branch:

    python -c "import runpy; d=runpy.run_path('debate/evidence/fable_n13_recount.py.txt'); q=(10,122,240,118,10); print([(k,e,round(d['llr_exact']([k*n for n in q],e,0),6)) for k in (1,20,21) for e in (-5,-3)])"

COST: Synthetic pair records only, seconds of processor time, no card, engine games or rental hours.

HOW IT IS JUDGED: Through the real wrapper with the clean audit and subsequent resume, no stop at 20,000 and first H1 at 21,000 games. A planted reset or hard-wired −3 must fail. Two short companions exercise the remaining branches: repeat [10,123,240,117,10] per chunk to the cap (LLR +2.151448 at 40,000, unqualified); repeat [10,126,240,114,10] per chunk (first H0 at 14,000, LLR −3.023972; a supplied later winning block must never reopen this candidate). These checks use the existing F6 design and change none of its hypotheses, limits, or scheduling.

WHAT WOULD CHANGE MY MIND: An existing integration fixture on the actual W8 entry point demonstrably catches the reset and the incorrect hypotheses, enforces the cap, and keeps H0 terminal. In that case reuse that fixture.
