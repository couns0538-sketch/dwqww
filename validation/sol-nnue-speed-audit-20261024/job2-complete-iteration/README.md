# Optional completed-iteration result coherence

Source parent: `76298789a5932f4933262ec75f3001cbc90ca5ec`.
Lock: `f4911f2709bd5ae7e5fca7aea30aac5d87314a05`.
The two-line production guard is `FORGE_COMPLETE_ITERATION_ONLY=1`;
undefined or zero preserves the legacy policy. No tuning or net changes.

A fresh single-thread node-limited search can advertise an unfinished iteration's
depth/PV with the preceding completed iteration's score. The public `SearchInfo`
also mixes its completed depth/score with the partial PV/best/ponder. Partial-move
selection is intentional legacy policy; this packet establishes tuple coherence,
not that the partial move is inferior or that this policy improves Elo.

Use a fresh process, waiting for `uciok`, `readyok` and finally `bestmove`:

```text
uci
setoption name Threads value 1
setoption name Hash value 16
setoption name OwnBook value false
ucinewgame
isready
position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
go nodes 600
quit
```

Completed depth3 at206 nodes is cp26 / `e2e4 h7h6 d2d4`. The lock subsequently
emits unfinished depth4/cp26 / `h2h3 g8f6 d2d4 d7d5` at600 nodes and returns
`h2h3`. A cold full depth4 needs772 nodes. Guard ON retains depth3/cp26 /
`e2e4 h7h6 d2d4` and returns `e2e4`. Its total work still correctly includes
the600 searched nodes. The restricted/Ponder witness and a node2 interruption
before any completed depth exercise the other affected return paths.

Actual validation:

- Portable UCI regression: lock RED exits1,8/19 checks pass; ON GREEN19/19,
  exit0. Each extended run contains19 fresh process exchanges. Root independently
  reran19/19 against both Release and ASan/UBSan ON builds, with native reference.
- Direct public `SearchInfo` checker: OFF15/19, expected exit1; ON19/19, exit0.
  Both normal completed depth4/depth10 result lines agree; portable UCI checks
  assert their exact tuples and node counts.
- Official OFF executable SHA256
  `d90f5060880c799ef8cdfd41bbef3668610a08619c9edaa266452f1bc656c47f`,
  byte-identical to the lock. Official ON SHA256
  `208e82c556d940c5cf519d330867f8fdfd0da4912e50134054b6417b5508d9de`.
- OFF and ON benchmark depths11/13/16/20/22 each produce
  `308972 / 745494 / 2460422 / 11901452 / 31111774`;
  startpos perft5 is4865609 for both. These runs check node correctness;
  concurrent compilation makes their timings unsuitable for speed comparisons.
- Release ON CTest13/14, exactly the four user-whitelisted failure lines and no
  changed expectations. OFF is the already-qualified identical lock binary.
- Six additional actual T1/T2 depth10 sanitizer searches pass; original commands,
  exits and transcripts are preserved. Leak detection and halt-on-error enabled.

Re-run the portable regression with Python3.11+; affinity is optional:

```sh
python3 -B tools/check_complete_iteration.py \
  --engine /absolute/path/forge-guard-on \
  --reference /absolute/path/forge-lock \
  --outdir /new/empty/output-directory
```

The reference must be this H256 lock. For RED, also use the lock as `--engine`.
The separate original C++ checker is `tools/check_complete_iteration_core.cpp`;
compile with the same H256 strict-float flags and link the relevant actual
`libforge_core.a` with `-static -pthread`. Exact executed commands and original
outputs, including failed controls, are in `native-original-text.json`.

That JSON stores original UTF-8 text reversibly, with each file's SHA256/size and
path; encode each `original_utf8` value to recover its bytes. Binary objects and
executables are recorded by hash and remain local. No match, SPRT, Elo, Windows
qualification or universal correctness claim is made. Keep the guard off until
the owner's separate engine QA decides whether to adopt this behavioral policy.
