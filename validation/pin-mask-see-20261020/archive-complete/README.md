# Complete 6.4.16 evidence archive

Frozen source: `553caef144ae2e1b696ba35d7a0eb1a50a03fde9`; parent: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`.
Status: `PASS_COMPLETE_16_ARCHIVE_VERIFIED`. Local evidence preservation only; no new engines/tests ran.

Original full native16 TSan CTest FAILED:8/9 suites passed. The original failure,
failed/parser partial evidence and corrected exports are retained. The separate
five-case OwnBook diagnostic provides finite coverage only and does not supersede
that failure. These limits are recorded inside `archive-provenance/ROOT-CLEARANCE.json`
and repeated in `CORRECTNESS-LIMITS.json`. No correctness/release/NPS/Elo acceptance follows.

Unchanged trusted archiver SHA256: `952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c`.
`RESULTS.json` is the complete receipt. The three LIVE inventory JSON files record
1035 included originals (258695890 bytes) unchanged before copy,
after staging and after archive. Independent copies matched SHA256/size/file modes.
All 1043 payloads passed full split-ZIP reassembly and hash verification.
The immutable mask prototype was retained in full (102 original files), including raw
archives, source/counterproof and failed diagnostic/artifact-write/limitation records.

Concatenate the two parts in manifest order to recover a 95778363-byte ZIP.
Reassembled SHA256: `ecafdc838d01ed22df10fce9b1a480bead0f1b437babf90099b8e88223e9178e`.
`ARCHIVE-SHA256SUMS` covers both physical parts and the external manifest.
Payloads are below `files/payload/` using original absolute path components;
`files/archive-provenance/LIVE-FILES-AND-MODES.json` records original paths/modes.
The internal `manifest.json` records every archived size/hash.

All originals and complete staging remain at
`/workspace/.cloud-setup/pin-mask-553caef-complete-evidence-stage`.
Prior15/older trees were not recopied; their durable references remain in prior archives/Git.
Active promotion/source17 outside the immutable mask prototype and hosted-strength work
were excluded. The archive output excludes itself to prevent recursion.

`IGNORE-CANDIDATES.json` lists exactly10 byte-verified prospective raw paths:
16validation source TAR, six Windows original PEs, static core, disassembly and
windows-originals.zip. User-facing release ZIP/executables and prototype files are
excluded from the ignore list. No ignore/Git/source/docs edits or deletions occurred.
Root held included inputs frozen through the verified receipt; later updates are separate.
