# 08-F31's "0 of 60" has no planted case — a Rule 1 gap, not a wrong finding

seat 19 · area 9 · a check of another seat's zero against Opus's Rule 1.

## 1. The three lines

**What was checked.** 08-F31 reports, among other things, that the **full-material class is 0 of 60** — no board
where a self-play target is the wrong kind of number — and offers that as "the consistent, actable result". Under
Opus's **Rule 1**, a zero counts only when the **same harness, unchanged**, counted one planted case.

**The answer.** **The 0-of-60 zero has no planted case through its own harness.** I looked in the report, the
harness, and the folder that 08-F31 names as its evidence (`pc20/REPORT_volatility_rate.md` +
`pc20/volatility_rate.py`): **no plant, no fake-engine mode, no control run** for *that* measurement. Seat 08 does
have two control files in its folder, but they cover **different harnesses** (`check_s06f4.py` and
`clock_latency.py`), not the volatility harness that produced the 0 of 60.

**How sure.** Certain of the absence — it is a grep of its committed report, script and folder for the words that
a plant would use, plus a read of the two control files it does have to see what they exercise. **I did not run
its harness**, so I am reporting the *documentation* gap, not re-measuring its zero.

## 2. What I found, precisely

| item | result |
|---|---|
| `08-F31`'s evidence pointer | `pc20/REPORT_volatility_rate.md` + `pc20/REPLICATION_seed902.md`, raw `volatility_rate.txt.jsonl` |
| plant/control mentioned in `REPORT_volatility_rate.md` | **none** (grep for plant/control/fake/Rule 1: 0 hits) |
| plant mode in `pc20/volatility_rate.py` | **none** (the only `control` hit is the words "owner's control" describing 6 s + 0.06) |
| control files seat 08 does own | `negative_control.{sh,txt}` → exercises **`check_s06f4.py`**; `job4/harness_refusal_control.{sh,txt}` → exercises **`job1/clock_latency.py`** |
| do either cover the 0-of-60? | **no** — different scripts, different measurements |

**To be fair, and this matters:** seat 08 is unusually disciplined about this rule elsewhere. Both of its control
files exist, both show a **non-zero exit** when fed bad input, and one is described as "`/bin/cat` as a fake
engine that answers readyok/uciok but never prints a number" — a genuinely good plant. **It applied Rule 1 twice
in this run and has not applied it to this particular zero.** That is a gap in coverage, not a habit of
carelessness.

## 3. Why it still matters, and what it does not mean

**It does not mean the 0 of 60 is wrong.** A zero with no plant is "not shown", which is exactly what Rule 1
says — not "false". The claim may well be true.

**But the specific risk is real for this harness.** Its measurement is: clocked score is cp, deep `go depth D+4`
finds a mate. **A harness that silently failed to see the deep mate would produce exactly 0 of 60.** The obvious
plant — a board where depth D+4 demonstrably mates, fed through the same code path, which must be counted as a
hit — is what would distinguish "no board has the defect" from "the harness cannot see the defect". **Without
it, the two are indistinguishable from the committed evidence.**

And note the direction of the risk: **the 0-of-60 is the claim seat 08 calls "the consistent, actable result"**
and contrasts with the 37 %/10 % sparse rate it declines to put a number on. **The weaker-evidenced claim is the
one being foregrounded** — not because seat 08 is being dishonest, but because a zero *feels* more solid than a
disputed percentage and does not get the same scrutiny.

## 4. Finding

**19-C28 — 08-F31's "0 of 60" full-material result has NO planted case through its own harness, so under Rule 1
it is "not shown" rather than established.** Its evidence report and script contain no plant or fake-engine mode;
the two control files seat 08 does own exercise different harnesses (`check_s06f4.py`, `clock_latency.py`). **The
finding is not thereby wrong** — but the harness's failure mode (missing the deep mate) would produce exactly
0 of 60, so the plant is the specific thing that separates "no defect" from "cannot see the defect". Worth noting
because it is the claim 08 foregrounds as actable while declining to quantify the sparse rate.

### What I did NOT do

- I did not run its harness or add a plant to it. That is seat 08's call and its file.
- I did not check whether a plant exists under a name I did not grep for; I searched the words plant, control,
  fake and Rule 1 in the report, the script and the folder listing.
- I did not audit 08-F32's numbers, which are a different measurement.

## 5. Files

The evidence pointer and control files are on branch `for-fable-and-opus/swarm-08` at the paths quoted above.
