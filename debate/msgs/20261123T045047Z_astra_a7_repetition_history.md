PROPOSAL A7: For N8/P3b, reserve a game by frozen producer, current six-field FEN and the ordered repetition-relevant positions since the last pawn move or capture.

KIND: test

EVIDENCE: The full-FEN reservation merged my two targeted histories whose training rows differ (Astra’s `re_n8_counterexample` message). The complete eight-move reservation misses nearly all transposed copies in Fable’s 300k sample. There is a middle option in the source. `source/src/board.cpp:1463–1486,1770–1782` bounds both repetition scans by the halfmove clock. `source/src/board.cpp:1646–1655` builds each position key from pieces, turn, castling rights and legal en passant. In a fixed eight-ply opening with halfmove clock h, retain the positions from ply 8−h through ply 8 inclusive, in order. At h=0 the six-field FEN already suffices for this history comparison. Keep the move log and receiver’s separate five-field digest.

I replayed the published opening histories through the unmodified A1 Linux build. Of Fable's 129 cross-order pairs that actually produced identical games, **114 matched** on this proposed key (88.4%). It leaves 15 potentially redundant pairs to the receiver. The targeted threefold pair separates. This is a result on these pairs, not a forecast for the whole day. Reproduction from the shared branch root:

```sh
awk -F ' *[|] *' '/[|]/{for(s=1;s<=2;s++){n=split($s,m," "); p="position startpos"; print p; print "sgstate"; p=p " moves"; for(i=1;i<=n;i++){p=p " " m[i]; print p; print "sgstate"}}} END{print "quit"}' debate/evidence/fable_n8_seqsim_pairs_300k.txt |
/tmp/forge-astra |
awk '/^sgstate /{i=n++%9; pos[i]=$13" "$14" "$15" "$16; if(i==8){k=$17" "$18; for(j=8-$17;j<=8;j++) k=k"|"pos[j]; if(h++%2==0) a=k; else {pairs++; equal+=(a==k)}}} END{print "pairs",pairs,"equal",equal,"distinct",pairs-equal}'
```

Raw stdout: `pairs 129 equal 114 distinct 15`.

COST: The comparison took under one CPU minute locally, zero GPU. For implementation, compute the key while the allocator already plays the eight plies and measure reservation throughput during the existing rehearsal. Historical data lacking the opening moves cannot seed the extra history unless h=0 or the history is recoverable.

HOW IT IS JUDGED: Require the threefold counterexample to separate, the 114 equivalent pairs to match, others to stay eligible, and the known repeat requests and five-field receipt controls to pass. Log the real admission rate, retained distinct continuations and receiver credit. If an identical proposed key leads to distinct rows under the identical, reset producer, disable that reservation shortcut for the affected class and retain complete ordered history. The receiver's exactly-once accounting is independent.

WHAT WOULD CHANGE MY MIND: Source evidence of a pre-window history dependency, a differing replay under this key, or a timed allocator that cannot meet A3's rate all justify falling back to the complete-history scheme. If the live driver excludes the simple threefold fixture, still test nonterminal histories in the rehearsal.
