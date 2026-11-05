# T04P verify (adversarial pass on cards/T04P, start 03:59 PC clock, board slot S2)
Scope: 1 card (T04P-01). Method: every cited source number re-opened once (commit message / PR text / fishtest api),
Elo recomputed from W/L/D and the pentanomial counts, licence rows re-run, forge_has re-run, own-port lines and exe
re-read, duplicate sweep over all 93 cards, card_lint. Scratch: F:/odr/work/T04P-verify/ (elo_check.py, gh api json).

## Numbers (6 of 6 confirmed; recompute = trinomial Elo from W/L/D, error = 95 % from the pentanomial counts)
| source | card says | recompute | pairs*2 == N |
|---|---|---|---|
| Caissa d39fcfb 40+0.4 (commit message, gh api) | +2.11 +- 1.55, N 48,018 | +2.11 +- 1.55 | yes |
| Caissa 9d566cc 10+0.1 (commit message, gh api) | +1.35 +- 1.06, N 112,192 | +1.35 +- 1.06 | yes |
| PlentyChess PR 373 STC 8+0.08 (PR body) | -1.26 +- 2.03, LLR -2.25 = H0, N 29,214 | -1.26 +- 2.03 | yes |
| PlentyChess PR 373 LTC 40+0.4 (PR body) | +1.73 +- 1.31, LLR 3.02, N 61,338 | +1.73 +- 1.31 | yes |
| Stockfish b280d2f STC (fishtest 66578e2e..., live api) | +3.91, 26,592 games, no error bar | +3.91 +- 2.13 | yes |
| Stockfish b280d2f LTC (fishtest 6657f46b..., live api) | +1.31, 142,572 games, no error bar | +1.31 +- 0.86 | yes |
Fishtest args confirmed live: tc 10+0.1 / 60+0.6, threads 1, book UHO_Lichess_4852_v1.epd, sprt normalized
elo0/elo1 0.0/2.0 and 0.5/2.5, alpha = beta 0.05, state accepted, LLR 2.93 / 2.96; base master, new ttcutTweaks7.
The two Stockfish error bars were added inline to card line 38 as "(by verify)"; no card number needed a correction.

## Mechanism reading (confirmed, one nuance)
- Caissa d39fcfb diff (MIT, read): needed TT depth = node depth + (ttScore >= beta), non-PV only -> form A; the side of
  beta decides, not the bound, as the card says. Commit message credits two other engines; no STC in the message.
- Caissa 9d566cc diff (MIT, read): + (ttScore >= beta && ttScore < beta + TTCutoffMargin), param 80 range 0-200 -> form
  B, measured against the d39fcfb rule, so "+1.35 = form B vs form A", as the card says.
- Stockfish PR 5314 body (text only): "master allows tt cutoffs only when depth from tt is strictly greater ... this
  patch also allows them when it's equal and if tt value is lower or equal to beta". So the measured +3.91 / +1.31 is
  the fail-low relaxation, which the lock already has (:921 one test for every bound). The card's "not evidence for
  this rule" and its Status line are right; CRITIC2 line 16's use of "STC +3.91" as evidence for the fail-high rule is
  not supported by the PR text.
- Nuance: the Stockfish boundary is score > beta (equal depth allowed at tt value <= beta), Caissa's is score >= beta;
  they differ only at score == beta. The card groups both as form A; immaterial to the gate (the Stockfish number is not
  used as evidence). A parenthetical was added inline on card line 19.

## Reading and licence rule
- 4 licence_at rows re-run: identical to notes/T04P/licences.md (Caissa MIT at both SHAs; Stockfish GPL-3.0 at
  b280d2f065; PlentyChess GPL-3.0 at 9c520de7b7).
- GPL sources: only PR title/body (gh api pulls/373, pulls/5314), the commit title of b280d2f065 (gh api commits with a
  --jq that printed date, title and the file count only; no patch saved or shown) and fishtest args/results. No source
  file, no diff of a GPL repo opened. Caissa diffs read under MIT (two one-line hunks). PlentyChess PR 5314 shows
  merged_at None (rebase merge); the merge commit 9f0088bb and commit b280d2f065 (2024-05-30) exist as the card says.
- Furybench pages 1384 / 7473 / 1382 / 1373 and the Obsidian origin commit were not fetched (cap, usage); the cited
  records are the commit messages and PR body, which carry the same numbers.

## Forge fit (confirmed)
- `bash tools/forge_has.sh 'tt_depth >= depth'` -> :921, :1003, :1090 (3 hits). Lock :921-926 read: one depth test
  `tt_depth >= depth` for every bound, halfmove < 90, bound test with `tt_score >= beta` / `tt_score <= alpha`. LACKS.
- Lock `RfpMargin = 72` at src/search.cpp:23: the card's own start value 72 is the lock's constant, not Caissa's 80.
- Own port (forge_push/qa_ltopgo_al1_stage/cands/caissa_c123/forge_caissa_c123_al1s198_src): search.hpp:217 extern,
  search.cpp:41 default 0, :89 spin 0-200, :931-933 depth term `+ (TtCutExtraMargin > 0 && tt_score >= beta &&
  tt_score < beta + margin)` = form B, exactly as the card says. CR_PASS_caissa_c123_al1_ltopgo_8924099a.ok read:
  "PASS-notes singles; MIT notice fix before merge; bundle HELD; C3 LTC flag", sha256 8924099AD4C4...; exe
  forge_push/bin/forge_ltopgo_x_caissa_c123_al1_8924099a.exe present, sha256 prefix 8924099ad4c42f45 (match).
- qa_v22_checks/xchk_caissa_c123_TtCutExtraMargin.json: OFF 312866/862329/3024920/12389307/34048354, perft5 4865609,
  kiwipete 193690690 (off_ok, perft_ok), ON at 80 = 342592/879873/2333863/12556911/39261538 (on_ok); the card's
  +9.5 / +2.0 / -22.8 / +1.4 / +15.3 % recomputed and match. The xchk exe is the pc1 kit copy; the .ok states pc1==pc2.
- tried_gates.py --grep "TtCut|Caissa|c123|ttcut|tt_cut|TTcut": 0 of 110 rows. Never gated: confirmed.
- Effort arithmetic: 3,000 games at 430-502 games/h = 6.0-7.0 h: matches "6-7 h".

## Tuned-constant rule (judgment: note, not a violation)
Start value 72 is own (lock RfpMargin). The spin range 0-200 equals Caissa's DEFINE_PARAM range because the own port
(CR-passed 2026-10-30, before this job) carries it and the built exe gates without a rebuild; the card says so openly.
A range bound is not a tuned value and the code is already Forge's own; recorded here, Status line unchanged.

## Duplicates (none)
Sweep of all 93 cards for TtCut / tt_depth / fail-high TT / b280d2f / d39fcfb / 9d566cc / PR 373 / :921: the only
other card on line :921 is T04D-02 (node-type match), whose Forge-fit text says "Related, not the same rule" and
names Caissa d39fcfb as an uncarded table row. notes/T04N/VERIFY.md:40 lists the caissa_c123 port for another purpose.
Not a duplicate. CRITIC2 line 16 asked for a one-liner under T04D-02; the researcher wrote a full card on the
coordinator's brief - a format choice for the coordinator, not a WORKER_RULES violation.

## Format, names, lint
60 lines (cap 60, so every verify edit stayed inline), 8 fields in template order, Status line present, every Forge
estimate labelled UNPROVEN, gate route = the crew decision (Threads=1, UHO, [0,5] nElo, alpha = beta 0.05, pentanomial,
cap 3,000, capped = no decision, one extension if positive). Vendor-name grep over cards/T04P and notes/T04P: none.
card_lint before edits: 0 findings, 0 PENDING; re-run after the inline edits: see the last line of this file.

## Unverifiable (stated as such in the card or notes)
- Books of the furybench tests (not in the commit messages or PR body).
- CR note CR_CAISSA_C123_AL1_20261030.md (md5 df095afd and "C3 LTC flag" quoted from the .ok file; file not located).
- Form B against the lock's rule has no direct measurement anywhere; the 0 to +2 estimate is an extrapolation from
  form A (40+0.4 passes, one STC loss) plus form B vs form A (+1.35 at 10+0.1), labelled UNPROVEN.

## Verdict
Card T04P-01: CONFIRMED. 0 corrections of numbers, 2 inline additions (Stockfish error bars line 38, boundary nuance
line 19), 0 violations, 0 duplicates. Checked 1 card, 6 source numbers, 4 licence rows, 3 forge_has hits, 1 own exe.

Lint after the inline edits (04:07 PC clock): # cards\T04P\T04P-01-failhigh-tt-deeper.md: 0 finding(s), 0 PENDING field(s); card 60 lines.
