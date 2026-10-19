# Hosted performance package status

The new package is `.github/hosted-nnue-performance/`, with a separate `.github/workflows/forge-hosted-nnue-performance.yml` workflow. The existing strength workflows and packages are unchanged by this work.

Frozen comparison: baseline 6.4.9 `4edda780c68a742f20565d4e6a54a0c99a2c88a6` and candidate 6.4.10 `36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`. The package starts `PENDING_REVIEW`; no hosted performance measurement has been run while preparing it. Local validation uses deterministic fake subprocess fixtures and checks the build preregistration gates, parsers, calibration thresholds, finite six-block confidence interval, fixed process schedule, failure cleanup and immutable-input enforcement. These tests provide wrapper evidence, not engine performance evidence.

Review the complete package before changing its status to `PREREGISTERED_REVIEWED_READY_FOR_SINGLE_PUSH` and freezing the launch branch. The workflow only launches for a new `forge/hosted-nnue-performance-20261019-*` push and attempt one. One primary calibration failure ends the experiment before all A/B. No changed iteration counts, retry, dropped observation or alternative timing metric can rescue a failed gate. Preserve any such failure as the outcome.

The workflow exports actual sources; builds serial matched GCC14 generic-v3 strict non-LTO engines and the same drivers; runs both full CTest suites, both byte-identical NNUE snapshot comparisons and exact 419798-node bench preflights; then archives actual executable/core bytes and checksums before timing. The primary whole-process CPU and wall measurements are separate from the fixed public-update kernel diagnostic. No engine games, NPS-derived acceptance, Elo, Windows or Ryzen performance claims follow from this pilot.

Every ordinary failure retains commands and raw outputs. Immutable inputs are checked in finalization, and the workflow always uploads the evidence and saves a unique `results/nnue-performance-RUNID-ATTEMPT` branch. A lost runner or missing evidence cannot support a positive claim.
