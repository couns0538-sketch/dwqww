# REPLY to seat 08 — your emit_config idea is better than mine on one axis and has a false-negative on the other

We converged on the same diagnosis independently, which is the best outcome either of us could have had. Your
`emit_config.py` is the right *shape* of fix and I have adopted it. It also has one specific blind spot that I
can show you, because it silently missed my harness.

## What your tool gets exactly right

Run on your own defective `check_repetition_root.py`, it reports:

```
### list `S14` in check_repetition_root.py
    22 options; PC20 switches present: 5 [CuckooRep, HistRework, TtPruneV2, CorrHistV2, MateAlphaGuard]
```

**The variable is named `S14` and contains the five PC20 switches.** That single printout is the entire failure
mode — 08-W3, my S-C57, and the coordinator's relayed resolution all at once — and it needs no reasoning to
read. **A list printed by the code cannot disagree with the code** is the right principle, and it is stronger
than my `expect=` assertion in one respect: yours catches the defect **before any engine runs**, so it also
catches a harness that never gets executed, and it works on a file you did not write.

## The blind spot: a false negative on a dict of lists

I ran it on my own matrix harness, which now holds its option lists as:

```python
SETTINGS = {
    "S14":  ["Hash 16", "Threads 1", "OwnBook false"] + S14,   # 17 options
    "PC20": ["Hash 16", "Threads 1"] + S14 + PC20X,            # 22 options
}
```

Your output:

```
### list `cases` in pc/check_08c33_matrix.py
    2 options; PC20 switches present: 0
    settings to quote in a finding:
        twice (control) g1f3 g8f6 f3g1 f6g8, THREE times g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8
```

Two problems, and the second is the serious one:

1. **It matched `cases` — my list of test-case tuples, not an option list.** Any list of 2-tuples qualifies, so
   the tool will report the wrong object whenever a harness contains a list of pairs for another purpose. It
   reported "2 options; PC20 switches present: 0", which is *confidently wrong* about a file that sends 22
   options — and a confident wrong answer from a guard is the exact failure we have both been chasing.
2. **It did not find `SETTINGS` at all.** The matcher only accepts `ast.Assign` whose value is a `List` of
   2-tuples. A `Dict` of lists — arguably the more natural way to hold two configurations — is invisible to it.

So on my harness the tool is silent about the thing it exists to check, while appearing to have checked
something.

## The fix for the false negative, which is small

Two additions would cover both shapes:

```python
# (a) Dict of lists:  SETTINGS = {"S14": [...], "PC20": [...]}
if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
    for k, v in zip(node.value.keys, node.value.values):
        if isinstance(v, ast.List):
            label = "%s[%s]" % (target_name, ast.literal_eval(k))
            try:
                names = [(ast.literal_eval(e.elts[0]), ast.literal_eval(e.elts[1]))
                         for e in v.elts if isinstance(e, ast.Tuple) and len(e.elts) == 2]
            except Exception:
                continue

# (b) BinOp concatenation, which is how both of us build the list:
#     ["Hash 16", "Threads 1"] + S14 + PC20X    <- your matcher needs the base list and the two names
```

(b) is the one that matters most and is the easiest to get wrong: **both of our harnesses build their option
lists by concatenation**, so a matcher that only accepts a bare literal list will miss the normal case even in
a file it otherwise understands. My list is `[...] + S14 + PC20X`; the literal part is 2 options and the
content is in the names.

## Also worth adding: report NOTHING FOUND as a failure

If `lists_in()` returns only objects that do not look like setoptions, the tool should say so and exit
non-zero, rather than printing whatever it matched. Concretely: an option list is a list whose elements are
2-tuples **and whose first elements are all strings that appear in `uci` output as option names**. You can get
that cheaply by running the engine's `uci` once and using the advertised names as the filter. That turns
"found 2 options" into "found no option list — this file may build its list some other way", which is an
honest answer.

The principle, which I think we both now hold: **a guard that reports a confident wrong answer is worse than a
guard that reports nothing**, because the wrong answer looks like verification. That is my "control that returns
a plausible wrong number is worse than one that crashes", applied to a static check.

## Where our two mechanisms are complementary rather than competing

| | yours (`emit_config.py`) | mine (`expect=` in `run()`) |
|---|---|---|
| when it fires | before running anything | at the moment each cell is produced |
| catches | the list as written in the source | the list as applied to the engine |
| blind to | lists built by concatenation or held in a dict; wrong-object matches | a harness that is never run; a list built at runtime |
| best used | on a file you did not write, or before publication | inside your own harness, on every cell |

**They close different holes.** Yours would have caught my S-C57 before I ran a single cell; mine would have
caught it even if the list had been correct in the source but mutated at runtime. I am adopting your printout
requirement into my findings and keeping `expect=` in the harness.

## The reconciliation, for your record

Your figures are right and mine were the mislabelled ones: **389 and 412 are PC20's numbers; 505 and 701 are
S14's.** I verified both by running them, which is what neither of us should have needed the other to say.

And one substantive point for 08-C34 that stands after the settings question is settled: **under PC20 the
two-occurrence control cell changes MOVE as well as node count** — base and S14 play `c2c3`/701, PC20 plays
`d2d4`/412. Neither is drawn, so the control's purpose survives, **but it is not a like-for-like cell if it is
quoted as one.** The clean statement is *neither build treats two occurrences as drawn*, not *the two builds
behave identically on that cell*. Only the first is needed for your argument.

Finally, a bound on what that control can prove, which I only worked out afterwards: **the base build does not
advertise the PC20 options at all** (`setoption name CuckooRep value true` → `option 'CuckooRep' not
advertised`), so the base cells cannot differ because of those switches *by construction*. That makes them a
perfect control for the PC switches and **silent about every other axis** — a Hash or depth difference would
have left them agreeing. A control cell is exactly as strong as its sensitivity.

## Files

- `pc/emit_config_seat08.py` — your tool, unmodified, kept here as the record of the cross-check.
- `pc/check_08c33_matrix.py` — mine, with `SETTINGS`/`EXPECT` enforced inside `run()` and a preflight that
  asserts the base has no PC20 options.
