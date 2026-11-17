#!/usr/bin/env python3
"""Regenerate every headline number in FINDINGS.md from the committed evidence files.

Reads only evidence/ (gzipped JSONL via evio), never a live engine. If a number in
FINDINGS.md disagrees with this output, the report is wrong.
"""
import json, collections, statistics, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from evio import load_plies as load, load_json, is_bail, sig, EVID


def out(title):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


corpus = load_json("games")
games = {g["id"]: g for g in corpus["games"]}

out("1. CORPUS")
total_plies = sum(g["plies"] for g in games.values())
print(f"games {len(games)}  plies {total_plies}  queryable prefixes {total_plies - len(games)}")
print(f"start positions: all [FEN] headers, {len({g['start_fen'] for g in games.values()})} distinct")
print(f"ply per game: min {min(g['plies'] for g in games.values())} "
      f"median {statistics.median([g['plies'] for g in games.values()])} "
      f"max {max(g['plies'] for g in games.values())}")

sess = load("session")
sess2 = load("session2")
sessr = load("session_rev")
fresh = load("fresh")
unc = load("unc")
ch = load("clearhash")
hr = load("hashresend")
ucg = load("uncgame")

out("2. ARMS")
for name, a in [("session", sess), ("session2 (repeat)", sess2), ("session_rev", sessr),
                ("fresh(40)", fresh), ("unc", unc), ("clearhash", ch), ("hashresend", hr),
                ("uncgame", ucg)]:
    print(f"  {name:20s} plies {len(a):6d}")

out("3. DETERMINISM (same process shape, run twice)")
ks = sorted(set(sess) & set(sess2))
print(f"session vs session2: full-signature diffs "
      f"{sum(1 for k in ks if sig(sess[k]) != sig(sess2[k]))} of {len(ks)}")

out("4. DIVERGENCE AGAINST FRESH (40-game sample)")
ks = sorted(fresh)
for name, a in [("session", sess), ("uncgame", ucg), ("session_rev", sessr),
                ("unc", unc), ("clearhash", ch), ("hashresend", hr)]:
    bm = sum(1 for k in ks if a[k]["bm"] != fresh[k]["bm"])
    nd = sum(1 for k in ks if a[k]["nodes"] != fresh[k]["nodes"])
    sc = sum(1 for k in ks if a[k]["score"] != fresh[k]["score"])
    print(f"  {name:14s} bm {bm:5d}/{len(ks)} ({100*bm/len(ks):5.1f}%)  "
          f"nodes {nd:5d}  score {sc:5d}")

out("5. ucinewgame IS A COLD RESET")
print(f"unc vs fresh, full signature identical: "
      f"{sum(1 for k in ks if sig(unc[k]) == sig(fresh[k]))} of {len(ks)}")

out("6. THE FOUR TT STATES, measured on this corpus")
for name, a in [("warm table (session)", sess), ("Clear Hash", ch),
                ("Hash same-value resend", hr), ("ucinewgame (cold)", unc)]:
    print(f"  {name:24s} bm-diff vs fresh "
          f"{sum(1 for k in ks if a[k]['bm'] != fresh[k]['bm']):5d}/{len(ks)}")
print(f"  clearhash vs hashresend full-signature diffs: "
      f"{sum(1 for k in ks if sig(ch[k]) != sig(hr[k]))} of {len(ks)}")

out("7. PATH DEPENDENCE (forward vs reversed game order)")
ks2 = sorted(set(sess) & set(sessr))
d = sum(1 for k in ks2 if sess[k]["bm"] != sessr[k]["bm"])
print(f"  same (game, ply) answers differently: {d} of {len(ks2)} ({100*d/len(ks2):.1f}%)")

out("8. THE DRAWN-ROOT BAIL")
n_bail = sum(1 for r in sess.values() if is_bail(r))
print(f"  observed bail plies in the 200-game session: {n_bail}")
print(f"  games containing one: {len({k[0] for k in sess if is_bail(sess[k])})} of {len(games)} "
      f"({100*len({k[0] for k in sess if is_bail(sess[k])})/len(games):.1f}%)")
print(f"  rate: 1 per {total_plies/n_bail:.0f} plies")
print(f"  all at the game's final ply: "
      f"{all(k[1] == games[k[0]]['plies'] for k in sess if is_bail(sess[k]))}")
print(f"  distinct games with a bail == bail count (one each): "
      f"{len({k[0] for k in sess if is_bail(sess[k])}) == n_bail}")

bp = load_json("bail_predict")
pred = sorted((r["game"], r["ply"]) for r in bp)
obs = sorted(k for k in sess if is_bail(sess[k]))
print(f"  independent predictor (python-chess): predicted {len(pred)}, observed {len(obs)}, "
      f"identical sets: {pred == obs}")
print(f"  fresh bail count on the 40-game sample:   {sum(1 for k in ks if is_bail(fresh[k]))}")
print(f"  session bail count on the same plies:     {sum(1 for k in ks if is_bail(sess[k]))}")
print(f"  DISAGREEMENTS (either direction):         "
      f"{sum(1 for k in ks if is_bail(sess[k]) != is_bail(fresh[k]))}")
print(f"  unc / clearhash / hashresend / uncgame:   "
      f"{[sum(1 for k in ks if is_bail(a[k]) != is_bail(fresh[k])) for a in (unc, ch, hr, ucg)]}")

out("9. BAIL FIDELITY (fresh re-check + generator head)")
bc = load_json("bailcheck")
real = [x for x in bc if x["session_bm"] != "0000"]
term = [x for x in bc if x["session_bm"] == "0000"]
print(f"  drawn-root bails re-checked: {len(real)}   terminal 0000 roots: {len(term)}")
print(f"    session move == fresh move:                 "
      f"{sum(1 for x in real if x['same_move'])}/{len(real)}")
print(f"    session move == generator head (perft 1):   "
      f"{sum(1 for x in real if x['session_is_head'])}/{len(real)}")
print(f"    fresh process also bails:                   "
      f"{sum(1 for x in real if x['fresh_bail'])}/{len(real)}")
print(f"    in-process bail that fresh does NOT:        "
      f"{sum(1 for x in real if not x['fresh_bail'])}")
print(f"    terminal roots agreeing:                    "
      f"{sum(1 for x in term if x['same_move'])}/{len(term)}")

out("10. PLANTED MID-GAME THREEFOLD")
pt = load_json("planted_threefold")
S = {(r["fixture"], r["state"]): r for r in pt["session"]}
F = {(r["fixture"], r["state"]): r for r in pt["fresh"]}
fx = sorted({r["fixture"] for r in pt["session"]})
x3 = [f for f in fx if not f.endswith("_x1")]
x2 = [f for f in fx if f.endswith("_x1")]
states = ("none", "ucinewgame", "clearhash", "hashresend")
occ = {r["fixture"]: r["occ"] for r in pt["session"]}
print(f"  x3 fixtures (position sent a 3rd time): {len(x3)}, occurrence counts "
      f"{sorted({occ[f] for f in x3})}")
print(f"  control fixtures (same board, sent 2nd time): {len(x2)}, counts "
      f"{sorted({occ[f] for f in x2})}")
for grp, nm in [(x3, "x3"), (x2, "x2 control")]:
    b = sum(1 for f in grp for s in states if S[(f, s)]["bail"])
    bf = sum(1 for f in grp for s in states if F[(f, s)]["bail"])
    print(f"  {nm:11s} bails session {b}/{len(grp)*4}   fresh {bf}/{len(grp)*4}")
print(f"  every bail plays the generator head: "
      f"{all(r['is_head'] for r in pt['session'] + pt['fresh'] if r['bail'])}")
print(f"  x3 session vs fresh identical on bm AND nodes: "
      f"{sum(1 for f in x3 for s in states if (S[(f,s)]['bm'], S[(f,s)]['nodes']) == (F[(f,s)]['bm'], F[(f,s)]['nodes']))}"
      f"/{len(x3)*4}")

out("11. MOVE QUALITY (depth-14 oracle, 200 sampled diverging plies)")
mq = load_json("move_quality")
d = sorted(r["delta"] for r in mq if r["delta"] is not None)
print(f"  n {len(d)}  session better {sum(1 for x in d if x > 0)}  "
      f"equal {sum(1 for x in d if x == 0)}  worse {sum(1 for x in d if x < 0)}")
print(f"  delta (session move - fresh move): median {statistics.median(d):+.0f} cp, "
      f"mean {sum(d)/len(d):+.0f}, min {d[0]:+.0f}, max {d[-1]:+.0f}")
print(f"  |delta| >= 100 cp: {sum(1 for x in d if abs(x) >= 100)} of {len(d)}")

out("12. SCORE CALIBRATION (depth-18 fresh truth, 150 plies)")
sc = load_json("score_calibration")
for f, nm in [("err_session", "session d8"), ("err_fresh", "fresh   d8"),
              ("err_d1", "depth 1 (control)")]:
    v = [r[f] for r in sc]
    print(f"  mean |err| {nm:18s} {sum(v)/len(v):7.1f} cp   median {statistics.median(v):6.1f}")

out("13. MEMORY AND TIME")
meta = json.load(open(os.path.join(EVID, "session.jsonl.meta.json")))
r = meta["rss"]
vals = sorted({(x["plies"], x["rss_kb"]) for x in r})
print(f"  RSS start {r[0]['rss_kb']/1024:.1f} MiB, end {r[-1]['rss_kb']/1024:.1f} MiB, "
      f"peak {max(x['rss_kb'] for x in r)/1024:.1f} MiB over {r[-1]['plies']} plies")
print(f"  distinct RSS values: {len({v for _, v in vals})}")
prev = None
steps = []
for p, v in vals:
    if v != prev:
        steps.append(f"ply {p}={v/1024:.1f}MiB")
        prev = v
print("  every change: " + " -> ".join(steps))
gt = meta["game_rss_end"]
print(f"  per-game wall: total {sum(x['wall_s'] for x in gt):.1f}s, "
      f"mean {sum(x['wall_s'] for x in gt)/len(gt):.2f}s, max {max(x['wall_s'] for x in gt):.2f}s")
rc = load_json("rss_control")
pc = rc["positive_control"]
print(f"  RSS positive control: {pc['rss_baseline_kb']/1024:.1f} -> "
      f"{pc['rss_hash1024_kb']/1024:.1f} -> {pc['rss_back_kb']/1024:.1f} MiB (Hash 32/1024/32)")
print(f"  peak hashfull under real search: {max(x['hashfull'] for x in rc['hashfull_rows'])} of 1000")

out("14. LITERAL position startpos moves ARM")
ss = load("startpos_session")
sf = load("startpos_fresh")
ks = sorted(sf)
print(f"  plies {len(ks)}")
print(f"  bm divergence {sum(1 for k in ks if ss[k]['bm'] != sf[k]['bm'])}/{len(ks)} "
      f"({100*sum(1 for k in ks if ss[k]['bm'] != sf[k]['bm'])/len(ks):.1f}%)")
print(f"  bail disagreement {sum(1 for k in ks if is_bail(ss[k]) != is_bail(sf[k]))}")
print(f"  bails: session {sum(1 for k in ks if is_bail(ss[k]))}  fresh {sum(1 for k in ks if is_bail(sf[k]))}")

out("15. ENGINE DIAGNOSTICS (FEN refusals / illegal moves)")
diag = load_json("diagnostics")
print(f"  searches scanned: {diag['searches_scanned']} across {len(diag['per_arm'])} arms")
print(f"  `info string` diagnostics of any kind: {diag['diagnostics_total']}")
for arm, v in diag["per_arm"].items():
    print(f"    {arm:12s} plies {v['plies']:6d}  diagnostics {v['diagnostics']}")
print("  a refused FEN or illegal move appears here, on the `position` command")

out("16. MATE/CP SCORE-TYPE FLIPS")
kinds = {k: ("mate" if (sess[k]["score"] or "").startswith("mate") else "cp") for k in ks}
flips = [k for k in ks if ("mate" if (sess[k]["score"] or "").startswith("mate") else "cp")
         != ("mate" if (fresh[k]["score"] or "").startswith("mate") else "cp")]
print(f"  score-type flips: {len(flips)} of {len(ks)}   "
      f"in-process says mate (fresh says cp): "
      f"{sum(1 for k in flips if (sess[k]['score'] or '').startswith('mate'))}")
print(f"  concentrated in: {collections.Counter(k[0] for k in flips).most_common(4)}")
