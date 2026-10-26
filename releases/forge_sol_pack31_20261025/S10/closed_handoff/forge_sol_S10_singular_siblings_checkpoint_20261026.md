# S10 SingularSiblingLmr checkpoint — 2026-10-26

Decision: **REJECTED search screen.** The original frozen Lprime screen solved263/300 at1000ms, below283, with0 illegal moves. Its d20 ON nodes were+24.6676204%, beyond the preregistered absolute20% deep-node guard. B reproduced the same node counts and guard failure. No repeat, tuning, strength match, speed claim or Elo claim.

The isolated hypothesis adds one LMR reduction to non-singular sibling moves after an established singular TT move. It uses only this Forge source's existing search quantities. Both the build switch and UCI option remain OFF by default; original compile-OFF source tokens and fixed OFF search are preserved.

Patch SHA256 `83b9e88b25347cf862761e54c1447d4f4edeccb1582c85dc6f5aff68d2712668`; frozen controller SHA256 `d6b8b9909373903e2ac3d2aca10e731acffeaff8352db8619d0577945f55b08b`.

|Depth|Lprime OFF|Lprime ON|B OFF|B ON|
|---|---:|---:|---:|---:|
|11|308972|336273|308972|336273|
|13|745494|708742|745494|708742|
|16|2460422|2814343|2460422|2814343|
|20|11901452|14837257|11901452|14837257|
|22|31111774|32299567|31111774|32299567|

Both bases passed the complete Release and ASan/UBSan configured CTest inventories: Lprime14/14 and B15/15 in each profile, exactly the four pinned known findings and zero new failures. Release startpos/kiwipete perft5 matched4865609/193690690. All scoped NNUE ELF/object FMA counts were0. The8-production-TU compile-OFF token proofs passed. FIRST bare d11 ran before UCI on every new main ELF and matched308972. ASan OFF/ON d11 matched308972/336273.

Each base also passed the reviewed v2 ON/Threads=2 ASan supplement: three legal searches, the actual typed option and exactly one active marker before the first bestmove, fully drained normal EOF, empty sanitizer stderr, unchanged source/runtime artifacts, and observed unlimited RLIMIT_AS before/after. Leak checking remained enabled. No second default OFF-d22 timeout occurred.

Original main result SHA256: Lprime `1634ec4b832aadab39f0c4d493adf71b255ac0ee2afc46bc88549563f0f754c1`; B `87d846e8f41ab656ee4ae29834fbd7d5de300172c590fcb73da223cb5bdcd5b2`.
Original T2 result SHA256: Lprime `c8dd302966bd16cd3dd25cd484faacc669e3e928b63ed61ba0b29542cd0d995b`; B `f7cf13bdc55b68e37ee690d48533221ad27beb9233c061c9930357323045acb1`.

Original source trees, binaries, caches and all raw observations remain intact locally. The separate sealed data archive and mapping receipt record every original data byte; private engine source and build binaries are excluded from publication encoding. Windows/owner-PC eligibility and equal-time playing strength remain UNVERIFIED. The next frozen candidate is CaptureHistoryLmp; its original180-second component deadline is unchanged.
