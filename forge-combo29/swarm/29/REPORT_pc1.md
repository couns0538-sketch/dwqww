# REPORT_pc1 - my TT patch on the PC build: the win REVERSES

what was asked: TEXT 2 says to re-run my own findings on the PC build under PC20. My main finding is the TT probe
patch (29-F12 + 29-F14), so this is that re-run.
the answer: **the patch does not help the PC build — it is measurably WORSE there.** On the base tree it removed
18.7 M instructions (-0.414 %); on the PC r15 build under PC20 it ADDS instructions: +19.7 M for the slot-0 change
alone and +11.3 M for both changes. Node counts are identical in every case, so this is a pure code-generation
effect, not a behaviour change. I am reporting the reversal rather than quoting the base-tree number as if it
applied to the PC.
how sure: high. Exact instruction counts, deterministic to 14 instructions on a 3.5-billion-instruction run (that is
4e-9 relative), with identical node counts on both sides.

## the numbers (PC r15 build, PC20, `bench 13`, Threads 1, portable `-g`)

| build | instructions | vs base PC |
|---|---|---|
| PC r15 base | 3,535,346,320 | — |
| PC r15 + slot-0 change only | 3,555,075,324 | **+19,729,004 (+0.56 %)** |
| PC r15 + slot-0 + vector scan | 3,546,664,639 | **+11,317,319 (+0.32 %)** |

and on the BASE tree, for contrast (my earlier job-9 numbers):

| build | instructions | vs base |
|---|---|---|
| base 6b98f217 | 4,513,768,543 | — |
| base + slot-0 + vector | 4,495,059,987 | **-18,708,556 (-0.414 %)** |

**The same source change is a win on one tree and a loss on the other.** That is the finding.

## correctness on the PC build: unchanged, and that is the important part
| check | result |
|---|---|
| all eight known numbers of file 5 (none / S14 / PC20) | **8/8 MATCH** with the patch applied |
| node count under PC20, bench 13 | 587,276 with and without the patch |
| PC20 options accepted (no `unknown option`) | 0 rejections |
| determinism of the measurement | base 3,535,346,320 twice (14-instruction jitter); patched 3,546,664,639 twice |

So the patch remains **behaviour-neutral** on the PC build; it is only the instruction count that moves the wrong
way. Anyone applying it must not expect a speedup there.

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| apply PC patch + my patch to one tree | done (after two setup errors, see below) | `/tmp/pconly3` | both present, verified by file existence AND by an option check |
| build with the guard flag | done | `~/build/pcslot0`, `~/build/pcpg` | both exit 0 |
| known numbers under all three regimes | done | `raw_pc_tt_ir.txt` run of `verify_pc_build.py` | 8/8 MATCH |
| isolate slot-0 vs vector | done | `raw_pc_tt_ir.txt` | slot-0 alone +0.56 %, both +0.32 % |
| determinism | done | two runs per configuration | jitter 14 instructions, effect 11 M |

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-F19 | 9 | The TT probe patch (29-F12+F14) REVERSES sign on the PC r15 build: it removes 18.7 M instructions on base 6b98f217 but ADDS 11.3 M on the PC build under PC20 (+19.7 M for the slot-0 half alone), with identical node counts and all eight known numbers still matching — so it must NOT be presented as a PC-build speedup. Builds: base 6b98f217 and 6b98f217+pc_r15.patch; settings PC20; **Threads 1**. | `forge-combo29/swarm/29/pc0/raw_pc_tt_ir.txt` | NEW |

## the two setup errors I made, recorded because they nearly produced a false alarm
1. I applied the PC patch with `>/dev/null 2>&1` and it silently SKIPPED all 11 files (its paths are relative to
   `forge-combo29/`, so `patch -p1` must run from inside that directory). The resulting "patch changes the node
   count!" panic was an artefact of an unpatched tree: the binary rejected every PC20 option (`unknown option
   CuckooRep` ...) and fell back to S14's node count, 656,525, which I mistook for 656,517 at first glance.
   **Lesson: never silence a patch's output, and always confirm the applied state by a positive check** (option
   list present), not by the absence of an error I did not look at.
2. A `git worktree add` failed because a stale registration existed; `git worktree prune` cleared it.

## suspicions, not proven
- WHY it reverses: the base tree's `probe_body` and the PC build's differ by the surrounding code the PC patch adds,
  so the compiler inlines and schedules the four-slot scan differently. A 0.5 % instruction swing from a
  code-layout change is large but not implausible in an inlined, hot function. I did not disassemble either build to
  confirm, and I am not claiming a mechanism — only the measurement.
- This is a warning for the whole swarm: an instruction-count win measured on the base tree is NOT evidence about
  the PC build. Any seat quoting a base-tree instruction saving as a PC improvement should re-measure it there.

## what I did NOT do
- No disassembly comparison, so no mechanism claimed.
- No wall-clock measurement on the PC build: per seat 04's rule the scores there are not trustworthy, and per my own
  29-N6 a single timing comparison on this machine is not resolvable at these sizes.

## what I am NOT sure about
- Whether the PC patch's four search switches being ON (PC20) rather than off (S14) changes which code paths the
  probe sits inside enough to matter; I measured only PC20, which is the configuration the owner uses.

times: see `pc0/stamps.txt`.
