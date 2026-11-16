import sys
sys.path.insert(0,'.')
from check_27sf12 import run, PC20, REPORTED_FEN
B="/agent/repos/base/forge-combo29/build-rel/forge"
P="/agent/repos/pcbase/forge-combo29/build-pc/forge"
print("REPRODUCIBILITY: two runs of each cell that matters, fresh process each time\n")
for label,exe,opts in [("PC r15 PC20",P,PC20),("BASE none",B,[])]:
    for n in (0,3000):
        a=run(exe,REPORTED_FEN,f"go wtime {n} btime {n}",opts)
        b=run(exe,REPORTED_FEN,f"go wtime {n} btime {n}",opts)
        same = (a['nodes']==b['nodes'] and a['best']==b['best'])
        print(f"{label:14s} wtime {n:>5}: run1 {a['nodes']:>7} nodes/{a['best']}  run2 {b['nodes']:>7}/{b['best']}  identical={same}")
