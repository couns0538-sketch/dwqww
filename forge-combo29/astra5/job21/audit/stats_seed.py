"""Job 12 opening-paired, symmetric-in-Elo confidence interval."""
from math import log10, sqrt
from statistics import NormalDist, fmean, pstdev

def evaluate(scores):
    p=fmean(scores)
    margin=NormalDist().inv_cdf(.975)*pstdev(scores)/sqrt(len(scores))
    def elo(x):return 400*log10(x/(1-x))
    value=elo(p)
    error=(elo(p+margin)-elo(p-margin))/2
    return value,value-error,value+error

