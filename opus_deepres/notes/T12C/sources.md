# T12C sources (one line per source read: url | licence tier | what it gave | idea)
Q1 (search, local): tools/mine_commits.py --grep over the job's cached GitHub commit lists (F:/odr/cache/commits/:
   Stockfish 2016-now; Caissa, Patricia, Stormphrax, PlentyChess, viridithas, Reckless 2024-now) - titles and parsed
   result lines only; plus a message scan (F:/odr/work/T12C/msgscan.py) for simplify / remove / revert commits per idea.
S1 https://github.com/official-stockfish/Stockfish/commit/180cab4438 | GPL-3.0 ideas only (commit message + fishtest links) | rule-50 damping simplified, kept; non-reg STC/LTC | idea 1 T06-05
S2 https://github.com/official-stockfish/Stockfish/commit/955edf1d1d | GPL-3.0 ideas only (message) | doEvenDeeperSearch reverted for search explosions (issue 4276) | idea 2 T04-02
S3 https://github.com/official-stockfish/Stockfish/commit/87814d2fb8 | GPL-3.0 ideas only (message) | doShallowerSearch simplified, non-reg 242k / 128k games | idea 2 T04-02
S4 https://github.com/official-stockfish/Stockfish/commit/5d1505d8c7 | GPL-3.0 ideas only (message) | cut-node no-TT-move LMR term simplified away, re-added at +1.0 / +1.3 | idea 4 T04D-01
S5 https://github.com/official-stockfish/Stockfish/commit/76c319f438 | GPL-3.0 ideas only (message) | TT-cut depth condition simplified at zero cost | idea 5 T04D-02
S6 https://github.com/official-stockfish/Stockfish/commit/5d72032559 | GPL-3.0 ideas only (message) | capthist in capture SEE pruning: earlier failed try, LTC +1.08 at 244k | idea 9 T04B-01
S7 https://github.com/Ciekce/Stormphrax/pull/310 (+ its commit titles) | GPL-3.0 ideas only (PR text, commit titles) | NMP combo of failed patches; TT-capture guard not among them -> no counter-evidence | idea 7 T04E-02
S8 https://github.com/official-stockfish/Stockfish/commit/1591e5ac3b | GPL-3.0 ideas only (message) | ttPv singular rule simplified away earlier, re-added, LTC +1.04 at 236k | idea 6 T04C-02
S9 https://github.com/Yoshie2000/PlentyChess/commit/9f2cfbc943 (PR 334) | GPL-3.0 ideas only (title + bench) | wrong ttpv in the excluded search fixed after PR 286 | idea 6 T04C-02
S10 https://github.com/codedeliveryservice/Reckless/commit/5b38ddf857 (PR 153) | no licence file at that commit (AGPL-3.0 now): ideas only, commit message log only | earlier milder form: more NMP reduction after a TT capture, +5.34 +- 3.81 | idea 7 T04E-02
S11 https://github.com/official-stockfish/Stockfish/commit/95d7369e54 | GPL-3.0 ideas only (message) | movecount pruning of quiet check evasions in qsearch, STC +1.90 / LTC +1.54 | idea 8 T04F-01
S12 https://github.com/official-stockfish/Stockfish/commit/de9fc53af5 | GPL-3.0 ideas only (message) | evasionPrunable removed, non-reg (neutral guard) | idea 8 T04F-01
S13 https://github.com/official-stockfish/Stockfish/commit/a49b52cf69 | GPL-3.0 ideas only (message) | malus scope revert (not the decay) STC/LTC/VLTC | idea 10 T04E-03
S14 https://github.com/official-stockfish/Stockfish/commit/e2fdf6f005 | GPL-3.0 ideas only (message) | separate malus formulas simplified, LTC +0.53 non-reg | idea 10 T04E-03
W1 (web search, no page read) "singular verification cutnode non-cut node SPRT" - no chess-engine result | - | nothing | idea 3 T04-01
Also titles only (cached lists, no message read): Caissa f2967c1 / 90670d9 / fbebb14 (MIT), viridithas c1bfc38 (MIT at that commit), Stockfish 39af98c, b59786e, 27428a6, a37b38b, e852d98, 6e9b5af, 75f07da, aff1f67, b177b73, d712ed3, b8ccaf0, 6ecab03, fcbb02f.
Count: 14 sources read (S1-S14), 1 web search, local cache searches.
