"""scipy.integrate.quad stand-in: adaptive Gauss-Kronrod 7/15 on finite intervals; returns (value, abs error estimate)."""
import heapq

# Kronrod 15 nodes/weights and the embedded Gauss 7 weights (standard tables, as in QUADPACK qk15)
_XGK = (0.991455371120812639206854697526329, 0.949107912342758524526189684047851, 0.864864423359769072789712788640926,
        0.741531185599394439863864773280788, 0.586087235467691130294144845693013, 0.405845151377397166906606412076961,
        0.207784955007898467600689403773245, 0.000000000000000000000000000000000)
_WGK = (0.022935322010529224963732008058970, 0.063092092629978553290700663189204, 0.104790010322250183839876322541518,
        0.140653259715525918745189590510238, 0.169004726639267902826583426598550, 0.190350578064785409913256402421014,
        0.204432940075298892414161999234649, 0.209482141084727828012999174891714)
_WG = (0.129484966168869693270611432679082, 0.279705391489276667901467771423780, 0.381830050505118944950369775488975,
       0.417959183673469387755102040816327)


def _gk15(f, a, b):
    c = 0.5 * (a + b); h = 0.5 * (b - a)
    fc = f(c)
    resk = fc * _WGK[7]; resg = fc * _WG[3]
    for j in range(7):
        x = h * _XGK[j]
        f1, f2 = f(c - x), f(c + x)
        resk += _WGK[j] * (f1 + f2)
        if j % 2 == 1:
            resg += _WG[j // 2] * (f1 + f2)
    return resk * h, abs((resk - resg) * h)


def quad(func, a, b, args=(), epsabs=1.49e-8, epsrel=1.49e-8, limit=50, **_ignored):
    f = (lambda x: float(func(x, *args)))
    a, b = float(a), float(b)
    val, err = _gk15(f, a, b)
    heap = [(-err, a, b, val, err)]
    total, toterr = val, err
    n = 1
    while toterr > max(epsabs, epsrel * abs(total)) and n < 10 * max(limit, 50):
        _, lo, hi, v, e = heapq.heappop(heap)
        mid = 0.5 * (lo + hi)
        v1, e1 = _gk15(f, lo, mid); v2, e2 = _gk15(f, mid, hi)
        total += v1 + v2 - v; toterr += e1 + e2 - e
        heapq.heappush(heap, (-e1, lo, mid, v1, e1)); heapq.heappush(heap, (-e2, mid, hi, v2, e2))
        n += 1
    # recompute the sum from the leaves (avoids drift of the running total)
    total = sum(item[3] for item in heap); toterr = sum(item[4] for item in heap)
    return total, toterr
