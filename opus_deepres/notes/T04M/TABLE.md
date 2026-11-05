# T04M TABLE - quiescence search details (stand pat, delta / futility, SEE thresholds, evasions, quiet checks, TT in qsearch, depth limits, recaptures)
Status: PARTIAL (rows added as sources are read)

Lock qsearch summary (own code, `src/search.cpp`): TT probe + non-PV cutoff `:786-797`; stand pat = corrected eval refined by the TT bound
`:806-815`, fail-soft return, stored only without a TT hit `:816-818`; futility base = static eval + QsFutilityMargin 160 `:821`;
captures / promotions only out of check (picker QsTT -> QsCaptures, quiet TT move dropped `:327-329`, order 10 x victim + capture history,
queen promo +20000 `:512-516`); per move: futility (not for checks / promotions) `:834-837`, SEE < -QsSeeMargin 40 skipped `:838`; in check all
evasions (captures by MVV-LVA first, quiets by quiet history + direct-check bonus `:538-555`); no move-count limit, no quiet checks, no
qsearch depth counter, no recapture rule, no history update; store depth 0, exact bound in PV qsearch `:867-869`.

| # | idea | source + link | licence | logged numbers | Forge has it (file:line) | verdict |
|---|---|---|---|---|---|---|
