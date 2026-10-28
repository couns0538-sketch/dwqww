#!/usr/bin/env python3
"""R3-1 self-play: writes the v2 nets the self-play configs load (all function-preserving copies).

usage: make_nets.py <stack worktree> <out dir> <stand-alone pure net .fnn2>

Residual lock replicas (evaluate exactly like the compiled-in net, tools/nnue/forge_nnue_v2.py from-inc):
  replica_rm8.fnn2                 rm8 (8 mirrored king buckets)              -> NNUEKingBuckets 8
  replica_r1_ob8.fnn2              r1 + 8 identical output heads              -> NNUEOutputBuckets 8
  replica_r1_thr0.fnn2             r1 + zero threat block                     -> NNUEThreats 1
  replica_r1_pp0.fnn2              r1 + zero pawn-pair block                  -> NNUEPawnPairs 1
  replica_rm8_ob8_thr0_pp0.fnn2    all four at once (all-ON config)           -> KB 8, OB 8, Threats 1, PawnPairs 1
Stand-alone (PureNnue) nets, from the O4 material-trained pure smoke net (opus_round1/O4/REPORT.md, fnv1a
1544ea643b9cd9a7, 1 king bucket, 1 head):
  pure_material.fnn2               byte copy                                  -> PureNnue 1
  pure_material_rm8_ob8_thr0_pp0.fnn2  the same function as rm8 + 8 identical heads + zero threat and pawn-pair
                                   blocks, residual flag 0 (all-ON PureNnue config) -> PureNnue 1, KB 8, OB 8, Threats 1, PawnPairs 1
"""
import os
import shutil
import sys


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    stack, out, pure_src = sys.argv[1:]
    sys.path.insert(0, os.path.join(stack, "tools", "nnue"))
    import forge_nnue_v2 as V2  # noqa: E402  (the stack's own writer)

    os.makedirs(out, exist_ok=True)
    inc = V2.read_inc(os.path.join(stack, "src", "nnue_weights.inc"))
    specs = [
        ("replica_rm8.fnn2", "rm8", 1, False, False),
        ("replica_r1_ob8.fnn2", "r1", 8, False, False),
        ("replica_r1_thr0.fnn2", "r1", 1, True, False),
        ("replica_r1_pp0.fnn2", "r1", 1, False, True),
        ("replica_rm8_ob8_thr0_pp0.fnn2", "rm8", 8, True, True),
    ]
    for name, kind, ob, thr, pp in specs:
        net = V2.replica(inc, kind, ob)
        if thr:
            net = V2.with_zero_threats(net)
        if pp:
            net = V2.with_zero_pawn_pairs(net)
        checksum = V2.write_v2(os.path.join(out, name), **net)
        print(f"{name}: replica {kind} king_buckets {net['king_buckets']} output_buckets {net['output_buckets']} "
              f"threats {int(thr)} pawn_pairs {int(pp)} residual {net['residual']} fnv1a {checksum:016x}")

    pure = V2.read_v2(pure_src)
    if pure["residual"] or pure["king_buckets"] != 1 or pure["output_buckets"] != 1 or pure["feature_set"]:
        raise SystemExit(f"{pure_src}: expected a 1-bucket 1-head stand-alone net without extra inputs")
    shutil.copyfile(pure_src, os.path.join(out, "pure_material.fnn2"))
    print(f"pure_material.fnn2: copy of {pure_src} fnv1a {pure['checksum']:016x}")
    # The replica builder takes the arrays of a one-bucket net; the result keeps residual = False.
    base = dict(w1=pure["w1"], b1=pure["b1"], w2=pure["w2"], b2=pure["b2"], residual=False, hidden=pure["hidden"])
    net = V2.with_zero_pawn_pairs(V2.with_zero_threats(V2.replica(base, "rm8", 8)))
    checksum = V2.write_v2(os.path.join(out, "pure_material_rm8_ob8_thr0_pp0.fnn2"), **net)
    print(f"pure_material_rm8_ob8_thr0_pp0.fnn2: stand-alone rm8 + 8 heads + zero threats + zero pawn pairs "
          f"residual {net['residual']} fnv1a {checksum:016x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
