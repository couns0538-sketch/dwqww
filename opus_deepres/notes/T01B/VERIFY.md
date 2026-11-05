# T01B verify (adversarial pass; start 01:16 PC clock, stop by 01:36)

Scope: cards/T01B/*.md (2 full cards + the T01B-03 MERGED stub = TABLE row 5), notes/T01B/{TABLE,sources,licences}.md.
Method: every cited source number re-opened (gh api commit / PR text, forum pages fetched live), Elo recomputed from
W/L/D where given; licence rows re-run; lock greps re-run and cited lines read; v2 file lines read in the worktree
D:/o30/wt (HEAD 32bb47cb); Forge-side numbers traced to the forge-o30-v2net skill and D:/o30/FINAL_REPORT.md;
duplicates checked against `ls cards/*/` and notes/TRIED_GATES.md. Scratch F:/odr/work/T01B-verify/ (no files needed).
Elo recompute: score = (W + D/2) / N, Elo = 400 log10(score / (1 - score)).

## Card T01B-01 (pairwise clipped product instead of SCReLU)
| card | claim | verdict | evidence |
|---|---|---|---|
| T01B-01 | Obsidian beaa1374 "pairwise CReLU instead of SCReLU": STC 6+0.06 1 thread 16 MB +3.18 +- 2.10, 29,514 g, penta 138/3441/7356/3657/165, LLR 2.90 [0,2.5], "false tc due to broken nps" | CONFIRMED | gh api commit message; W/L/D 7604/7334/14576 -> score 0.50457 -> +3.18 recomputed; TC / Threads / Hash / LLR / bounds / penta identical |
| T01B-01 | lower 95 % bound ~+1.1 | CONFIRMED | 3.18 - 2.10 = 1.08 |
| T01B-01 | Obsidian hidden size at beaa1374 not stated; 1280 at 132e8653 (STC -5.01 +- 5.23, LTC +0.04 +- 5.02) | CONFIRMED | beaa1374 message has no size; 132e8653 message read ("now it is 1280", both numbers identical) |
| T01B-01 | "the later 62f32032 arch is not named" | UNVERIFIABLE | commit not re-opened in the window (secondary; sources.md row 3) |
| T01B-01 | Stormphrax PR 183 "pairwise mul support": no body, no test | CONFIRMED | gh api body = null |
| T01B-01 | Stormphrax PR 237: (704x16hm->1792)x2 layer stack, pairwise CReLU -> CSReLU -> CReLU; LTC 40+0.4 +22.69 +- 6.51 (2,730 g); STC +8.15 +- 5.10 [-3,1]; 25k +41.04 +- 2.23 (40,062 g); confounded | CONFIRMED | PR text; LTC W/L/D 740/562/1428 -> +22.68 recomputed; the PR also lists a DFRC 25k +41.26 +- 4.47 (not cited, fine) |
| T01B-01 | licence Obsidian beaa13742e GPL-3.0; Stormphrax 41f435dd88 GPL-3.0 (= PR 237 merge sha) | CONFIRMED | tools/licence_at.py --row re-run 8/8 identical to notes/T01B/licences.md; 41f435dd88 = merge_commit_sha of PR 237 |
| T01B-01 | forge_has 'pairwise\|crelu\|screlu' = 1 hit include/forge/nnue.hpp:11 | CONFIRMED | re-run: 1 hit; line 11 read = the SCReLU architecture comment |
| T01B-01 | v2port.patch:21 SCReLU; trainer main.rs:316-317, 407-408 screlu(); nothing pairwise | CONFIRMED | lines read in D:/o30/wt/opus_30h/a (HEAD 32bb47cb) |
| T01B-01 | from-scratch KB4 at 1.46G positions S31 +7.7e-4 (worse than the lock) | CONFIRMED | D:/o30/FINAL_REPORT.md:162 (+7.72e-4), skill line 92 |
| T01B-01 | own recipe lr 1e-3 cosine to 1e-5, WDL 0.4, 700 SB = 11.7G positions, ~70 min at 2.8-3M pos/s | CONFIRMED (own values, not another engine's) | FINAL_REPORT.md:150 (r1_kb4 "1e-3 cosine to 1e-5", 1 h 10 m, 2.78M pos/s), :236; skill lines 81-82; WDL 0.4 = opus_30h/PLAN.md:107 and a/queue_runner.sh:10 |
| T01B-01 | seed noise ~4e-6; lock rule S31 >= 2e-5 below the lock and jobA z <= +2; control -20.9 +- 18.5 | CONFIRMED | FINAL_REPORT.md:375, skill line 56, WORKER_RULES Round 2 |
| T01B-01 | "the integer path's magnitude bounds carry over" | CORRECTED | Forge's lock and v2 paths accumulate in float32 (WORKER_RULES Forge facts; nnue.hpp:20 WeightScale 4096 as float); the bound remark itself holds; card text annotated "(corrected by verify: ...)" |
| T01B-01 | reading rule / own constants | CONFIRMED | only commit messages and PR text of GPL repos named (sources.md rows 1-4); flag bit 2 and the 128/128 halves are marked own choice; no foreign constant, no code |
| T01B-01 | duplicate check | CONFIRMED none | grep 'pairwise' over cards/*/ hits only T01-01 (bullet recipe context, threats card); TRIED_GATES.md: 0 hits for pairwise / crelu / mirror / bucket / factor |

## Card T01B-02 (mirrored KB8 at an equal count)
| card | claim | verdict | evidence |
|---|---|---|---|
| T01B-02 | Stormphrax PR 166 "net032 (L1 1536, horizontally mirrored)": 25k +34.97 +- 9.51 (2,522 g); STC 8+0.08 -4.84 +- 4.02 (9,190 g, FAILED [0,3]); LTC 40+0.4 +4.90 +- 2.91 (14,550 g, LLR 2.89 [0,3]) | CONFIRMED | PR text (tests 7178-7180); recomputed: 885/632/1005 -> +34.97; 2241/2369/4580 -> -4.84 (LLR -2.29); 3593/3388/7569 -> +4.89 |
| T01B-02 | Obsidian d8e8007f "2x(4x768 -> 768) -> 8x1, with horizontal mirroring": STC 10+0.1 +10.18 +- 5.92 (6,898 g, LLR 2.91 [0,3]); "25% speedup"; "150MB table" | CONFIRMED | commit message; 1900/1698/3300 -> +10.18 recomputed; author: "10 Elo STC despite 25% speedup" |
| T01B-02 | Leorik forum post 2025-12-27: mirroring "+20 Elo", "nps goes down by 10%", no TC / games / error; 5-bucket edge / centre map; hidden 640; ~30 Elo for all NNUE changes; 1B FRC positions | CONFIRMED | https://talkchess.com/viewtopic.php?p=987095 fetched live: all quotes verbatim; the map printed in the post = rank 1 edge (a,b,g,h) / centre, ranks 2-3 the same split, ranks 4-8 one bucket |
| T01B-02 | counterpoint p=954027: Berserk's author 64 squares vs 32 mirrored "not even 1 Elo on UHO"; Ethereal's author mirrored HalfKA "basically nil", gains from speed-ups, merging a7/a8/b7/b8 "Can't know without trying it"; third poster "pretty much 0", endgame concern | CONFIRMED | fetched live, quotes verbatim (posts 2023-10-27/28); nuance: the first poster adds "it's been a long time since that test, so it may not be accurate anymore" (the card says "old test") |
| T01B-02 | "No book named anywhere" (sources) | CONFIRMED | no book in the PR / commit texts; UHO appears only in the forum counterpoint, as the card says |
| T01B-02 | licence Stormphrax 3ff4e1a02a (= PR 166 merge sha), Obsidian d8e8007f15, both GPL-3.0 | CONFIRMED | licence_at re-run identical; 3ff4e1a02a = merge_commit_sha of PR 166 |
| T01B-02 | forge_has 'king.?bucket\|kbucket\|mirror' = 0 hits | CONFIRMED | re-run: 0 hits |
| T01B-02 | v2 has the mirror flag but no mirrored net: o30_v2net.py:16 (bit1 mirror), :31 (FLAG_MIRROR = 2), :6-8 (from-lock exact only unmirrored), :47-59 (maps one / rank4 / rank4x2 / rank4x4 / rank4x8); main.rs:214 (mirror 0\|1), :222-249 (map match), :280 (mirror arg); import_v2r.py:33, :37; export_v2r.py:43 | CONFIRMED | every cited line read in D:/o30/wt/opus_30h/a (HEAD 32bb47cb); line numbers match |
| T01B-02 | warm-start recipe lr 2e-5, 200 SB, ~13-15 min; control = KB8 run 5; KB nps 0.988x / 0.969x / 0.942x of KB4; seed noise ~4e-6 | CONFIRMED | skill lines 94-97, 114; FINAL_REPORT.md:241, :288-289, :375 |
| T01B-02 | castling remark (kingside stays on e-h, queenside crosses d/e once) | CONFIRMED | own reasoning, correct for standard chess (e1->g1 stays in e-h; e1->c1 crosses) |
| T01B-02 | "every arch line read ... is mirrored" | CONFIRMED | notes/T01/sources.md rows 3, 11, 12: 704x16hm / 768x16hm (hm = horizontally mirrored) |
| T01B-02 | duplicate check | CONFIRMED none | T01-04 = KB16 count + halfmove-clock inputs (different lever); T05E-01 = HalfKA refresh cache (mirror flips only as a refresh cause); T06C-02 names mirroring as a confound; TRIED_GATES.md 0 hits |

## Stub T01B-03 = TABLE row 5 (factorised king buckets)
| card | claim | verdict | evidence |
|---|---|---|---|
| T01B-03 / row 5 | PlentyChess PR 202 "NNUE with factorised king buckets": STC 8+0.08 +2.84 +- 2.08 (30,054 g, LLR 2.90 [0,3]); no LTC | CONFIRMED | PR text; 7282/7036/15736 -> +2.84 recomputed; the PR body carries only this one test |
| T01B-03 / row 5 | Viridithas v99 25k nodes +7.81 +- 4.08 (11,082 g) | UNVERIFIABLE here | traced only to notes/T01/sources.md row 11 (release text, CC0; "whole-network factorisation", i.e. not a king-bucket-only factoriser); the release page was not re-opened in the window |
| T01B-03 / row 5 | licence PlentyChess 9686668c65 (= PR 202 merge sha) GPL-3.0 | CONFIRMED | licence_at re-run; 9686668c65 = merge_commit_sha of PR 202 |
| T01B-03 / row 5 | 0 hits for "factor" in forge_v2_bullet_o30/src/main.rs and o30_v2net.py | CONFIRMED | grep -c = 0 / 0; also forge_has 'factori' = 0 hits in the lock |
| T01B-03 / row 5 | bullet 3_input_buckets.rs (MIT): 10 mirrored back-rank-heavy buckets, hidden 1024 SCReLU, 8 material output buckets, zero-start factoriser merged at save | CONFIRMED | D:/o30/bullet/examples/progression/3_input_buckets.rs lines 20, 26, 28-39, 44-51, 61-67, 73 (MIT, reading allowed) |
| T01B-03 / row 5 | local bullet copy = da426a49 | UNVERIFIABLE | no git metadata printed for D:/o30/bullet; the id comes from notes/T01/sources.md row 1 |
| T01B-03 | MERGED stub format | CONFIRMED | card_lint accepts it (0 findings); the row cites the retired card's numbers in full |

## Notes and licences
| item | verdict | evidence |
|---|---|---|
| notes/T01B/licences.md 8 rows | CONFIRMED | all 8 `tools/licence_at.py OWNER/REPO SHA --row` re-runs print identical rows (GPL-3.0 at every commit) |
| TABLE.md row 6 / section C: Stormphrax PR 177 (16 buckets + L1 1280) 25k +9.01 +- 4.66 (10,110 g), STC 8+0.08 +13.72 +- 5.42 (5,296 g, LLR 2.92 [0,3]), "tests predate cutnode lmr" | CONFIRMED | PR text re-opened (tests 7459 / 7460); 1456/1247/2593 -> +13.72 recomputed |
| TABLE.md section C: Stormphrax PR 341 (pawn pairs) 25k +6.36 +- 3.82 (15,470 g), STC +2.08 +- 1.67 (57,208 g, LLR 2.92 [0,3]), LTC 40+0.4 +3.09 +- 2.15 (25,524 g, LLR 2.94 [0,3]), together +10.54 +- 4.61 | CONFIRMED | PR text re-opened (tests 14231 / 14233 / 14234); 14385/14042/28781 -> +2.08 recomputed |
| TABLE.md row 10 / section C: PlentyChess PR 400 (threats, L1 1792 -> 640) 20k +45.49 +- 2.23 (40,034 g), STC 8+0.08 -3.08 +- 2.89 (15,354 g, LLR -2.26 FAILED [0,2.5]), LTC +1.78 +- 1.37 (58,474 g, LLR 2.90 [0,2.5]) | CONFIRMED | PR text re-opened; 3823/3959/7572 -> -3.08 recomputed; the 20k row's game count (40,034) is not in the TABLE (no error) |
| TABLE.md row 9: Obsidian 8361be0d output buckets STC 8+0.08 +6.30 +- 4.50 (11,640 g) | CONFIRMED | commit message re-opened; 3075/2864/5701 -> +6.30 recomputed |
| TABLE.md rows 8, 11, 12 (part), 13 and section C remainder (SP PR 198 / 239 / 291 / 293, PC PR 183 / 256) | UNVERIFIABLE here | not re-opened in the 20-minute window (no T01B card rests on them) |
| TABLE.md section B Forge rows (304,999,573 rows; KB8 0.988x, KB16 0.969x, KB32 0.942x; gate exe + KB8 soup 0.893x, + KB32 soup 0.849x) | CONFIRMED | skill lines 61, 97, 117; FINAL_REPORT.md:288-289 |
| sources.md cap bookkeeping: 9 sources, 2 forum threads, stop after 2 no-card sources | CONFIRMED | rows 8 and 9 = "no new card"; <= 15 sources, <= 5 threads, 3 engines deep-read (Stormphrax, Obsidian, PlentyChess) |
| names (no vendor / model-company names) | CONFIRMED | card_lint name check 0 findings; own grep over cards/T01B and notes/T01B clean (grok-pc only) |
| card count <= 4, crew hours, UNPROVEN labels, gate routes | CONFIRMED | 3 files; crew ~6-8 h / ~2-3 h / 2-3 h; every Forge estimate labelled UNPROVEN; both routes UHO SPRT [0,5] STC then LTC vs the v2 control |
| writes outside the track | CONFIRMED none seen | hand-back lists only cards/T01B, notes/T01B and F:/odr/work/T01B (empty) |

## Verdict
- Violations: none found. Duplicates: none. Corrections: 1 (T01B-01 wording, float32 not integer path).
- Unverifiable in the window: Obsidian 62f32032 arch wording; Viridithas v99 release number (traced to T01 row 11 only);
  bullet local copy id da426a49; TABLE rows 8, 11, 12 (Ob 132e8653 confirmed, the rest not), 13 and the section C
  numbers of SP PR 198 / 239 / 291 / 293 and PC PR 183 / 256 (no T01B card rests on them).
- Counts (table rows above): 44 checked, 39 confirmed, 1 corrected, 4 unverifiable, 0 violations, 0 duplicates.
- Lint: `card_lint.py cards/T01B/*.md` re-run after the correction = 0 findings, 0 PENDING in all 3 files; T01B-01 is
  57 lines. Verify finished 01:25 PC clock (clock read in the same step).

## Continuation (second verifier; start 01:31 PC clock, writing at 01:34, stop by 01:51)
Scope: only what the first pass left unverifiable, plus the task's checks 4-6 re-run. Same method and Elo recompute.
| card / note | claim | verdict | evidence |
|---|---|---|---|
| T01B-01 / sources row 3 | Obsidian 62f32032 "New NNUE architecture": arch not named; STC -3.96, 25k +23.34 | CONFIRMED | gh api commit message (2024-05-10): no arch named; STC 8+0.08 -3.96 +- 4.80 (10,006 g, LLR -1.81 [0,2.5]); 25k +23.34 +- 8.10 (4,354 g); 2438/2552/5016 -> -3.96 recomputed |
| sources row 3 | Obsidian d89064ed 2025-01-24 LTC +7.73 +- 3.35 (9,482 g, [0,2.5]), arch not named | CONFIRMED | commit message; 2417/2206/4859 -> +7.73 recomputed |
| TABLE row 13 / sources row 2 | SP PR 198 net038 "first net on the regenerated dataset" STC +47.53 +- 10.30 (1,574 g) | CONFIRMED | PR text (test 8843): 8+0.08, Threads 1, Hash 32 MB, LLR 2.92 [0,3]; 517/303/754 -> +47.5 recomputed; merge 8c2d228eb2 |
| TABLE row 11 / sources row 4 | SP PR 239 dual activation: STC +6.20 +- 3.44 (12,046 g), LTC +12.05 +- 4.69 (5,076 g); "duplicate L1 pre-activations, square one side, clip both, concat" | CONFIRMED | PR text (tests 10932 / 10933); 3178/2963/5905 -> +6.20 recomputed; the PR also lists 25k +6.95 +- 3.88 (12,744 g), not cited (fine); merge 880a021a46 |
| TABLE section B / C, sources row 8 | SP PR 291 split accumulators STC +9.04 +- 4.10 (7,652 g) | CONFIRMED | PR text (test 13389); 1892/1693/4067 -> +9.04 recomputed; merge df22d41c9f |
| TABLE section B / C, sources row 8 | SP PR 293 threats (704x16hm+60144->640)x2->(32x2->32->1)x8, L1 1792 -> 640, L2 16 -> 32, no king threats: 25k +33.51 +- 9.35 (2,600 g), STC +2.73 +- 2.07 (37,524 g), LTC +9.85 +- 4.24 (6,736 g), 20+0.2 4 threads +13.03 +- 4.94 (5,042 g) | CONFIRMED | PR text (tests 13390-13392, 13395); 9853/9558/18113 -> +2.73 recomputed; merge e4b88b7a67 = licences.md row 6 |
| TABLE row 8 / sources row 5 | PC PR 183 King Buckets STC +17.07 +- 7.64 (3,932 g); finny tables STC +10.04 +- 5.65 (6,300 g) | CONFIRMED | PR text (tests 566 / 559), 8+0.08 [0,3]; 1069/876/1987 -> +17.07 and 1462/1280/3558 -> +10.04 recomputed; merge 69e3f025b6 |
| TABLE row 6 + section C / sources row 5 | PC PR 256 net 0058r "7 factorised king buckets": 0058-320 vs 0057r STC +4.96 +- 2.96 (15,006 g) LTC +3.95 +- 2.52 (18,018 g); 0058 vs 0058-320 STC +4.46 / LTC +4.46; 0058r vs 0058 STC +5.17 / LTC +9.22 | numbers CONFIRMED; qualifier CORRECTED | PR text (tests 4749-4765); 3775/3561/7670 -> +4.96 recomputed; LTC Hash 64 MB; merge ec2edf14c3. The "(with more training)" / "+ longer training" qualifier attached to the +4.96 / +3.95 pair is not in the PR text: the longer-training step is the separate pair 0058 vs 0058-320 (+4.46 / +4.46); what else differs between 0057r and 0058-320 is not stated - "confounded" stands, "more training" does not; annotated at the end of TABLE.md |
| licences.md rows 5, 8 | eea6168441 = SP PR 341 merge; fbc64b5ba8 = PC PR 400 merge | CONFIRMED | gh api merge_commit_sha, merged 2026-06-13 / 2025-10-12 |
| check 4 | notes/TRIED_GATES.md: packa, packb, E3, Sf26Bundle, CorrHistPlus, SingularV2 vs the T01B cards | CONFIRMED no duplicate | tools/tried_gates.py --grep: 32 rows, all search-side or eval post-processing options (NonPawnCorr, ReSearchAdjust, EvalMatScale/Optimism/Rule50Damp, Sf26Bundle, CorrHistPlus), no SingularV2 row at all; --grep 'pairwise\|crelu\|mirror\|bucket\|factor\|KB[0-9]\|v2\|net' = 23 rows, all net-file (EvalFileHalfKA) or search gates, none a pairwise / mirrored / factorised net |
| check 5 | duplicates against all cards (ls cards/*/: 85 files, T04I / T04J / T04L / T04N empty) | CONFIRMED none | grep mirror / pairwise / factoris over cards/*/ hits only T01-01, T01B-01, T01B-02, T05E-01, T06C-02 (assessed in the first pass) |
| check 6 | 3 files (<= 4); T01B-01 and T01B-02 57 lines each, stub 1 line; crew hours; UNPROVEN labels; names | CONFIRMED | card_lint re-run at 01:34: 0 findings, 0 PENDING in all 3; vendor / model-company grep over cards/T01B + notes/T01B clean |
| T01B-03 / TABLE row 5 | Viridithas v99 25k nodes +7.81 +- 4.08 (11,082 g) "(fixed nodes only)" | number CONFIRMED; qualifier CORRECTED | viridithas-networks release v99 (2025-05-18, CC0 release text, gh api): "fresh retrain using whole-network factorisation", 25k +7.81 +- 4.08, LLR 2.99 [0,3], 3261/3012/4809 -> +7.81 recomputed; the release ALSO lists LTC 40+0.4 Threads 1 Hash 128 MB +2.06 +- 1.61 (47,132 g, LLR 2.96 [0,3]) - so not "fixed nodes only"; confounded with the retrain and a whole-network (not king-bucket-only) factoriser, so the row 5 verdict (row only, cheap offline A/B) stands; annotated at the end of TABLE.md |
| T01B-01 / sources row 7 | local bullet copy D:/o30/bullet = da426a49 | CONFIRMED by file identity | no git metadata in D:/o30/bullet, but examples/progression/3_input_buckets.rs (103 lines) and Cargo.toml fetched at da426a49b2 (gh api contents, MIT) are byte-identical to the local copies (diff -q); id itself from notes/T01/licences.md row 1 (jw1912/bullet da426a49b2 2026-10-26 MIT) |

## Continuation (third verifier; start 01:39 PC clock, written at 01:41, stop by 01:54)
Scope: only what passes 1-2 left open (TABLE rows 2, 7, 9, section B traces, sources row 1 titles), check 2 for T01B-02
(pass 1 recorded it for T01B-01 only), the annotations' presence on disk, lint. Same method and Elo recompute.
| card / note | claim | verdict | evidence |
|---|---|---|---|
| TABLE row 7 | SP commit 12ddec9f "support networks with merged king planes", no test | CONFIRMED | gh api commit 12ddec9f63: message = title "(#179)" + "Bench: 5554869" only; PR 179 body length 0 |
| TABLE row 7 | V PR 221 merged king planes non-regression +0.29 +- 1.74 ([-3,0]) | CONFIRMED | gh api PR text: 2+0.02 Threads 1 Hash 16 MB, LLR 2.95 [-3,0], 60,412 g; 16996/16945/26471 -> +0.29 recomputed; merge 1aa7a0e3 = notes/T01 row 8 |
| TABLE row 7 | "768 per bucket (o30_expand_kb.py:27)" | CONFIRMED | D:/o30/wt/opus_30h/a/o30_expand_kb.py:27 counts = [kb * 768 * h, ...] |
| TABLE row 9 | OB8 at o30_expand_kb.py:23 | CONFIRMED | line 23 = BUCKETS = 8 |
| TABLE row 2 | V v92 LTC +9.44 +- 4.12 (from notes/T01 row 11) | CONFIRMED | viridithas-networks release v92 "hyperstition" (2024-08-09, CC0 text, gh api): 40+0.4 Threads 1 Hash 128 MB, LLR 2.98 [0,3], 7,028 g; 1661/1470/3897 -> +9.45 recomputed; arch 2048x2 -(pairwise)-> 16 -> 32 -> 1 = a layer stack, so row 2's "pairwise inside a new layer stack / no card" classification holds and T01B-01 rightly does not cite it |
| sources row 1 | SP PR titles: #71 "8 buckets 1024 L1", #179 merged king planes, #206 "return to 1536 L1", #246 sparse FT->L1 | CONFIRMED | gh api titles: "8 buckets, 1024 L1" (merged 2024-03-25), "support networks with merged king planes" (body empty), "return to 1536 l1", "compute FT -> L1 matmul in sparse blocks" |
| TABLE section B | rows traced to notes/T01 only: v61 963M / 768 no buckets, v84 1536 4 mirrored, v91 2048 + 16 buckets (T01 row 11); v107 1024 (T01 row 10); V PR 425 ~87 % speed (T01 row 3); V PR 445 pawn pairs (T01 row 4); I PR 266 +6 % merged accumulator (T01 row 6); I README "hundreds of millions" of games, L1 768 vs PR 266 1024 (T01 row 12) | CONFIRMED (trace only) | every item found verbatim in notes/T01/sources.md rows 3, 4, 6, 10, 11, 12; those release / PR / README pages were not re-opened here (v92 and PR 221 were) |
| TABLE row 4 | "no source compares shapes at an equal count (web search 00:49 found none)" | UNVERIFIABLE | a negative search result; not re-run (no card rests on it: row 4 is the own second arm inside T01B-02 without a source number) |
| T01B-02 / check 2 | reading rule, own words, no foreign constant, no code | CONFIRMED | lines 7-32 read: Mechanism in own words (reflection on files e-h, refresh on the d/e crossing); the only foreign numbers are the sources' logged test numbers and net sizes quoted as such; the KB8 shape, start weights and the warm-start recipe (lr 2e-5, 200 SB = 30-h job values, pass 1) are own; OFF design = no engine change, net file under EvalFileV2, gate vs the v2 control |
| corrections on disk | pass-1 and pass-2 annotations present | CONFIRMED | T01B-01 line 18 "(corrected by verify: ...)"; TABLE.md lines 63-64 verify notes (PR 256 qualifier, V v99 qualifier); card Status lines COMPLETE / COMPLETE / MERGED stub (no violation or duplicate to mark) |
| check 6 | lint, counts, lengths | CONFIRMED | card_lint re-run at 01:41: 0 findings, 0 PENDING in all 3 files; 57 / 57 / 1 lines; 3 files <= 4 cards |

## Final verdict (all three passes)
- Rows checked: 44 (pass 1) + 14 (pass 2) + 11 (pass 3) = 69. Pass 2 resolved all 4 pass-1 unverifiables (62f32032, V v99,
  bullet da426a49, TABLE rows 8 / 11 / 13 + section C PRs), so the final state is: 61 confirmed, 3 corrected (T01B-01 float32
  wording; TABLE row 6 / section C "more training" qualifier; TABLE row 5 "fixed nodes only" qualifier), 1 unverifiable
  (TABLE row 4 negative web search) plus the section-B traces confirmed at the notes/T01 level only, 0 violations, 0 duplicates.
- Every source number a T01B card rests on was re-opened and recomputed from W/L/D (passes 1-3); all 8 licence rows re-run
  identical; forge_has greps re-run (1 hit nnue.hpp:11 SCReLU; 0 hits king bucket / mirror / factori); TRIED_GATES.md
  (packa, packb, E3, Sf26Bundle, CorrHistPlus, SingularV2) has no net-architecture gate; no duplicate among the 85 card files.
- Lint clean. Nothing written outside notes/T01B/ (cards untouched in pass 3; F:/odr/work/T01B-verify/ unused).
- Pass 3 written at 01:41 PC clock (clock read in the same step).
