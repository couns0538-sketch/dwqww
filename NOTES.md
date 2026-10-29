# B5 completed checkpoint — 2026-10-29

Base b7c177222038e9332965a95ec53ea3b94e90dbc9; frozen implementation fde944ae38e6bbfef0b38f2c4a207e08285fcc1d. SingularV2 defaults0, N1 is CorrHistPlus4+SingularV2. Same-repository Fable J3 port, with CorrExt mutual exclusion; PORT_NOTES.md lists every changed engine/build line and interactions.

OFF nodes312866/862329/3024920/12389307/34048354. ON404121/1005954/4120585/11497954/34264955. N1277579/814055/2651984/18648191/40304213. Startpos perft54865609, NNUEFMA0. Native96/96, UCI27checksPASS. Release and complete leak-enabled ASan/UBSan CTest each56/57, rawexit8: only the four known forge_tests diagnostics, zero sanitizer findings in the completed outside-sandbox run. Preserve interrupted sandbox attempt separately.

No speed or Elo claim. Candidate is ready for independent review and equal-time N1/SingularV2 gates; not accepted into the integration branch. Windows, TSan, actual Syzygy files and combined B1/B2/B4 integration are unverified. Exact commands, source/binary hashes and every bench record are in astra2_evidence/B5. Do not repeat completed qualification without a changed source or a specific unresolved question.

IDEA_SOURCE: this repository's FB2-J3 experiment and user's isolated validation requirements.
