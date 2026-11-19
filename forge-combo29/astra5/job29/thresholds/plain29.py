"""Measure the literal optional footer on Job 29 plain E-A searches."""
import argparse
import json
from collections import Counter
from pathlib import Path
from threshold29 import check, csvrows, mean, read_source, write_tsv


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("blocks",type=Path);p.add_argument("out",type=Path)
    args=p.parse_args()
    chosen=json.loads((args.out/"status.json").read_text())["common_complete_blocks"]
    totals=Counter()
    rows=[];examples=[];observed_total=[]
    headers=["scope","E_A_searches","footer_reported","footer_below_4000","footer_at_4000",
             "footer_above_4000","below_at_depth_64","footer_sum","footer_min","footer_max",
             "mean_reported_footer","mean_finished_depth_n","mean_E_B_softnodes","A_reported_footer_to_B_mean"]
    def summary(label,c,observed):
        check(c["n"]==c["low"]+c["eq"]+c["high"]+c["missing"],"Plain footer counts")
        observed_n=len(observed)
        ratio=(c["sum"]/observed_n)/(c["b_sum"]/c["b_n"]) if observed_n else None
        return [label,c["n"],observed_n,c["low"],c["eq"],c["high"],c["depth64_low"],
                c["sum"],min(observed) if observed else "",max(observed) if observed else "",
                mean(c["sum"],observed_n),mean(c["info_sum"],c["info_n"]),mean(c["b_sum"],c["b_n"]),
                f"{ratio:.12f}" if ratio is not None else ""]
    seen_cat=Counter()
    for b in chosen:
        stage=args.blocks/f"block{b:03}"/"E"
        if not stage.is_dir():continue
        receipt=json.loads((stage/"receipt.json").read_text())
        c=Counter();observed=[]
        for r in csvrows(read_source(stage,"searches.tsv",receipt["files"])):
            if r["side"]=="B":
                c["b_n"]+=1;c["b_sum"]+=int(r["n"])
                continue
            check(r["side"]=="A" and r["go"]=="go nodes 4000","E-A command")
            c["n"]+=1
            if r["n"]!="NA": c["info_sum"]+=int(r["n"]);c["info_n"]+=1
            if r["soft_line"]=="NA":
                check(r["soft_n"]=="NA","Plain missing footer");c["missing"]+=1
                continue
            n=int(r["soft_n"])
            check(r["soft_line"]==f"info string softnodes nodes {n}","Plain footer mismatch")
            cat="low" if n<4000 else "eq" if n==4000 else "high"
            c[cat]+=1;c["sum"]+=n;observed.append(n)
            c["depth64_low"]+=int(n<4000 and r["depth"]=="64")
            example_cat=("low-depth-other" if n<4000 and r["depth"]!="64" else cat)
            if seen_cat[example_cat] < (2 if cat=="low" else 1):
                examples.append([b,r["game"],r["ply"],r["color"],r["go"],r["n"],r["soft_n"],r["depth"],r["score"],
                                 r["bestmove"],r["info_line"],r["soft_line"]])
            seen_cat[example_cat]+=1
        rows.append(summary(f"block{b:03}",c,observed))
        totals.update(c);observed_total.extend(observed)
    if rows:rows.append(summary("all",totals,observed_total))
    write_tsv(args.out/"E-plain-footers.tsv",headers,rows)
    write_tsv(args.out/"E-plain-examples.tsv",
              ["block","game","ply","color","go","n","footer_n","depth","score","bestmove","info_line","footer_line"],examples)


if __name__=="__main__":
    main()
