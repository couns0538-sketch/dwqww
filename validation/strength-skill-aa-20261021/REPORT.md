Repository-local strength skill refined to separate deterministic fixed-node A/A
from timed operational A/A. Existing skill and scenarios reused; no new skill,
global installation, engine run, match, packet edit or Git operation.

Before-edit copies, static old-wording/actual22 contract mismatch, and every
available prior strength-skill proof-file hash are retained here. The new scenario
uses actual22 protocol fields:4pairs,1+0.01,nodes0,identical_moves_required=false,
baseline/baseline. Its producer calls the actual PGN checker with identity off and
labels success operational readiness only. Eight normal complete paired games,
legality/openings/fault/input checks remain; variable timed moves/results alone
are not a harness fault. Frozen fixed-node identity failures remain failures.

Validation adapts existing skill-harness frontmatter/link/preservation checks into
this new directory; the old harness is not run in place because it writes its
historical outputs and hard-codes its original link count. Its source/hash and
all old receipts remain unchanged. New source-only application invokes the actual
PGN checker on the original8-game deterministic hosted A/A capture, then a clearly
labeled derived legal-prefix move-difference fixture. Identity-on must reject the
derived fixture; identity-off only establishes bookkeeping acceptance, not full
readiness or legality of an actual timed match. Normal-termination and complete-
pair negative controls must fail even with identity off. No claim is made that
any new timed A/A or positive producer readiness result was executed.

Actual checks/results, input hashes, derived-fixture provenance, prior-proof count
and diffs are in APPLICATION.json, validation logs and SHA256SUMS. This is static
and pure-data workflow validation, not a fresh-agent effectiveness study, causal
skill efficiency result, hardware qualification, speed or Elo evidence. Old failed
approaches/proofs retain original labels and bytes.
