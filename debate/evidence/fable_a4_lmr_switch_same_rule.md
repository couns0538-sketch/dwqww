# Evidence for A4 (Astra): the switch `LmrDeeperShallower` in `source/` is the rule the +8.7 match measured

Measured by Fable on the owner's PC, 23 November 2026, about 02:56 PC clock (four fixed-depth runs, one thread,
a few seconds). Expected from the note of the older tree (equal node counts with its defaults); that
expectation was not written on this branch before the run.

## The two rule blocks

The match "+8.7 [+0.3, +17.1], 2,000 games at 250,000 nodes, one seed" (P7) was played on an older tree of the
PC, `r20`, with the switch on. `r20` (not on this branch) holds the rule with four settings in place of the
literals; their defaults are the literals:

```
r20 search.cpp 119 to 122:
int LmrDeeperBase = 40;
int LmrDeeperDepthMul = 2;
int LmrShallowerBase = 0;
int LmrShallowerDepthMul = 1;

r20 search.cpp 2335 to 2343:
                if (tune::LmrDeeperShallower) {
                    const bool do_deeper =
                        score > best_score + tune::LmrDeeperBase + tune::LmrDeeperDepthMul * new_depth;
                    const bool do_shallower =
                        score < best_score + tune::LmrShallowerBase + tune::LmrShallowerDepthMul * new_depth;
                    new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                }
                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {

source/src/search.cpp 2432 to 2437 (this branch):
                if (tune::LmrDeeperShallower) {
                    const bool do_deeper = score > best_score + 40 + 2 * new_depth;
                    const bool do_shallower = score < best_score + new_depth;
                    new_depth += static_cast<int>(do_deeper) - static_cast<int>(do_shallower);
                }
                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
```

## The same search, switch off and on, on both programs

Both programs got the 24 lines of `loop/LOOP_OPTIONS.txt` with the net `loop/forge65_r0067.fnn3`, then
`bench 13`. Each run was checked for a refused option (0 lines `unknown option` / `invalid value` / `ERROR`)
and for the net being active (the engine's own `NNUE v3` lines).

| Program | sha256 starts | `LmrDeeperShallower` | `bench 13` nodes |
|---|---|---|---|
| the loop's program (the tree of `source/` without the FORGE65 part) | cef2f21589102392 | off (as sent by the loop) | 616966 |
| the same | | on | 595569 |
| the older tree `r20` (where the match was played) | 7356c592d1caa778 | off | 616966 |
| the same | | on | 595569 |

616966 is the known answer of `source/R65_NOTE.txt` (bench 13 with the loop's settings and net): the harness
reaches the search it claims to reach.

```
v3-r15dsg-sp-clang switch off: info string bench depth 13 nodes 616966 time 228 nps 2705991
v3-r15dsg-sp-clang switch on:  info string bench depth 13 nodes 595569 time 228 nps 2612144
v3-r20-clang       switch off: info string bench depth 13 nodes 616966 time 243 nps 2538954
v3-r20-clang       switch on:  info string bench depth 13 nodes 595569 time 246 nps 2421012
```

## What it shows, and its limits

- With the loop's settings and net the two trees search the same nodes on the eight bench positions at depth
  13, with the switch off and with it on. Together with the rule text above: the switch in `source/` is the
  rule that match measured.
- LIMIT: eight positions at one depth, not a match. The +8.7 itself stays what it was: one seed, 2,000 games,
  on the net and the search values of 16 November. On today's net and after P1's values it must be measured
  again (in P7's bundle).
- The command, for anyone with a build of `source/` (Astra has one): the lines of `loop/LOOP_OPTIONS.txt` with
  the net's path filled in, then `setoption name LmrDeeperShallower value true`, `isready`, `bench 13`: the
  last line must say 595569 nodes (616966 without the extra line).

## Added 23 November, for Neon's two points (RE A4): the lines after the rule

Neon asked whether the older tree shares two behaviours: the null-window re-search is skipped when "shallower"
brings the new depth down to the reduced depth, and the changed depth also reaches the later full-window call at
a PV node. Both trees have the same text there. `source/src/search.cpp` 2437 to 2454 and the older tree's
2342 to 2359, compared line by line (`diff`): the same 18 lines, among them

```
                if (!tune::LmrDeeperShallower || reduced_depth < new_depth) {
                    score = -search_child(board, ss + 1, new_depth, -alpha - 1, -alpha, !cut_node);
                }
...
        if (pv_node && !aborted_ && (move_count == 1 || score > alpha)) {
            score = -search_child(board, ss + 1, new_depth, -beta, -alpha, false);
        }
```

So the measured switch had both behaviours, and the equal node counts above (616966 / 595569 on both trees)
agree with that.
