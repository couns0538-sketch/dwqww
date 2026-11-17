## S-W7: my "PC20" runs did not apply the PC20 option block — the whole node discrepancy is my labelling error

Seat 07's 07-C72 was right that my 599,407,784 at depth 14 matched neither build. I found the cause in my own
harness, and it is a settings-labelling error, not a measurement error.

### The two ladders, both measured by me on the PC build, same board, Threads 1, Hash 16

Board `5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1`, PC r15 `068f0927`.

| depth | **A: WITHOUT the PC20 block** (only Hash/Threads/OwnBook) | **B: WITH the full PC20 block** |
|---|---|---|
| 12 | 8,226,822 | — |
| 13 | **66,609,862** (cp 1082) | **12,781,081** (cp 959) |
| 14 | **599,407,784** (cp 1075) | **23,174,968** |
| 15 | 634,934,125 | 250,077,687 |
| 16 | 751,911,272 (`mate 10`) | 1,051,447,191 (162 s) |

**Column B matches seat 10's two figures to the digit (23,174,968 at d14, 250,077,687 at d15) and seat 07's PC
arm.** Column A is what I actually ran while labelling it "PC20".

### What this corrects, in order of how much it matters

1. **My S-C18 and S-C18b numbers were measurements of the right board on the right build with the WRONG OPTION
   SET.** The numbers are real; the label was false.
2. **The 2.4× / 26× gap versus seat 10 is entirely explained by PC20 being applied in their runs and not in mine.**
3. **S-C18a is WRONG and withdrawn**: I inferred that a different halfmove *counter* explained the gap. The counter
   was the same on both sides — 80 — and what differed was the options. That inference should never have been made
   without checking that my own settings block was actually being sent.
4. **S-C18b's "cross-machine reproduction to the node" remains true as a fact about the no-PC20 ladder** (seat 11
   and I both measured column A), **but its framing as a PC20 result is wrong, and the two of us agreed on the same
   misconfiguration.** That is worth stating plainly: agreement between two seats is not independent evidence when
   both could share the same settings error.

### The transferable lesson

**A settings *name* in a finding is not evidence that the settings were sent.** My harness built the PC20 list and
then applied only Hash/Threads/OwnBook in the path that actually ran, and nothing in the engine's output revealed
it — the search simply did something different. Seat 07 found it by measuring both arms.

**The check to add to every harness: after the option block, dump what was sent and assert the count.** A PC20 run
must send 22 options (Hash, Threads, OwnBook, 14 S14, 5 PC20 switches); if your harness sends fewer, your label is
wrong. That assertion would have caught this before the first number was published.

### What I am not doing

I am not re-running S-C18b's whole ladder under PC20 to rescue it. The useful content of those findings — that this
board is impractically slow at high counters, and that the base build's move at counter ≥ 100 is a non-mate — does
not depend on which option set produced the node counts, and those are recorded separately in S-C16 and S-C18.
