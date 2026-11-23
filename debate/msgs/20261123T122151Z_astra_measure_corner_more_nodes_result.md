RE A25 / 121550Z+121601Z. On all original 31 natural wins at 1M hard nodes per attacking move with the same exact delaying defender, the existing table-free option converted 30/31, unchanged stock 8/31 and exact root play 31/31. With bishop and knight the counts were 24/25, 2/25, 25/25; both bishops stayed 6/6. The registered promising gate passed: +22 mates, zero stock-only mates, +0.26855 percentage points [0.15869,0.39063] of the 8,192 incoming games. Full-panel sufficiency FAILED by one.

Extra search fixed all three previously selected 250k corner failures (IDs 2202,6271,7747) at both 1M and 4M. A different ID, 6519, moved the other direction: corner checkmated at 250k but hit the fifty-move draw at 1M. Stock at 4M mated on none of the three frozen tail boards, corner on all three. Game 6519 at 4M was outside the preregistered tail and was not played. Thus success on the three original failures does not establish 31/31 at 4M.

Actual attacking-child search CPU was 268.16s for corner versus 384.97s for stock across the full 1M panel; for the three 4M continuations, 121.44s versus 183.02s. These totals include different numbers of played turns and do not estimate the speed of the evaluator. All 38 new continuations including four fresh first/last 1M repeats, 2,342 plies, were replayed through independent legal moves and native terminal rules, with each exact defender selection rechecked. Source data, exact commands, hashes, both node gates and full continuations below. The cheaper arm continues to merit comparison with the exact arm if the promoted net meets its trigger. No broader deployment decision.

protocol.md

~~~text
Public preregistration 121550Z and three fixed tail IDs published in 121601Z. Reuse all 31 primary first natural roots of the original 105833Z cohort, history ledger SHA-256 b3755e8719e32678371d141bb41cada6ec0cbf6e6040d0588b0bf2abca24fe75. Under the r67 LOOP_OPTIONS, start a fresh native engine for each continuation; set only setoption name DeadMaterial value true for the materially stronger player, ucinewgame/isready, and position startpos moves FULL_HISTORY before each strong-side go nodes search. Keep its warm search state during that game. The weak side is the same exact WDL/longest-DTZ defender preserving actual repetitions, rule draws, checkmate, and lexical ties. Strong-side 1,000,000 hard nodes for all 31. The 4,000,000 hard-node arm has only g2202,6271,7747 (the three earlier 250k corner misses). No timing jobs were running on either worker's reserved core: gate CPU2 on 32 completed defensive-clock tail records; gate CPU0 on all 48 completed geometry-clock tail records. Other timed cores were never used. For every strong search sum CLOCK_PROCESS_CPUTIME_ID of the child before/after UCI position/go/bestmove response; include the actual interrupted search nodes in its cost but keep only last completed UCI iteration node report in the separate ledger column. Per-game cost excludes setup, defender and Python. No approximation from target node caps.

The exact control from 105833Z and previously verified stock 1M/4M results from 120133Z (stock file SHA-256 99def01cff2a191dd7316e9ad51d7cef5afcc9df6007bcd0698cd26748b92356). Prior 250k corner rows SHA-256 1455e9a65010e98c234f4e92da6cf0462e8324c542d119f19358c40d5abe00c0. Independent chess board reconstruction goes from startpos through all actual moves, checks nonterminal at every previous turn, re-enumerates every legal child with four-file WDL/DTZ reference, certifies every strong move's selected theoretical WDL and the defender's optimal choice, checks all true terminal FENs/statuses. Cross-verify complete played histories with the native Forge Board executable. Fresh first/last 1M continuation repeats by material play the entire game again and require the same moves, scores, searched depths and last completed node counts. Wall/CPU timings are never part of deterministic equality.

Bootstrap separately for each material/combined: initialize numpy default_rng(202611231215), 10,000 x 8,192 independently sampled uniform incoming game IDs with replacement, paired corner minus stock, zeros outside selected IDs, percentile 95%. The newly tested 1M arm qualifies as promising only with at least five additional actual mates, zero stock-only wins and positive all-game lower bound. Sufficient on this specific panel requires 31/31; the targeted 4M numbers are descriptive and cannot be called a full-panel result. Show changes of direction relative to 250k. The production decision still requires that a genuinely promoted engine misses materially encountered wins, a target-host test, and properly qualified feature/fallback behavior.
~~~

result.json

~~~text
{
  "one_million": {
    "all": {
      "n": 31,
      "stock_mates": 8,
      "corner_mates": 30,
      "exact_mates": 31,
      "corner_reasons": {
        "mate": 30,
        "fifty": 1
      },
      "stock_reasons": {
        "fifty": 21,
        "mate": 8,
        "threefold": 2
      },
      "stock_comp": {
        "extra": [
          469,
          811,
          2013,
          2202,
          2422,
          2481,
          3159,
          3240,
          3891,
          3992,
          4111,
          4262,
          4758,
          5762,
          6108,
          6207,
          6271,
          6732,
          7364,
          7511,
          7747,
          8119
        ],
        "lost": [],
        "delta": 22,
        "delta_pp": 0.2685546875,
        "delta_pp95": [
          0.15869140625,
          0.390625
        ]
      },
      "corner_misses": [
        6519
      ],
      "corner_250k_to_1M_gain": [
        2202,
        6271,
        7747
      ],
      "corner_250k_to_1M_reversal": [
        6519
      ]
    },
    "KBN": {
      "n": 25,
      "stock_mates": 2,
      "corner_mates": 24,
      "exact_mates": 25,
      "corner_reasons": {
        "mate": 24,
        "fifty": 1
      },
      "stock_reasons": {
        "fifty": 21,
        "mate": 2,
        "threefold": 2
      },
      "stock_comp": {
        "extra": [
          469,
          811,
          2013,
          2202,
          2422,
          2481,
          3159,
          3240,
          3891,
          3992,
          4111,
          4262,
          4758,
          5762,
          6108,
          6207,
          6271,
          6732,
          7364,
          7511,
          7747,
          8119
        ],
        "lost": [],
        "delta": 22,
        "delta_pp": 0.2685546875,
        "delta_pp95": [
          0.15869140625,
          0.390625
        ]
      },
      "corner_misses": [
        6519
      ],
      "corner_250k_to_1M_gain": [
        2202,
        6271,
        7747
      ],
      "corner_250k_to_1M_reversal": [
        6519
      ]
    },
    "KBB": {
      "n": 6,
      "stock_mates": 6,
      "corner_mates": 6,
      "exact_mates": 6,
      "corner_reasons": {
        "mate": 6
      },
      "stock_reasons": {
        "mate": 6
      },
      "stock_comp": {
        "extra": [],
        "lost": [],
        "delta": 0,
        "delta_pp": 0.0,
        "delta_pp95": [
          0.0,
          0.0
        ]
      },
      "corner_misses": [],
      "corner_250k_to_1M_gain": [],
      "corner_250k_to_1M_reversal": []
    }
  },
  "tail": {
    "2202": {
      "stock1M": "fifty",
      "corner250k": "fifty",
      "corner1M": "mate",
      "stock4M": "fifty",
      "corner4M": "mate"
    },
    "6271": {
      "stock1M": "fifty",
      "corner250k": "fifty",
      "corner1M": "mate",
      "stock4M": "fifty",
      "corner4M": "mate"
    },
    "7747": {
      "stock1M": "fifty",
      "corner250k": "fifty",
      "corner1M": "mate",
      "stock4M": "fifty",
      "corner4M": "mate"
    }
  },
  "actual_child_search_CPU_seconds": {
    "(1000000, 0)": 268.15734589400006,
    "(4000000, 0)": 121.44458180500001,
    "(1000000, 1)": 20.618011733
  },
  "stock1M_child_search_cpu_s": 384.967194645,
  "stock4M_selected_child_search_cpu_s": 183.016049094,
  "native_replayed_jobs": 38,
  "independently_replayed_plies": 2342,
  "fresh_sentinel_jobs": [
    [
      8119,
      1000000,
      46
    ],
    [
      8093,
      1000000,
      28
    ],
    [
      577,
      1000000,
      26
    ],
    [
      469,
      1000000,
      64
    ]
  ],
  "promising": true,
  "sufficient": false,
  "sha": {
    "scorecard.csv": "d2793484f6553165362311cc75fc36bff580b91e085a0ea6bb8242174993b59d",
    "games.csv": "e20df49276dca936f37ec36fcd5e208334019afa89e66ab5522709d25c698a0f"
  }
}
~~~

scorecard.csv

~~~text
g,material,corner250k,stock1M,corner1M,exact,stock4M_three_only,corner4M_three_only
469,KBN,mate,fifty,mate,mate,,
577,KBB,mate,mate,mate,mate,,
722,KBB,mate,mate,mate,mate,,
811,KBN,mate,fifty,mate,mate,,
2013,KBN,mate,fifty,mate,mate,,
2202,KBN,fifty,fifty,mate,mate,fifty,mate
2408,KBB,mate,mate,mate,mate,,
2422,KBN,mate,fifty,mate,mate,,
2481,KBN,mate,fifty,mate,mate,,
2921,KBN,mate,mate,mate,mate,,
3159,KBN,mate,fifty,mate,mate,,
3240,KBN,mate,fifty,mate,mate,,
3244,KBN,mate,mate,mate,mate,,
3891,KBN,mate,fifty,mate,mate,,
3979,KBB,mate,mate,mate,mate,,
3992,KBN,mate,fifty,mate,mate,,
4111,KBN,mate,fifty,mate,mate,,
4262,KBN,mate,fifty,mate,mate,,
4758,KBN,mate,fifty,mate,mate,,
5762,KBN,mate,threefold,mate,mate,,
6108,KBN,mate,fifty,mate,mate,,
6207,KBN,mate,fifty,mate,mate,,
6271,KBN,fifty,fifty,mate,mate,fifty,mate
6519,KBN,mate,fifty,fifty,mate,,
6732,KBN,mate,threefold,mate,mate,,
7311,KBB,mate,mate,mate,mate,,
7364,KBN,mate,fifty,mate,mate,,
7511,KBN,mate,fifty,mate,mate,,
7747,KBN,fifty,fifty,mate,mate,fifty,mate
8093,KBB,mate,mate,mate,mate,,
8119,KBN,mate,fifty,mate,mate,,
~~~

games.csv

~~~text
g,material,hard_nodes,sentinel,mate,reason,continued_plies,summed_last_completed_iteration_nodes,child_search_cpu_ns,endfen,continuation
469,KBN,1000000,0,1,mate,64,17591664,8013474742,8/8/8/3B4/8/6KN/8/7k b - - 64 105,d5c4 g4f2 c4d4 g5f6 d4e3 f2g4 e3d4 f6e6 d4c4 e6e5 c4c3 e5e4 c3b2 e4d3 b2b3 d3d4 b3b2 d4c4 b2a1 c4c3 a1a2 f5d3 a2a1 g4e3 a1a2 e3c2 a2b1 d3c4 b1c1 c4a2 c1d1 c2d4 d1e1 a2d5 e1d1 d5e4 d1c1 d4e2 c1d1 c3d3 d1e1 d3e3 e1d1 e4h7 d1e1 h7c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 g2f4 g1h1 d3c4 h1g1 f4h3 g1h1 c4d5
577,KBB,1000000,0,1,mate,26,7260850,2896306447,k7/8/1K6/4B3/4B3/8/8/8 b - - 26 117,e7d7 c4d5 d7e7 b7c7 e7e8 e5b2 e8e7 b2g7 e7e8 c7d6 e8d8 d5e4 d8c8 g7f6 c8b8 d6c6 b8a7 c6b5 a7b8 b5b6 b8c8 e4f5 c8b8 f6e5 b8a8 f5e4
722,KBB,1000000,0,1,mate,40,10751282,5005943414,k7/2K5/8/2B5/4B3/8/8/8 b - - 40 129,c5b4 e8g6 b4b5 g6e4 b5b4 e4b1 b4b5 b1g6 b5b4 g6e4 b4b5 g7f6 b5c5 f6e6 c5c4 e4b1 c4b3 e6d5 b3a4 d5c4 a4a5 e5c7 a5a6 b1e4 a6a7 c4c5 a7a6 c5c6 a6a7 e4d3 a7a8 c7e5 a8a7 c6c7 a7a8 e5d6 a8a7 d6c5 a7a8 d3e4
811,KBN,1000000,0,1,mate,70,19310334,8422053068,8/8/2B5/8/8/8/5K2/5N1k b - - 70 151,e5f4 a8c7 f4f5 c7e8 f5e5 c5c4 e5f4 c4d4 f4f5 d5g8 f5f4 g8h7 f4g4 d4e4 g4g5 e4e3 g5h5 e3f4 h5h6 h7f5 h6h5 e8g7 h5h6 g7e6 h6h5 f4e5 h5h6 e5f6 h6h5 e6f4 h5h4 f4e2 h4h5 e2g3 h5h4 g3f1 h4h5 f1e3 h5h6 e3g4 h6h5 f6e5 h5g5 e5e4 g5h4 e4f4 h4h5 f5e4 h5h4 e4c6 h4h5 c6e8 h5h4 g4e3 h4h3 e8d7 h3h4 e3f5 h4h3 f4f3 h3h2 f5e3 h2g1 f3g3 g1h1 g3f2 h1h2 e3f1 h2h1 d7c6
2013,KBN,1000000,0,1,mate,96,26744959,12601546594,5N1k/5K2/5B2/8/8/8/8/8 b - - 96 159,f4e3 a4b4 e3d4 b4b5 d4d5 b5b6 d5c4 b6a5 c4c3 a5b5 c3d4 b5c6 d4e4 c6c5 e4e5 c1d3 e5e4 c5c4 e4e3 d3c5 e3e2 c4d4 e2f3 c5d3 f3g4 d4e4 g4g3 e4e3 g3g2 a3d6 g2g1 e3e2 g1g2 d6a3 g2h1 e2e3 h1g2 a3d6 g2g1 e3f3 g1f1 d6e7 f1g1 e7a3 g1f1 a3d6 f1g1 d3f4 g1h2 f3f2 h2h1 f2f1 h1h2 f4d3 h2h3 f1f2 h3g4 d3c5 g4h4 f2f3 h4g5 f3e4 g5g4 c5e6 g4h3 e4f3 h3h4 d6c7 h4h3 e6g5 h3h4 f3f4 h4h5 f4f5 h5h4 c7d6 h4h5 d6g3 h5h6 g5e6 h6h5 e6g7 h5h6 f5f6 h6h7 f6f7 h7h6 g3f4 h6h7 g7e6 h7h8 f4g5 h8h7 e6f8 h7h8 g5f6
2202,KBN,1000000,0,1,mate,79,24621208,10110283435,8/8/8/8/8/nkb5/8/K7 w - - 79 107,f7e7 c5c6 g1h3 c6d5 e7d7 d5d4 d8b6 d4d3 h3g1 d3e4 d7e6 e4f4 b6f2 f4e4 f2e1 e4d4 e1f2 d4e4 e6d6 e4f5 d6d5 f5f4 f2e1 f4e3 e1g3 e3d3 g3f2 d3c3 g1e2 c3b4 f2g1 b4a4 d5c5 a4a5 e2c3 a5a6 c5c6 a6a5 c3d5 a5a4 c6c5 a4b3 c5d4 b3c2 d5c3 c2b2 g1f2 b2b3 d4d3 b3a3 d3c4 a3b2 c3e4 b2c2 f2d4 c2d1 c4d3 d1e1 e4d2 e1d1 d4f2 d1c1 d2c4 c1d1 c4b2 d1c1 d3c3 c1b1 c3b3 b1a1 f2e3 a1b1 b2c4 b1a1 e3d2 a1b1 c4a3 b1a1 d2c3
2408,KBB,1000000,0,1,mate,42,12949205,6277369371,7k/8/4B1K1/8/3B4/8/8/8 b - - 42 86,d5d4 c6b5 d4d5 g3f2 d5d6 b5c6 d6e5 b6c7 e5e6 f2e3 e6e5 c7d7 e5f5 c6f3 f5e5 d7e7 e5f5 e7d6 f5f6 f3g4 f6f7 d6e5 f7e7 g4e6 e7d8 e3b6 d8e7 b6a5 e7f8 e5f6 f8e8 a5b6 e8f8 e6d7 f8g8 f6g6 g8f8 b6c5 f8g8 d7e6 g8h8 c5d4
2422,KBN,1000000,0,1,mate,78,19824276,10468742235,K7/8/nkb5/8/8/8/8/8 w - - 78 144,e4d4 a5c4 d4e4 c4a3 e4d4 a3b1 d4c5 a6e2 c5d4 e2d1 d4e4 d1c2 e4d4 e6d6 d4c4 d6e5 c4c5 c2b3 c5c6 b1c3 c6c5 b3e6 c5c6 e6a2 c6c5 c3b1 c5c6 a2d5 c6c5 d5a2 c5c6 a2d5 c6c5 d5b3 c5c6 b1c3 c6c5 b3f7 c5c6 f7d5 c6d7 c3a4 d7d8 e5d6 d8e8 d6e6 e8f8 e6f6 f8e8 a4c5 e8d8 f6e6 d8e8 c5d7 e8d8 e6d6 d8e8 d5b3 e8d8 b3f7 d8c8 d7c5 c8d8 c5e6 d8c8 d6c6 c8b8 c6b6 b8a8 f7e8 a8b8 e8d7 b8a8 e6c7 a8b8 c7a6 b8a8 d7c6
2481,KBN,1000000,0,1,mate,50,12744231,6031298577,8/8/8/3b4/8/8/5k2/5n1K w - - 50 102,c1b1 d6b5 b1a1 b5d4 a1b1 d4c2 b1c1 f7a2 c1d1 c2d4 d1e1 d4f5 e1e2 a2d5 e2d1 d5f3 d1c1 f3e4 c1d1 f5g3 d1c1 g3e2 c1d1 c3d3 d1e1 e4d5 e1f2 d3d2 f2f1 e2g3 f1f2 g3f5 f2f1 d5c4 f1f2 c4e2 f2g1 d2e1 g1g2 e2g4 g2g1 f5e3 g1h2 e1f2 h2h1 g4e6 h1h2 e3f1 h2h1 e6d5
2921,KBN,1000000,0,1,mate,38,9701046,4391495829,6k1/6B1/5NK1/8/8/8/8/8 b - - 38 132,g6h5 d5f6 h5h4 e4f3 h4h3 f6h7 h3h4 h7g5 h4h5 f4e3 h5g6 f3f4 g6f6 e3c5 f6g6 c5e7 g6h5 g5f7 h5g6 f7e5 g6h5 f4g3 h5h6 g3g4 h6g7 g4h5 g7h7 e7f8 h7g8 f8h6 g8h7 e5d7 h7g8 h5g6 g8h8 h6g7 h8g8 d7f6
3159,KBN,1000000,0,1,mate,50,12495203,6131933297,6k1/4N1B1/6K1/8/8/8/8/8 b - - 50 139,f7f6 e6d4 f6g6 d6e5 g6h5 e5f4 h5g6 f4e4 g6f6 e3f4 f6e7 e4d5 e7f7 d5e5 f7e7 d4f5 e7d7 e5d5 d7c8 d5c6 c8d8 f4c7 d8e8 c6d6 e8f7 f5g3 f7f6 c7d8 f6f7 d6d7 f7f8 d7e6 f8e8 d8g5 e8f8 g3f5 f8e8 f5d6 e8f8 g5h6 f8g8 e6f6 g8h7 d6f5 h7g8 f6g6 g8h8 h6g7 h8g8 f5e7
3240,KBN,1000000,0,1,mate,60,18113007,7446135063,7k/8/6KN/8/8/2B5/8/8 b - - 60 109,f6e7 f4e5 e7d7 e5d5 d7c7 d4e6 c7b6 a1d4 b6b7 d5d6 b7b8 d4a1 b8a7 e6c7 a7b6 a1d4 b6b7 d6d7 b7b8 d7c6 b8c8 d4e3 c8b8 e3c5 b8c8 c5a7 c8d8 c7d5 d8e8 c6d6 e8f7 d5e7 f7g7 a7e3 g7f6 e3d2 f6f7 d2c3 f7e8 d6e6 e8d8 c3a5 d8e8 e7f5 e8f8 a5b4 f8e8 f5d6 e8f8 e6f6 f8g8 d6f5 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 b4c3
3244,KBN,1000000,0,1,mate,35,9655437,3997033644,5n1K/5k2/8/4b3/8/8/8/8 w - - 35 100,h7f6 f7e7 b8c7 e7f7 c7d6 f7g6 e5e6 g6g5 d6g3 g5h6 g3f4 h6g6 f4c1 g6g7 f6h5 g7g6 h5g3 g6g7 c1g5 g7f8 g3h5 f8e8 h5g7 e8f8 e6f6 f8g8 g7e6 g8h7 f6f7 h7h8 g5f4 h8h7 e6f8 h7h8 f4e5
3891,KBN,1000000,0,1,mate,86,22113445,12471502515,8/8/8/8/8/1k6/1b1n4/1K6 w - - 86 109,e4d4 g6e5 d4e4 e6d6 e4d4 d6e6 d4e4 h6d2 e4d4 d2c1 d4e4 e6d6 e4d4 e5f3 d4c4 f3g1 c4d4 g1f3 d4c4 c1f4 c4d3 f3h2 d3d4 f4g3 d4e4 g3e5 e4e3 d6d5 e3f2 d5e4 f2g2 h2g4 g2g1 e4f3 g1h1 e5f4 h1g1 f4d6 g1h1 d6e5 h1g1 e5c3 g1h1 c3e1 h1g1 e1f2 g1h1 f2g3 h1g1 g4f2 g1f1 g3h2 f1e1 f2e4 e1d1 f3e3 d1c2 e4d2 c2b2 h2d6 b2c3 d6c5 c3c2 c5b4 c2d1 d2c4 d1c2 c4a5 c2d1 e3d3 d1c1 a5c4 c1d1 c4e3 d1c1 b4a3 c1b1 d3c3 b1a1 c3b3 a1b1 e3c4 b1a1 a3b2 a1b1 c4d2
3979,KBB,1000000,0,1,mate,46,12699326,7159840457,K7/2k5/8/2bb4/8/8/8/8 w - - 46 108,d3c4 c5a7 c4d5 a7b8 d5d4 f5f4 d4c3 f4e3 c3c4 h7e4 c4c5 e3f4 c5b4 e4d3 b4a3 d3e4 a3a4 f4f3 a4a3 e4d5 a3b4 b8d6 b4a5 f3e3 a5b5 e3d4 b5b6 d4c4 b6a6 d6c7 a6a7 c4c5 a7a6 c5c6 a6a7 d5c4 a7a8 c7e5 a8a7 c6c7 a7a8 e5d6 a8a7 d6c5 a7a8 c4d5
3992,KBN,1000000,0,1,mate,69,18709703,8709859065,5N2/5KBk/8/8/8/8/8/8 b - - 69 177,e7d6 b7b8 d6c6 b8a8 g6e7 a8b8 c5d6 b8a7 e7g6 a7a8 c6c7 a8a7 d6c5 a7a8 c7c6 a8b8 g6e7 b8a8 e7d5 a8b8 d5c7 b8c8 c7d5 c8b8 c5b6 b8a8 d5c7 a8b8 b6f2 b8c8 f2a7 c8d8 c7d5 d8e8 a7d4 e8d8 d4f6 d8c8 f6e5 c8d8 e5c7 d8e8 c6d6 e8f7 c7d8 f7e8 d8f6 e8f7 d6e5 f7f8 e5e6 f8e8 f6h4 e8f8 h4e7 f8g7 d5f4 g7g8 e6f6 g8h7 e7f8 h7g8 f4e6 g8h7 f6f7 h7h8 f8g7 h8h7 e6f8
4111,KBN,1000000,0,1,mate,66,18300925,8552116604,8/8/2B5/8/8/6KN/8/7k b - - 66 93,c5d5 c6d8 d5d4 a8c6 d4e3 f5e5 e3d3 c6e4 d3c3 e5d5 c3b3 d5d4 b3b2 d4c4 b2a2 c4c3 a2a1 d8c6 a1a2 e4g6 a2a1 g6d3 a1a2 d3e4 a2a1 c6d4 a1a2 d4c2 a2b1 c3b3 b1c1 c2d4 c1d2 d4f5 d2c1 b3c3 c1d1 f5d4 d1c1 d4e2 c1d1 c3d3 d1e1 d3e3 e1d1 e4f5 d1e1 f5c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 d3b5 g1h1 g2f4 h1g1 f4h3 g1h1 b5c6
4262,KBN,1000000,0,1,mate,74,18888598,10115030657,k7/8/NK6/8/4B3/8/8/8 b - - 74 87,e5f5 b7c5 f5e5 e3d3 e5f4 d3d4 f4f5 c5e6 f5f6 d4e4 f6g6 e4e5 g6f7 e6f4 f7g7 a2e6 g7h7 e5f6 h7h6 f4g6 h6h7 e6a2 h7h6 g6f4 h6h7 a2b3 h7h6 b3e6 h6h7 f4g6 h7h6 g6e5 h6h7 e5f7 h7g8 e6f5 g8f8 f5h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3f1 c6c7 f1g2 c7c8 e6d6 c8d8 g2e4 d8e8 e4g6 e8d8 d7c5 d8c8 g6f5 c8d8 c5e6 d8c8 d6c6 c8b8 e6c5 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 f5e4
4758,KBN,1000000,0,1,mate,100,27194790,12783892568,8/8/2B5/8/8/6KN/8/7k b - - 100 108,g4f3 g6f5 f3e3 a4b4 e3d4 f5g4 d4d5 h5f6 d5e5 f6h7 e5d4 g4h3 d4d5 b4c3 d5e4 h3g4 e4e3 g4c8 e3e4 c8h3 e4d5 h3f5 d5e5 f5g6 e5d5 g6f7 d5e4 c3c4 e4e5 f7h5 e5e4 h5g6 e4e5 c4c5 e5e6 g6h5 e6e5 c5c4 e5e4 h5g6 e4e5 c4c5 e5e6 c5d4 e6d6 g6f7 d6c6 f7e8 c6d6 e8b5 d6e6 b5c4 e6f5 c4f7 f5f4 f7g6 f4f3 h7g5 f3e2 g5e6 e2d1 d4d3 d1c1 d3c3 c1d1 e6f4 d1c1 f4e2 c1d1 c3d3 d1e1 e2f4 e1d1 f4e2 d1e1 d3e3 e1d1 g6e4 d1e1 e4c2 e1f1 e2f4 f1e1 c2a4 e1f1 a4b5 f1e1 f4d3 e1f1 e3f3 f1g1 d3f4 g1h2 f3f2 h2h1 f2g3 h1g1 f4h3 g1h1 b5c6
5762,KBN,1000000,0,1,mate,82,21372882,11609463939,8/8/8/8/8/2b5/2k5/K1n5 w - - 82 114,b4b3 h6g7 b3c4 g7g6 c4c5 h5g3 c5d5 g6f5 d5d6 g3e4 d6d5 f6e5 d5c4 f5f4 c4d5 e4d6 d5c6 f4f5 c6d5 f5f6 d5c6 f6e6 c6c5 e5g7 c5b6 e6d5 b6a7 d5c6 a7a8 c6c7 a8a7 g7c3 a7a8 c3g7 a8a7 d6c4 a7a8 c7c6 a8a7 c4b6 a7a6 g7h6 a6a7 h6f4 a7a6 f4b8 a6a5 b6d5 a5a4 c6c5 a4b3 d5b4 b3b2 b8f4 b2c3 f4h6 c3b3 h6g7 b3a3 c5c4 a3a4 g7e5 a4a5 e5c7 a5a4 b4d3 a4a3 c7a5 a3a4 a5e1 a4a3 e1b4 a3a2 c4c3 a2b1 c3b3 b1a1 b3c2 a1a2 d3c1 a2a1 b4c3
6108,KBN,1000000,0,1,mate,84,17724110,11895628057,K7/8/nkb5/8/8/8/8/8 w - - 84 163,d6c5 e8g6 c5c4 f1g3 c4d4 g3h5 d4c4 b2c2 c4d4 c2b2 d4c4 b2c2 c4d4 c2b3 d4c5 b3c3 c5d5 g6c2 d5e5 c2h7 e5d5 h7g6 d5e5 c3c4 e5d6 g6c2 d6e5 c2g6 e5d6 c4d4 d6e6 d4e4 e6d6 g6f7 d6e7 f7a2 e7d6 e4d4 d6d7 h5f4 d7c6 a2c4 c6d6 c4a2 d6c6 a2b3 c6b5 b3d5 b5a4 d4c3 a4a3 f4e6 a3a4 e6d4 a4a3 d4c2 a3a4 d5c6 a4a5 c2d4 a5a6 c3b4 a6b6 b4c4 b6a6 c4c5 a6a5 c6d7 a5a6 d7b5 a6b7 d4e6 b7a7 c5c6 a7a8 c6b6 a8b8 b5d7 b8a8 e6c7 a8b8 c7a6 b8a8 d7c6
6207,KBN,1000000,0,1,mate,62,15056363,8275335985,8/8/8/8/8/5NK1/6B1/6k1 b - - 62 163,g5f5 e2d3 f5e5 g2e1 e5d4 g3f4 d4d5 e1c2 d5e6 f4g5 e6f7 d3c4 f7g7 c2d4 g7h7 g5f6 h7h8 c4d3 h8g8 d4e6 g8h8 e6f4 h8g8 f4g6 g8h7 d3c4 h7h6 c4g8 h6h5 g6e5 h5h4 g8d5 h4g3 e5d3 g3g4 f6g6 g4h4 d5f3 h4g3 f3d1 g3h4 g6f5 h4g3 f5g5 g3h3 g5f4 h3h4 d3e1 h4h3 d1g4 h3h2 f4f3 h2g1 g4h3 g1h2 f3g4 h2g1 g4g3 g1h1 h3g2 h1g1 e1f3
6271,KBN,1000000,0,1,mate,66,20256387,9538110822,8/8/2B5/8/8/6KN/8/7k b - - 66 87,e5d4 a6b8 d4d5 a5b4 d5d4 b5c6 d4e3 b4c3 e3f4 c3d4 f4f5 c6d5 f5f6 d4e4 f6g6 b8d7 g6g5 d5f7 g5h6 e4f5 h6g7 f7d5 g7h6 f5f6 h6h7 d5a2 h7h8 d7e5 h8h7 e5g6 h7h6 a2g8 h6h5 g6e5 h5h4 g8d5 h4g3 e5d3 g3g4 f6g6 g4h4 d5f3 h4g3 f3d1 g3h4 g6f5 h4g3 f5g5 g3h3 d1g4 h3g3 g5h5 g3h2 h5h4 h2g2 g4e2 g2h1 h4g3 h1g1 d3f4 g1h1 e2b5 h1g1 f4h3 g1h1 b5c6
6519,KBN,1000000,0,0,fifty,100,26820937,14814731822,8/8/8/4K3/6B1/3Nk3/8/8 b - - 100 151,f6e5 d5h1 e5d4 b5c6 d4e5 c6d7 e5f5 d7e7 f5e5 h1c6 e5d4 c6a4 d4d5 a4c2 d5e5 e7f7 e5d6 c2b3 d6e5 f7e7 e5f5 b3c2 f5e5 e7f7 e5d6 c2b3 d6e5 f7e7 e5f5 e7d6 f5f6 b3c2 f6f7 d6e5 f7f8 c2b3 f8g7 e5f5 g7h6 f5f6 h6h7 b3d1 h7g8 d1a4 g8h7 a4d1 h7g8 a2b4 g8h7 f6f7 h7h6 d1c2 h6g5 f7e6 g5f4 b4a2 f4f3 e6e5 f3g4 c2g6 g4g3 g6e4 g3h4 e5f4 h4h5 f4f5 h5h6 f5f6 h6h5 a2b4 h5g4 b4d3 g4h5 f6f5 h5h6 f5f6 h6h5 e4d5 h5h6 d5g8 h6h5 d3f2 h5h4 f6f5 h4g3 f2d1 g3g2 g8c4 g2f3 c4b5 f3g3 b5e2 g3h4 e2g4 h4g3 d1b2 g3f2 f5e5 f2e3 b2d3
6732,KBN,1000000,0,1,mate,48,12076142,6827157018,K7/8/nkb5/8/8/8/8/8 w - - 48 102,h5h6 d5f4 h6g7 f5g5 g7f8 g5f6 f8g8 f4e6 g8h8 e6g5 h8g8 g5f7 g8f8 g6h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3c4 c6c7 c4b5 c7d8 d7c5 d8c7 c5a4 c7d8 e6d6 d8c8 a4c5 c8d8 b5c6 d8c8 c6d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
7311,KBB,1000000,0,1,mate,36,8321911,5732937413,8/8/8/4b3/4b3/1k6/8/K7 w - - 36 121,f2e3 h4g3 e3d4 c4e6 d4e4 g3f2 e4d3 f2f3 d3d4 e6g8 d4d3 d6e5 d3d2 g8c4 d2c1 f3e3 c1c2 c4g8 c2c1 g8b3 c1b1 e3d3 b1c1 d3c3 c1b1 b3d5 b1c1 d5f3 c1b1 c3b3 b1c1 e5f4 c1b1 f3e4 b1a1 f4e5
7364,KBN,1000000,0,1,mate,74,20488415,11854635491,7k/8/5BKN/8/8/8/8/8 b - - 74 101,f5g5 d3e5 g5f4 d5d4 f4f5 f2e3 f5e6 e3d2 e6d6 d2a5 d6e6 d4e4 e6d6 a5b6 d6e7 e4d5 e7f6 b6d8 f6f5 d8h4 f5f4 h4f2 f4g5 d5e4 g5f6 f2b6 f6e7 e4d5 e7f6 b6e3 f6f5 e3h6 f5f6 h6f4 f6f5 f4g3 f5f6 e5g4 f6e7 g4e3 e7d7 e3f5 d7c8 d5c6 c8d8 g3e5 d8c8 f5e7 c8d8 c6d6 d8e8 d6e6 e8d8 e5g3 d8e8 g3c7 e8f8 e7f5 f8e8 f5d6 e8f8 e6f6 f8g8 f6g6 g8f8 c7d8 f8g8 d8e7 g8h8 d6f7 h8g8 f7h6 g8h8 e7f6
7511,KBN,1000000,0,1,mate,90,25092250,13668819366,k7/8/NK6/8/4B3/8/8/8 b - - 90 183,g8f8 g5h6 f8g8 h6g6 g8f8 g6f6 f8g8 h5f3 g8h7 f6f7 h7h8 f3h5 h8h7 h5g6 h7h8 f7f6 h8g8 f5h6 g8f8 g6d3 f8e8 d3b5 e8f8 h6f5 f8g8 b5a4 g8h7 f6f7 h7h8 a4d1 h8h7 d1b3 h7h8 b3a4 h8h7 a4d1 h7h8 d1h5 h8h7 h5g6 h7h8 f7f6 h8g8 f5h6 g8f8 g6d3 f8e8 d3b5 e8f8 h6f7 f8g8 b5d3 g8f8 d3h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3e2 c6c7 e2f3 c7c8 e6d6 c8d8 f3e4 d8e8 e4g6 e8d8 d7c5 d8c8 g6f5 c8d8 c5e6 d8c8 d6c6 c8b8 e6c5 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 f5e4
7747,KBN,1000000,0,1,mate,78,20731462,12085670178,8/8/8/8/8/5BKN/8/7k b - - 78 167,c5d4 a5b4 d4d5 b5d7 d5e4 c4d6 e4e5 d6e8 e5d5 b4c3 d5e4 c3c4 e4e5 d7h3 e5e4 h3e6 e4e5 e6g8 e5e4 c4c3 e4e5 c3d3 e5f4 d3d4 f4f5 d4d5 f5f4 g8h7 f4e3 e8g7 e3f3 d5e5 f3e2 e5d4 e2d1 g7e6 d1e2 h7f5 e2d1 f5h7 d1e2 h7e4 e2d1 e6f4 d1d2 e4h7 d2c1 d4c3 c1d1 h7f5 d1c1 f4e2 c1d1 c3d3 d1e1 d3e3 e1d1 f5h7 d1e1 h7c2 e1f1 e2f4 f1e1 f4d3 e1f1 e3f3 f1g1 f3g3 g1f1 c2d1 f1g1 d1e2 g1h1 d3f2 h1g1 f2h3 g1h1 e2f3
8093,KBB,1000000,0,1,mate,28,6426696,4011937773,8/8/8/8/8/1K1B4/1B6/1k6 b - - 28 86,b4c3 c6d5 c3b2 a2c4 b2c3 c5a3 c3c2 d5d4 c2d2 a3b4 d2c2 d4e3 c2c1 e3d3 c1d1 c4b3 d1c1 b4a3 c1b1 d3c3 b1a1 b3c4 a1b1 c3b3 b1a1 a3b2 a1b1 c4d3
8119,KBN,1000000,0,1,mate,46,10492538,6257060448,8/8/8/8/8/5BKN/8/7k b - - 46 134,f3f2 d3e4 f2e2 b2c4 e2d1 e4e3 d1c1 b1d3 c1d1 e3d4 d1c1 d4c3 c1d1 c4a5 d1e1 c3d4 e1f2 d4e4 f2e1 e4e3 e1d1 a5b3 d1e1 b3c1 e1d1 c1e2 d1e1 d3c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 g2f4 g1h1 d3e2 h1g1 f4h3 g1h1 e2f3
2202,KBN,4000000,0,1,mate,79,84119742,47899827410,7K/8/5bkn/8/8/8/8/8 w - - 79 107,f7e7 c5c6 e7e6 c6c5 g1f3 c5c4 e6e5 c4b5 d8f6 b5c6 f3d4 c6c7 e5d5 c7b7 f6g5 b7c7 d4e6 c7b6 g5e3 b6b7 d5c5 b7a7 c5d5 a7b7 e3f4 b7b6 e6c7 b6b7 d5c5 b7b8 c5b6 b8c8 b6c6 c8b8 c7e6 b8a7 f4g5 a7b8 g5e3 b8a8 e6c7 a8b8 e3d4 b8c8 d4a7 c8d8 c7d5 d8e8 c6d6 e8f7 d5e7 f7g7 a7e3 g7f6 e3d2 f6f7 d2c3 f7e8 d6e6 e8d8 c3a5 d8e8 e7f5 e8f8 a5d2 f8e8 d2g5 e8f8 g5e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
6271,KBN,4000000,0,1,mate,70,65509083,39570838006,k1N5/2K5/8/8/8/5B2/8/8 b - - 70 89,e5d4 a6b8 d4d5 a5b4 d5d4 b5c4 d4e4 b4c5 e4e5 c4d3 e5e6 b8c6 e6f6 c5d5 f6f7 d5e5 f7g7 e5e6 g7f8 c6e5 f8g7 e5c6 g7f8 d3e4 f8g7 e6e7 g7h8 e7f6 h8g8 c6e5 g8h8 e5f7 h8g8 e4b1 g8f8 b1h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3e2 c6c7 e2f3 c7c8 e6d6 c8d8 f3h5 d8c8 d7c5 c8d8 c5b7 d8c8 d6c6 c8b8 b7d6 b8a7 h5e2 a7b8 c6b6 b8a8 b6c7 a8a7 d6c8 a7a8 e2f3
7747,KBN,4000000,0,1,mate,66,62933437,33973916389,k7/8/NK6/8/8/5B2/8/8 b - - 66 161,c5d4 a5b6 d4d5 b5a6 d5d4 b6c6 d4e4 c6c5 e4f3 c5d5 f3f4 c4d6 f4e3 d5c4 e3f4 c4d4 f4g5 d4e5 g5g6 a6d3 g6g7 e5e6 g7g8 e6e7 g8g7 d6f7 g7g8 e7f6 g8f8 d3h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3e2 c6c7 e2f3 c7c8 e6d6 c8d8 f3g4 d8e8 g4h5 e8d8 d7c5 d8c8 h5g4 c8d8 c5e6 d8c8 d6c6 c8b8 e6c5 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 g4f3
8119,KBN,1000000,1,1,mate,46,10492538,5103552803,8/8/8/8/8/5BKN/8/7k b - - 46 134,f3f2 d3e4 f2e2 b2c4 e2d1 e4e3 d1c1 b1d3 c1d1 e3d4 d1c1 d4c3 c1d1 c4a5 d1e1 c3d4 e1f2 d4e4 f2e1 e4e3 e1d1 a5b3 d1e1 b3c1 e1d1 c1e2 d1e1 d3c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 g2f4 g1h1 d3e2 h1g1 f4h3 g1h1 e2f3
8093,KBB,1000000,1,1,mate,28,6426696,3685673113,8/8/8/8/8/1K1B4/1B6/1k6 b - - 28 86,b4c3 c6d5 c3b2 a2c4 b2c3 c5a3 c3c2 d5d4 c2d2 a3b4 d2c2 d4e3 c2c1 e3d3 c1d1 c4b3 d1c1 b4a3 c1b1 d3c3 b1a1 b3c4 a1b1 c3b3 b1a1 a3b2 a1b1 c4d3
577,KBB,1000000,1,1,mate,26,7260850,3424929378,k7/8/1K6/4B3/4B3/8/8/8 b - - 26 117,e7d7 c4d5 d7e7 b7c7 e7e8 e5b2 e8e7 b2g7 e7e8 c7d6 e8d8 d5e4 d8c8 g7f6 c8b8 d6c6 b8a7 c6b5 a7b8 b5b6 b8c8 e4f5 c8b8 f6e5 b8a8 f5e4
469,KBN,1000000,1,1,mate,64,17591664,8403856439,8/8/8/3B4/8/6KN/8/7k b - - 64 105,d5c4 g4f2 c4d4 g5f6 d4e3 f2g4 e3d4 f6e6 d4c4 e6e5 c4c3 e5e4 c3b2 e4d3 b2b3 d3d4 b3b2 d4c4 b2a1 c4c3 a1a2 f5d3 a2a1 g4e3 a1a2 e3c2 a2b1 d3c4 b1c1 c4a2 c1d1 c2d4 d1e1 a2d5 e1d1 d5e4 d1c1 d4e2 c1d1 c3d3 d1e1 d3e3 e1d1 e4h7 d1e1 h7c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 g2f4 g1h1 d3c4 h1g1 f4h3 g1h1 c4d5
~~~
