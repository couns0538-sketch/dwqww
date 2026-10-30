# QA fixes checkpoint, 2026-10-30

Starting reviewed source: 41d23db076f1b217d90a6f26779deb7125361edc.
Box-only work. No grok-pc access or training was attempted.

Completed: verified embedded GPL provenance in exact pinned external dependency
bytes; corrected current manifest/fetcher/wrapper/docs; explicit --accept-gpl3,
reject repository destinations; optional external adapter tests no longer run
implicitly. Four red policy tests now pass. Original historical logs retained.

WIP: safe disposable-index pruning, preflight/in-loop disk guards, no duplicated
full-FEN adapter input, measured disk budget, independent full-013/014 clearance
CLI. Current runbook already states intended final usage; those WIP commands are
not released for PC use until final validation is recorded. Full private holdout
clearance remains UNVERIFIED and blocks training, regardless of synthetic tests.

IDEA_SOURCE: crew QA review; original safety and provenance checks.
