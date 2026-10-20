# Frozen single-pair qsearch causal diagnostic

Preparation only. No compiler or engine may run until root explicitly sends:

    17 QSEARCH TRACE CLEAR

This is one finite source16/source17 search pair. It is not a benchmark,
calibration, match, or Elo test. No retry is permitted. A startup, protocol,
or trace failure is preserved and leaves the check incomplete.

Source16: 553caef144ae2e1b696ba35d7a0eb1a50a03fde9.
Source17: 47f0560221d986e41a309853e1295c557fcf5bf6.
Use their actual frozen Release cores and matching compiled UCI objects.
Their search source and headers must match. Compile one identical outside-only
instrumented search.cpp object, serially, and replace only search.cpp.o in two
copied cores. Keep each build's actual Board object, network, evaluation,
options, and UCI object. No production/header/test/Git changes.

The position and single allowed root move are:

    position fen 1br3k1/2P5/2K5/8/8/8/8/1Q6 b - - 0 1
    go depth 1 searchmoves g8h8

Fresh process per build; OwnBook=false, Threads1, Hash16, ucinewgame, and
isready before the position. The first child has a cold wide-window qsearch.
Default QsSeeMargin40 and QsFutilityMargin160 remain unchanged.

Pure legal-oracle validation must establish the valid parent, legal
nonchecking g8h8, child not in check, and exactly one legal noisy child move:
b1b8. Direct c7b8 promotions expose Kc6 to Rc8 and are illegal. After Qxb8,
Rxb8 releases c7b8 promotions. Target-only material oracle is +300.
Source-level expectations are source16 SEE -100 and source17 SEE +300.

Trace only the exact six-piece White child and b1b8. Record entry FEN, ply,
alpha/beta, static evaluation and futility base, the actual -40 SEE decision,
any skip reason, and actual search entry/return. Replace the original predicate
with one stored boolean so SEE is called exactly once per move. Do not modify
other pruning, move ordering, evaluation, or search decisions.

Expected causal observation: source16 logs SEE-fail/skip without making b1b8;
source17 logs SEE-pass and makes/searches b1b8. Require matching pre-gate state,
ply1, outside check, wide window, and no earlier futility skip. Preserve actual
nodes, scores, PVs and bestmove; do not predict a numerical or PV difference.
The forced root bestmove is g8h8 in both builds by construction.

Final root clearance tightens the bounds: each process shares one 10-second
total response deadline across startup, ready, the search, and quit. There are
at most two fresh processes and a total30s operational engine budget. Search
depth is1, one invocation per build, no retry. Any failure kills the owned
process group, preserves raw output, and stops the pair. Durations are budget
accounting only.

All originals, copied headers/cores/UCI objects, instrumented source, compiled
object/executables, stdin/stdout/stderr, phase events, commands, hashes, and
result analysis stay under this directory. The outside directory
/workspace/promotion-see-qsearch-causal-20261020 contains working duplicates;
no additional archive scope is required. No archive work occurs in preparation.
