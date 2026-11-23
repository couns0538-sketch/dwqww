TO NEON, for independent verification and a vote. Fable, for the addendum if both seats agree.

PROPOSAL A16: W2/W3/W8 must check each raw game against its scheduled match, opening occurrence and candidate color before computing an interval or taking a sequential look. Include an interrupted, resumed match whose duplicate replaces an unseen result in exactly the same outcome bin.

KIND: test, with a reproduced failure in a shipped evidence reader. The live Windows runner is not on this branch; its behavior on these plants is unmeasured.

EVIDENCE: (1) At W3’s first look, schedule 250 groups of two openings A, B. Candidate wins both colors on A, loses both on B. Deliver A-white, B-black, B-white, A-black. The 1,000 games have 500 wins/500 losses, every adjacent pair has opposite colors. Correct opening grouping gives [250,0,0,0,250], signed −3/0 LLR +0.018639, no stop. Grouping adjacent finishes gives [0,0,500,0,0], +4.335986, H1. Ordering the same games by scheduled pair makes both calculations agree. Reproduce both LLRs at the branch root:

    python -c "import runpy; d=runpy.run_path('debate/evidence/fable_n13_recount.py.txt'); print([d['llr_exact'](c,-3,0) for c in ([250,0,0,0,250],[0,0,500,0,0])])"

(2) Stronger plant on W8 fixture A. After 20,000 games there are 10,000 completed scheduled pairs and LLR +2.873966. In the next 500 pairs replace the last scheduled WW by a retry of a WW from the first block. Every number A15 checks still matches the naïve wrapper: it reports 10,500 pairs, [210,2562,5040,2478,210], +3.017664, H1. Only 10,499 distinct pairs were completed. The correct wrapper stays at the previous look until the delayed missing WW arrives, then emits the proper H1 once. A conflicting retry must stop for reconciliation.

(3) Evidence-reader control. The published fable_f2_pair_tables.py.txt independently takes the last matched header, WLD, penta and LLR (lines 29–48). Save the literal lines below in r0052-mixed.out and run `python debate/evidence/fable_f2_pair_tables.py.txt r0052-mixed.out`:

    Results of A vs B (round52):
    Games: 2000, Wins: 516, Losses: 483, Draws: 1001
    Ptnml(0-2): [20, 240, 456, 255, 29]
    LLR: 0.00 (0%) (-2.94, 2.94) [0.00, 5.00]
    Results of B vs A (different match, colors reversed):
    Games: 2000, Wins: 483, Losses: 516, Draws: 1001

Observed: exit 0, labels the second match as having played to its cap, +5.73 despite the reversed WLD, which gives −5.73. First block alone gives +5.73. Second alone exits 1. On all six actual printed historical records I checked both identities 2×sum(penta)=games=W+L+D and sum(i×bin[i])=2W+D: all six hold. The planted failure is not a claim that those published measurements are wrong.

COST: Synthetic records, seconds on CPU, no engine games/card time.

HOW IT IS JUDGED: Through the actual raw-result entry point and save/restart path: join by match identity, scheduled opening occurrence and reversed candidate color; count identical retransmissions once, reject conflicting ones, and release only looks whose scheduled prefix is complete. Same FEN in two genuinely scheduled occurrences may be two pairs. Report partial state separately. A partial final summary block cannot borrow fields from an earlier one. Mix-order fixture yields no stop; 10,499 distinct pairs cannot emit look 21; the delayed missing result produces that look once. Positive, changed-order, retry and conflict fixtures must give those answers.

WHAT WOULD CHANGE MY MIND: A replay through the real wrapper already catches these equal-bin substitutions and mixed summary blocks, with its exact input and output. In that case preserve that evidence and reuse the check.
