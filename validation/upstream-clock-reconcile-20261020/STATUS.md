# Forge 6.4.13 clock-contract reconciliation

Source `cecf0b9e3af5602053bcaf5c5d16ffc09f58850d` merges the newer accepted
integration356e863 into the current candidate, preserving every prior TT/NNUE
repair. Accepted start_time is authoritative; legacy request_start remains a
fallback. Automatic origins apply to finite timed searches. Unset untimed and
ponder searches keep worker-local reporting; ponder budgets still start at hit.

Release, ASan/UBSan and TSan each passed nine CTests, seven main-origin groups
and seven actual TT API groups. Eight active UCI TSan transitions passed. Six
parent cold/warm cases are exact and Linux bench remains419798 nodes. Eight
Wine checks and872 independent artifact checks passed; Windows bench351063.
These are finite correctness proofs, not NPS, Elo or native Ryzen results.

The original GNU-wrap diagnostic observed zero shared-library thread creations
and failed validity. It is retained unchanged. The corrected executable-symbol
interposer delegates RTLD_NEXT, observes three helpers, reproduces old886's five
untimed/ponder failures and seven current passes. The exact accepted440ms UCI
shim gives timed456ms and untimed1ms. The original production review and its
follow-up interposer review state the main-worker-only observation limit.

No strength gain is accepted. The independent6.4.12 TT match was invalidated by
a baseline time forfeit; this analysis-reporting repair is not demonstrated to
remedy it. Preserve its complete raw exchange and all reserved openings. Next
candidate repairs demonstrated extension-path counter reuse, in a separate
branch. Original failure attempts, binaries, source and logs remain retained.
