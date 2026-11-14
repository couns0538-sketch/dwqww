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
21 28b3a7520de0bdd16105c94b7496cf603127704f grok47/r3-21-mate-score-tt
24 eb2dda7a68f6605fa298c3fddec81b099fcd5501 grok47/r3-24-tt-duplicate-shadow
22 143f3c5c6953ecfb8826553200e90f31dc91baae grok47/r3-22-time-safety
01 79242482ac4bff090ce73291d790ce2dad83f5e3 grok47/r3-01-eval-rule-50-damp
02 040883c378e3549d075068f0d0513a936702fbf8 grok47/r3-02-threat-history
03 04137a9059a3dced53e292dbc66e26bf60342b17 grok47/r3-03-lmr-signed-correction
04 a334661b975c7be116b48867062e8e7399446c9f grok47/r3-04-lmr-late-parent-relief
05 4ecdfc48bae8273c7de8ebf76498854d920dd743 grok47/r3-05-hindsight-depth
06 fcedbaa45f932277e9893c714d771d468c34e359 grok47/r3-06-null-threat-verify
07 6679cc47c3be4ec3504e172ccd4ceeefa4ee6996 grok47/r3-07-null-see-veto
08 1e7e15673cca486ee1960e32a3ba6a3ca326560e grok47/r3-08-asp-capped-reopen
09 8e988f4b683f8a888e4a71a9ca255fb0d785c173 grok47/r3-09-asp-arm-late
10 86889df387350e4d551cf54f11e77b77f3676ae0 grok47/r3-10-evasion-ordering
11 b27a351b71762b3f27b18e4e1a196a6f2e1da2f2 grok47/r3-11-dead-material
12 6d8717d287cc5f1038d53355b8b03d3cbba9e604 grok47/r3-12-soft-nodes
13 662caa22fa0752f54d97faac82b3acf3b63d3360 grok47/r3-13-quiet-extinction
14 5073747042b305eba413a4e9c3f97df738c71275 grok47/r3-14-draw-jitter
15 fa79e52ed15d57a792735c0d5dbbf4d091c432dc grok47/r3-15-tm-finish-iteration
16 c22999f834be1dfda1e4ca58d3253199ed3ea923 grok47/r3-16-tm-node-share
23 c5f76289b585a6622270abe320655dc81e90aee2 grok47/r3-23-sound-mate-pruning

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
EvalRule50Damp        true   79242482ac4bff090ce73291d790ce2dad83f5e3    1049205    1049205
ThreatHistory         true   040883c378e3549d075068f0d0513a936702fbf8    643389     643389
LmrSignedCorrection   true   04137a9059a3dced53e292dbc66e26bf60342b17    862329     862329
LmrLateParentRelief   true   a334661b975c7be116b48867062e8e7399446c9f    818656     818656
HindsightDepth        true   4ecdfc48bae8273c7de8ebf76498854d920dd743    840387     840387
NullThreatVerify      true   fcedbaa45f932277e9893c714d771d468c34e359    789456     789456
NullSeeVeto           true   6679cc47c3be4ec3504e172ccd4ceeefa4ee6996    929140     929140
AspCappedReopen       true   1e7e15673cca486ee1960e32a3ba6a3ca326560e    850997     850997
AspArmLate            true   8e988f4b683f8a888e4a71a9ca255fb0d785c173    870398     870398
EvasionOrdering       true   86889df387350e4d551cf54f11e77b77f3676ae0    772890     772890
DeadMaterial          true   b27a351b71762b3f27b18e4e1a196a6f2e1da2f2    862329     862329
QuietExtinction       true   662caa22fa0752f54d97faac82b3acf3b63d3360    632155     632155
DrawJitter            8      5073747042b305eba413a4e9c3f97df738c71275    857947     857947
TmFinishIteration     true   fa79e52ed15d57a792735c0d5dbbf4d091c432dc    862329     862329
TmNodeShare           true   c22999f834be1dfda1e4ca58d3253199ed3ea923    862329     862329
SoundMatePruning      true   c5f76289b585a6622270abe320655dc81e90aee2    980408     980408

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
a screen snapshot with no source change. At 16:25 UTC r3-10 moved to
6f0d2e4336c2af27b5884eed3bb7f13313d48051, also with no source change.
At 16:31 UTC r3-07 moved to acdcb7d7dc1dce997638230e90d32db170f7c17d,
a report note with no source change. At 16:32 UTC r3-09 moved to
3b94d827fee3239e3be920e42619f3db7cf01e20, a screen chunk with no
source change. At 16:32 UTC r3-13 moved to
dfe64bf8200e449ca0ff37127f1535e8f841f254, screen chunks with no source
change. At 16:32 UTC r3-14 moved to
158b5d61a9bf708b39eed350f73f1a6ac3daa599, a screen snapshot with no
source change. Pins and the option table were run again after each
of those merges and matched the numbers above. Where a newer tip does not change
src or include, the expected bench is the number already measured
on that same engine source.

Tip r3-03 176aa9fc1edd53c15b37ab966dc1eb4457a43377 merged with no source change; pins and the option table matched.
Tip r3-05 c50314ab9472610847194d9fd871ae38d7eef666 merged with no source change; pins and the option table matched.
Tip r3-06 e6bb8f273849f5c8fc9382638e1864e3e28b4859 merged with no source change; pins and the option table matched.
Tip r3-07 9564de36aa9d4ed17b19d8f7d6468f61ac286efc merged with no source change; pins and the option table matched.
Tip r3-08 3b41775159d67c1336876ece36cdfcb71c4a8c86 merged with no source change; pins and the option table matched.
Tip r3-10 0c89887f480e71e5068d736f80a48e9aa2b9e8c1 merged with no source change; pins and the option table matched.
Tip r3-11 1f613a1b026451289ff1a8a3b90d1b174c5e013e merged with no source change; pins and the option table matched.
Tip r3-15 cbe5010c012512ecdaecba830595e81ed1219883 merged with no source change; pins and the option table matched.
Tip r3-16 3337249994829603e92da529a25f42fc3149d4bb merged with no source change; pins and the option table matched.
Tip r3-23 68b3720c4274e3a646f73ca92b228cbb686b5a3e merged with no source change; pins and the option table matched.
Tip r3-21 28b3a7520de0bdd16105c94b7496cf603127704f merged with no source change; pins and the option table matched.
Tip r3-24 eb2dda7a68f6605fa298c3fddec81b099fcd5501 merged with no source change; pins and the option table matched.
Tip r3-22 143f3c5c6953ecfb8826553200e90f31dc91baae merged with no source change; pins and the option table matched.
Tip r3-01 485e27bd80e76c7973cb5428d0df307baad5123d merged with no source change; pins and the option table matched.
Tip r3-04 d71f002fde848d2a4c3ef661dde152a442d395c6 merged with no source change; pins and the option table matched.
Tip r3-06 544c108818eaaaaf25336b3e26531353876773e1 merged with no source change; pins and the option table matched.
Tip r3-11 c1ed7a071efd09871249cd1cf1fcc9119ff3f95c merged with no source change; pins and the option table matched.
Tip r3-13 3f06b04a630445e7cabe9d27a3315d73e6a711f3 merged with no source change; pins and the option table matched.
Tip r3-14 9bb8e1e5bb6583431ca78bcd979bf4c298694c5c merged with no source change; pins and the option table matched.
Tip r3-15 24fc1d9c0ebf0b044cc96c5fe24260a2da48fa4e merged with no source change; pins and the option table matched.
Tip r3-01 56c0bbc3f71cbd82df0cf6fc73ab1ff53aaa7213 merged with no source change; pins and the option table matched.
Tip r3-02 e7f5bc837eb7461c21779dc182eda5b9cfc4b1c7 merged with no source change; pins and the option table matched.
Tip r3-05 da44ae67e647d50f73ee3477fe1e3c255c38abf4 merged with no source change; pins and the option table matched.
Tip r3-09 1482b396e71968005ac296030c2a84936729aa1c merged with no source change; pins and the option table matched.
Tip r3-10 d13efcd0b18ba10c5d88651ebffbff489d3a1818 merged with no source change; pins and the option table matched.
Tip r3-23 21867c5ac27a8db6f4d8dd2187c4fa7ede5204e8 merged with no source change; pins and the option table matched.
Follow-up commits checked at 2026-11-14 17:13 UTC. Both named engine
fixes are already in this branch, so merging them again changes
nothing and the pins were not re-run.

r3-21 `R3 FOLLOW-UP DONE af1c998304dbfbcb997b757a7ce43af7cdf6e933`
is the mate-score fix. It is an ancestor of HEAD. The later tip
edc2aec48f60363e6061d53377ae8ca20c21a11e is the chunk-4 match report
and was not merged.

r3-24 `R3 FOLLOW-UP DONE 0ca8cb1009dfd1c8e58dc793c3e760d1c88628f3`
is the duplicate-shadow fix. It is an ancestor of HEAD. The later tip
9976bc698fed6654ff5609780ccd51697c0a4de7 is the chunk-4 match report
and was not merged.

The literal line was not present in the files fetched at 17:13 UTC.
The commits named by those lines are the engine fixes above.

Tip r3-03 73d9f20e5dd1d1fba1d919b1e72162ebe90f84e2 merged with no engine-source change; pins were not re-run.
Tip r3-05 e7f2ab305c2031fe61edfbc0017153af4280c692 merged with no engine-source change; pins were not re-run.
Tip r3-06 e0c1252e498f2d587052a33e200163468803d7db merged with no engine-source change; pins were not re-run.
Tip r3-07 06b49fd5a154caf13f401874cd01787fbf617045 merged with no engine-source change; pins were not re-run.
Tip r3-08 fc0598ab4ddebc55ef2c5b0dee2a214c00d56fb8 merged with no engine-source change; pins were not re-run.
Tip r3-10 70aa5474059498df8a4925a37daeb70f1cb771df merged with no engine-source change; pins were not re-run.
Tip r3-11 6a37cd41aaf976094696f9fd3fbf15bea8f0eaf0 merged with no engine-source change; pins were not re-run.
Tip r3-16 4bb15fdbe2aa38bf1a89251df294d7e56089b074 merged with no engine-source change; pins were not re-run.
Tip r3-02 ab21443c460723c618041db2840cd28e3e15cb80 merged with no engine-source change; pins were not re-run.
Tip r3-04 5e7fb50c17e41baa3acd1cf4ab87303ec9bc74db merged with no engine-source change; pins were not re-run.
Tip r3-09 97b51960d6c91a14c068ff87c13fbf0487721ddd merged with no engine-source change; pins were not re-run.
Tip r3-13 a17b76e14c5d2b9ccbad9169bbca73e5963b6e79 merged with no engine-source change; pins were not re-run.
Tip r3-14 c3774151754e6c0c76a3e1d427c1e511e1f4318c merged with no engine-source change; pins were not re-run.
Tip r3-23 1c76659e0ce0afe97091ba220ed2c5ee0cb74686 merged with no engine-source change; pins were not re-run.
Tip r3-03 42ef3a1edbacdc2ce992d66215d3a6b58de62f8c merged with no engine-source change; pins were not re-run.
Tip r3-06 49c56b1406b29d94410957fae8f0a5d284cd7905 merged with no engine-source change; pins were not re-run.
Tip r3-11 b27a351b71762b3f27b18e4e1a196a6f2e1da2f2 merged with no engine-source change; pins were not re-run.
Tip r3-01 837b0f8d9baea2f51f5346a537f10e0453a8b4ee merged with no engine-source change; pins were not re-run.
Tip r3-05 2b3f4b4f9f2fd020869a976baf4523607e4afbf0 merged with no engine-source change; pins were not re-run.
Tip r3-07 1e2c513f49f1058fdb80befff2df3e2fd442d311 merged with no engine-source change; pins were not re-run.
Tip r3-08 2ee71d705dde420c05e3228e27adbc4785622f37 merged with no engine-source change; pins were not re-run.
Tip r3-10 59cab756b2f3ed26761000dbdeb85c46d1f20e49 merged with no engine-source change; pins were not re-run.
Tip r3-13 662caa22fa0752f54d97faac82b3acf3b63d3360 merged with no engine-source change; pins were not re-run.
Tip r3-15 fa79e52ed15d57a792735c0d5dbbf4d091c432dc merged with no engine-source change; pins were not re-run.
Tip r3-02 afa7ca21ff0a7fc61d0161c8baa8cb0760f94235 merged with no engine-source change; pins were not re-run.
Tip r3-03 04137a9059a3dced53e292dbc66e26bf60342b17 merged with no engine-source change; pins were not re-run.
Tip r3-04 a334661b975c7be116b48867062e8e7399446c9f merged with no engine-source change; pins were not re-run.
Tip r3-05 5e71bcd3059db2b7674fb04be431f72c9d240b14 merged with no engine-source change; pins were not re-run.
Tip r3-07 dd4c65ee84a7f03783406aa85835a0948dc15129 merged with no engine-source change; pins were not re-run.
Tip r3-09 8e988f4b683f8a888e4a71a9ca255fb0d785c173 merged with no engine-source change; pins were not re-run.
Tip r3-14 5073747042b305eba413a4e9c3f97df738c71275 merged with no engine-source change; pins were not re-run.
Tip r3-16 c22999f834be1dfda1e4ca58d3253199ed3ea923 merged with no engine-source change; pins were not re-run.
Tip r3-23 c5f76289b585a6622270abe320655dc81e90aee2 merged with no engine-source change; pins were not re-run.
Tip r3-01 79242482ac4bff090ce73291d790ce2dad83f5e3 merged with no engine-source change; pins were not re-run.
Tip r3-02 040883c378e3549d075068f0d0513a936702fbf8 merged with no engine-source change; pins were not re-run.
Tip r3-05 4ecdfc48bae8273c7de8ebf76498854d920dd743 merged with no engine-source change; pins were not re-run.
Tip r3-06 fcedbaa45f932277e9893c714d771d468c34e359 merged with no engine-source change; pins were not re-run.
Tip r3-07 6679cc47c3be4ec3504e172ccd4ceeefa4ee6996 merged with no engine-source change; pins were not re-run.
Tip r3-08 1e7e15673cca486ee1960e32a3ba6a3ca326560e merged with no engine-source change; pins were not re-run.
Tip r3-10 86889df387350e4d551cf54f11e77b77f3676ae0 merged with no engine-source change; pins were not re-run.
Not verified. The other in-scope branches still have no
`R3 FOLLOW-UP DONE` line in the files on origin.
Playing strength was not measured. Address and thread sanitizers were
not run on the integrated tree. The KRK threads-2 miss above was not
reproduced.

R4 DONE 8e805fb482a97b7182f3fa4c12f26ce7e1d88c19
