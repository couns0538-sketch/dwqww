# Complete 6.4.15 evidence archive

Frozen source: `8d303e4ca0428e9750bbf3e2663c64d9fafbd1ad`; parent: `21538ec5416c909fc98a08688242a0b3b9710b25`.
Status: `PASS_COMPLETE_15_ARCHIVE_VERIFIED`. This is local evidence preservation, not publication or a strength/speed result.

The trusted unchanged archiver SHA256 is `952a090fee4f5ce67df93f5f389be5e46138f5b5787161c96156d80ad1fbaf6c`.
`RESULTS.json` records the complete receipt. `LIVE-BEFORE.json`, `LIVE-AFTER-STAGING.json`
and `LIVE-AFTER-ARCHIVE.json` are identical inventories of all 994 original files
(229419849 bytes), including original modes and timestamps. Independent staged copies
were checked by size, SHA256 and file mode. Full raw-ZIP reassembly and every one of the
1002 payloads were verified. No engine ran. Driver stderr is empty.

Reassemble the ZIP by concatenating the two parts in manifest order. Its SHA256 is
`5d09fd80411f2cd9b7039b3926c7567df7697784e6183b804bea2f8ba5c399d2` and size is 85979658 bytes.
`ARCHIVE-SHA256SUMS` covers both physical parts and the external manifest.
Payload files are below `files/payload/` using original absolute path components;
`files/archive-provenance/LIVE-FILES-AND-MODES.json` records their original paths and modes.
The internal `manifest.json` records every archived size and hash.

Originals and complete staging remain at `/workspace/.cloud-setup/pin-see-8d303-complete-evidence-stage`.
No prior 6.4.14 archive tree was recopied. Separate filter-cost and hosted-strength preparation
experiments are excluded. Prototype/coverage failed harness attempts and known limitation cases
are included in full. The output directory excludes itself to prevent archive recursion.

`IGNORE-CANDIDATES.json` lists exactly 31 prospective repository binary/archive paths, their
SHA256/size and matching raw archive member. These were byte-verified before this receipt;
no Git or ignore rules were changed, and no originals were deleted. Root clearance and the
prepared driver/scope/review metadata are retained here and inside archive provenance.
Included live inputs were frozen until the receipt; later documented changes are separate.
