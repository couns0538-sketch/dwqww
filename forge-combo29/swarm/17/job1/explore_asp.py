import json, sys, os
sys.path.insert(0,'.')
from uci_driver import run_one
exe='/agent/repos/base/forge-combo29/build-asan/forge'
fens=[l.split(';')[0].strip() for l in open('G.epd') if l.strip()]
# mate-in-1 and mate-in-2 positions make the aspiration window open to a mate score
mate_fens=[
 "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",          # Ra8 mate in 1
 "r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4", # mate already
 "8/8/8/8/8/5k2/6q1/7K w - - 0 1",                 # black mates
 "3k4/8/8/8/8/8/8/R3K3 w Q - 0 1",                 # castling position
 "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
]
os.makedirs('explore_asp',exist_ok=True)
out=[]
for i,fen in enumerate(mate_fens):
    info=run_one(exe,["uci","isready","position fen "+fen,"go depth 12"],90,f"explore_asp/p{i}.log",
                 env=dict(os.environ,ASAN_OPTIONS="detect_leaks=0",UBSAN_OPTIONS="print_stacktrace=1"))
    text=open(f"explore_asp/p{i}.log").read()
    info['fen']=fen
    info['san']=[w for w in ("AddressSanitizer","runtime error:","SUMMARY:") if w in text]
    info['depths']=len([l for l in text.splitlines() if l.startswith("info depth")])
    info['scores']=[l.split(' score ')[1].split(' ')[0]+' '+l.split(' score ')[1].split(' ')[1] for l in text.splitlines() if ' score ' in l][-2:]
    print(json.dumps(info))
    out.append(info)
json.dump(out,open('explore_asp/results.json','w'),indent=1)
