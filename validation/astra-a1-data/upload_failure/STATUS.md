# Upload-specific authentication failure, 2026-10-30

The release page was created successfully (id428684041), but cloud gh asset upload exited1 with HTTP401 Bad credentials from uploads.github.com. API-host POST is unsupported (404). Release metadata confirmed zero assets after that failed attempt. Git pushes/API writes remain verified. Source, tests and compact audits are pushed; no large-asset publication is claimed.

An additive OPTIONAL FORGE_RELEASE_TOKEN requirement was saved to the cloud environment draft for uploads.github.com only; it is NOT supplied, applied or published. Do not change working GH_TOKEN/proxy credentials. The supported UI would require review/save/publish if this alternative credential becomes necessary. A repository Actions delivery route using exact Git blob bytes is being tested first; no user action is required if that succeeds.

Original artifacts remain under /tmp/astra-a1-publication. The workspace filesystem has only about8MiB free; /tmp has3.5GiB free. No files were deleted to gain space. Keep this active workspace until original artifacts are published or copied securely; Git contains all small recovery receipts and hashes.
