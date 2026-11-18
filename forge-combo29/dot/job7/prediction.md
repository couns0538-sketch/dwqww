# Job 7 prediction

W1 r15d versus kF: equal on all1000 rows;0 differing nodes/bestmoves. Bucket-changing legal king-move coverage:100–600 of1000 positions.
W2 r15d versus kF: equal after excluding time,nps,hashfull;0 differing normalized output lines. The literal final ucinewgame resets Board to startpos (uci.cpp:574–577), so the additional last-search versus fresh-original-position condition is predicted to FAIL for20 of20 positions in each program. I will not silently insert another position command.
W3 kF versus prescribed kF0: equal on300 search rows and1000 eval outputs;0 differences. Macro evidence shows both still select v3 AVX512, so this is not a prediction of AVX512-versus-AVX2 equivalence. eval uses scalar evaluate_reference (uci.cpp:901–910), another explicit coverage limit.
W4 if completed: equal on all20 paired rows;0 differences.

Step0 and0b passed before this prediction. No workload search or coverage count has been viewed yet. This prediction will not be edited.
