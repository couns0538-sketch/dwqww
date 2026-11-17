import io

p = 'consistency_check.py'
s = io.open(p, encoding='utf-8').read()

# 1. the median regex was too greedy: "~625 cp" inside "median ~625 cp" plus bare "~1000 cp" from a RANGE are the same
#    claim in two spellings, and "median 4 cp" comes from an unrelated sample. Track only the COST figure explicitly.
old = '''    "median cost": r"median of roughly ([0-9,\\u2013\\-]+) cp|median ~?([0-9,]+) cp|~([0-9,]{3,4}) cp",'''
new = '''    # only the cost-of-index-0 figure: an explicit "median ... cp" of 3+ digits. Deliberately narrow, because the first
    # version matched "median 4 cp" from an unrelated sample and every "~N cp" anywhere in the file (23-F165's lesson:
    # a check that fires on correct usage gets ignored).
    "median cost": r"median of roughly ([0-9\\u2013\\-]+) cp|median ~?([0-9,]{3,4}) cp",'''
assert old in s
s = s.replace(old, new, 1)

# 2. widen the exemption window: the quoted phrase can be 400+ chars from the row's own finding id in a long table row
old2 = '''            ctx = text[max(0, m.start() - 300):m.start() + 300].lower()'''
new2 = '''            # a findings table row is one long line, so the row's own id may be far from the phrase in either
            # direction along that line: widen to 900 characters, and add the row's own id as context.
            ctx = text[max(0, m.start() - 900):m.start() + 900].lower()'''
assert old2 in s
s = s.replace(old2, new2, 1)

# 3. "0 info lines" inside a row that is ABOUT the correction is exempt by definition
old3 = '''        "0 info lines": ("19-f12", "23-f8", "23-f19", "quit", "eof", "abort", "fabricated", "a2a3", "per depth"),'''
new3 = '''        "0 info lines": ("19-f12", "23-f8", "23-f19", "23-f98", "23-f146", "quit", "eof", "abort", "fabricated",
                         "a2a3", "per depth", "phrasing was wrong"),'''
assert old3 in s
s = s.replace(old3, new3, 1)

io.open(p, 'w', encoding='utf-8').write(s)
print("narrowed the cost pattern, widened the exemption window")
