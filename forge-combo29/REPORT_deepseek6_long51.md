# REPORT — deepseek6, long 51 (long 41's bundle and best pair on G at depth 14)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long51/`
Model: DeepSeek V4.1 Flash 1017

## 1. What was asked, the answer, how sure

**Asked:** long 41/42's bundle of four and its best G-shrinking pair, on **G at depth 14** — do the interactions
grow or shrink with depth?

**Answer:** **they do not merely grow or shrink — the interaction CHANGES SIGN.**
At depth 12 the bundle of four measures **0.8569 against a 0.8007 product (+7.02 % above it)**; at depth 14 the same
four measure **0.8675 against a 0.9198 product (−5.69 % below it)**. The best pair does the same:
SD7+LQD193 **+0.65 % at d12 → −3.00 % at d14**. So on G the four settings compose sub-multiplicatively at depth 12
and super-multiplicatively at depth 14, and any product-of-singles estimate is only valid at the depth it was built
at — one depth pair deeper it gets the *direction* wrong.

**How sure:** certain of all seven sums (353 positions each, committed rows and metas, one command re-derives the
table). Every product here is built from singles **measured at depth 14 in this item**, never from the depth-12
table — that is exactly the error long 36 made and I avoided it by running the singles.

## 2. Honesty numbers

Build: the plain 6b98f217 release build, `/tmp/ds6/build-release/forge`, sha256
`7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622` (the same binary whose four pins were exact at
the start of this chat and in `raw/` of my long 23). No new build this item; the base run's own value is the pin:

**G at depth 12 under S14 = 18,466,239** is the depth-12 anchor (my long 43's `runs/G_m2_d6.rows`, exact). G at
depth 14 under S14 is not a published known sum — **43,345,893 is this item's measurement** and is used as the
baseline for every ratio below.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed with `claim.sh`, its line first in stamps.txt | done | `stamps.txt` line 1 | exit 0, 20:36:58Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions with kill ranges |
| batch 1: base + four singles, G depth 14 | done | `runs/G14_{S14,SD7,LQD193,LQB101,IIR1}.rows` | 353 rows each |
| batch 2: pair + bundle | done | `runs/G14_{SD7_LQD193,BUNDLE}.rows` | 353 rows each |
| products from the depth-14 singles | done | `interact51.py`, `interact_out.txt` | section 4 |
| scorecard | done | `scorecard.txt` | 2 held, 1 partly, 3 killed |

## 4. The table (`python3 interact51.py runs`)

**G at depth 14, 353 positions:**

| run | nodes | ratio to S14 |
|---|---|---|
| S14 | 43,345,893 | 1.0000 |
| SD7 (`SingularDepth 7`) | 41,482,242 | 0.9570 |
| LQD193 (`LmrQuietDivisor 193`) | 41,320,169 | 0.9533 |
| LQB101 (`LmrQuietBase 101`) | 42,632,235 | 0.9835 |
| IIR1 (`IirDepth 1`) | 44,436,634 | 1.0252 |
| **pair** SD7+LQD193 | 38,357,013 | **0.8849** |
| **bundle** of four | 37,604,007 | **0.8675** |

**The interactions, both depths:**

| set | d12 measured | d12 product | d12 off % | d14 measured | d14 product | d14 off % |
|---|---|---|---|---|---|---|
| pair SD7+LQD193 | 0.8504 | 0.8449 | **+0.65** | 0.8849 | 0.9123 | **−3.00** |
| bundle of four | 0.8569 | 0.8007 | **+7.02** | 0.8675 | 0.9198 | **−5.69** |

The depth-12 columns are quoted from `REPORT_deepseek6_long41.md` and `REPORT_deepseek6_long42.md` (their products
were built from long 27's singles at the same values); the depth-14 products are
`0.9570 × 0.9533 = 0.9123` and `0.9570 × 0.9533 × 0.9835 × 1.0252 = 0.9198`.

## 5. Findings, each with the command that shows it again

**F1. The interaction changes sign with depth — the headline.** +7.02 % at depth 12, −5.69 % at depth 14, for the
same four settings on the same 353 positions. Reproduce: `python3 interact51.py runs`, the interaction table.
This is not a small drift: the product over-estimates the bundle's tree by 7 % at d12 and under-estimates it by
5.7 % at d14, a swing of 12.7 percentage points across two plies.

**F2. The pair flips too, and earlier.** SD7+LQD193 is +0.65 % at d12 and −3.00 % at d14 — already
super-multiplicative at depth 14 while still slightly sub-multiplicative at depth 12. So the sign flip is not an
artefact of stacking four settings; two are enough.

**F3. `IirDepth 1` is the only setting that GROWS the G tree at depth 14 (1.0252) and it drags the bundle's
product up.** At depth 12 on G it was 1.0042 (nearly inert). Long 41 kept it in the bundle as "the odd one"; at
depth 14 it is an outright cost, and because a product multiplies, it inflates the bundle's product (0.9198)
against a bundle that actually shrinks to 0.8675. Anyone reading the product as a forecast would over-predict the
bundle's size by 6 %.

**F4. The singles' leading pair swaps with depth.** At depth 12 SD7 (0.9092) shrinks G more than LQD193 (0.9293);
at depth 14 LQD193 (0.9533) shrinks it more than SD7 (0.9570). Both are within 0.4 % of each other at d14, so the
swap is small — but it is a swap, and it is why my P2 is killed.

**F5. Best-move churn at depth 14 is LOWER than at depth 12, not higher.** Against the depth-14 S14 run:
SD7 79/353, LQD193 81, LQB101 92, IIR1 90, pair 85, bundle 97. My P5 predicted ≥100; the measured values are all
below it, and the bundle is still the largest of the six (97), as predicted. Deeper search converges, the same
effect I measured in long 25 on O (churn fell from 133–143 at d12 to 41–51 at d14).

## 6. What I read from my colleagues

- **long 41's and long 42's reports** (this session's own earlier items, on the branch) — the source of the four
  settings, the depth-12 measured ratios and the depth-12 products. I read them to fix the settings rather than
  trusting the job file's prose, and F1 is a direct continuation of long 42's "does the bundle follow the
  product" question, answered at one more depth.
- **long 43's `runs/G_m2_d6.rows`** — the depth-12 G anchor (18,466,239) that proves this item's base binary is
  the same one.
- No colleague note was treated as an instruction.

## 7. What I did NOT do

- **Did not run O at depth 14** — the item says G.
- **Did not run the four triples at depth 14** — the item names the bundle and the best pair.
- **Did not reuse the depth-12 singles in any product** (F1's whole point).
- **Did not run any match** — node counts only; nothing here says the bundle is stronger or weaker.
- No pull request, no branch but mine, no engine source.

## 8. What I am NOT sure about

- **Why the sign flips.** A plausible reading: at depth 12 each setting removes nodes near the frontier where the
  four overlap heavily (sub-multiplicative); at depth 14 the tree is dominated by deep re-searches that the four
  settings each *avoid starting*, so their effects reinforce rather than overlap. I have not instrumented it, so
  that is a suspicion, not a result.
- Whether the flip happens between depth 13 and 14 specifically or is a smooth drift — I have two depths only.
- Whether it also happens on O. Long 42 measured O at depth 12 (0.9221 against 0.9648, −4.42 %); O at depth 14 is
  not measured here, so I say nothing about O.

## 9. A better way

For any future "do interactions grow with depth" item, **run the singles at every depth you claim a product at** —
that is seven runs instead of three, and it is the only way the product means anything. This item's design (name
the bundle and the pair, leave the singles implicit) would have produced a number that looked like an interaction
but was a depth artefact; I spent four extra runs to avoid it and would do the same again.

## 10. Times and the folder

times: see `stamps.txt` (its first line is `claim.sh`'s output, as file 12/13 require).
Model name my runtime gives: **DeepSeek V4.1 Flash 1017**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
