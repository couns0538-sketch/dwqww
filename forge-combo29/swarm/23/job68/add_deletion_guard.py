import io

p = 'doc_check.py'
s = io.open(p, encoding='utf-8').read()

old = '''print()
print("VERDICT:", "PASS" if overall_ok else "check the unresolved names above (may be prose)")'''
new = '''# DELETION GUARD across the reference pages (23-F197). A section heading that disappears is a silent edit: valid
# markdown, fluent reading, missing content. The counts below are the BASELINE recorded when this guard was added; if a
# heading count DROPS, something was overwritten and the edit must be re-read. A count that RISES is fine (the documents
# grow). This is the same "an add-only edit cannot decrease a count" rule `rule_check.py` applies to the rule page.
BASELINE = {'TRIGGER.md': 9, 'GUI_HAZARDS.md': 14, 'HANDOFF_drawn_root_trigger.md': 10,
            'FIXTURE_RULES.md': 5, 'FINAL_CHAIN_LINE.txt': 11}
print()
print("heading counts against the last recorded baseline (a DROP means something was overwritten):")
_any_drop = False
for page, base in sorted(BASELINE.items()):
    if not os.path.exists(page):
        continue
    n = len(re.findall(r"^#", open(page).read(), re.M))
    flag = ""
    if n < base:
        flag = "  <-- DROP (was %d)" % base
        _any_drop = True
    print("  %-34s %2d (baseline %2d)%s" % (page, n, base, flag))
if _any_drop:
    overall_ok = False

print()
print("VERDICT:", "PASS" if overall_ok else "check the unresolved names above (may be prose)")'''
assert old in s
s = s.replace(old, new, 1)
io.open(p, 'w', encoding='utf-8').write(s)
print("deletion guard added to doc_check")
