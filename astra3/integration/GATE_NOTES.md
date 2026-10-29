# A1 integration gate handoff — 2026-10-29

Status: Linux identity/protocol qualification complete; Windows and final review pending. No gate is run and no queued gate, lock, or live executable is changed.

The accepted integration input is b7c177222038e9332965a95ec53ea3b94e90dbc9. The isolated astra3-integration branch uses real no-ff merges in the supplied order. See REPORT.md for each tested source and its binary SHA256.

A candidate for replacing the executable of a queued R5A single must reproduce that gate's full five-depth ON vector from `opus_r5/r5a/gate_specs.json`, plus the fixed OFF vector312866/862329/3024920/12389307/34048354, startpos4865609, kiwipete193690690, and whole-executable FMA0. The final Release head passes all these exact identities, including all eight R5A singles. Windows qualification and CR approval remain separate; this is no instruction to migrate a live executable.

CorrMargins1/Scale100 uses343365/858019/2522546/12894582/22287047, as confirmed by the user. CorrMargins0/Scale100 keeps OFF pins. No threshold or queued ON meaning is changed.

Even after native identity passes, these identities are not Elo or speed evidence. QA/CR own adoption, Windows checks, installation and fresh gate seeds. Existing gates must not be rewritten in flight. No strength result transfers automatically to a combined bundle: CorrMargins and TtPruneV2 affect shared margins; CorrHistPlus and CorrHistV2 are exclusive; CorrExt and SingularV2 are exclusive. N1 is CorrHistPlus4 plus SingularV2 only; independent SmpV2 and TmSoftHardClamp survive preset changes and are not implied by N1.

For any later authorized strength gate proposal: one explicit option set, normalized SPRT[0,10], cap_games3000 as an integer, and empty srand/openings_start for QA assignment. Node-identical speed switches instead require NPS evidence and a[-10,0] non-regression proposal. No result is claimed here.

IDEA_SOURCE: Engine QA round-three contract, same-repository R5A gate specifications, and the user's CorrMargins clarification.

## Native Release qualification update

Source926c55f33227bc4a030d7ce5b1140528aeba75af passes all75 matrix cells. All eight queued R5A singles have their exact five ON counts; the fixed OFF counts, both perfts and FMA0 pass. CTest64/65 has only the four known forge_tests lines. All102 advertised-option contract cases pass; strict positive two-game and named-negative exit1 checks meet the user contract. These are identity/protocol prerequisites only: full ASan/UBSan CTest has only the four known functional failures and zero sanitizer findings; TSan requested tests/stress pass after the documented timeout replay. Windows execution remains pending. No live gate migration is authorized or performed by this report.

## A2 adoption limitation

The isolated A2 diagnostic branch6a9cc2b7a23ed29f6bc77ad9a496b4cfc6e6e391 reproduces main-worker mate loss after serialized helper TT seeding. No production fix is demonstrated. Do not interpret A1 integration qualification as resolving that bug or qualifying SmpV2-on for adoption. R5A single identities here use SmpV2 defaultfalse. This is a review limitation for future adoption; no running or queued gate is changed.
