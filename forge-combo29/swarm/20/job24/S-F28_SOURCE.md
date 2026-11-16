# S-F28 — the drawn-root repair: exact source, exact wording, and what it does NOT say

Written because a patch decision rests on this. Everything below is quoted from the file as committed, not
paraphrased. If a word here differs from the file, the file wins.

## 1. Where the text comes from

| item | value |
|---|---|
| branch | `handoff/fable-opus-combo29-all-20261114` |
| commit | `511d334fdb5b7c4dc5f6cdc4222b694465fb37c8` ("Opus to swarm, file 4: pins default regime, sums S14", 2026-11-16T20:54:51-08:00) |
| file | `forge-combo29/soak_all/FABLE_TO_swarm_3.md` |
| git blob | `8b668cd5c125ab024e5495baa5a82fb9e478e4eb` |
| sha256 of content | `cefd84fb2accedfaa08695fce5d4a75ea9134ce94aea1d9dc5b3df5e14b717c3` |
| lines of interest | 13–18 (of 29) |
| base commit it refers to | **`6b98f217`** — named in line 13 as "the base tree 6b98f217" |

The commit fetched contains file **4** as the newest (`FABLE_TO_swarm_4.md`); file 3 is what carries the drawn-root
text and is unchanged in that commit. File 4 adds only the pins-vs-sums regime clarification and repeats nothing
about the drawn root.

## 2. The passage, verbatim (lines 13–18)

```
- A drawn root on the base tree 6b98f217 (third occurrence, or halfmove counter 100 or more): the engine searches 0
  nodes and plays its first legal move, even with a mate on the board (seats 01, 20, 27, 28). On the owner's PC this
  is REPAIRED since 15 November: the PC's engine searches such a root like any other (only a root with insufficient
  material is still answered at once). It also needs a THIRD occurrence: a second one is searched normally
  (`Board::is_repetition`, `matches >= 2`). Seat 20's "the repetition door stays open" is covered by that repair.
  A patch for the base tree is not needed.
```

## 3. What it says, word by word — and what it does not

It **does** say, in these exact words:
1. "On the owner's PC this **is REPAIRED since 15 November**" — a positive statement, with a date.
2. "the PC's engine **searches such a root like any other**" — the repair's content.
3. "**only a root with insufficient material is still answered at once**" — one named exception, so the repair is
   not absolute.
4. "**Seat 20's 'the repetition door stays open' is covered by that repair.**" — it addresses my S-F13 by name.
5. "**A patch for the base tree is not needed.**" — an explicit instruction not to patch.

It **does not** say:
- that a patch would be *harmful* — only that it is not needed;
- that the PC's engine and the base tree are otherwise identical, or that the repair's source is in this repository
  (the repair itself is not shown to me, and I have no file or commit for it);
- that seat 01's patch is *wrong* for the base tree — my S-F13 measured what that patch does **to 6b98f217**, and
  that measurement is unaffected by the PC having a different repair.

## 4. The narrow reading I stand behind (and the wide one I do not)

- **Wide (mine, from before):** "the repetition door is open" as a live defect. **Withdrawn for the PC.** Per the
  quoted text the PC does not have it.
- **Narrow (still true):** on the base tree `6b98f217`, removing only the halfmove term from `root_drawn` leaves the
  repetition term live — I built that patched binary, its pins were unchanged, and a third-occurrence mate-in-1
  still answered `f2f3`/`cp 0`/0 nodes (`job7/CHECK_s28F4.md`, `job7/halfmove_control_out.txt`). That is a
  statement about a specific patch applied to a specific commit, not about the owner's engine.

**Recommendation to the coordinator: hold the patch off, exactly as you have told the owner.** Nothing in my work
supports sending it, and Opus says plainly it is not needed. My S-F13 is worth keeping only as the reason one should
not assume that patch is sufficient if anyone ever patches the base tree for another purpose.

## 5. Independent consistency check (in my favour, and it is a real check)
Opus's "It also needs a THIRD occurrence: a second one is searched normally" matches what my own construction did
before I read their file: in `job7`, the **second** occurrence (ply 4) searched normally — `d1d8`, `mate 1`,
168 nodes — and only the **third** (ply 8, `is_repetition(3)` true) collapsed to `f2f3`, `cp 0`, 0 nodes. Two
independent routes to the same rule.

## 6. How to check every claim in this file
```
git fetch -q --depth 1 origin handoff/fable-opus-combo29-all-20261114
git rev-parse FETCH_HEAD                                   # 511d334f...
git rev-parse FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_3.md   # 8b668cd5...
git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_3.md | sha256sum  # cefd84fb...
git show FETCH_HEAD:forge-combo29/soak_all/FABLE_TO_swarm_3.md | sed -n '13,18p'
```
