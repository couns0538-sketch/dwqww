import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT'))
from hardened import Engine, exe_identity
EXE = '/agent/repos/build-v3/forge'
NET = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testnet.fnn3'))
S14 = [("Threads", 1), ("Hash", 16),
       ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]

def bench(pre, opts, n, timeout=300.0):
    e = Engine(EXE, list(pre) + list(opts))
    try:
        e.isready()
        k = e.mark()
        e.send(f"bench {n}")
        got, ok = e.expect("info string bench", timeout)
        if not ok:
            return None, "\n".join(got)[-300:]
        line = [l for l in got if l.startswith("info string bench")][-1]
        return int(re.search(r"nodes (\d+)", line).group(1)), line
    finally:
        e.close()

ident = exe_identity(EXE)
print("EXE sha256", ident['sha256'])
print("EXE id    ", ident['id_name'])
ROWS = [("no net, no setoption", [], [("Threads", 1), ("Hash", 16)]),
        ("PC20, no net", [], PC20),
        ("test net only", [("NNUEArchFile", NET), ("NNUEArch", "true")], S14),
        ("PC20, then the test net", [("NNUEArchFile", NET), ("NNUEArch", "true")], PC20)]
PUB = {("no net, no setoption"): (312866, 862329), ("PC20, no net"): (278024, 587276),
       ("test net only"): (965454, 4151906), ("PC20, then the test net"): (625258, 3652372)}
for label, pre, opts in ROWS:
    got = {}
    for n in (11, 13):
        v, _ = bench(pre, opts, n)
        got[n] = v
    pub = PUB[label]
    verdict = "MATCH" if (got[11], got[13]) == pub else "DIFF"
    print(f"{label:26s} bench11={got[11]!s:9s} bench13={got[13]!s:9s} published=({pub[0]},{pub[1]}) {verdict}", flush=True)
