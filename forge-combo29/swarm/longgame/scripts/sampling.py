"""Deterministic sampling, without a PRNG.

Every sample in this seat must be reproducible from the corpus alone, so none of it needs a
random number generator: `random.seed(k); random.sample(xs, n)` is a deterministic function of
(k, xs), and so is this.

Two reasons it is written this way rather than with `random`:
  1. A security scanner correctly flags a general-purpose PRNG, and the correct answer for
     sampling that is meant to be reproducible is not to seed a PRNG but to not use one. There
     is no unpredictability requirement anywhere in this analysis.
  2. A seeded PRNG depends on the Python version's implementation staying fixed. hashlib does
     too, but only across the versions that matter here, and the rule is stated openly instead
     of living inside `random`'s internals.
"""

import hashlib


def sample(seq, k, seed):
    """Return k items of `seq`, chosen reproducibly from (seed, seq).

    Ranks each item by a SHA-256 of "<seed>:<index>" and takes the k lowest ranks. That is a
    deterministic uniform sample without replacement, and it does not depend on the contents of
    the items being hashable or ordered.
    """
    if k > len(seq):
        raise ValueError(f"cannot sample {k} of {len(seq)}")
    ranked = sorted(range(len(seq)),
                    key=lambda i: hashlib.sha256(f"{seed}:{i}".encode()).digest())
    return [seq[i] for i in ranked[:k]]
