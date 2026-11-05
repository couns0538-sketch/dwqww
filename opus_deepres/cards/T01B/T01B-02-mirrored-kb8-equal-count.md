# T01B-02: king-map shape at an equal count - horizontally mirrored KB8 vs the unmirrored rank4x2 map
Status: COMPLETE

## Source
- Stormphrax PR 166 "net032 (L1 1536, horizontally mirrored)": https://github.com/Ciekce/Stormphrax/pull/166
- Obsidian commit d8e8007f (2024-03-24, "2x(4x768 -> 768) -> 8x1, with horizontal mirroring"):
  https://github.com/gab8192/Obsidian/commit/d8e8007f151b341789ff66e6faaaa88256ce8ec5
- Leorik devlog (forum text, 2025-12-27): https://talkchess.com/viewtopic.php?p=987095
- Every arch line read (Stormphrax PR 237 704x16hm; Viridithas, Integral, bullet example in notes/T01) is mirrored.

## Licence
Stormphrax GPL-3.0 at 3ff4e1a02a, Obsidian GPL-3.0 at d8e8007f15 (tools/licence_at.py) = ideas only; PR text and
commit message read, never source. Forum post: text only, no repo read.

## Mechanism
When a perspective's own king stands on files e-h, that perspective's whole board is reflected left-right before the
bucket lookup and feature indexing, so the map only has to cover files a-d and the net learns each pattern once for
both wings. At an equal bucket count every bucket then covers half as many king squares (finer shape for free). Cost: a
full accumulator refresh when the own king crosses between files d and e (the king starts on e: kingside castling
stays on e-h, queenside castling crosses once; the refresh cache absorbs repeats).

## Forge fit
`bash tools/forge_has.sh 'king.?bucket|kbucket|mirror'` = 0 hits (the lock has no king buckets). v2 already carries
it: FORGENN2 flag bit 1 = mirror (opus_30h/a/o30_v2net.py:16, :31), engine "king buckets 1-32 + mirror" (v2port.patch,
forge-o30-v2net skill), trainer argument mirror 0|1 (forge_v2_bullet_o30/src/main.rs:214, :280), import / export
--mirror (import_v2r.py:33, export_v2r.py:43). Lacks a mirrored net: from-lock writes unmirrored maps only (o30_v2net.py:6-8,
exact lock warm start) and the forge-o30-v2net skill names only unmirrored rank maps for the 30-h runs. Own shape for the A/B:
mirrored KB8 = rank groups 1 / 2 / 3-4 / 5-8 (as rank4x2) x file pairs a-b / c-d on the a-d half. Start: the lock
weights written into it = exact for kings on a-d, the lock on the reflected board for kings on e-h (approximate).
Change: one map name in the trainer (main.rs:222-249) + o30_v2net.king_map, a from-lock --mirror writer.

## Expected gain
No source isolates mirroring at an equal bucket count and L1. Stormphrax PR 166 (with L1 1536): 25k nodes +34.97 +-
9.51 (2,522 g), STC 8+0.08 -4.84 +- 4.02 (9,190 g, FAILED [0,3]), LTC 40+0.4 +4.90 +- 2.91 (14,550 g, LLR 2.89 [0,3]).
Obsidian d8e8007f (4 mirrored buckets, L1 768, 8 output buckets; "25% speedup", old net had "the 150MB table"): STC
10+0.1 +10.18 +- 5.92 (6,898 g, LLR 2.91 [0,3]). Leorik: "+20 Elo" with "nps goes down by 10%", no TC / games / error.
No book named anywhere. Counterpoint (forum, https://talkchess.com/viewtopic.php?p=954027): 64 unmirrored king
squares vs 32 mirrored "not even 1 Elo on UHO", mirrored HalfKA "basically nil" (no TC / games) - at that fine
resolution mirroring only halves the weights; our case is the reverse (equal count, finer shape).
Forge estimate: 0 to +2 Elo over the unmirrored KB8 net of the same recipe, before the d/e refresh cost (nps
unmeasured) **UNPROVEN**.

## Effort
Crew ~2-3 h (map name, writer, random mirrored KB8 checks, packaging). GPU: 2 warm-start runs of the 30-h recipe (lr
2e-5, 200 SB, ~13-15 min each): mirrored KB8 and an unmirrored back-rank arm (rank 1: 4 file pairs, rank 2: 2 halves,
ranks 3-4: 1, ranks 5-8: 1 = 8 buckets, own shape, exact lock start), control = KB8 run 5. CPU: STC + LTC SPRT ~13 h each.

## Test plan
Offline: score the approximate mirrored start itself (S31 + jobA vs the lock = the warm-start penalty), then each arm
vs KB8 run 5 paired beyond the ~4e-6 seed noise, plus the lock rule (S31 >= 2e-5 below, jobA z <= +2). Pre-gate: OFF
pins (EvalFileV2 empty); a random mirrored KB8 net: parity 10000/10000, incremental == refresh walk with d/e crossings,
verify build; nps ABBA of both nets on one fixed move sequence. Gate: UHO SPRT [0,5] at STC, then LTC, against the
identical-eval v2 control (-20.9 +- 18.5, sanity only).

## OFF-by-default design
No new option or code path in the engine: flag bit 1 and the 64-entry map come from the file under `EvalFileV2`
(empty = off = the lock's compiled net and code path, bench pins unchanged); unmirrored files behave as today.
