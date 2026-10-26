# Independent read-only S09 source review, 2026-10-26

The reviewer confirmed that the single-bucket forward expression/export path
remain unchanged, bucket8 head selection includes kings, and head-major W2/B2
layout matches the preserved step1 contract. Recipe values match source log
line1627. No edits or heavyweight probes were performed.

Two concrete findings were corrected:

- Commented output-head defines could bypass shape validation; a shared literal
  directive parser now validates and replaces the same spans. A RED regression
  reproduces the former acceptance of contradictory heads8/single-head arrays.
- The standalone trainer's default optimizer import lacked qa_adam_dml.py; the
  unchanged supplied helper is now bundled with a full source hash.

Final read-only source recheck found no remaining blockers in the reviewed
paths. The reviewer did not run Torch, training or native tests and did not
claim their validation. Raw export/numeric test evidence is recorded separately.
