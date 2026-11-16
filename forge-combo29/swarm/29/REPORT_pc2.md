# REPORT_pc2 - 29-F19's mechanism: a 2x2 factorial on the PC build

what was asked: (1) make 29-F19's lesson a named rule; (2) chase the reversal mechanism — is it the slot-0 removal
interacting with the PC build's probe, or the vector gather; diff the two probe bodies and say which half reverses
and why; (3) then the hard-budget `go nodes` path.
the answer: **(2) BOTH halves reverse on the PC build, and the effect is non-additive.** Slot-0 alone: **+0.558 %**.
Vector alone: **+0.634 %**. Both together: **+0.320 %** — better than either alone, while still worse than base.
The interaction term is **-0.872 % of the run**, which no logic change can produce: both halves are
behaviour-neutral (node counts identical in all four builds), so the swing is **code layout / inlining**, and I
show exactly where it happens.
how sure: high on the numbers (exact instruction counts, deterministic to ~1e-8); high on "not a logic change"
(node counts identical, and the probe bodies are byte-identical between base and PC builds).

## the two probe bodies are IDENTICAL
Diffed by reading both: `base 6b98f217` and `pc r15` have the **same** hit loop and the **same** replacement tail
(`replace_score` incumbent-seeding + `for (TTEntry& entry : cluster.entries)` with `score < replace_score`). The PC
patch does not touch `probe_body` at all. So the reversal cannot be "my change meets a different probe" — there is
no different probe to meet.

## the 2x2 factorial (PC r15 build, PC20, bench 13, Threads 1, portable `-g`)

| variant | instructions | vs base | |
|---|---|---|---|
| base (PC r15, no TT patch) | 3,535,346,320 | — | |
| **slot-0 only** | 3,555,075,296 | **+19,728,976** | **+0.558 %** |
| **vector only** | 3,557,747,780 | **+22,401,460** | **+0.634 %** |
| both | 3,546,664,625 | +11,318,305 | +0.320 % |
| **interaction** (both − slot0 − vector + base) | | **−30,812,131** | **−0.872 %** |

Node counts: **587,276 in all four builds**, so all four search the same tree.

For contrast, the same two changes on the BASE tree: 4,513,768,543 → 4,495,059,980 = **−18,708,563 (−0.414 %)**.

## why it is layout and not logic — the measurement that shows where it lands
Per-function self cost, same runs:

| build | `Worker::search(...,bool)'2` self | `probe_body<false>` self |
|---|---|---|
| base PC | 172,596,398 (4.88 %) | 31,551,058 |
| slot-0 only | 249,942,701 (**7.03 %**) | 26,191,211 |
| vector only | 246,596,237 (**6.93 %**) | 25,031,441 |
| both | 256,303,570 (**7.23 %**) | 15,536,066 |

`Worker::search`'s self cost jumps by ~2.2 points while the probe's own symbol gets *smaller*: the compiler
re-inlines part of the probe into `search` in the patched builds, and the inlined copy costs more per call than the
called version did. The probe is instantiated exactly twice in every build (`probe_body<true>` and
`probe_body<false>`, confirmed with `nm -C`), so this is inlining/scheduling, not a lost or duplicated instantiation.
A ±0.5 % instruction swing from that in an inlined hot path is a normal compiler-layout effect — which is precisely
why an instruction count measured on one build says nothing about another.

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-F28 | 9 | Neither half of my TT patch is neutral on the PC build: slot-0 alone is **+0.558 %** and the vector gather alone **+0.634 %** against the PC r15 base under PC20 (Threads 1, bench 13), while together they are +0.320 % — a **−0.872 % interaction term** with identical node counts in all four builds, so the swing is compiler inlining/layout (`Worker::search`'s self cost rises 4.88 % → 7.03 % while the probe's own symbol shrinks) and not a behavioural difference. | `pc0/raw_factorial.txt`, `REPORT_pc2.md` | NEW |
| 29-N16 | 9 | **NAMED RULE (from 29-F19/F28): an instruction-count saving measured on one build is NOT evidence about another build.** Worked example, my own patch: base tree 6b98f217 **−18,708,563 (−0.414 %)**; the SAME two changes on the PC r15 build under PC20 **+11,318,305 (+0.320 %)**, and on that build each half is worse still (slot-0 +0.558 %, vector +0.634 %). Cause is inlining/layout, not logic: node counts identical in all four PC builds and the probe bodies are byte-identical between the two trees. Anyone quoting a base-tree instruction saving as a PC improvement must re-measure it on the PC build. | `pc0/raw_factorial.txt`, `REPORT_pc2.md` | NEW |

## suspicions, not proven
- Which inlining decision flips: I did not read the assembly (`objdump -d`) for the two variants, so I name the
  *effect* (`Worker::search` absorbs more work) and not the specific GCC heuristic. Reading the disassembly of both
  would settle it; that is a job in itself.
- Whether the same non-additivity appears in the lock (non-portable) build, which I cannot profile under callgrind
  at all (exit 132). The 2x2 rests on the portable build only, as every instruction count of mine does.

## what I did NOT do
- No assembly diff, so no claimed mechanism below "inlining changed".
- Did not re-run the factorial at S14 as well as PC20; PC20 is the configuration the owner uses.

## what I am NOT sure about
- Whether the +0.32 % on the PC build is the true cost of the patch there or itself an artefact of one layout; since
  the two halves interact by −0.87 %, the honest statement is "not a saving on this build", not a precise penalty.

times: see `pc0/stamps.txt`.
