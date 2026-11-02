# Collector identity correction — UNPROVEN

Focused independent review identified one confirmed defect: the collector bound
the admission JSON and completed launch manifest, but did not rehash the archived
launcher and wrapper named by the command-binding receipt. It could therefore
have packaged later changed helper bytes while retaining an earlier claim.

The fix rehashes the archived launcher against both the receipt and the accepted
immutable identity
`842d6520058eb9f5c14d7426ca3bad92f080afb5f5684f1c43ab1a56fe38c21d`.
It also rehashes the wrapper against its bound SHA256, returns both bindings and
checks them again against the final source-to-pack artifact map. The collector
itself remains unexecuted; no sample, native input freeze or pack was created.

Six focused synthetic fixtures passed, zero errors/failures/skips, under the
full-root safe launcher. They cover valid bindings, helper/wrapper drift before
validation, a wrong archived identity in the binding, and helper/wrapper drift
after validation but before artifact freezing. Original evidence is
`sealer-tests-bindings01/` and `sealer-tests-bindings01-launch/`.
Admission was separately inspected: CPU3 9.9%/21.2%, host mean 80.375%/83.575%.
The launcher exited 0, Idle CPU3, one worker, without capture/floor errors.

Tested collector SHA256:
`e04445badcf2aea07da3684a9ff085d13f3c175943cbd2add5d9a76dbb8f2f74`.
Fixture SHA256:
`ea9589133f40b0152358d56087b89a25a5b8e3dc78d032932c379e183a940451`.

The focused independent recheck by proof_contract closed the admission identity
finding at the tested E04445BA candidate without another finding.

A later, separately reviewed metadata addition corrects the runtime evidence
mapping. Final collector SHA256:
`fe30f3e3f5a590ea966ce1b2f44066caecf8d1d5bc56cd1643993e771928f497`.
It requires the original malformed receipt and the new current-D identity
manifest as separate artifacts. INPUT_MAP labels the original as a historical
copy receipt with lost per-file-list limitation, and the new receipt as current
D-only identities. Both pinned hashes are checked again against final artifacts;
the 11,015,923-byte current report is hashed as an artifact, not JSON-parsed.
Proof_contract's focused recheck found no issue in that addition. Admission
logic and its six fixture cases were unchanged; no repeated full review or
native collector execution occurred.

The draft is ready for root-controlled collection after final native/regression
receipts and HANDOVER are frozen. This review is not a claim that a pack or sample
already exists, or that training is ready.
