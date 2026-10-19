# Local run filename clarification

The successful three compiler/sanitizer commands in EVIDENCE.md were executed locally against `github_short.cpp`, which is byte-for-byte identical (SHA-256 `5279c3f1a8f6a777caf99a778513efcc81dcbf6ea90d7cc8b40be2528c9599ce`) to the GitHub-published source `rule50_producer_consumer_repro.cpp`. The commands in EVIDENCE.md replace that local filename with the published filename for easy reproduction. Everything else in those commands is unchanged. The original logs and source hash are preserved.
