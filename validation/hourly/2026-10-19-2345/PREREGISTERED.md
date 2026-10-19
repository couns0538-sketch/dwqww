# 2026-10-19 23:45 Forge 6.4 OwnBook UCI candidate

Baseline: 9108d012526be80c6d163f7cab684e6acd9abf8d. Isolated branch. Hypothesis: an external Polyglot book is used even when OwnBook=false due to the OR condition in src/uci.cpp. Earlier 19:00 audit reproduced the source-level condition. Plan: require own_book in dispatch, verify using positive/negative/re-enabled real UCI controls, CTest, perft, bench and sanitizers. No merge before real-engine tests. No Elo claim.
