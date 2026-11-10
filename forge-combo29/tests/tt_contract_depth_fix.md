# Opt-in LOW TT depth-overflow hardening

`FORGE_FIX_TT_DEPTH_OVERFLOW` defaults to 0. The enabled path changes both TT
store replacement predicates from `depth + 4 > entry->depth` to
`depth > static_cast<int>(entry->depth) - 4`. Entry depth is an unsigned byte,
so the right-hand side is always representable. The predicates are equivalent
where the original addition was defined; the new one also accepts INT_MAX
without overflow before the existing [0,255] storage clamp.

The exact original predicates remain under `#else`. No locked constants,
networks, datasets or normal search policy are changed. This addresses a
**LOW public-API edge**: normal search depth is bounded and no UCI-gameplay
trigger was demonstrated.

## Red/green evidence

- Original/default path: both NOTLS=0 and NOTLS=1 raise UBSan signed overflow
  for a same-key, occupied, BoundLower store at INT_MAX depth. Logs are
  `tt_contract_extreme0_ubsan.log` and `tt_contract_extreme1_ubsan.log`.
- Enabled path: both NOTLS variants exit 0, preserve the new score and clamp
  stored depth to 255, without UBSan diagnostics.
- Enabled ordinary contract suites also pass under TSan: stale/foreign/key
  rejection, generation wrap, replacement, rule50/clamping/partial-update
  policy, and 4 threads × 5000 exact-store/probe iterations per variant.

From `forge-combo29`:

```sh
# Known failing comparison, if rechecking the default-off branch:
tests/tt_contract_extreme_check.sh /tmp/tt-depth-red
# Enabled green, both implementations:
tests/tt_contract_extreme_check.sh /tmp/tt-depth-green \
  -DFORGE_FIX_TT_DEPTH_OVERFLOW=1
tests/tt_contract_check.sh /tmp/tt-depth-tsan \
  -DFORGE_FIX_TT_DEPTH_OVERFLOW=1
```

The enabled output and binary hashes are preserved in
`tt_contract_depth_fix_results.json` and `tt_contract_depth_fix.log`.
No speed or strength conclusion follows from these correctness checks.
