"""Reproduce fastchess v1.8.3-alpha logistic Elo and 95% pair-based error."""
import argparse
import math
from pathlib import Path
import re

Z = 1.959963984540054
TARGET = {"K8": 50, "C8": 100, "K9": 50, "C9": 100, "K11": 25, "C11": 100, "M1": 1000, "M1b": 1000, "M2": 400, "M2b": 400, "M2c": 400, "M2d": 400, "K12": 10, "C12": 50, "M3": 300, "M3b": 300}


def logistic_elo(score):
    if score == 0.5:
        return 0.0
    if score == 0:
        return -math.inf
    if score == 1:
        return math.inf
    if not 0 < score < 1:
        return math.nan
    return -400 * math.log10(1 / score - 1)


def measures(counts):
    pairs = sum(counts)
    values = [i/4 for i in range(5)]
    mean = sum(n*v for n, v in zip(counts, values)) / pairs
    variance = sum(n*(v-mean)**2 for n, v in zip(counts, values)) / pairs
    se = math.sqrt(variance/pairs)
    lo, hi = (logistic_elo(mean + s*Z*se) for s in (-1, 1))
    elo = logistic_elo(mean)
    error = (hi-lo)/2
    return mean, variance, se, lo, hi, elo, error


def read_fastchess(path):
    text = path.read_text(errors="replace")
    # H2H fastchess emits Elo, Games and Ptnml in the same summary block.
    pattern = r"^Elo: ([-+.\w]+) (?:\+/-|\+-) ([-+.\w]+),[^\n]*\n(?:[^\n]*\n){0,4}?Ptnml\(0-2\): \[([\d, ]+)\]"
    blocks = list(re.finditer(pattern, text, re.M))
    if not blocks:
        return None
    p = blocks[-1]
    return float(p[1]), float(p[2]), [int(c) for c in p[3].split(",")]


def render(match, counts, out=None):
    assert len(counts)==5 and all(c>=0 for c in counts) and sum(counts)<=TARGET[match]
    pairs = sum(counts)
    complete = pairs == TARGET[match]
    lines=[f"Match {match}; {'complete' if complete else 'incomplete'}",
           f"Pairs {pairs}/{TARGET[match]}; games in these complete pairs {2*pairs}",
           "Pentanomial [0,0.5,1,1.5,2] "+" ".join(map(str,counts))]
    if not pairs:
        return lines+["No complete pair; Elo/interval and reading unavailable."]
    score,var,se,xlo,xhi,estimate,err = measures(counts)
    low,high=estimate-err,estimate+err
    lines += [f"Normalized pair mean {score:.15g}",f"Pair population variance {var:.15g}; standard error {se:.15g}",
              f"Logistic Elo {estimate:.12f}; fastchess 95% halfwidth {err:.12f}",
              f"Reported Elo [95%] {estimate:+.2f} [{low:+.2f}, {high:+.2f}]",
              f"Symmetric endpoints before display rounding {low:.12f} {high:.12f}",
              f"Directly transformed score endpoints (asymmetric, for comparison) {xlo:.12f} {xhi:.12f}"]
    if out:
        data = read_fastchess(out)
        if data:
            pe, perr, penta=data
            lines += [f"Last fastchess H2H display {pe:.2f} +/- {perr:.2f}, bins {penta}"]
            if penta != counts and complete:
                raise ValueError("Final fastchess bins differ from complete-match audit")
            if penta == counts:
                # fastchess prints rounded magnitudes. On a cut the last print may predate the final complete pair.
                if abs(pe-estimate)>0.005001 or abs(perr-err)>0.005001:
                    raise ValueError("Recalculated Elo or margin differs from fastchess display")
                lines += ["Reconstructed Elo and error agree with the runner to its two displayed decimals."]
            else:
                lines += ["Incomplete run; last printed runner summary covers different pairs. Estimate uses only the audited finished pairs."]
        else:
            lines += ["No fastchess pentanomial summary block available for display comparison."]
    if not complete:
        lines += ["Incomplete; no reading."]
    elif match == "K12":
        lines += ["Zero observed pair-score variance gives [0,0]; K12 also requires the independent move-list check." if counts == [0,0,pairs,0,0] else "K12 pentanomial control failed."]
    elif match == "C12":
        lines += ["C12 upper endpoint < 0: "+("PASS" if high<0 else "FAIL")]
    else:
        lines += ["Measured seed; the declared strength reading uses the pooled counts and the M3 seed sign."]
    return lines


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("match", choices=TARGET)
    p.add_argument("counts", type=int, nargs=5)
    p.add_argument("--fastchess-out",type=Path)
    args=p.parse_args()
    print("\n".join(render(args.match,args.counts,args.fastchess_out)))


if __name__ == "__main__":
    main()
