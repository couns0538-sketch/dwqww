# Buffer patch and source-ZIP delivery verification

**PASS.** Both delivered patches apply to exact lock
`f4911f2709bd5ae7e5fca7aea30aac5d87314a05` in fresh scratch exports with
`/usr/bin/patch --batch --forward --fuzz=0 -p1`, first using `--dry-run` and
then actually applying. Every exit is 0; no offset, fuzz, rejected or reversed
hunk is reported. `*.command.json`, `*.stdout` and `*.stderr` retain each exact
invocation and output. This verification made no repository/index/ref changes
and ran no compiler, benchmark or engine.

| Delivered file in `releases/sol-next-20261024/` | SHA256 |
| --- | --- |
| `buffer_fix.patch` | `3cf718189340d1b8ea47361e4c8ede0203b39da749938a670a41d50cad19fc6c` |
| `buffer_only.patch` | `32967232826f1fb446ae7651068446926ce37a727ca71b480d5f465efc4bd6ab` |
| `forge-buffer-source.zip` | `e05e75180a6e9b2c390fb7711aa6f686b51ac172333ab65670347bbce852fb51` |

All 34 core/build files (`CMakeLists.txt`, license, bench, include, src and
tests) resulting from the cumulative patch are byte-identical to the ZIP.
The standalone patch preserves lock `nnue.cpp` and imports no optional
partial-iteration guard. The cumulative patch intentionally retains those
previously reviewed optional changes; these are distinct patch scopes.

ZIP CRC, safe unique paths, external archive size/hash, and all 99 embedded
manifest size/hash entries pass. Each of the 99 files is byte-identical to
declared source commit `30e703edc90976b9c59fb22912ddabb3b690658f`.
All 89 tracked paths under CMake/license/bench/include/src/tests/tools are
present. All CMake-referenced inputs and quoted local includes resolve.
The four included `.inc` files are `book_data.inc`, `eval_params_table.inc`,
`nnue_weights.inc` and `polyglot_keys.inc`; the network remains
`74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`.

`RESULT.json` SHA256:
`4148c382990295038d1c467b450e5d05fd118889ba75bf32246d2b19e07474bb`.
`TRACKED_BUILD_INPUTS.json` preserves the additional complete-subtree check.
These checks establish delivery integrity, not new runtime qualification.
The int16 cumulative delivery remains pending until root supplies its files.
