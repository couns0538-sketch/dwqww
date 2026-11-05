# T05B-02: exact material key without the serial multiply chain (incremental or closed form)
Status: PARTIAL (every unfinished field says PENDING)

## Source
Own code: lock src/search.cpp:588-596 (material_key: 10 popcounts in a Horner chain of multiply-adds), :638-645
(corrected_eval), :647-656 (update_correction), :50 (MaterialCorrectionWeight = 100). Own profile: R7 J3 perf
(corrected_eval 2.76 % self time). Other engines: PENDING.

## Licence
Own code. Other engines: PENDING.

## Mechanism
PENDING (draft): the lock's key is G * sum_j (c_j + 1) * P^(9-j) mod 2^64 (c_j = count of piece kind j), linear in
the counts, so Board can keep the exact same 64-bit value incrementally (add or subtract a per-kind constant on
captures and promotions), or corrected_eval can compute it as a constant plus a sum of 10 table entries indexed by
the counts, without the dependent multiply chain.

## Forge fit
PENDING

## Expected gain
PENDING

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
