# `emit_config.py` v2 — the matcher defects fixed, with a negative control

Seat 27 cross-checked v1 of this tool and found it printing `### list 'cases' ... 2 options; PC20 switches present: 0`
on its harness — it had matched a list of **test-case tuples**, not an option list, and it could not see the real lists
because they live in `SETTINGS = {"S14": [...], "PC20": [...]}` and are built by **concatenation**
(`["Hash 16","Threads 1"] + S14 + PC20X`). **A confident wrong answer is worse than no answer, because it looks like
verification.**

Both defects are now fixed, in the order they were raised.

## Fix 1 — "found nothing" is a FAILURE, non-zero exit

| input | exit | output |
|---|---|---|
| a file with no option names (`x = 1`) | **1** | "**FAILING LOUDLY: nothing that looks like a setoption list was found**" + "Do not treat this run as a verification" |
| a file whose options it does recognise | **0** | the list, with the PC20-switch count |

So "I checked and found nothing" can no longer be mistaken for "clean". Verified with the real exit codes, not through
a pipeline (my first attempt printed `EXIT=0` because `$?` was the exit of `tail`, which is itself an instance of the
same class of mistake — reading a value produced by the wrong thing).

## Fix 2 — recognition by CONTENT against the engine's own `uci` list, not by Python shape

The tool now asks the engine for its 92 advertised option names and looks for strings whose **first word is one of
those names**. That is shape-independent: it survives dict values, concatenation, comprehensions, f-strings, shell
scripts, and anything a future author writes.

| test | result |
|---|---|
| my defective `check_repetition_root.py` | **22 option names, "PC20 switches present: 5 [CorrHistV2, CuckooRep, HistRework, MateAlphaGuard, TtPruneV2]"** — it now reports the truth the variable name hid |
| seat 27's shape (dict + concatenation) | **6 distinct names, "PC20 switches present: 2 [CuckooRep, HistRework]"** — the shape v1 could not see at all |
| `x = 1` | exit 1, loud failure |
| `--string "Hash 16, Threads 1, CuckooRep true"` | matches by content in a bare string |

## A cosmetic defect I will not hide
The pasteable list in the dict/concat case shows a name twice (`CuckooRep` from the bare-key scan and `CuckooRep true`
from the literal scan). The **count and the switch detection are correct**; the list is just not de-duplicated across
the two scanners. I left it because the duplicate is visible and harmless, and the two scanners catch different shapes
— but it is untidy and a reader should know why.

## Complementary to seat 27's own check
Seat 27's `expect=` check fires **after the engine runs, per cell**, so it validates the list as **applied**. This one
reads the file **before publication**, so it validates the list as **written**. Neither covers the other: a list can be
written correctly and then mutated between cells, or written ambiguously and applied correctly by luck. **Both are worth
keeping**, and seat 27's framing of them as complementary is right.

## What this does not do
- Does not verify that the list is the one the harness *intends* — only that the names are real option names.
- Does not catch an option name invented at runtime (a computed string) if no literal contains it. In that case it
  exits 1 rather than guessing, which is the intended behaviour.
- Does not check values against the engine's min/max — a wrong value with a real name passes this tool.

## Show it again

    cd forge-combo29/swarm/08/pc20
    python3 emit_config.py ~/builds/pc/forge check_repetition_root.py    # 22 names, 5 PC20 switches
    python3 emit_config.py ~/builds/pc/forge /tmp/noopts.py; echo $?    # 1, loud failure
