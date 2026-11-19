"""Generate job 18's tab-separated value table from its handoff file.
Usage: python3 generate-sets.py FABLE_TO_astra5_18.md > sets.txt
"""
import csv
from pathlib import Path
import random
import re
import sys

def parameters(handoff):
    section = handoff.split('\nTHE 40 SETTINGS ', 1)[1].split('\n', 1)[1]
    section = section.split('\n\nTHE FIVE VALUE SETS', 1)[0]
    tokens = section.split()
    if len(tokens) != 40 * 5:
        raise ValueError('expected 40 names, each followed by four integers')
    table = []
    for index in range(0,len(tokens),5):
        name, start, lower, upper, step = tokens[index:index+5]
        if not re.fullmatch('[A-Za-z][A-Za-z0-9]+', name):
            raise ValueError(name)
        table.append((name, int(start), int(lower), int(upper), int(step)))
    if len({row[0] for row in table}) != 40:
        raise ValueError('duplicate setting')
    return table

def write(handoff, target):
    table = parameters(handoff)
    columns = []
    for v in range(1,6):
        rng = random.Random(9000 + v)
        column = []
        for name, start, lower, upper, step in table:
            if not lower <= start <= upper or step <= 0:
                raise ValueError(name)
            offset = rng.randint(-3, 3)
            column.append(max(lower, min(upper, start + offset * step)))
        columns.append(column)
    writer = csv.writer(target, delimiter='\t', lineterminator='\n')
    writer.writerow(['name','start','min','max','step','v1','v2','v3','v4','v5'])
    for row, values in zip(table,zip(*columns)):
        writer.writerow((*row,*values))

if __name__ == '__main__':
    write(Path(sys.argv[1]).read_text(), sys.stdout)
