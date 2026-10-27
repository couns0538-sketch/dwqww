"""scipy.optimize.brentq stand-in: a step-by-step transcription of SciPy's C brentq (Zeros/brentq.c)."""
import math

import numpy as np

_RTOL = 4 * np.finfo(float).eps


def brentq(f, a, b, args=(), xtol=2e-12, rtol=_RTOL, maxiter=100, full_output=False, disp=True):
    xpre, xcur = float(a), float(b)
    xblk = fblk = spre = scur = 0.0
    fpre = float(f(xpre, *args)); fcur = float(f(xcur, *args))
    if fpre == 0:
        return xpre
    if fcur == 0:
        return xcur
    if math.copysign(1, fpre) == math.copysign(1, fcur):
        raise ValueError("f(a) and f(b) must have different signs")
    for _ in range(maxiter):
        if fpre != 0 and fcur != 0 and math.copysign(1, fpre) != math.copysign(1, fcur):
            xblk = xpre; fblk = fpre
            spre = scur = xcur - xpre
        if abs(fblk) < abs(fcur):
            xpre = xcur; xcur = xblk; xblk = xpre
            fpre = fcur; fcur = fblk; fblk = fpre
        delta = (xtol + rtol * abs(xcur)) / 2
        sbis = (xblk - xcur) / 2
        if fcur == 0 or abs(sbis) < delta:
            return xcur
        if abs(spre) > delta and abs(fcur) < abs(fpre):
            if xpre == xblk:
                stry = -fcur * (xcur - xpre) / (fcur - fpre)          # interpolate
            else:
                dpre = (fpre - fcur) / (xpre - xcur)                  # extrapolate
                dblk = (fblk - fcur) / (xblk - xcur)
                stry = -fcur * (fblk * dblk - fpre * dpre) / (dblk * dpre * (fblk - fpre))
            if 2 * abs(stry) < min(abs(spre), 3 * abs(sbis) - delta):
                spre = scur; scur = stry                              # good short step
            else:
                spre = sbis; scur = sbis                              # bisect
        else:
            spre = sbis; scur = sbis                                  # bisect
        xpre = xcur; fpre = fcur
        if abs(scur) > delta:
            xcur += scur
        else:
            xcur += delta if sbis > 0 else -delta
        fcur = float(f(xcur, *args))
    if disp:
        raise RuntimeError("brentq: failed to converge after %d iterations" % maxiter)
    return xcur
