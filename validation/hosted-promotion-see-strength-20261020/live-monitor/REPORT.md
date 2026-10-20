# Hosted 17 first-attempt observation

The immediate observation at **2026-10-20 20:32:48 UTC** found [run 39492317400](https://github.com/couns0538-sketch/dwqww/actions/runs/39492317400) already **failed**. The public commit link verifies exact payload `352b6ff2c0e4d05310451cb7ae4f3474e45670ed`. Its job is `118868403295`, `promotion-see-strength`.

| Public step | Result | UTC interval |
| --- | --- | --- |
| Freeze/build serially before any timing | Success | 20:29:26–20:30:49 |
| Calibrate then run one bounded 128-pair native SPRT | Failure | 20:30:49–20:30:52 |
| Archive original evidence | Success | 20:30:52–20:30:53 |
| Upload all raw evidence | Success | 20:30:53–20:30:56 |
| Preserve evidence on fresh results branch | Success | 20:30:56–20:31:00 |

The visible error is only **“Process completed with exit code 1.”** Logs require sign-in. The failed step combines readiness and SPRT; **actual A/B match start is not established**, and no particular readiness subgate, engine fault or root cause can be identified from this page. The Node.js deprecation annotation is separate and does not establish the cause. No PGN, strength result, hosted executable hash or raw transcript was verified.

The public run lists artifact `12296253341`, `forge-hosted-promotion-see-strength-39492317400-1`, displayed size `21.9 MB`, displayed SHA256 `ed08f163ddefe4917984e44c969facf202adc66a782f2fda4bc3c9bea7b1582b`. This is metadata, not a downloaded/verified ZIP. The existing local workflow derives results branch `results/promotion-see-strength-39492317400-1`; its existence/content was not independently fetched here. Root can inspect that preserved attempt without repeating it.

Original HTTP-200 run/job HTML, access records, parsed step attributes, visible annotation text and qualified state are preserved under `20261020-203248/`. `qualified-state.json` also records hashes of the local frozen workflow/protocol/runner/inventory and source pins baseline `21538ec5416c909fc98a08688242a0b3b9710b25`, candidate `47f0560221d986e41a309853e1295c557fcf5bf6`; those local hashes do not substitute for hosted runtime provenance.

Monitoring stopped after this one terminal observation (two public GETs). No further polling, API/auth retries, engine/test/build execution, Git action, dispatch, rerun or recovery was performed. Frozen package/protocol/workflow and earlier reports were untouched.
