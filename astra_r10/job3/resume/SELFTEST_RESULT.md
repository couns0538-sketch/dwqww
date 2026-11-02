# Bundled disposable selftest — UNPROVEN

The matching skill requires its disposable selftest before the native adapter
proof. R10 missed that ordering: this selftest ran after native proofs01/02/03.
That deviation is explicit and is not retroactively satisfied by a later PASS.
The native adapter proofs retain their own independent evidence and limitations.

`skill-fixture-actual01/RESTART_PROOF.json` reports PASS. Only the newly spawned
fixture child was terminated (exit 1); one genuinely incomplete next-shard stage
and two stage files were retained. Uninterrupted and resumed outputs matched:

- MD5: `efd4d2e8d2829b84108d7da32bae00dd`
- SHA256: `703ae72d2663d0f196854151eebfc9a1f85a22f3cb8606898a5fdebfe121916f`

Helper SHA256: `78192863ce64214b8f463231e319286a9c401013d0db4dd7e1e40c8c43b2e2ca`.
`ORDERING.json` binds the helper and states auxiliary disposable-fixture scope.
This is not a chess-format adapter, native teacher qualification or training gain.

The first admission observation was rejected (CPU3 38.9%/38.5%); no workload ran.
A later inspected pair passed (CPU3 10.9%/17.2%, host mean 79.98125%/82.425%).
The safe launcher then exited 0, Idle CPU3, one worker, no capture/floor errors.
Both rejected and accepted observations are retained under packaging loadshard01
and loadshard02 launcher records. No trainer, gate, crew or other process was
stopped or modified; no GPU/training work occurred.
