# Archived NPS affinity claim check

Inspected immutable source/evidence revision:
`3afd230fb26dcf70771133dc513b527763f2f8fa`.
No engine, build, timing or performance experiment was run.

**Factual correction:** the archived records show same-guest-logical-CPU-4
launches and ABBA pairing. The review's statement that these runs were "not
same-core paired" conflicts with the recorded protocol. This corrects the
affinity/order description only. Shared-host speed remains unproven, and
stage 2 remains a possible regression pending the controlled PC protocol.

| Original directory in `/workspace/forge-sol-nnue-speed-audit-20261024/` | Launch records | Recorded pin | Warmups | Measured order |
| --- | ---: | --- | ---: | --- |
| `nps-avx512-stage1` | 20 | `taskset -c 4` | 4 | 4 × OFF/ON/ON/OFF |
| `nps-nocopy-stage2` | 20 | `taskset -c 4` | 4 | 4 × OFF/ON/ON/OFF |
| `nps-align64-stage3` | 20 | `taskset -c 4` | 4 | 4 × OFF/ON/ON/OFF |

For all 60 processes, `process.json` and `sample.json` agree on the full argv,
and their fields agree with the corresponding `profile.sequence` and
`summary.samples` entries. Every process records `EXITED`, exit 0. Each profile
selects CPU 4 from allowed affinity `[0,1,2,3,4]`; each stage's timestamps are
serial and nonoverlapping. There are 12 warmups and 48 measured processes
overall, grouped into 12 ABBA blocks / 24 adjacent ON/OFF pairs. All rows retain
identical before/after source, executable and runner hashes and bench20 nodes
11901452. These are checks of archived records, not new measurements.

All three original `summary.json` files are byte-identical to the immutable
Git proofs below. Their embedded samples are exactly equal to every original
row `sample.json`. Stage 1's original profile is also byte-identical to the
committed `stage1/nps-profile.json`; all three summary profile hashes match
their corresponding original profile bytes.

| Committed path under `validation/sol-nnue-speed-audit-20261024/` | SHA256 |
| --- | --- |
| `stage1/nps-summary.json` | `280f8429ae093f998ac35c8da5258ab0a4b0ee76f633c621d83222e428bfe04a` |
| `stage2/nps-summary.json` | `aa6e87e840a09301dc9ba08f85e6ca76faa1f4422b40923031071480d7f30308` |
| `stage3/nps-summary.json` | `7e4bacf1a64e6f5e5dba3a53748a212d7647fd78d87544f96d70874bff0daf72` |

The JSON stores requested launch affinity and exit status; it does not contain
independent continuous kernel affinity readback. Pinning a guest logical CPU
also does not guarantee exclusive physical-host resources or eliminate
hypervisor/shared-host noise. The original descriptive median ratios remain
0.9562505598 / 0.9154113959 / 1.2488884484, without accepted speed conclusions.

`OLD_NPS_AFFINITY_RECEIPT.json` preserves all 60 row arguments/order, timestamps,
original process/sample SHA256 values, profile/summary hashes and commit
comparisons. `audit_old_nps_affinity.py` repeats this read-only audit without
launching any engine or opening transcript bodies. Original evidence was not
changed; no repository files or refs were modified by this audit.
