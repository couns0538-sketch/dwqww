# C4 IirShallowTt - internal iterative reduction for a too shallow hash entry (UNPROVEN)

Gate line: engine A = `D:\o15\cands\c4_iirshallowtt\forge_ltopgo_c4iir.exe` + `setoption name IirShallowTt value 1`,
engine B = the lock. Exe sha256, ON bench and check results: `D:\o15\cands\INDEX.md` and `logs/RESULT.json`.
Patch: `c4_iirshallowtt.patch` (src/search.cpp only, +9), applies with `patch -p1` to git d4f4312.

## What it changes
The lock reduces the depth by one at PV and cut nodes (not in check, depth >= IirDepth = 4) when there is no hash
move. With the option, the same one-ply reduction also applies when a hash move exists but its entry is more than
IirDepth plies shallower than this search (`tt_depth < depth - IirDepth`). Option `IirShallowTt` (spin 0..1, default 0).

## Why it should gain
Internal iterative reduction exists because a node without a hash move will probably be ordered badly and is likely
less important than one with a good hash move; a hash move from a search more than four plies shallower carries
little of that ordering knowledge (it often comes from a quiescence or very low-depth store), so the same argument
applies to it. Searching such a node one ply shallower first keeps the work where the table already knows the
position well, and the next iteration - which then finds a deeper entry here - does the full-depth work only for the
nodes that still matter (ON bench d22 19,939,843 vs 34,048,354 nodes).

## OFF identity
`IirShallowTt 0` fails the first test: the lock's search. Kit OFF node identity ALL OK, bench d11-d22 + perft = pins.

## Own review (structured self-review, NOT independent)
- The two IIR tests exclude each other (no hash move / a hash move), so a node is reduced at most once.
- `tt_depth` is -1 without a TT hit; a hash move implies a hit, so the comparison uses a real stored depth.
- Singular extension needs `tt_depth >= depth - 3` (before the reduction), so it never runs at a node this rule
  reduces; a singular verification search (excluded move) sees a deep entry and is not reduced by it.
- Quiescence stores depth 0: positions first met in quiescence and later in the main search at depth >= 5 are now
  reduced once - that is the intended case, not a side effect.
- Risk: PV nodes after an aspiration re-search that only hit shallow entries lose one ply once; the next iteration
  restores it. Node counts at depth drop a lot (d13 724,372 vs 862,329), which is not strength by itself.
- PGO cold-path note as for every option line.

## Check results (generated)

- exe `D:\o15\cands\c4_iirshallowtt\forge_ltopgo_c4iir.exe` sha256 `34055169d6c33e5ba94cfecc6b4699ede5e7dfa8a77c3e093c6343e72f2aea05` md5 `5ef69ec6f71b8a0bc60f360f65a85943`; kit pc1 = pc2 `34055169d6c33e5ba94cfecc6b4699ede5e7dfa8a77c3e093c6343e72f2aea05`
- ON bench d11 / d13 / d16 / d20 / d22: 309855 / 724372 / 2173900 / 12053035 / 19939843; OFF = the lock pins; perft 4865609 / 193690690 both ways
- cand_pack checks: patch_applies PASS, cleanroom_lint PASS, kit_build PASS, pc1_equals_pc2 PASS, kit_identity PASS, kit_vfmadd0 PASS, kit_missing_profile0 PASS, kit_on_live PASS, exe_copy_sha256 PASS, pin_off PASS, pin_on_live PASS, smoke PASS
- smoke with the fixed clock (12:37 fix): PASS - 21 games, 2634 plies, illegal 0, crashes 0, hangs 0, time losses 0
- R13 cand_checks (T1 / T4 movetime smoke with perft-1 legality, mate probe 22 positions at 3M nodes): FAIL; mates OFF 19 / ON 21; strict-rule flips: mate lost: IirShallowTt=1 3k4/8/8/8/7r/8/8/6K1 b - - 0 1 OFF mate 15 ON cp 517
  - 30M re-probe (lost) `3k4/8/8/8/7r/8/8/6K1 b - - 0 1`: 3M OFF mate 15 / ON cp 517; 30M OFF mate 11 / ON mate 12 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/1r6/8/8/8/4K2k/8/8 b - - 0 1`: 3M OFF cp 474 / ON mate 16; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/8/5K2/7r/8/8/k7/8 b - - 0 1`: 3M OFF cp 503 / ON mate 17; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
  - 30M re-probe (gained) `8/3k4/5R2/8/8/8/8/2K5 w - - 0 1`: 3M OFF cp 544 / ON mate 21; 30M OFF mate 14 / ON mate 13 -> horizon flip (both find it at N)
- CI ASan+UBSan self-play: run 41628366851 success on 9fc59ea3c497 (patch sha256 = the built one)
