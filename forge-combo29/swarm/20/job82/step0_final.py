import sys, os, re, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'AUDIT'))
from hardened import Engine, exe_identity, assert_regime
EXE = '/agent/repos/build-v3/forge'
NET = os.path.abspath(os.path.join(os.path.dirname(__file__), 'testnet.fnn3'))
HARNESS = [("Threads", 1), ("Hash", 16)]
S14 = HARNESS + [
    ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
    ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
    ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
    ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
assert_regime(S14, "S14"); assert_regime(PC20, "PC20")
NETON = [("NNUEArchFile", NET), ("NNUEArch", "true")]

def bench(pre, opts, n, timeout=300.0):
    e = Engine(EXE, list(pre) + list(opts))
    try:
        e.isready(); k = e.mark(); e.send(f"bench {n}")
        got, ok = e.expect("info string bench", timeout)
        if not ok: return None
        line = [l for l in got if l.startswith("info string bench")][-1]
        return int(re.search(r"nodes (\d+)", line).group(1))
    finally:
        e.close()

IDENT = exe_identity(EXE)
ROWS = [
  ("no net, no setoption",   [],     HARNESS, (312866, 862329)),
  ("PC20, no net",           [],     PC20,    (278024, 587276)),
  ("test net only",          NETON,  HARNESS, (965454, 4151906)),
  ("PC20, then the test net",NETON,  PC20,    (625258, 3652372)),
]
res = {"exe": IDENT, "net_sha256": "1db8525e4eeb3c4cf425faf89a5dbb7e5aec0a9d00fd7de2c7cd25a7673ffd4a", "rows": []}
print("EXE", IDENT['sha256'][:16], "|", IDENT['id_name'])
print(f"{'row':26s} {'bench11':>9s} {'bench13':>9s}   {'published':>18s}  verdict")
allok = True
for label, pre, opts, pub in ROWS:
    v = (bench(pre, opts, 11), bench(pre, opts, 13))
    ok = v == pub
    allok &= ok
    print(f"{label:26s} {v[0]!s:>9s} {v[1]!s:>9s}   ({pub[0]},{pub[1]})  {'MATCH' if ok else 'DIFF'}", flush=True)
    res["rows"].append({"row": label, "bench11": v[0], "bench13": v[1], "published": list(pub),
                        "match": ok, "n_options": len(opts), "net": bool(pre)})
res["all_eight_match"] = allok
json.dump(res, open("job82/step0.json", "w"), indent=1)
print("\nALL EIGHT MATCH" if allok else "\nMISMATCH -> STOP THE JOB")
