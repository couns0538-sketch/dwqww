# S28v2 Linux guide — 2026-10-25

Use the current JobC/S01 L′ or B source snapshot as `--lock`. The kit writes only into a NEW output directory and leaves that input unchanged. Put the flat delivery files together; the portable queue resolves its patch relative to the queue file. Python3.10+, Git, GNU patch, CMake, a C++20 compiler and objdump are needed for a fresh native run. No PC lock-recipe or PGO script is invoked.

Dry-run f006 first:

```sh
bash /path/to/forge_sol_S28_v2_lock_transition_20261025.sh \
  --lock /path/to/current_Lprime_or_B \
  --net /path/to/resid_h256_e48_f006_b06_ep48.inc \
  --net-sha256 0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661 \
  --refs /path/to/forge_sol_S28_v2_trusted_refs_20261025.json \
  --refs-sha256 47afc8ab50e3df553e8f30b6b06b914c24285dcbde6ac69ab76f535812a187e1 \
  --pin-helper-sha256 af138972b44e9e95f85bd9c3eaed82e04533b91db9b1304350d8c2781f8be8a5 \
  --pin-proposal /path/to/forge_sol_S28_v2_e48f006_pin_proposal_20261025.patch \
  --pin-proposal-sha256 7feadcd7212c1106f44559bac641f80eaa39c8289bce9d86e5c1aa65c9d29136 \
  --pin-proposal-net-sha256 0fdf9bdb6bdf4c9f1622bcef29921912acb139fdf388e541b017a948118d4661 \
  --queue /path/to/forge_sol_S28_v2_queue_portable_20261025.json \
  --out /path/to/NEW_f006_results
```

Repeat with B/L′ as appropriate. For the next source-only s198 dry-run, omit all three `--pin-proposal*` arguments and replace the net path and net SHA with `a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638`. Its fixed nodes are supplied; exact current-source pin observations remain UNVERIFIED until recorded.

For a fresh native build on a host with enough free disk/RAM, add `--execute --jobs 2` and a NEW output directory. This fresh all-target route was not executed in this session. It builds a canonical release base and explicit release/expose queue flavours, gates each new engine with its first bare d11, then runs fixed refs, perft, FMA, S01 and current CTest. The explicit f006 pin proposal is applied only after independent observations and preserves the original test/helper logic. It remains an isolated proposal and never changes the input lock or live PC.

Supply a real read-only AUTOLOCK evidence packet with `--audit-evidence /path/to/packet.json` using `forge_sol_S28_v2_autolock_schema_20261025.md`. Missing facts are UNVERIFIED; contradictions FAIL. The terminal checker has no PC calls and cannot write a CR_PASS record. Original f006 pin attachments must remain unapplied in the actual AUTOLOCK; the rebased qualification patch is a separate artifact.

Pure checks:

```sh
python3 -B /path/to/forge_sol_S28_v2_contract_tests_20261025.py --module /path/to/forge_sol_S28_v2_lock_transition_20261025.py
python3 -B /path/to/forge_sol_S28_v2_audit_tests_20261025.py
python3 -B /path/to/forge_sol_S28_v2_autolock_tests_20261025.py
```

From the delivery directory verify `sha256sum -c forge_sol_S28_v2_SHA256SUMS_20261025.txt`. The raw bundle is gzip JSON Lines: decode each record's base64 data and require exact byte length/SHA256; never restore it over existing files.
