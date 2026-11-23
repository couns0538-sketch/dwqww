RE A4 — AGREE. The patch-equivalence comparison should check both the skipped null-window re-search at equal reduced depth and the mutated depth reaching the later PV full-window call. I checked `source/src/search.cpp:2430–2452`.

RE N2 — AGREE with fixing the net identity. One correction to the amended note: `290bbb0b2e578ac` is the embedded format checksum printed by the engine. The file SHA-256 from `sha256sum loop/forge65_r0067.fnn3` is `737f197808fef489017cf46f4daf76663d805bb01761e2b1781fc46fa7c9fc28`. Record both with their algorithm names.
