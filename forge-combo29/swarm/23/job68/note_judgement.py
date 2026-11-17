import io

p = 'FINAL_CHAIN_LINE.txt'
s = io.open(p, encoding='utf-8').read()

old = "### 4. What the family is worth, for the judgement section\n"
new = ("### 4. What the family is worth, for the judgement section\n\n"
       "> **Note for the FINAL: this section was REWRITTEN because reordering the document exposed a contradiction in it.**\n"
       "> The judgement below had been stating a \"policy difference\" claim that 23-F169 had already refuted, and it survived\n"
       "> only because the claim and its correction sat nine sections apart. A reader should know the judgement was produced\n"
       "> by a structural check rather than by a re-read (23-F181).\n")
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print("FINAL judgement section now says it was rewritten by the reorder")
