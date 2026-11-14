Round-3 integration on grok47/r4-01-integrate-r3.

Base is integrate/combo29-all at e04556ddc3a430b2e751159b0d46111ef56c8b89.
Branches 18, 19, and 20 were not merged.
No branch report ended with `R3 FOLLOW-UP DONE <commit>` at the freeze
(2026-11-14 16:08 UTC). Each named branch was merged at its then-current
tip, and merged again when that tip moved. The second wave after the
search source was frozen added screen logs only. src, include, and
tests_r4_01 are unchanged from 8e805fb482a97b7182f3fa4c12f26ce7e1d88c19.

Build. The machine has AVX-512F and BMI2, so the owner build is
g++ 13.3.0 with -DFORGE_MARCH=x86-64-v4 and -DFORGE_PORTABLE=OFF.
CMakeLists.txt was not edited and no FORGE_* macro was defined or
undefined outside that configure line. /usr/bin/c++ is Clang 18.1.3
and cannot link libstdc++, so the compile used CXX=g++.
The binary reports FORGE_SPD_SLIDER_PEXT=1 and FORGE_SPD_NNUE_ZMM=1.

Frozen input commits

17 02674044d770fc756ea2cc1041726d23bad6c659 grok47/r3-17-merge-legal-node-limit
21 d30c2746d3f1dfd931ff75bde455a060f75cff6a grok47/r3-21-mate-score-tt
24 67f96d9b5e477ec212bbe36f5d1994c87cafd590 grok47/r3-24-tt-duplicate-shadow
22 b8d47952f21fec0185df8509d53a2bafd7373313 grok47/r3-22-time-safety
01 c0aaf80df40213f867038d2280abbc954d8b9e98 grok47/r3-01-eval-rule-50-damp
02 8fe3867a098b7df57d731a3e3581c1be51ea5c57 grok47/r3-02-threat-history
03 1ecc1d33156d1833701b98586f9c17bd4f67da91 grok47/r3-03-lmr-signed-correction
04 feccf387e16ac19233f77413a113134467b3f0f3 grok47/r3-04-lmr-late-parent-relief
05 f9022e2b0fe573fdf1265b115ff9d48ce895273e grok47/r3-05-hindsight-depth
06 55d714b10c4aa837cab381e2f8cd46e62cea1c48 grok47/r3-06-null-threat-verify
07 7e738ba98d440f5a9ff9a7393d5abd8fcd23f67d grok47/r3-07-null-see-veto
08 043097d56bfc0a8f206690044c5b597658356bd0 grok47/r3-08-asp-capped-reopen
09 3b8c3fe58259a7fe34d62069a30a877db3aa205f grok47/r3-09-asp-arm-late
10 1664a60202b885790b96d5c1d2f1c7eb63628823 grok47/r3-10-evasion-ordering
11 d7d52cbb7db65c2a4c182658ce40d25c967cb8b3 grok47/r3-11-dead-material
12 6d8717d287cc5f1038d53355b8b03d3cbba9e604 grok47/r3-12-soft-nodes
13 eebb14ca513d56c4227d69cfdada30707f5b6cf3 grok47/r3-13-quiet-extinction
14 99997aa0cbf445c6a829b29c4960a32143be9dcf grok47/r3-14-draw-jitter
15 29a38cf9df7b2de94bcb3dd9bbbfcc2430059f68 grok47/r3-15-tm-finish-iteration
16 f8d188b7b0597a6ec629012edd4e6655d4474c47 grok47/r3-16-tm-node-share
23 2bba512e6f88bc2953e27445f1a2156a758a9b21 grok47/r3-23-sound-mate-pruning

Conflict handling. Helpers observe the shared node budget and then
ignore the clock. The main worker stops when Move Overhead has already
used the remaining time. An empty clock plays a legal hash move, or
one ply capped at 2000 nodes, and does not start helpers. Each UCI
option keeps its own name, default, and setter. uci lists all of them.
AspArmLate, after its follow-up, uses a full window on the iteration
after a root fail-high or fail-low. AspCappedReopen still caps the
current window. DrawJitter clears the hash when its value changes.
DeadMaterial changes the evaluation of bare king plus one minor and
leaves the historical draw cutoff in place.

(a) Threads 1, Hash 16, OwnBook false

bench 11 = 312866
bench 13 = 862329
perft 5 = 4865609

(b) Bench 13 with that option alone on. Expected is a fresh x86-64-v4
build of the merged commit, every other option at default. Got is the
integrated binary with only that option changed.

option                value  commit                                     expected   got
EvalRule50Damp        true   c0aaf80df40213f867038d2280abbc954d8b9e98    1049205    1049205
ThreatHistory         true   8fe3867a098b7df57d731a3e3581c1be51ea5c57    643389     643389
LmrSignedCorrection   true   1ecc1d33156d1833701b98586f9c17bd4f67da91    862329     862329
LmrLateParentRelief   true   feccf387e16ac19233f77413a113134467b3f0f3    818656     818656
HindsightDepth        true   f9022e2b0fe573fdf1265b115ff9d48ce895273e    840387     840387
NullThreatVerify      true   55d714b10c4aa837cab381e2f8cd46e62cea1c48    789456     789456
NullSeeVeto           true   7e738ba98d440f5a9ff9a7393d5abd8fcd23f67d    929140     929140
AspCappedReopen       true   043097d56bfc0a8f206690044c5b597658356bd0    850997     850997
AspArmLate            true   3b8c3fe58259a7fe34d62069a30a877db3aa205f    870398     870398
EvasionOrdering       true   1664a60202b885790b96d5c1d2f1c7eb63628823    772890     772890
DeadMaterial          true   d7d52cbb7db65c2a4c182658ce40d25c967cb8b3    862329     862329
QuietExtinction       true   eebb14ca513d56c4227d69cfdada30707f5b6cf3    632155     632155
DrawJitter            8      99997aa0cbf445c6a829b29c4960a32143be9dcf    857947     857947
TmFinishIteration     true   29a38cf9df7b2de94bcb3dd9bbbfcc2430059f68    862329     862329
TmNodeShare           true   f8d188b7b0597a6ec629012edd4e6655d4474c47    862329     862329
SoundMatePruning      true   2bba512e6f88bc2953e27445f1a2156a758a9b21    980408     980408

softnodes is a go keyword, not a setoption. The r3-12 commit
6d8717d287cc5f1038d53355b8b03d3cbba9e604 built with defaults gives
bench 13 = 862329, and the integrated default is 862329.
Turning every option back off returns bench 13 = 862329.

(c) First 10000 positions of forge-combo29/soak_all/search_corpus.txt,
go depth 8, all options off, Threads 1, Hash 16, OwnBook false,
compared with a build of e04556dd. Best move, score, and nodes matched
on all 10000. Identical 10000. Explained differences 0.
Branches 21, 22, and 24 did not move any of these positions.
The comparison was repeated after the follow-up source merges, with
the same 10000 identical.

(d) Every test program under tests_t1, tests_t3, tests_t6, tests_t8,
tests_t12 through tests_t23, and tests_r3_01 through tests_r3_17,
tests_r3_21, tests_r3_22, tests_r3_23, and tests_r3_24 was compiled
against the integrated objects and exited 0. tests_t16 own-book spec
is ok 54 lines and the search spec is ok 7 lines. The raw options and
clamp diffs gain the option lines this integration advertises; after
those lines are removed, both diffs are empty. tests_t19 widened net
matches tests_t19/nnue_weights_512.inc. tests_t12 missed 1 of 400
threads-2 searches on the first sample and missed 0 of 400 on two
repeats. A base build of the same test missed 0 of 400. The miss did
not reproduce.

(e) tests_r4_01/reused_searcher.cpp. One Searcher at Threads 2 spends
the 8000-node budget (8000 nodes), then Threads 4 spends a 400-node
budget (402 nodes). A mated root, a stalemated root, and a drawn root
then report 0 nodes, the same as a fresh Searcher. Old helper counts
are not included. The program exits 0.

(f) The eight depth-9 cases from soak/combo29-all, faults 084 through
091, still fail equality against the pre-t23 lock. The integrated
engine matches the base build on move, score, and nodes for every one
of them. The rule-50 transposition gates, and for fault 090 the
rule-50 pruning guards as well, are the intended behaviour recorded in
soak_all/search_equality_investigation.md. They were not weakened.

fault  index  fen                                              move   integrated score and nodes     lock nodes
084    3228   5k2/8/7p/1K5P/8/8/8/7q w - - 76 136               b5c4   cp -1689, 31749                32435
085    9834   8/4k3/8/2q3b1/6K1/5B2/8/8 w - - 74 132            f3e2   cp -1164, 49669                43672
086    10567  1b6/6k1/6b1/3r3r/8/8/8/2K5 w - - 76 134           c1b2   mate -8, 7582                  7581
087    11000  1k4r1/8/8/8/8/8/8/1K6 b - - 79 146                g8g2   cp 460, 14025                  14618
088    12276  8/8/5R2/8/8/8/7K/2k5 w - - 79 151                 f6f5   cp 443, 8688                   8682
089    12999  8/1k6/5K2/B4N2/8/R7/8/8 w - - 79 147              f6e5   cp 1187, 12663                 12873
090    14002  8/6b1/6k1/B7/7K/4q3/8/8 w - - 79 145              a5c7   cp -1178, 26217                36360
091    25354  8/r7/1k4n1/5p2/2K5/7n/8/8 w - - 72 141            c4d4   cp -1812, 29687                29685

Re-check at 2026-11-14 16:11 UTC. Origin was fetched again. The trees of
r3-17 at 02674044d770fc756ea2cc1041726d23bad6c659 and r3-12 at
6d8717d287cc5f1038d53355b8b03d3cbba9e604 do not contain the line
`R3 FOLLOW-UP DONE`. Those tips were already merged. r3-01 moved to
c0aaf80df40213f867038d2280abbc954d8b9e98, a screen chunk and report
update with no source change. At 16:16 UTC r3-04 moved to
feccf387e16ac19233f77413a113134467b3f0f3, also with no source change.
At 16:18 UTC r3-05 moved to f9022e2b0fe573fdf1265b115ff9d48ce895273e,
again with no source change. At 16:23 UTC r3-21 moved to
d30c2746d3f1dfd931ff75bde455a060f75cff6a, a match log with no source
change. At 16:24 UTC r3-24 moved to
67f96d9b5e477ec212bbe36f5d1994c87cafd590, also with no source change.
At 16:25 UTC r3-02 moved to 8fe3867a098b7df57d731a3e3581c1be51ea5c57,
a screen snapshot with no source change. Pins and the option table
were run again after each of those merges and matched the numbers above. Where a newer tip does not change
src or include, the expected bench is the number already measured
on that same engine source.

Not verified. No `R3 FOLLOW-UP DONE` commit existed to merge.
Playing strength was not measured. Address and thread sanitizers were
not run on the integrated tree. The KRK threads-2 miss above was not
reproduced.

R4 DONE 8e805fb482a97b7182f3fa4c12f26ce7e1d88c19
