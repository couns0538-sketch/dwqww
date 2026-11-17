import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT'))
from hardened import Engine
EXE='/agent/repos/build-v3diag/forge'
NET=os.path.abspath(os.path.join(os.path.dirname(__file__),'testnet.fnn3'))
# CONTROL 1 (planted zero): v3 path OFF  -> counter must be exactly 0
# CONTROL 2 (planted positive): v3 path ON -> counter must be > 0
for label, pre in [("v3 OFF (NNUEArch unset)", []),
                   ("v3 ON  (test net loaded)", [("NNUEArchFile",NET),("NNUEArch","true")])]:
    e=Engine(EXE, pre+[("Threads",1),("Hash",16)])
    try:
        e.isready(); e.send("bench 13"); e.expect("info string bench",300)
        e.isready(); k=e.mark(); e.send("quit"); got,_=e.expect("info string diag",20)
        d=[l for l in got if "diag" in l][-1]
        m=re.search(r"refresh_calls (\d+)", d)
        print(f"{label:28s} refresh_calls={m.group(1) if m else '?'}")
    finally:
        pass
