# Synthetic identity ambiguity

Status: PASS for this information-loss counterexample only. Production game
separation and training readiness remain UNVERIFIED. These tiny files are
synthetic proof artifacts, not training exports or copied production rows.

From the ordinary initial board, both games play e4 e5 Nf3 Nc6 Bc4 Bc5 d3 Nf6
O-O O-O. Call the resulting position A. X cycles Nh4 Ng4 Nf3 Nf6; Y cycles
Nc3 Ng4 Nb1 Nf6. Both stop at the actual third occurrence after two cycles,
at ply18. The oracle verifies every move and the claimed draw. Eight quiet
noncheck positions are buffered per game at plies10 through17. Score0 is an
admitted synthetic value, not an engine-search claim. B is Y's position after
its first Nc3, at ply11.

In RAM, initialize the shared seen set to the union of all buffered first-four-
field keys except A and B. This is four keys. No key/hash set is serialized.
H1 appends Y: it emits A then B, both from Y, dropping six of eight rows.
H2 appends X then Y: X emits A; Y emits B, dropping fourteen of sixteen rows.
Both final seen states are equal and contain six keys. All six fixture keys
have distinct 128-bit digests. The emitted full ASCII bytes, clocks, result and
score are identical between H1 and H2. Their MD5/SHA256 values are in PROOF.json.

Assign A to train and B to val. Shared six-field, four-field and board+side keys
are each zero with 2/2 valid keys (100% fill, no parse failures). A reaches B by
the legal move b1c3 with exact full-FEN and halfmove-clock consistency. Yet H1's
two rows belong to one original game while H2's belong to two original games.
Legal continuity therefore cannot identify the original boundary. Buffered
writing and zero position overlap do not remove this information loss.

Formally, this serialization maps two different original game-ID sequences to
the same observation. Any rule using only that observation must give the same
answer for both histories and hence cannot universally recover their different
IDs. This does not prove leakage or ambiguity for any particular real shard.
It assumes the specified synthetic initial seen state; no preceding production
history for that state is asserted. Actual historical engine choices and
configuration remain unknown. The inspected writer's actual-threefold stopping
rule, first-four-field dedup and row serialization motivate this model; source
agreement is not provenance of the real shards.

The negative control uses an empty initial seen set and does not produce the
same two-row observation. The illegal-move fixture is refused. Reproduce with
the owned runtime and tools/r14_identity_ambiguity.py --out NEW_OWNED_DIRECTORY,
using the recorded one-CPU Idle resource-admission command. Never reuse an output
directory. MANIFEST.json binds the proof artifacts; proof and test logs are
separate evidence, and independent review remains required.
