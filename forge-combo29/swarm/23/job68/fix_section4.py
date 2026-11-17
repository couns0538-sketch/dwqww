import io

p = 'FINAL_CHAIN_LINE.txt'
s = io.open(p, encoding='utf-8').read()

old = ('**The score is largely SOUND and the damage lives in the MOVE.** Automatic draws (insufficient material) are handled\n'
       'correctly by BOTH builds (23-F128); on claimable draws the two builds differ only in whether to claim \u2014 a POLICY\n'
       'difference, consistent across two boards, not a correctness defect in either (23-F128/F131).')
new = ('**The score is largely SOUND and the damage lives in the MOVE.** Automatic draws (insufficient material) are handled\n'
       'correctly by BOTH builds (23-F128). On claimable draws the two builds differ \u2014 but NOT by a "claim policy": 23-F169\n'
       'refuted that reading by showing the PC reports `cp 0` on a winless drawn root, i.e. it does claim. The correct\n'
       'statement is that the repaired build finds the win where one exists and reports the draw where none does, which is\n'
       'correct behaviour and a better result for the repair than the policy framing was (23-F128/F131 superseded by\n'
       '23-F169).')
assert old in s, "policy sentence not found"
s = s.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print("section 4 policy claim replaced with the F169 correction")
