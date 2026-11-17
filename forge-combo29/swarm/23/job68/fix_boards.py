import io

p = 'FINAL_CHAIN_LINE.txt'
s = io.open(p, encoding='utf-8').read()

old = ("confirmed in both directions across nine boards of different material (23-F125/F132/F133), and refined to follow the\n"
       "searched position rather than the game's root")
new = ("confirmed in both directions across nine boards of different material (23-F125/F132/F133), then extended to a DENSE\n"
       "MIDDLEGAME board with about thirty legal moves and to the END OF A LONG MOVE LIST (23-F141/F143), and refined to\n"
       "follow the searched position rather than the game's root")
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print("extended to name F141/F143")
