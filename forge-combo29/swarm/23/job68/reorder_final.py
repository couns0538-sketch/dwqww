import io

p = 'FINAL_CHAIN_LINE.txt'
src = io.open(p, encoding='utf-8').read()
lines = src.split('\n')

def block(start_prefix, stops):
    """Return the text from the line starting with start_prefix up to (not including) the next stop prefix."""
    i = next(n for n, l in enumerate(lines) if l.startswith(start_prefix))
    j = len(lines)
    for n in range(i + 1, len(lines)):
        if any(lines[n].startswith(s) for s in stops):
            j = n
            break
    return '\n'.join(lines[i:j]).strip('\n')

STOPS = ('ONE-LINE CHAIN', 'SECOND LINE', 'THIRD LINE', 'FOURTH LINE', 'FIFTH LINE', 'SIXTH LINE',
         'SEVENTH LINE', 'EIGHTH LINE', 'NINTH LINE')

first = block('ONE-LINE CHAIN', STOPS)
second = block('SECOND LINE', STOPS)
ninth = block('NINTH LINE', STOPS)
third = block('THIRD LINE', STOPS)
fourth = block('FOURTH LINE', STOPS)
fifth = block('FIFTH LINE', STOPS)
sixth = block('SIXTH LINE', STOPS)
seventh = block('SEVENTH LINE', STOPS)
eighth = block('EIGHTH LINE', STOPS)

out = []
out.append("# FINAL CHAIN — READ THE FIRST THREE SECTIONS ONLY IF YOU READ NOTHING ELSE")
out.append("")
out.append("Ordered so the first page is the COMPLETE, CALIBRATED claim: the defect, the mechanism, the cost, each with")
out.append("its own qualification directly beneath it. The remaining six sections are the detail behind them.")
out.append("")
out.append("---")
out.append("")
out.append("## 1. THE DEFECT AND ITS EXACT TRIGGER")
out.append("")
out.append(first)
out.append("")
out.append("## 2. THE MECHANISM, AND WHAT THE SCORE IS WORTH")
out.append("")
out.append(second)
out.append("")
out.append("## 3. THE COST, AND ITS CALIBRATION")
out.append("")
out.append(ninth)
out.append("")
out.append("---")
out.append("")
out.append("## Supporting sections — the detail behind the three above")
out.append("")
out.append("### 4. What the family is worth, for the judgement section")
out.append("")
out.append(third)
out.append("")
out.append("### 5. What was re-verified before the FINAL, and what was not")
out.append("")
out.append(fourth)
out.append("")
out.append("### 6. Ordering for the drawn-root section (lead with the realistic case)")
out.append("")
out.append(fifth)
out.append("")
out.append("### 7. The GUI hazard table, to be reproduced verbatim")
out.append("")
out.append(sixth)
out.append("")
out.append("### 8. The one command that checked the report's central claims")
out.append("")
out.append(seventh)
out.append("")
out.append("### 9. A correction I passed on twice (the claim policy)")
out.append("")
out.append(eighth)
out.append("")

io.open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print("reordered: 1 defect / 2 mechanism / 3 cost, then six supporting sections")
