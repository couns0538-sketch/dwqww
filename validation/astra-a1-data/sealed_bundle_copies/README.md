# Complete sealed relabel copies

These four subfolders are byte-preserving copies of the original completed runs,
without outer console logs added inside their seal boundary. All pass
`tools/data/check_data_bundle.py <subfolder> --full-records` after copying.
Original native IPC and all retained spool files are included.

Earlier sibling `relabel_256_*` folders are historical evidence assemblies:
console.log was added alongside their original manifest, so the strict checker
correctly reports an extra unmanifested file. They are preserved without changing
or deleting original evidence. Use these clean subfolders for bundle checking.
The compact pilot_10000 folder likewise contains selected evidence, not a full
sealed data bundle; the final release artifact will retain its complete original.

This packaging correction changes no records, hashes inside original manifests,
measurements or engine code. The checker caught a delivery-boundary issue.
IDEA_SOURCE: this project's immutable bundle verification contract.
