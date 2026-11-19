"""Reproduce Job 28's paired and independent-width comparisons from public text rows."""
import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

PRIOR = "ebda573523ab9be9a1b1438eb15788c096ac9946"
OLD_PATH = "forge-combo29/astra5/job27"
PRIOR_TREE = "9a819f556e20fea8c11da6e4417e278a979e84df"
ARMS = ("M4", "M5", "M6")
WHITE_HALF = {"0-1": 0, "1/2-1/2": 1, "1-0": 2}
Z = statistics.NormalDist().inv_cdf(0.975)


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def rows(data):
    return csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter="\t")


def table(path, header, data):
    with path.open("w", newline="") as out:
        writer = csv.writer(out, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(data)


@dataclass(frozen=True)
class Pair:
    white_a: str
    black_a: str

    @property
    def points(self):
        return (WHITE_HALF[self.white_a] + 2 - WHITE_HALF[self.black_a]) / 2


def pair_table(data):
    pairs = {}
    for row in rows(data):
        n = int(row["opening"])
        check(n not in pairs and int(row["A_White_game"]) == 2*n-1
              and int(row["B_White_game"]) == 2*n, f"Pair game IDs for {n}")
        p = Pair(row["A_White_result"], row["B_White_result"])
        check(p.points == float(row["A_pair_points"]), f"Pair score for {n}")
        pairs[n] = p
    return pairs


def raw_pairs(game_bytes, fen_bytes, openings):
    fens = {}
    for row in rows(fen_bytes):
        k = int(row["opening"])
        check(k not in fens, f"Duplicate opening {k}")
        fens[k] = row["fen"]
    check(set(fens) == set(openings), "Opening range")
    results = {}
    for row in rows(game_bytes):
        k, game = int(row["opening"]), int(row["game"])
        check(k in fens and game not in results, f"Duplicate or unexpected game {game}")
        colors = ["B","A"] if game % 2 == 0 else ["A","B"]
        check([row["white"],row["black"]] == colors and k == (game+1)//2, f"Color reversal game {game}")
        check(row["result"] in WHITE_HALF, f"Invalid result in game {game}")
        results[game] = row["result"]
    pairs = {k: Pair(results[2*k-1], results[2*k]) for k in openings}
    check(len(results) == 2*len(openings), "Missing or extra game")
    return pairs, fens


def describe(xs, ys):
    n = len(xs)
    deltas = [x-y for x,y in zip(xs,ys, strict=True)]
    mean = statistics.fmean(deltas) if n else None
    trace = {"n": n}
    if n < 2:
        return [n,mean,None,None,None,None,None,None,None], trace
    sx, sy, sd = map(statistics.stdev,(xs,ys,deltas))
    half = Z * sd / math.sqrt(n)
    paired = 2*half
    independent = 2*Z*math.hypot(sx,sy) / math.sqrt(n)
    reduction = independent - paired
    pct = 100*reduction/independent if independent else None

    # Independent route: integer counts of half-points and exact rational moments.
    xh, yh = ([int(2*v) for v in seq] for seq in (xs,ys))
    xsum, ysum = sum(xh), sum(yh)
    x2, y2 = sum(v*v for v in xh), sum(v*v for v in yh)
    xy = sum(a*b for a,b in zip(xh,yh))
    denom = 4*n*(n-1)
    vx = Fraction(n*x2-xsum*xsum, denom)
    vy = Fraction(n*y2-ysum*ysum, denom)
    cov = Fraction(n*xy-xsum*ysum, denom)
    vd = vx+vy-2*cov
    m = float(Fraction(xsum-ysum, 2*n))
    w = 2*Z*math.sqrt(vd/n)
    iw = 2*Z*math.sqrt((vx+vy)/n)
    for first, second in zip((mean, sx*sx, sy*sy, sd*sd, paired, independent),
                             (m, float(vx), float(vy), float(vd), w, iw)):
        check(math.isclose(first,second,rel_tol=1e-12,abs_tol=1e-12), "Two variance calculations differ")
    trace.update(sum_x_half=xsum,sum_y_half=ysum,sum_sq_x_half=x2,sum_sq_y_half=y2,
                 sum_xy_half=xy,var_x_points=str(vx),var_y_points=str(vy),cov_xy_points=str(cov),
                 var_delta_points=str(vd),verified=True)
    return [n,mean,sd,mean-half,mean+half,paired,independent,reduction,pct], trace


def fmt(value, places=12):
    if value is None:
        return "NA"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{places}f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo",type=Path,required=True)
    ap.add_argument("--blocks",type=Path,required=True, help="Job 28 matches/ directory containing schedule-end.json")
    ap.add_argument("--audit",type=Path,required=True, help="Job 28 audit/final/")
    ap.add_argument("--out",type=Path,required=True)
    args = ap.parse_args()
    receipts = []

    def record(label, data):
        receipts.append([label,len(data),sha(data)])
        return data

    def old(name):
        spec = f"{PRIOR}:{OLD_PATH}/{name}"
        # All Job 27 files are retained under this subtree even in a depth-one checkout.
        data = subprocess.check_output(["git","-C",str(args.repo),"show",f"{PRIOR_TREE}:{name}"])
        return record(spec,data)

    def new(root, name, namespace):
        return record(f"job28/{namespace}/{name}",(root/name).read_bytes())

    def raw(block, name):
        return new(args.blocks, f"block{block:03d}/{name}", "matches")

    historical = old("audit/final/M1-pairs.tsv")
    m1 = pair_table(historical)
    historical_summary = json.loads(old("audit/final/independent.json"))["arms"]["M1"]
    check(len(m1) == historical_summary["pairs"] == 434, "Historical cohort")
    old_run = json.loads(old("matches/run.json"))
    current_run = json.loads(new(args.blocks, "run.json", "matches"))
    check(old_run["L27_sha256"]==current_run["L27_sha256"], "Opening list digest across runs")
    end = json.loads(new(args.blocks, "schedule-end.json", "matches"))
    audit = json.loads(new(args.audit, "independent.json", "audit/final"))
    blocks = end["common_complete_blocks"]
    check(audit["final"] and blocks == audit["common_block_ids"], "Audit and runner eligible blocks")
    check(blocks == list(range(1,len(blocks)+1)), "Common block IDs")
    old_blocks = json.loads(old("matches/schedule-end.json"))["common_complete_blocks"]
    vectors = {arm:{} for arm in (*ARMS,"M1")}
    fen_hashes = {}
    for block in blocks:
        rc = json.loads(raw(block,"receipt.json"))
        check(rc["complete"] and rc["completed_stages"] == list(ARMS) and rc["block"] == block, "Block seal")
        check(block in old_blocks, "Historical block outside approved cohort")
        opens = range((block-1)*50+1, min(block*50,434)+1)
        check((rc["opening_first"],rc["opening_last"]) == (opens.start,opens.stop-1),"Block opening range")
        old_stage = f"matches/block{block:03d}/M1/"
        local_m1, fens = raw_pairs(old(old_stage+"games.tsv"),old(old_stage+"openings.tsv"),opens)
        check(local_m1 == {k:m1[k] for k in opens}, "Historical M1 committed pair table differs from game rows")
        vectors["M1"].update({k:m1[k] for k in opens})
        fen_hashes.update({k:sha(f.encode()) for k,f in fens.items()})
        for arm in ARMS:
            pairs, afens = raw_pairs(raw(block,f"{arm}/games.tsv"),raw(block,f"{arm}/openings.tsv"),opens)
            check(afens == fens, "FEN mismatch at common opening")
            vectors[arm].update(pairs)
    for arm in ARMS:
        published = pair_table(new(args.audit, f"{arm}-pairs.tsv","audit/final"))
        check(published == vectors[arm], f"{arm} pair table differs from raw games")

    ids = sorted(fen_hashes)
    check(ids == audit["common_opening_ids"], "Eligible opening IDs differ from audit")
    args.out.mkdir(exist_ok=True, parents=True)
    order = ("M1","M4","M5","M6")
    fields = ["opening","fen_sha256","A_White_game","B_White_game"]
    for arm in order:
        fields.extend(f"{arm}_{s}" for s in ("A_White_result","B_White_result","A_pair_points"))
    fields.extend(["M4_minus_M1","M5_minus_M6"])
    all_rows = []
    for k in ids:
        row = [k,fen_hashes[k],2*k-1,2*k]
        for arm in order:
            p = vectors[arm][k]
            row += [p.white_a,p.black_a,p.points]
        row += [vectors["M4"][k].points-vectors["M1"][k].points,vectors["M5"][k].points-vectors["M6"][k].points]
        all_rows.append(row)
    table(args.out/"per_opening.tsv",fields,all_rows)
    metrics = []
    traces = {}
    for first,second in (("M4","M1"),("M5","M6")):
        key = f"{first}-{second}"
        stats,trace = describe([vectors[first][k].points for k in ids],[vectors[second][k].points for k in ids])
        metrics.append([key,*stats])
        traces[key]=trace
    header = ["comparison","n","mean_delta","sd_delta","ci_low","ci_high","paired_width",
              "independent_width","width_reduction","narrowing_pct"]
    table(args.out/"comparisons.tsv",header,([r[0],*[fmt(v) for v in r[1:]]] for r in metrics))
    (args.out/"moment-check.json").write_text(json.dumps(traces,indent=2)+"\n")
    table(args.out/"input-hashes.tsv",["input","bytes","sha256"],receipts)
    old_elo, lo, hi = historical_summary["elo_lower_upper"]
    (args.out/"source.txt").write_text(f"""Job 27 source commit {PRIOR}
Job 27 subtree {PRIOR_TREE}
M1 audited pair source {OLD_PATH}/audit/final/M1-pairs.tsv
M1 audited pair source SHA256 {sha(historical)}
M1 audited pair source rows {len(m1)}
Job 27 M1 Elo {old_elo:.12f}, 95% interval [{lo:.12f}, {hi:.12f}], reading {historical_summary['reading']}
Job 27 and 28 L27 list SHA256 {current_run['L27_sha256']}
Job 28 schedule ended with {end['reason']}. Common complete blocks {blocks}.
Verified {len(ids)} common opening IDs, matching FENs, correct color reversal, and matching raw results and final audit pairs across M1, M4, M5, M6.
Each per_opening.tsv FEN digest is SHA256 of the exact six-field FEN, UTF-8, without a trailing newline.
Every raw and derived input read by this comparison is identified in input-hashes.tsv.
""")
    (args.out/"method.txt").write_text(f"""Unit: A points per color-reversed two-game opening pair, range 0 to 2. The game result fields retain White's viewpoint.
The cohort contains openings in every common-complete block of the final Job 28 schedule. All were also complete in Job 27 M1.
For each contrast form D = X - Y on the same opening. Means, standard deviations and intervals refer to pair points. Standard deviations use the sample denominator n - 1.
Two-sided normal approximation: z = {Z:.15f}. The paired interval of the mean is mean(D) +/- z * sd(D) / sqrt(n). Both reported widths are full widths.
The hypothetical independent width is 2*z*sqrt((var(X)+var(Y))/n) for two independent matches of n opening pairs each, using both observed marginal variances on those same n openings.
Width reduction = independent width - paired width. Narrowing percent = 100*reduction/independent width. A negative value indicates widening. An unavailable denominator or deviation is NA.
The direct calculation uses per-opening differences. The independent calculation in moment-check.json reconstructs both marginal variances and the covariance from integer half-point sums and obtains var(D) = var(X)+var(Y)-2*cov(X,Y). All means, variances and widths were checked to 1e-12.
Reproduce from the repository root with python3 forge-combo29/astra5/job28/comparisons/compare28.py --repo . --blocks forge-combo29/astra5/job28/matches --audit forge-combo29/astra5/job28/audit/final --out /tmp/job28-comparisons.
""")
    md = ["| Difference | Openings | Mean | SD | 95% interval | Paired width | Independent width | Width reduction |",
          "|---|---:|---:|---:|---|---:|---:|---:|"]
    for name,n,m,s,lo,hi,w,iw,d,pct in metrics:
        md.append(f"| {name} | {n} | {fmt(m,4)} | {fmt(s,4)} | [{fmt(lo,4)}, {fmt(hi,4)}] | {fmt(w,4)} | {fmt(iw,4)} | {fmt(d,4)} ({fmt(pct,2)}%) |")
    (args.out/"comparison-table.md").write_text("\n".join(md)+"\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
