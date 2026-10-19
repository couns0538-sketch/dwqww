# Forge 6.4 bug audit - 2026-10-19 22:00 CEST

Accepted SHA: 9108d012526be80c6d163f7cab684e6acd9abf8d. No mainline edits.

P1 source-policy gap: the 21:45 rule50 candidate guards TT score reuse using the current halfmove clock (<90), but does not track the clock from which a cached score originated. Scores stored from clocks 90-99 may therefore remain eligible at clocks 0-89 for the same position key. This is a follow-up to the existing rule50 investigation, not a proven incorrect engine score.

Standalone C++20 model: 33 scenarios; 12 high-origin to low-probe eligibility cases. GCC, Clang, ASan/UBSan pass. Full Forge build, UCI, perft, bench and fastchess unavailable; 0 matches, no Elo claim.

Next: independently reproduce via full-engine warm/cold TT instrumentation and a legal position oracle; assess producer context tagging versus suppressing high-clock score storage. No fix merged. Audit branch: forge/audit-rule50-reverse-contamination-20261019-2200.
