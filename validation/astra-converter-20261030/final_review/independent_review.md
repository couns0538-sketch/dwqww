# Forge Job 2 converter: independent final review

Review agent: `/root/final_converter_review`. Date: 2026-10-30 UTC.
Workspace: `/tmp/forge-astra-fen-convert`. Initial HEAD observed:
`0b1daabea591ef625538f9356566386059e9fa44`.
This review does not edit engine, implementation, or shared test files. The
implementation agent receives reproductions and makes the fixes. Root owns the
overall requested 20-minute review window; this document makes no independent
elapsed-window claim.

## Findings and active resolution record

1. **Completion accounting could report PASS for impossible receipts.** At
   approximately 09:24:51 UTC a generated one-row artifact was altered only in
   `COMPLETE.json`: `counts.in_check = 400`, `chunks = 999`. `verify()` accepted
   it. Preserved reproduction:
   `/tmp/astra-converter-review-_h2j_egr/summary_count`.
   The implementation now checks exact integer/nonnegative known counts,
   per-chunk waterfall totals, summary status/chunk count, and aggregate counts.
   Independent recheck rejected this case with
   `ValueError('summary status/chunk-count mismatch')`. Companion unknown/negative
   count mutations were rejected. This finding is fixed in the reviewed code.

2. **Required file roles were not bound to the hashed file map.** At 09:28:42 UTC,
   changing `chunk.text` to `../input.txt`, while leaving the original `files`
   map unchanged and recomputing the COMPLETE receipt hash, was accepted. The
   external text had the same row so bullet comparison also passed. Artifact:
   `/tmp/astra-review-role-ysk4m05n/text_escape`.
   This is a schema-validation defect: receipt hashes do not substitute for
   required-role membership and path confinement. Sent to implementation agent.
   Independent recheck of the original saved artifact now rejects with
   `ValueError('required data role absent from files manifest')`. Fixed.

3. **Requested binpack could be omitted without verification failure.** In a
   generated-binpack run, the binpack entry was removed from the chunk map and
   the bytes moved to a retained sibling file. COMPLETE still said `GENERATED`;
   its chunk hash was recomputed. `verify(out, adapter)` returned PASS and
   `PERFORMED_WHERE_PRESENT`, although it decoded zero chunks. Artifact:
   `/tmp/astra-review-role-ysk4m05n/omitted_binpack`; retained binpack:
   `/tmp/astra-review-role-ysk4m05n/retained_omitted.binpack`.
   Sent to implementation agent: require binpack for every configured chunk,
   bind it to its file map, and report actual decode counts. The original saved
   artifact now rejects with `ValueError('required binpack missing from sealed
   files')`. The valid native fixture reports exactly one decoded chunk and one
   decoded row. Fixed.

4. **A retargeted source symlink could falsify the recorded input identity.** At
   09:29:14 UTC, the source link resolved to A during initial hashing, then to B
   before the source iterator opened it. The run sealed B's row but its input
   identity claimed A's SHA256. The final guard rehashed the already-resolved A
   path rather than the original link. Artifact:
   `/tmp/astra-review-input-identity-_b94nv36`. No source bytes were deleted;
   `original_input_link` retains the original link. The race was injected by a
   local wrapper around `sources()` solely in the test process.
   Sent to implementation agent to pin resolved references and recheck original
   bindings. A fresh replay against the fixed code at
   `/tmp/astra-review-input-fixed-rkx12jfq` read only pinned A bytes and raised
   `ValueError('input path binding changed during run')`; COMPLETE was absent.
   Fixed. This does not invalidate the separately checked real 1M artifacts.

5. Documentation initially omitted required `--shard-id` in its production
   command and retained the superseded requirement for authenticated game IDs.
   The current converter document now states the user's accepted whole-shard
   013/014 policy, rejects those training shard IDs, and retains separate
   position-holdout exclusion without inventing game IDs. Rechecked corrected
   document. An unclosed holdout-text stream also emitted ResourceWarnings in
   the first test run; the later 35-test run emitted none.

## Independent verification performed

- `python3 -m unittest discover -s tests/data2 -v` from the workspace: initial
  31 cases passed, then 35 cases passed after accounting regressions were added,
  and finally 38 cases passed after role and input-binding fixes.
  The adapter tests used `/tmp/astra-binpack-work/forge_binpack_adapter`.
- All ten original 100,000-row bullet chunks had every file size/SHA256 checked
  against their chunk receipts, then were read by the independent official
  MIT bulletformat loader:
  `/tmp/astra-bullet-check-target/release/forge_bullet_loader_check <bullet> <text>`.
  Fresh result: 1,000,000 rows, zero mismatches, all chunk hashes passed.
- Fresh native decode of
  `/tmp/astra-binpack-work/sample_first_1000000.binpack` using
  `/tmp/astra-binpack-work/forge_binpack_adapter decode <binpack>` compared every
  returned line with the first 1,000,000 rows of
  `/tmp/astra-a1-data-input/extracted/forge_selfplay_003.txt`.
  Result: exact bytes, 1,000,000 rows, 216,652 castling-right rows, 35,547 EP rows.
  Decoded/original slice SHA256:
  `f8fb8e78cfc643bbc3a79f0384aafc848bb679e01a9e5b71ca97fd91966766be`.
  Binary SHA256:
  `db200a129194456ffbdc101e2154a5d5fd920c175fea12b69e878c38a28c9396`.
  These are format qualifications; transport fallback moves do not establish
  teacher filtering or training readiness.
- Partial-tail recovery: checkpoint a two-row conversion after one row; add
  `data_aborted/rows.bullet` containing invalid tail bytes plus an incomplete
  `chunk_000001.json.pending_abort`; resume. Exactly two rows verified, and all
  ten previously existing files retained byte-identical contents. Artifact:
  `/tmp/astra-review-recovery-61elc2jn`.
- Native filter fixture: eight input rows produced exactly one each of
  `score_cap`, `result_disagreement`, `in_check`, `bestmove_capture`,
  `bestmove_promotion`, `terminal`, `duplicate`, and `kept`. The single retained
  row also passed native binpack decode comparison. Artifact:
  `/tmp/astra-review-filter-hxzkd6bk`; probe:
  `/tmp/astra-a1-native-build/budget-status/forge_data_probe`, nodes=1024,
  one thread, 1 MB hash; declared shard `003`.
- MIT closure: independently checked the sizes and SHA256 of all five external
  headers in `/tmp/astra-binpack-work/deps` against the committed dependency
  manifest; each contains the explicit MIT permission notice; every quoted
  include resolves within the same five-file set. No GPL loader code is in the
  dependency closure. The bullet loader Cargo lock has only bulletformat and
  the original checker package.

## Reproduction commands for preserved failure artifacts

```bash
cd /tmp/forge-astra-fen-convert
python3 tools/data2/convert_dataset.py verify --out /tmp/astra-converter-review-_h2j_egr/summary_count
python3 tools/data2/convert_dataset.py verify --out /tmp/astra-review-role-ysk4m05n/text_escape --binpack-tool /tmp/astra-binpack-work/forge_binpack_adapter
python3 tools/data2/convert_dataset.py verify --out /tmp/astra-review-role-ysk4m05n/omitted_binpack --binpack-tool /tmp/astra-binpack-work/forge_binpack_adapter
python3 tools/data2/convert_dataset.py verify --out /tmp/astra-review-filter-hxzkd6bk/out --binpack-tool /tmp/astra-binpack-work/forge_binpack_adapter
```

The first three should fail after fixes; the last should pass. The link-race
test must start a fresh run with the source reference changed between initial
hashing and iteration; reading the already sealed artifact alone does not
replay the race.

## Reviewed hashes at 09:29:41 UTC

Concurrent implementation work was ongoing; these identify that checkpoint,
not the final delivery. A final hash snapshot will be appended after rechecks.

| File | SHA256 |
| --- | --- |
| `tools/data2/convert_dataset.py` | `13c983b86fff0ed4290d953d2f380a0dd9255bd1254620fbee3ea48d827cd566` |
| `tools/data2/bullet_records.py` | `1f07d91863aaababbab0f84e489a4a2daa23acc538a392b3454d22219d7aad36` |
| `tools/data2/forge_binpack_adapter.cpp` | `267a0da5ed7b0131a09a1554549c2c6b50dd64833f35b22962f09e9409b15152` |
| `tools/data2/run_1m_roundtrip.py` | `25803c8308ef18e89566283f56fa6a6598a7c515605745284dd760f29a322dd1` |
| `tools/data2/fetch_binpack_dependency.py` | `620832159a4a5740078f772cfec3cb491bc6f6424e11654997b550ef8522129b` |
| `tests/data2/test_converter.py` | `215b1ff8f03764c879cfa0d2d3d6a2fcf2c0d4af5c20ed2a638f8a4a51f744a9` |
| `tests/data2/test_binpack_adapter.py` | `52ca9b564d2fc580967c30b6ad4def05a20ceca9dfdaf62d3756e1894f79690a` |
| native binpack adapter | `d97b9eacbe7ed757359f0f2dc05a3a313a1c470f485a957b0a55b3243bf56c86` |
| independent bullet checker | `0134d1f4928d6a4ea6b23109359bdddf685878b7d52b3f387991d12f392586d2` |

## Scope limits

Private complete 013/014 position holdouts were unavailable to this review.
No claim of zero overlap against those absent files is made. The accepted
whole-shard split is the user's policy, not reconstructed game authentication.
Windows execution, GPU training, one-epoch loading, engine strength, and export
parity are outside this review. The binpack decoder explicitly handles this
adapter's independent-record format; this is not a general arbitrary-binpack
fuzz-security audit.

## Final recheck checkpoint: 09:33:28 UTC

All four concrete findings above were independently replayed and are fixed.
The fresh full data2 suite passed 38 tests. The original malformed-manifest
artifacts reject; the valid native filter artifact still verifies. Implementation
also now hashes imported converter dependencies, closes holdout/source streams,
checks free space before index creation, and fsyncs native output/log files and
the chunk directory before publishing the receipt. These are source-reviewed
hardening changes; a power-failure durability test was not performed.

Only `tests/data2/test_converter.py` and `tools/data2/convert_dataset.py` appear
in the tracked working diff at this checkpoint. The added data2 adapter,
qualification code, documentation, and evidence are separate untracked additions;
no engine source edit was observed.

| Final reviewed file | SHA256 |
| --- | --- |
| `tools/data2/convert_dataset.py` | `64166f4d6b4ccad63d89ad07bd412546820cc5ae1981c8b348a66afd68c2260b` |
| `tests/data2/test_converter.py` | `ebfd00b7ab49f7ef46e739b54a9474394c9201ab72c5fdef9bd24153f173617d` |
| `docs/ASTRA_CONVERTER_20261030.md` | `6c4103ab8195df98e2f0592d293a53343253d9080564d2d8a5a71628e2f13655` |

Other reviewed code/native hashes remain as recorded in the 09:29:41 table.
Future changes require a new verification checkpoint; this is not a blanket
approval of subsequent edits.
