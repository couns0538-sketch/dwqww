import io

p = 'FINAL_CHAIN_LINE.txt'
s = io.open(p, encoding='utf-8').read()

# Section 2 must not quote a single median when section 3 corrects it to a range. Same figure, qualified once.
old = "→ priced at a median ~625 cp over 12\ndeterministically sampled positions, ten of twelve ≥ 300 cp (23-F101) →"
new = ("→ priced at a median of roughly 600–1,000 cp across TWO DISJOINT 12-position samples, nine or ten of twelve ≥ 300 cp\n"
       "each (23-F101/F144 — quote it as a range, never 625 alone) →")
assert old in s, "cost phrase not found in section 2"
s = s.replace(old, new, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print("section 2 cost corrected to the range")
