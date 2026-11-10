# Final bounded TT outline experiment: negative assembly screen

Production unchanged. Temporary source-only snapshot2da9593 with adjacent
patch inside the candidate macro only. Reproduce with
`python3 forge-combo29/tests/tt_replace_outline_validate.py`.
Exact compiler flags derive from tt_replace_cache_receipt.json. Snapshot reads
only src/include; no bundled binaries. SHA256 of temporary engine:
5cd90a356e5b2c2e876a800cefadef207e97ec26124006a832e38643176e7053

Source retains full hit scan followed by first-empty scan. Only a full cluster
calls a noncapturing noinline lambda returning a completed TTProbe, with
owner/cluster/index/key explicit arguments. GCC/Clang attribute is conditionally
compiled; no new production attribute or portability requirement was added.

GCC14 generated owned probe begins with rbp save at0x307a0, rbx save0x307aa
and24-byte stack allocation0x307ae, before any hit or occupancy test. Rare full
replacement uses a real call at0x30836, not a tail-call, with lambda-object
address setup. Common hit/empty returns therefore still pay frame/save costs.
Probe body395 bytes plus outlined helper242 bytes; aggregate size637 bytes
versus664 original lock. Size reduction does not establish lower execution cost.

This source shape fails the specific objective of keeping common returns free
of newly introduced save/frame costs. No timing, TT semantic oracle, full pins,
equivalence or promotion performed for this shape. No runtime defect alleged.
This bounded TT refinement line stops here rather than forcing a production
patch or interpreting mixed straight-cache timings as a gain. Other compiler
or helper designs might differ, but are outside this screen's evidence.
