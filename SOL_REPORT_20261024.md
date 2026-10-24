# Forge — Sol report, 2026-10-24

Final source SHA: **074102419c90c6b3725cd83c172e1ec22a2d8203**, isolated branch `forge/sol-next-20261024`. Lock: `f4911f2`; supplied H256 network unchanged. Integration and the earlier WIP branch were preserved. The final publication SHA is printed with delivery.

Implemented the defensive deferred-capture capacity repair and OFF-default `NnueInt16` H256 inference, widening output groups to int64 before accumulation. **Overflow was not reachable with FENs tried, fixed defensively**; no native overflow was reproduced. Integer inference stays research code, with +272 KiB accumulator storage per worker even OFF.

Verified first-d11 gates, all five OFF lock signatures, startpos/kiwipete perft5 **4865609/193690690**, and clean ON ASan/UBSan bench13 plus T1/T2 and mid-search mode-switch tests. Full Release and ASan suites each passed **14/15**; the same four known FAIL lines remain inside `forge_tests`, reproduced exactly in both CR drafts. Null d8 attempts/cutoffs: **7/5**, pawn-only **0/0**.

100,000 unique legal FENs: mean/max/p99 absolute error **0.0147/1/1 cp**, strict sign flips **0**; fixed limits passed. Depth13 bestmoves changed **6/32**. Synthetic positive/negative output totals beyond int32 passed. ON nodes d11/13/16/20/22: **335382/850773/3130100/10757244/27884195**. NNUE FMA count **0**. Supplemental strict-pthread builds retained exact OFF bytes; buffer AVX512+alignment Release passed all five depths/perft.

Fresh WAC OFF/ON/OFF: **274/271/278**, 900 legal results. Earlier 492-row watchdog failure remains failed, separate and unresolved. Buffer WAC **276/265/279** is a possible regression. Native six-AA/fourteen-ABBA speed verdict: **NOISE**, median **+0.44%**, 8/14 positive versus **21.47%** AA band. **No verified speed or Elo improvement; no matches were run.**

Deliveries: [full source ZIP and hashes](releases/sol-next-20261024/int16-source-manifest.json), [clean -p1 patch](releases/sol-next-20261024/int16_fix.patch), [buffer handoff](validation/sol-next-20261024/buffer/CR_DRAFT.md), [int16 handoff](validation/sol-next-20261024/int16/CR_DRAFT.md), [Windows qualification tools](releases/sol-next-20261024/sol-zen5-qualification.zip). Both source packages passed Git/ZIP/patch reconstruction audits. Existing SIMD skill improved; no duplicate/global installation claim.

Open: native Zen5/Windows execution, combined stage3/int16 qualification, whole-engine phase percentages, unsupported-network runtime exercise, inherited tactical failures and independent CR approval. Windows helpers are cross-built and synthetic script gates passed; that is not native Windows evidence. Next: owner's documented native qualification, preserving all hashes and original outputs. [Recoverable checkpoint](validation/sol-next-20261024/CONTINUE.md).
