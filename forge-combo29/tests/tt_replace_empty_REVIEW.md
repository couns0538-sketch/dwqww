# Dedicated first-empty pass: temporary code-generation screen

Production unchanged. A source-only snapshot of 2da9593 was patched only inside
FORGE_SPD_TT_REPLACE_CACHE, preserving the entire prior hit scan. The temporary
candidate first scans all slots for the first empty, then enters cached-score
replacement only if all four slots are occupied. No occupied-prefix assumption
is made; BoundNone holes remain semantically supported by this source shape.

Reproduction: `python3 forge-combo29/tests/tt_replace_empty_validate.py`.
This recreates the temporary source-only snapshot and builds with the exact
GCC14 O3 strict-FP x86-64-v4 flags retained in tt_replace_cache_receipt.json.
Patch and pristine generated owned-probe disassembly are adjacent artifacts.
Temporary binary SHA256:
8afc01eb83760fc343f279304fd7953d2bb00518eb953e2590ceb3d659db7113

## Finding: intended save deferral does not happen

In the owned probe GCC delays age/depth scoring until after all four occupancy
checks (scoring begins0x30628, final occupancy branch0x30622), but hoists six
register saves to function entry: rbp0x30580, r15/r14/r13/r12/rbx0x3058a..30595.
It also spills the slot2 pointer to stack at0x305cd before the final hit checks.
Consequently even hit and first-empty-slot0 returns pay save/restore overhead.
This fails the requested objective of protecting common paths from scoring
AND register-save setup. Fewer source-level operations is not sufficient.

Owned-probe size622 bytes and locked-probe650 bytes are smaller than the prior
candidate, but code size alone does not show a speed improvement. No timing,
full-engine validation, or semantic TT oracle was run for this shape because
the initial assembly screen was not promising. No runtime defect is alleged;
this is a failed optimization-shape hypothesis for this compiler/flags.
