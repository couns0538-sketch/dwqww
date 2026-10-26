# Wave16: exact closed S08v2 cache proposal

Only two explicit CLOSED v2 build roots are allowed: Release_ON_window1/build and ASAN_v2_window1/build. The current B build cache and every other root are excluded. Source Lprime_v2 matches all80 freeze2923e86... hashes before/after; all24 executables, source/data/nets, raw logs, receipts, CMake/compile/link recipes and existing archives/maps remain intact.

42 singleton cache groups measure57,559,102 raw bytes and12,713,276 gzip6 bytes:44,845,826 net payload bytes. Projected allocated gain is44,855,296 bytes (42.78 MiB). Largest projected archive4,011,006 bytes. No selected alias is missing, no group was skipped, and the all-workspace alias scan reports no errors.

Reuses the vetted wave15 generator with exact v2 constants, current80-source freeze, latest cumulative12-target build receipts and native qualification receipts. Whole-build activity hits now propagate to all groups within that root; the original wave15 cwd gap is fixed in this generator.10 scope and4 activity tests pass. A port test's old three-root error-message expectation is retained as RED evidence and corrected to the two-root message.

Root must review the proposal and rerun `forge_sol_S00_sixteenth_activity_preflight_20261026.py --out NEW.json` immediately before retirement. Any visible cwd/exe/fd/map reference at or beneath either exact root blocks all its groups. Proc denials prevent a global absence claim; exact closed leases are still required.

This packet wrote metadata only. Root alone preserves sequential deterministic gzip archives, fsyncs, independently decodes/hashes using Python and GNU gzip, persists a durable all-alias restore map/journal, and retires complete verified groups. No original cache/source/ELF byte was changed by this subagent.
