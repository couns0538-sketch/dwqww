# Buffer capacity checkpoint

Not reachable with the fixed FENs tried; fixed defensively. The normal original64-entry assertion build completes both supplied depth3 searches without an assertion. Actual SEE counts are50 and45, not more than64. No blocked checker, generated input search or parser bypass was used.

The deferred array now has MoveList::Capacity entries, matching its producer, with a compile-time containment contract. The new CTest exercises both supplied positions, a forced deferred SEE-losing capture, both-color promotions and PV legality.

All three profiles pass d11 FIRST. OFF all5 signatures and bothperft checks match the lock. Release, AVX512+ALIGN64 ASan/UBSan, and AVX512+ALIGN64 _GLIBCXX_ASSERTIONS each have14/15 CTests: one forge_tests failure with precisely the four exact lines saved alongside. No sanitizer finding. Both instrumented profiles also pass bench13. The new full sanitizer suite closes the previously omitted stage3 suite with the defensive repair included.

The unchanged supplied SIMD v2 has a strict256-bit AVX2 contract: PASS onOFF, width-mismatch FAIL on512-bitON. The separate existing AVX512 checker passes with actualZMM and0ForgeFMA. The original v2 failure is preserved rather than relabeled.

Source/code state, exact commands, original smalllogs and SHA256s are retained. buffer_only.patch is the isolated -p1 delta againstf491; the cumulative buffer_fix.patch and fullsourceZIP bind the inherited optionalSIMD context separately. WAC300 is an outstanding later handoff gate at this checkpoint. No speed or Elo claim.
