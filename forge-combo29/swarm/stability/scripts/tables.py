"""Collapse the measured JSON into the report's tables.

Every figure this prints is a literal count with its denominator beside it, or
a difference of two measured integers. Nothing here is a rate computed from a
sample and presented as if it were a population.
"""
import json
import os

EV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evidence")


def load(name):
    with open(os.path.join(EV, name)) as f:
        return json.load(f)


def main():
    print("== M1: one position, 30 fresh processes, Threads 1 ==")
    for fn in ["m1_t1_g00p30.json", "m1_t1_g00p14.json", "m1_t1_g00p70.json",
               "m1_t1_g00p100.json", "m1_t1_d16_g00p30.json"]:
        d = load(fn)
        print(f"{d['label']:26} distinct_scores={d['distinct_score_count']} "
              f"range={d['cp_range']} scores={d['distinct_scores']} "
              f"bm={d['distinct_bestmove']} depth={d['distinct_depth']} "
              f"nodes={d['nodes_min']}..{d['nodes_max']} bail={d['bail_count']}")

    print("\n== M2: same position set, Threads 4, 30 fresh processes ==")
    for fn in ["m2_t4_g00p30.json", "m2_t4_g00p14.json", "m2_t4_g00p70.json", "m2_t4_g00p100.json"]:
        d = load(fn)
        print(f"{d['label']:26} distinct_scores={d['distinct_score_count']}/{d['runs']} "
              f"cp {d['cp_min']}..{d['cp_max']} range={d['cp_range']} "
              f"n_bestmoves={len(d['distinct_bestmove'])} bm={d['distinct_bestmove']} "
              f"nodes={d['nodes_min']}..{d['nodes_max']} "
              f"node_ratio={d['nodes_max']/d['nodes_min']:.2f}")

    print("\n== M3: 200 corpus positions, twice, fresh process per run ==")
    for fn, tag in [("m3_corpus_T1.json", "Threads 1"), ("m3b_corpus_T4.json", "Threads 4")]:
        d = load(fn)
        print(f"{tag}: n={d['n_positions']} pairs={d['n_pairs']} "
              f"any={d['diff_any']} score={d['diff_score']} depth={d['diff_depth']} "
              f"bestmove={d['diff_bestmove']} nodes={d['diff_nodes']} "
              f"combos={d['field_combo_counts']} cp_gap_max={d['cp_gap_max']} "
              f"cp_gap_mean={round(d['cp_gap_mean'],1)} bail={d['bail_positions']} "
              f"refused={d['refused_positions']}")
        print(f"   by phase {d['diffs_by_phase']} of {d['phase_counts']}")

    print("\n== M4: order dependence, one process per arm ==")
    for arm in load("m4_order.json")["arms"]:
        print(f"{arm['comparison'][:62]:64} any={arm['diff_any']} score={arm['diff_score']} "
              f"depth={arm['diff_depth']} bm={arm['diff_bestmove']} {arm['field_combos']}")

    print()
    for arm in load("m4b_order_reset.json")["arms"]:
        print(f"{arm['comparison'][:62]:64} any={arm['diff_any']} score={arm['diff_score']} "
              f"bm={arm['diff_bestmove']} cp_gap_max={arm['cp_gap_max']} "
              f"cp_gap_mean={arm['cp_gap_mean']}")

    print("\n== M5: resets, batch vs the fresh-process reference ==")
    for arm in load("m5_resets.json")["arms"]:
        print(f"{arm['comparison'][:62]:64} any={arm['diff_any']} score={arm['diff_score']} "
              f"bm={arm['diff_bestmove']} {arm['field_combos']}")

    print("\n== M6: book RNG and depth reachability ==")
    d = load("book_rng.json")
    for k in ["q1_default_variety", "q1_variety_0", "q1_ownbook_off", "q1_default_variety_T4"]:
        a = d[k]
        print(f"{k:26} distinct_moves={a['distinct_moves']} hist={a['move_hist']} "
              f"book_replies={a['book_reply_count']}/{a['runs']}")
    print("go depth with OwnBook true -> book replies:",
          d["q2_depth_book_replies"]["bookish"], "/", d["q2_depth_book_replies"]["runs"])
    print("clock control with OwnBook true -> book replies:",
          d["q2_clock_control_book_replies"]["bookish"], "/",
          d["q2_clock_control_book_replies"]["runs"])


if __name__ == "__main__":
    main()
