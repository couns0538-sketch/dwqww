"""Compare the compact-data recount to the independently replayed games and scores."""
import argparse
import csv
import json
import math
from pathlib import Path


def read_tsv(path):
    with path.open() as source:
        return list(csv.DictReader(source,delimiter="\t"))


def compare(a,b,key):
    if a in ("",None) or b in ("",None):
        ok = a in ("",None) and b in ("",None)
    elif isinstance(b,str):
        ok = a == b
    else:
        ok = math.isclose(float(a),float(b),abs_tol=1e-9,rel_tol=1e-13)
    if not ok:
        raise ValueError((key,a,b))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("thresholds",type=Path);p.add_argument("audit",type=Path)
    p.add_argument("--stages",type=Path)
    args=p.parse_args()
    own=args.thresholds
    mine=json.loads((own/"status.json").read_text())
    other=json.loads((args.audit/"independent.json").read_text())
    if mine["common_complete_blocks"]!=other["common_complete_blocks"]:
        raise ValueError("Different sets of complete blocks")
    other_thresholds={(r["match"],r["side"],r["threshold"]):r for r in read_tsv(args.audit/"thresholds.tsv")
                      if r["match"] in mine["counted_matches"]}
    summary=read_tsv(own/"summary.tsv")
    assert len(summary)==len(other_thresholds)
    for m in summary:
        key=(m["match"],m["side"],m["threshold_cp"]);other_row=other_thresholds[key]
        for a,b in [("games_reached","reached"),("won","wins"),("drew","draws"),("lost","losses"),
                    ("mean_plies_remaining","mean_remaining_plies")]:
            x,y=m[a],other_row[b]
            compare(x,float(y) if y not in ("","None","NA") else None,(key,a))
    for r in read_tsv(own/"match-check.tsv"):
        key=r["match"];v=other["arms"][key]
        for a,b in [("pairs","pairs"),("games","games"),("mean_plies","mean_plies"),
                    ("reading","reading"),("A_to_B_spend","nodes_ratio")]:
            compare(r[a],v[b],(key,a))
        for fields,vals in [(("A_wins","A_losses","A_draws"),v["A_WLD"]),
                            (("p0","p05","p1","p15","p2"),v["penta"]),
                            (("elo","ci_low","ci_high"),v["elo_lower_upper"])]:
            for a,y in zip(fields,vals,strict=True): compare(r[a],y,(key,a))
    for r in read_tsv(own/"search-check.tsv"):
        key=(r["match"],r["side"]);v=other["arms"][r["match"]]["players"][r["side"]]
        for a,b in [("searches","searches"),("sum_n","n_total"),("mean_n","mean_n"),("sum_spent","spent_total"),
                    ("mean_spent","mean_spent"),("scored_searches","depth_reported"),("no_score","no_score"),
                    ("sum_depth","depth_total"),("mean_scored_depth","mean_depth"),("soft_cap_hits","hardcap"),
                    ("soft_cap_share","hardcap_share")]:
            compare(r[a],v[b],(key,a))
    ends={(r["match"],r["ending"]):int(r["games"]) for r in read_tsv(own/"endings-check.tsv")}
    assert ends=={(arm,ending):n for arm,v in other["arms"].items() if arm in mine["counted_matches"]
                  for ending,n in v["endings"].items()}
    print(f"Verified {len(summary)} match-side-threshold rows against independent first-crossing statistics.")
    print(f"Verified game totals, W-L-D, pentanomial counts, Elo and interval, all ending counts, mean plies, budgets and A/B ratios for {', '.join(mine['counted_matches'])}.")
    print("Verified per-side searches, node/depth sums and means, missing score counts and soft-cap counts and shares. Numeric tolerance 1e-9 absolute, 1e-13 relative.")
    if args.stages is not None:
        check_games={}
        for b in mine["common_complete_blocks"]:
            for path in (args.stages/f"block{b:03d}").glob("*.json"):
                stage=json.loads(path.read_text())
                assert stage["complete"] and stage["block"]==b
                for g in stage["games"]:
                    key=(b,stage["match"],g["game"])
                    assert key not in check_games
                    check_games[key]=g
        seen=set()
        for row in read_tsv(own/"per_game.tsv"):
            b=int(row["block"]);m=row["match"];gid=int(row["game"]);side=row["side"];th=row["threshold_cp"]
            k=(b,m,gid,side,th);assert k not in seen;seen.add(k)
            g=check_games[b,m,gid]
            ply=g["first"][side].get(th)
            score=g["score"] if side=="A" else 2-g["score"]
            vals=dict(first_ply=ply,plies_remaining=g["plies"]-ply if ply is not None else None,
                      outcome=("L","D","W")[score],end_ply=g["plies"],opening=g["opening"],
                      color="W" if g["white"]==side else "B")
            for f,y in vals.items(): compare(row[f],y,(k,f))
        assert len(seen)==10*len(check_games)
        print(f"Verified every first reaching ply or absence, remaining plies, side color, game outcome and opening ID in {len(seen):,} game-side-threshold rows from {len(check_games):,} games.")
    print("Common block IDs",mine["common_complete_blocks"])


if __name__=="__main__":
    main()
