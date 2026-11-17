# REPORT job12 — a TEXT PATCH for 21-F8 (`fullmove 0` refused), seat 21

**What was asked.** The brief's area 7 rule for a repair: a TEXT PATCH only (unified diff
against 6b98f217, file ending `.patch.txt`, applying with `patch -p1` without fuzz) and the
honesty numbers unchanged with the patch applied. 21-F8 is the one engine defect in my area
whose repair is unambiguous, so this job does it.

**The answer.** `fullmove0_accept.patch.txt` changes two lines of
`forge-combo29/src/board.cpp` so that a FEN with `fullmove 0` is ACCEPTED (a value FEN
writers emit and python-chess treats as valid) while a NEGATIVE fullmove is still refused,
and the stored counter keeps a floor of 1 so the engine never records a fullmove number of 0.
Verification: the fault is fixed, six negative controls still refuse, 6,073 real positions are
still all accepted, perft 2 on 200 G positions still matches python-chess, and all four
honesty numbers are unchanged.

**How sure.** High. The patch applies to a clean copy of 6b98f217 with `patch -p1` and no fuzz
(`DRY RC=0`, then applied and byte-identical to the build that was measured), and the honesty
numbers were measured on that same build.

## My own first attempt was WRONG, and my negative control caught it

Removing the `fullmove < 1` test outright also accepts `fullmove -1`. My verification script's
`NEG fullmove_-1` row reported `ACCEPTED (REGRESSION)` and the script printed
`PATCH NOT VERIFIED`. The final patch tests `fullmove < 0` instead and clamps the stored value,
so `-1` is refused and `0` is accepted. The first attempt and its failure are in the git
history of `job12/`; the record is not edited to hide it.

## The patch

```
--- a/forge-combo29/src/board.cpp
+++ b/forge-combo29/src/board.cpp
@@ -264,7 +264,7 @@
     if (rank != 0 || file != 8 || kings[White] != 1 || kings[Black] != 1 ||
-        (side != "w" && side != "b") || halfmove < 0 || fullmove < 1) {
+        (side != "w" && side != "b") || halfmove < 0 || fullmove < 0) {
@@ -349,7 +349,8 @@
-    candidate.fullmove_ = static_cast<std::uint16_t>(std::min<long long>(fullmove, 65535));
+    candidate.fullmove_ = static_cast<std::uint16_t>(
+        std::min<long long>(std::max<long long>(fullmove, 1), 65535));
```

## Honesty numbers, patched build vs the base build

| command | expected | base build | patched build |
|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 |
| bench 13 | 862329 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 | 4865609 |

Base sha256 `e06310ec…6a83`; patched sha256 `d3104f44…2603`. Raw: `job12/honesty_base.txt`,
`job12/honesty_patched.txt`.

## Verification (pasted from `job12/out/summary.md`)

| case | base | patched | python-chess legal moves | verdict |
|---|---|---|---|---|
| A_fullmove0 | refused=True nodes=20 | refused=False nodes=15 | 15 | FIXED |
| B_fullmove0_game | refused=True nodes=20 | refused=False nodes=30 | 30 | FIXED |
| NEG fullmove_-1 | – | refused=True nodes=20 | – | still refused (good) |
| NEG halfmove_-1 | – | refused=True nodes=20 | – | still refused (good) |
| NEG three_fields | – | refused=True nodes=20 | – | still refused (good) |
| NEG nine_in_rank | – | refused=True nodes=20 | – | still refused (good) |
| NEG two_kings | – | refused=True nodes=20 | – | still refused (good) |
| NEG ep_wrong_rank | – | refused=True nodes=20 | – | still refused (good) |
| E base: refusals over 6,073 real FENs | | 0 | | reference |
| E patched: refusals over 6,073 real FENs | | 0 | | same as base |
| F perft 2 on 200 G positions, patched vs python-chess | | 0 mismatches | | ok |

`=> PATCH VERIFIED`

## Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| build a patched copy outside the work tree | done | `/tmp/patched_tree`, `~/b/patched` | builds clean |
| honesty with the patch | done | `honesty_patched.txt` | 4/4 unchanged |
| fault fixed, with a control | done | `out/summary.md` A/B | 15 and 30, not the stale 20 |
| negative controls | done | `out/summary.md` NEG rows | 6/6 still refused |
| no stricter parsing on real positions | done | `out/summary.md` E | 0 refusals both builds |
| perft 2 regression on 200 G positions | done | `out/summary.md` F | 0 mismatches |
| patch applies with `patch -p1`, no fuzz | done | `fullmove0_accept.patch.txt` | dry run RC 0, then clean |

## Findings

No new finding; this is the repair for 21-F8. It does NOT repair 21-F9 (the halfmove ≥ 100
root shortcut), which is a different and more consequential fault, and 30-F8 already shows
that the naive fix for that one trades a missed mate for a missed draw — so I did not touch it.

## Suspicions, not proven

- Whether the owner *wants* `fullmove 0` accepted. The patch assumes yes, because python-chess
  accepts it and FEN writers emit it. If the owner prefers strict refusal, this patch should
  not be applied; the finding (21-F8) stands either way.

## What I did NOT do

- Did not repair 21-F9 or 21-F2.
- Did not run the patched build under ASan+UBSan (it is a two-line parser change and I changed
  no memory ownership; the base sanitizer evidence stands for the surrounding code, but this
  patch itself is not sanitizer-tested).
- Did not run a node-count bench on the patched build at any other depth.

## What I am NOT sure about

- Whether accepting `fullmove 0` and clamping it to 1 changes any engine behaviour that reads
  the fullmove number. I searched no consumer of `fullmove_number()`; the honesty numbers are
  identical, which is evidence but not a proof that nothing reads it.

## Times

see `job12/stamps.txt`.

## Last command's output

```
$ git status --short
(clean)
$ ls job12
fullmove0_accept.patch.txt  honesty_base.txt  honesty_patched.txt  honesty_patch.sh  out  stamps.txt  verify_patch.py
```
