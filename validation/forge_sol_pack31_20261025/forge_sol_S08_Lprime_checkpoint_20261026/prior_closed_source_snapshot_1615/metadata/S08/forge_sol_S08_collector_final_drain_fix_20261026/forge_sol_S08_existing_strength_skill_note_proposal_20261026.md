# Proposed addition to the existing strength-validation reference

Existing target: `.agents/skills/validating-chess-strength/SKILL.md`, directly after its parser/readiness and process-observation guidance. This is an additive reference proposal for root, not a new/global skill installation or an already applied guide change.

After an expected terminal and explicit readiness fence, drain the owned child to EOF and validate both newly read and already queued stdout before accepting the result; retaining a raw log does not validate its contents. Include an actual deferred-queue control, late stdout on graceful quit for both precheck and operation children, stderr, and nonzero-exit controls; cleanup must release selectors, streams and pending reader queues on every path while preserving original raw bytes and return codes.

S08 proof: old collector5ef437/testsa054 falsely passed four late-stream close cases and did not reject the queued-tail case (five failing assertions). Fixed collectorbf5d18/testdb16 passes all29 combined tests. Exact records are in this folder; no native engine, compiler or Git command was run.
