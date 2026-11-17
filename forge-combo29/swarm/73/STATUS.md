# swarm-73 — STATUS

**Seat:** report assembly for the owner. Synthesising; not measuring.
**Branch:** `for-fable-and-opus/swarm-73` — `forge-combo29/swarm/73/`
**Window:** opened 03:48Z, audit closes 2026-11-17T10:20Z.
**Provenance audited against the 31 branch tips listed in `OWNER_SUMMARY.md`'s header** (fetch 04:36Z).

## State: DONE — summary current as of the 04:36Z fetch

`OWNER_SUMMARY.md` — **2,549 lines, 64 rules, 22 recommendations** (14 ship / 5 do-not-ship / 4 needs-more-evidence — 23 markers over 22 items; §1.7 carries two). Sixteen rounds.

## Numbers the coordinator asked for

> **Unsourced figures: 9** (of 284 tokens).
> **Findings synthesised: 2,380** = 2,371 distinct table-row ids + 9 prose findings in `swarm-75`; 2,392 raw rows, 21 re-runs under an existing id.
> **Branches read: 31** carrying a `FINDINGS.md`, of 63 `swarm-NN` branches on the remote.

| cause | figures |
|---|---|
| no committed output (script ships, evidence does not) | `0.024`, `0.44`, `442` |
| no committed occurrence | `929` |
| **contradicted by evidence** | `42` (noise floor; evidence gives **66 cp**) |
| budget absent from the sweep | `40 of 40` at 2M |
| **THE SHIPPABILITY COUNT** | **`0 of 125`, `13 of 13`, `220-280 ns`, `13,707`** — the numbers licensing the headline SHIP |
| *(verified by arithmetic, excluded)* | `0.0712` |

**Two figures came OFF the list in later rounds:** `13.2 %` (now in `swarm-27` `S-C108`) and `54,379` (now in
`swarm-71`). **That is three timing artefacts in total**, which is why the header names commits.

**The shippability count is the serious one** and I have flagged it in §1.2's own text, not only in §5: the
adversarial-family and depth-contract results are sourced, but the claim "the scan fires on drawn roots only" is
report-only. Re-measuring it on the owner's build is the conversion check.

## Twenty-third round — both rules stated, not just applied

**The gap was that I had applied both behaviours and written neither as a rule.** Stating them found three more
unlabelled sites, which is the usual result.

**Rule 55a — two counts side by side with no label read as a stale number.** The measured case is my own: **"four
honesty pins" in §1.1 and "11 documented pins" in §1.22** with nothing saying they differ — genuinely different sets
(**bench 11/13/16 + perft 5** versus **five depths × two net settings + perft 5**), both pinned, and the book patch
moves neither. **A reader had two numbers, no explanation, and a document full of rules about stale totals — the
reasonable inference was that one was out of date.** The fix is six words per count: say what the set contains.
- **Applied at all four citation sites**, and a script now flags any pin-count mention without a set-definition nearby.
  It found the two sites I had missed and **false-positived on the rule text that quotes the example**, which is the
  checker-judges-text-not-the-thing failure again — recorded, not suppressed.

**Rule 55b — a repair that may land after the document closes is PENDING, not fixed, and the HEADING must say so.**
Writing it as fixed is the same error as a figure with no committed source. §2.7's heading now reads
**"broken (silent); a fix is PENDING, not landed"** and carries the check that will settle it.
- **The distinction that makes it worth a rule: a pending repair is a different category from an unstarted one**, and
  collapsing both into "broken" loses the most useful thing a reader can know — **that someone is already on it, and
  what to test when it arrives.**
- **It generalises past patches:** anything described in the future tense anywhere needs its status **where a reader
  looks first, which is the heading, not the fourth paragraph of the body.**

**On rewriting versus annotating:** you named the mechanism — a footnote leaves the old framing as the primary claim,
which is the failure mode behind most of tonight's corrections. **That is now the reason the book sections were
rewritten, stated rather than left as a preference.**

## Twenty-second round — a diagnosis becomes a measured fix

**The book pre-emption moves from "broken" to "broken, and the FIX IS MEASURED"**, which is a change of status rather
than of wording, so §1.22 and §2.8 were both rewritten rather than annotated.

- **The patch is one hunk and a PREDICATE, not a reordering:** `!root_drawn` added to the book condition, using the
  same three tests as the bail. **`search.cpp` untouched, so node counts cannot move** — which is what makes the pin
  check a real test: **all 11 documented pins reproduce on both builds** (five depths × two net settings, plus perft 5).
- **Effect on six roots:** fifty-move-with-entry and repetition-with-entry both go **book move → bail cp 0, empty pv
  (FIXED)**; insufficient material and fifty-move-with-no-entry **unchanged**; an ordinary book position **still books**;
  an opening with no entry **still searches, cp 91**. **Pre-emption 2 → 0.**
- **The two controls are what make it a fix rather than a removal:** a patch that simply disabled the book **would pass
  the first four rows and fail the fifth.** Recorded because that is the difference between a patch and a lobotomy.
- **Two owner decisions stated AS decisions, not folded into the recommendation:** whether a drawn root should *ever*
  book (a repetition at move 8 in a forced-draw line is arguably a book situation — so "always report drawn" is
  policy); and whether to **share the predicate** with `search.cpp`, where the same three conditions now exist in two
  copies **that agree today with nothing enforcing it.**

**Also noted: a pin-set distinction that would otherwise read as a contradiction.** This document cites **four honesty
pins** (§1.1) and **11 documented pins** (§1.22) — different sets, 5×2+1 versus 4, both pinned, and the patch moves
neither. Now stated explicitly so a reader does not see two pin counts and assume one is stale.

**Trap 1 (one-sided clock) is flagged as PENDING rather than fixed** — a patch is being prepared with the same gate,
so it may move after this document closes. Marked as pending with the check that will settle it.

## Final state

**Cross-checked against the coordinator's own verification: both tables are now 4-branch-complete on the two
self-disagreeing surfaces and their prose totals are computed from the rows.** Their eight-row version and my nine-row
version differ only in whether `position fen`'s short and illegal cases share a row — **both are internally consistent,
which is the property that matters.**

**One thing I recorded as plausible-but-unverified rather than asserting:** the coordinator's mechanism for the
exchange — **that the prose total selected the row rather than the rows producing the total.** It is consistent with
both tables, and **I could not confirm it on mine: the `searchmoves` row and the "8 rows, 4 report, 4 do not" total
landed in the same commit**, so the ordering is not recoverable from the history. **A mechanism claim I cannot check is
recorded as such**, which is the same standard I applied to the report's `929` and to the latency percentiles.

**The remedy holds either way and is the actionable half: write the prose total FROM the table, never beside it.** A
total stated first is a hypothesis about the table, not a report of it — and a hypothesis is precisely what will quietly
select the rows that confirm it.

## Final counts, all computed

| quantity | value | how |
|---|---|---|
| lines | **2,460** | `wc -l` |
| rules | **64** | grep of numbered bold items in §4 |
| recommendations | **22** | grep of `### 1.N`, verdicts 14 ship / 5 do-not-ship / 4 needs-more-evidence (23 markers, §1.7 split) |
| findings synthesised | **2,380** | 2,371 distinct table-row ids + 9 prose ids, re-derived at the named tips |
| branches with a `FINDINGS.md` | **31** of 63 `swarm-NN` | per-branch file check |
| unsourced figures | **9** of 284 tokens | token audit + context reads, at the named tips |
| parser-surface table | **9 rows, 5 report, 4 silent** | grouped by surface, both self-disagreeing surfaces split |
| section refs / rule refs unresolved | **0 / 0** | printed with targets, not resolution-only |

**All eight re-derived from artefacts at the tips named in the summary's header, not carried forward.**

## Twenty-first round — the collapsed row, found in my own table

**You asked me to flag a contradiction, and there was one — the same failure you had just fixed in yours.** Your
"one row per branch" principle applied to my table found `searchmoves` carried as a **single row covering only the
mixed list**, hiding that **the all-illegal branch does report** (`0000` + `info string` + 0 nodes).

| | before | after |
|---|---|---|
| rows | 8 | **9** |
| report the fault | 4 | **5** |
| do not | 4 | **4** |

**So my table under-counted the TRUTHFUL side by one** — the mirror of your error, which under-counted the silent side
by collapsing a different branch of the same surface. **Both of us collapsed `searchmoves`, in opposite directions.**

**The generalised rule, which is yours and is sharper than the arithmetic argument:** **a surface whose branches
disagree with itself needs one row per branch**, and collapsing them under-counts. **Two surfaces qualify** —
`position fen` (short/illegal report, surplus silent) and `searchmoves` (all-illegal reports, mixed silent) — and
**both are now split in my table and verified split by script.**

**And the count is now computed by a check that knows what to look for:** group rows by surface, and flag any surface
appearing once that is known to have disagreeing branches. It reports **0 flagged**, both surfaces split, 9 rows
matching the prose.

**Worth recording about the sequence:** we spent three exchanges arguing arithmetic, and the resolution was that
**neither table was complete** — not that one was wrong. **A counting dispute can be a symptom of a missing row rather
than a mistyped total**, which is a different failure from the double-count, and the script found it only because I
grouped the rows by surface instead of totalling them.

## Twentieth round — I was wrong in a counting dispute, and the fix is to compute it

**The coordinator's sentence was correct and mine was wrong.** They ran the count; I compared their sentence against
**my** table's row count and called it inverted. Their table: **7 rows, 3 YES, 4 no** — matching "three report the fault
and four do not". Verified by script in a second, which is the point.

**My own table was also wrong, differently, and the script found that too:**

| | before | after |
|---|---|---|
| rows | 7 | **8** |
| truthful | 4 | **4** |
| silent | 3 | **4** |
| prose said | "7 rows, 4 report, 3 do not" | "8 rows, 4 report, 4 do not" |

**The missing row was the `searchmoves` mixed list** — one legal plus one illegal move, **byte-identical to pinning the
legal move alone, no diagnostic on either stream.** That is the worst of the silent surfaces because there is **nothing
to filter on after the fact**: the check has to live in the client. It was in the report's table and absent from mine,
so my table under-counted the silent side by one.

**Added rule 56, which is the coordinator's and is narrower than anything I had:** a counting claim about a table must
be **computed**, and **a counting dispute is decidable by script in one command — so neither party should settle one by
reading.** The dispute is itself the defect signal: **if either of us had run the count there would have been nothing to
dispute**, and confidence on both sides of an arithmetic question is a reason to compute, not to argue politely.

**And the checker I wrote to enforce this immediately false-positived** on §7b, because that passage *cites* a count
from rule 12's table rather than carrying its own. **A check that cannot tell a local claim from a citation of one is
the same class as a checker that judges text instead of the thing** — recorded rather than papered over, and the
passage now says explicitly that it is counting another section's rows.

## Nineteenth round — the correction propagated, and the parser table now adds up

**Applying rule 12's own consequence to the rest of the document found two more instances of the same class**, both
created by my own earlier partial edits:

1. **The parser-surface table's heading claimed "two of five refuse safely, three improvise silently, and one surface
   does both"** — which does not add up, because the third clause makes six of five. The move list was also **missing
   from the table entirely**, because I had classified it as a hazard when it is now a **truthful** surface. The table
   now has seven rows over five surfaces with an explicit **verdict column**, and the arithmetic is stated so it can be
   checked: **three surfaces report the fault, two improvise, and `position fen` counts in both** because its
   surplus-fields branch is silent.
2. **§7b repeated the same stale "two of five / three improvise" sentence and pointed at rule 11 instead of 12.** Both
   fixed by the same rewrite.

**A judgement I had over-asserted, and have retreated from:** my text called the junk-before-`moves` behaviour a defect
("a malformed position silently becomes a real one"). **Discarding an unrecognised token before a keyword is ordinary
leniency**, and the measurement supports "the command is honoured with the junk dropped" — not a verdict on whether that
is wrong. **The section now records the behaviour and says explicitly that the report's "defect" framing is a judgement
the measurement does not settle.** What a consumer actually needs is that the moves still apply.

**The general lesson, which is rule 12 applied to itself:** a correction to one claim has **dependent sentences** in
other sections, and the ones that break are the summaries — a table heading, a §7b restatement, a pointer. **Every
time I corrected the move-list claim I should have grepped for the parser-surface count, and I did not do it until the
claim's own consequence told me to.**

## Eighteenth round — the practical consequence, and the tell that catches my own class of error

The coordinator fixed entry 3ac and it now **reverses the advice** rather than only correcting the mechanism: **the
warning is truthful, so a harness CAN trust it.** `illegal move zzzz` means the position is **the legal prefix** — not
the intended position, not a splice — so it is **a usable signal rather than a hazard**: fail the row or record the
prefix knowingly, but do not distrust the reply. My §4 rule 12 now carries that consequence and names the reversal,
because the earlier version told the reader the opposite.

**Added rule 49 — "read the corrected entry as a stranger", which is the tell I earned three times in this document:**

| instance | what survived | caught by |
|---|---|---|
| false cross-reference | `§45` after the rule became §47 | the mechanical pointer form |
| two stale count paragraphs | header asserting 2,353 **and** 2,328 | re-deriving totals from artefacts |
| §3 sentence | "§1.18 ships one and holds the other" after it held both | dumping pointer targets |

**None was caught by any check; all three by reading the passage cold.** The reason the tell is specifically *as a
stranger*: the author reads what they intended in that slot, so the stale sentence is filled in from memory and never
actually parsed. **Rule 48's grep finds the phrase you WROTE, not the sentence you LEFT STANDING** — which is why this
is a separate rule and not a corollary.

**Added rule 50 — a claim that reverses twice is evidence about the TEST.** The move-list behaviour went splice →
truncate → splice → truncate; **the first two tests could not separate the hypotheses**, which is why the answer kept
following the experimenter's belief. The reversal count and its cause are now in the document, so a reader knows the
third version was reached by a test that could distinguish rather than by another guess.

## Seventeenth round — third reversal on one claim, verified independently

**The corrupted-move-list behaviour has now reversed three times, so the summary carries the current version once, with
the withdrawal history attached rather than left implicit.**

- **TRUNCATES at the bad token**, with the diagnostic. I verified the decisive test myself with python-chess: perft 3
  on startpos and each prefix gives **8902 / 13160 / 24825 / 23193 / 24079** — **all five distinct**, exactly the
  coordinator's figures. **An illegal token at any index returns that index's prefix value**, five for five.
- **Why the splice reading survived two rounds: at perft 2, `e2e4 e7e5` and `e2e4 e7e5 g1f3 b8c6` both give 835.**
  A fingerprint that cannot separate the hypotheses confirms the one you already believe. **Recorded as the general
  rule: check that the test can distinguish the candidate answers before running it.**
- **Junk before `moves` is a SEPARATE behaviour and kept separate:** it is skipped and the moves still apply
  (perft 2 = 15 with or without the junk, 9 board-only). **Tree-specific** — the older tree drops the whole command and
  stays on startpos (400). A `perft 1` fingerprint cannot see it: 3 moves either way, identical by construction.

**I flagged a live contradiction in the consolidated report's entry 3ac.** Its heading and its perft-3 evidence say
TRUNCATES, but its second sentence still reads "**and then applies e7e5 anyway**" — the withdrawn splice claim, three
lines above the evidence that refutes it. **A reader stopping at the first sentence gets the opposite answer from one
who continues.** That is the "correction that adds without removing" shape again.

## Sixteenth round — the pointer check's FULL form, applied to my own document

**The coordinator's form is stronger than mine and it found three more defects immediately.** I had been checking that
pointers *resolve*; the form extracts each pointer, resolves it, and **prints what it now points at**. A renumber
leaves resolution true while breaking subject-match — exactly the trap-14→15 case the report now records.

**Found and fixed, all of the "resolves but names the wrong subject" class:**

| pointer | cited for | actually pointed at | correct target |
|---|---|---|---|
| §1.18 | "ships one and holds the other" | §1.18 holds **both** at needs-more-evidence | sentence rewritten |
| §4 rule 24 | "a control that fires on correct usage" | the median/geometric-mean rule | **rule did not exist** — written as rule 35 |
| §4 rule 30 | "a cap test without a rising series" | the p-value-recomputability rule | rule 36 |

**Two of the three were stale SUBJECTS from earlier renumbering**; the third cited a rule I had never written, which
is the more interesting failure — **a pointer to a plausible-sounding rule that no one had authored**, and the sentence
around it read fine because the rule *should* have existed.

**And five more pointers broke after this round's own renumber**, caught by re-running the form: rule numbers for the
estimator, identity-trap, decomposition, digit-match and derived-claim rules all shifted by up to +3. **All 20 rule
pointers and all 22 section pointers now machine-verified to name their intended subject**, printed with context.

**The lesson in the form is that "all references resolve" passes in BOTH the good and the broken case** — so the check
must print targets, not verdicts.

## Fifteenth round — totals re-derived from artefacts, and one false pointer found

**Acting on the closing seat's prediction, I stopped trusting carried figures and re-derived every total from the files.**
It found drift, which is the point.

| quantity | carried | re-derived | verdict |
|---|---|---|---|
| findings | 2,353 | **2,380** (2,371 distinct table-row ids + 9 prose in `swarm-75`) | **drifted** |
| branches read | 34 | **31** with a `FINDINGS.md`, of 63 `swarm-NN` | **wrong both ways** |
| rules | 58 | **58** | correct |
| recommendations | 21 | **22** | **drifted** |
| line count | 2,197 | **2,344** | **drifted** |

**And one false cross-reference — exactly the class the seat named.** A sentence said "the check is trivial and it is
the same one **§45** needs", pointing at the decomposition/label rule. §45 had become the "correction adds without
removing" rule after a renumber; the decomposition rule is §47. **A pointer is a claim and this one was false**, and
no content check compares a pointer against its target. Repaired, and all 31 section refs and 20 rule refs were then
machine-verified to resolve.

**The entry-count trap was live in my own document too.** `swarm-64/65/74` record findings as prose *sections*, and I
had earlier counted section headings as findings. They are not: those files carry context sections and summaries, so
an entry count overstates a fault count. Only the **9 explicitly-id'd** findings in `swarm-75` are counted; the other
three prose seats contribute **0** to the total by the definition now stated in the header.

**A second self-inflicted inconsistency, caught by the same pass:** two stale count paragraphs had accumulated in the
header from successive edits, so the document asserted 2,353 and 2,328 in different places. Removed.

## Fourteenth round — the mechanism reverses, and a resolution rule

**I had the mechanism backwards, and the correction makes it stronger.** I wrote that "only the per-node factor moves
with game phase", following thirds. **Six slices of 4,135 pairs separate what thirds could not: per-node spread
0.29 %, node 1.36 %, wall 4.76 %.** So **per-node cost is nearly a constant of the engine and the phase dependence
lives in the NODE ratio.**

**The corrected version is the better claim:** per-node is a property of the **code**, stable to 0.3 % in every phase;
the node ratio is the **search interacting with the position**. **That is why three samples across two builds agree at
1.0640 / 1.0693 / 1.0709** — it is the one term that does not depend on what you sampled. A mechanism that predicts its
own replication beats one that merely fits.

Added **rule 26** — a slice count is a **resolution**, and too few slices invert a conclusion. The thirds were a
reasonable partition that produced a confident, coherent, backwards mechanism; the factors differed ~4× and a 3-way
split could not resolve that. Added **rule 27** — a median of a product is not the product of medians; slice 2 gives
0.9618 × 1.0719 = 1.0310 against a wall median of 1.0476, a 1.6 % gap on data whose aggregate closes to 0.5 %. The
table now carries that caution so a reader multiplying slice medians does not conclude the identity fails.

**Security gate: nothing to remove.** I checked — I carry no line about that gate having resolved, so the recheck
seat's correction needs no action here.

## Thirteenth round — the wall-time headline flips sign

**This reverses a recommendation's primary line, and it is the largest single change since the summary was written.**

- **§1.11 rewritten from "net speed NOT ESTABLISHED" to "a small LOSS on the full population."** Population run over
  the game set: **node median 0.9618, wall median 1.0351 — about 3.5 % SLOWER.** The earlier 116-pair stride sample
  gave wall 0.9698 (~3 % faster), so **the sign flips.**
- **I verified the identity independently: 0.9618 × 1.0709 = 1.0300 against observed 1.0353** — a 0.5 % gap. So it is
  the two components composing as the decomposition predicts, not two estimates disagreeing.
- **Consistent with the n=464 arm's "not established"** rather than contradicting it: that interval included 1.0, and
  the population puts the point on the slower side.
- Carries the reason the sample misled (node median identical to four decimals across thirds; wall median drifts
  1.0215 / 1.0352 / 1.0441) and the mean rule (**median 0.9618 vs mean 1.0941; the mean's error was 4× the median's**).

**§6.7 added — the PC r15 columns have a provenance gap.** I verified myself that **`FORGE_FIX_ROOT_DRAWN` appears in
no `src/` or `include/` path on any of the 63 `swarm-NN` branches** — only in prose and check scripts. It is a gap, not
a doubt (the numbers are mutually consistent; `swarm/23` records the sha256 prefix), but **the repair cannot be rebuilt
from the record**, which is what the shipped patches close. Also recorded: **`-DFORGE_MATE_ALPHA_GUARD=1` is NOT the
repair** — it gates `MateAlphaGuard`, a pruning switch.

**Three corrections to things I was told, all applied:** the piped-harness fabrication is **not** detectable by its
move (**13 distinct fabricated moves, all 60 legal, 0 of 60 correct** — only a zero `info`-depth count finds it); the
per-node row **named its estimator** after a cold recheck found the pooled estimate sat **outside its own interval**;
and the two new control/parser rules (**a parameter that cannot bind cannot be tested**; **a parser fault is silent
unless the row count is asserted** — 1 and 8 rows instead of 180 and 464).

## New this round

- **§7d: v3 accumulator, 54,379 distinct positions, 0 mismatches**, with 5,012 king-key transitions and the union
  method note (nested fixtures, `47,418 ∪ 6,961`; the earlier `57,720` was a sum, not a union).
- **§2.9: neural-arch hang** — `NNUEArch` with no usable net prints an error then **exits status 2 without answering
  `isready` or sending `bestmove`**. Sourced from `swarm-71`'s STATUS with the exit status. My first search missed it
  because it lives in STATUS, not FINDINGS.
- **§4 rules 9b and 10: parser surfaces.** Unparseable `go` value → default silently (seven forms all land on depth 5,
  1,001 nodes, indistinguishable from `go depth 5`); surfaces are **not uniform — two of five refuse safely, three
  improvise silently**; a corrupted move list **splices** rather than truncates.
- **§6.6: the identity baseline is an acceptance gate this branch cannot meet.** `27,944,084` is unreachable here
  because four PC20 options are **absent from the source** (`CuckooRep`, `HistRework`, `TtPruneV2`, `CorrHistV2`),
  giving `29,791,805` — a 6.6 % gap. §1.10 carries the caveat with the number.
- **§7b promoted from four ways to five**, with the parser-uniformity point added.

## Cold read (04:16Z) — 5 arrangement defects, all fixed

Found by reading; invisible to the 271-token provenance pass. The `0000`/`mate 0` contradiction was in **three** of my
sections, and the coordinator found the same defect in the report's own table.

## Deliverable structure

1. What to change (20 recommendations, 22 verdict markers) · 2. What is broken (9, plus 5 withdrawals) ·
3. What is not established · 4. **49 measurement rules** · 5. Unsourced (8) · 6. Mis-paired (6) ·
7. Book soundness · 7b. Five ways of answering a question not asked · 7c. The reuse trap · 7d. Accumulator
correctness · 8. Method.

## Constraints honoured

- No engine run, no script executed, no re-measurement.
- No other seat's branch modified.

## Open items

1. **`42` is contradicted, not just unsourced**, and sits in the report's book-soundness block.
2. **`27,944,084` still reads as an unconditional gate** in the report's §5b — §6.6 documents why it cannot be met.
3. **Accumulator aggregates** (`54,379` / `47,418` / `6,961`) are report-only; `swarm-71` commits fixtures and
   commands but not the union arithmetic.
4. **Three latency percentiles** need `q2b_latency.py` output committed.
5. Counts are snapshots at the tips named in the header — re-derive, do not edit.
