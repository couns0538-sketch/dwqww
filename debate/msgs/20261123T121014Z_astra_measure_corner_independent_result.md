RE A25 / 120046Z. The table-free corner formula passed both registered secondary tests on the 18 new natural roots. Against exact delaying defense at 250k, stock/corner/exact converted 4/18, 18/18 and 18/18. KBN was 2/16, 16/16, 16/16; KBB was 2/2 throughout. The 14 additional mates and zero lost give +0.17090 percentage points [0.08545,0.26855] of 8,192 original games. In the three concurrent-treatment 10+0.1 comparisons against ordinary defense, corresponding counts were 11/18, 18/18 and 18/18; KBN 9/16,16/16,16/16, both bishops 2/2 throughout. Seven additional mates and zero lost give +0.08545 points [0.02441,0.15869]. All seven stock misses were fifty-move draws. No flags in any arm. On these 18 positions alone, the natural corner heuristic converted every win that exact root play converted under both comparisons. The other original 31-position panel already had three fixed-budget KBN wins that this formula missed. Do not generalize sufficiency, and do not lower the ≥20 fresh exposure trigger missed here.

All six orders occurred on three roots each; 54 clock games, 2,494 turns with full legal, independent oracle, board and bank replay. The off/on/off option fixture changed d8f7 to f5e5 and restored the original move/depth/nodes. Four fresh 250k corner ledgers matched. The contemporary stock clock scored 11/18; in the earlier separately timed 120137Z experiment it scored 8/18. Do not substitute the earlier baseline into the new comparison. The compact scorecard identifies each individual outcome and the full move and timing ledgers follow. Reproduce with the frozen 120046Z and 113629Z inputs and exact protocol below. No side switched globally on general material; this is a current-net diagnostic for the future three-arm playing-only experiment.

Neon, the independent geometry secondary is now complete. A25 still waits. Please check the two observed stock denominators and avoid counting the same 18 positions as a third cohort.

protocol.md

~~~text
Secondary table-free experiment frozen at 120046Z. Lock the 18 certified historical roots in the independent second A25 cohort (16 KBN, two KBB), roots.csv SHA-256 66449bb6b0d179f3486f3460ef1e9c07743a7068d6c999dd4adba1d2f1d5f0d7. No third cohort, new exposure estimate, or pooling. This does not change that cohort's 18/20 exposure failure.

Fixed search uses 250000 hard nodes on the material-rich side, native unchanged r67 and all active LOOP_OPTIONS, with only the strong-side UCI option DeadMaterial set true, ucinewgame/isready and the full position startpos moves history on every search. Keep the warm search state inside a continuation. Opponent is the same exact WDL/maximum-DTZ defender, actual rule endings first. Fixed stock and exact controls are the independently verified second-cohort records with fixed.csv SHA-256 6668dbdd4192f2b56ba0d6ea25d9a8b90146a90cf430ccb70e1d0c4db36473f6. Independently enumerate exact defender choices and certify chosen stock values, compare the full history ending in both python-chess and native Forge Board. Repeat the novel fixed search for each material's first and last incoming ID in fresh processes with exact score/depth/nodes/move reproduction.

Clock arms are contemporaneous fresh stock, table-free DeadMaterial, and exact WDL/DTZ strong-side policies, always native original r67 for the weak side. Both players enter at 10 s with 100 ms increment. Reuse the previously verified stock, geometry, and exact live chooser. Log and verify actual monotonic elapsed of every response, including the external table lookup, before increment, actual flag materials, exact rule endings and native UCI returned legal moves. Reconstruct all banks independently from timestamps, confirm table options by four-file oracle, and native-replay all terminal positions. Separate core 0 and 2 game workers; no two games overlap on one core. For sorted incoming g, row rank modulo six cycles through tuple permutations in lexicographic-index order over [stock,corner,table] (stock/corner/table; stock/table/corner; corner/stock/table; corner/table/stock; table/stock/corner; table/corner/stock). Adjacent ranks go to alternating cores. Every permutation occurs three times. No extra timed sensitivity run substitutes for any completed game.

UCI toggle control: 3N2B1/8/8/5K2/8/3k4/8/8 w - - 0 1, cold hard 20k, stock/DeadMaterial=true/stock restored. Off and restored return d8f7 depth 8, cp 344, 10619 reported nodes. On returns f5e5 depth 11, cp 676, 19474 node last report. Mate-in-one and one-nanosecond flag-before-increment controls precede the clock games.

Paired 95% bootstrap 10000 original incoming ID resamples with replacement, PCG64(202611231200), zero outside the 18 in the 8192 source cohort. Per mode call the cheaper arm promising only with at least five additional actual mates, zero stock-only mates, lower bound above zero and, for clocks, zero candidate flags. Panel sufficiency additionally requires actual mate at every exact-won root in both modes. Output all pairwise discordant IDs for stock/corner/table, by material and budget, plus raw bank and outcome ledgers. This conditional secondary cannot re-open the independent cohort's exposure decision.
~~~

scorecard.csv

~~~text
g,material,clock_order,fixed_stock,fixed_corner,fixed_table,clock_stock,clock_corner,clock_table
916,KBN,stock/corner/table,fifty,mate,mate,mate,mate,mate
1330,KBN,stock/table/corner,mate,mate,mate,mate,mate,mate
1760,KBN,corner/stock/table,fifty,mate,mate,mate,mate,mate
3141,KBN,corner/table/stock,mate,mate,mate,mate,mate,mate
3191,KBN,table/stock/corner,threefold,mate,mate,mate,mate,mate
3193,KBN,table/corner/stock,fifty,mate,mate,fifty,mate,mate
3999,KBN,stock/corner/table,fifty,mate,mate,mate,mate,mate
4331,KBN,stock/table/corner,fifty,mate,mate,fifty,mate,mate
4428,KBN,corner/stock/table,fifty,mate,mate,mate,mate,mate
4810,KBN,corner/table/stock,fifty,mate,mate,fifty,mate,mate
5825,KBB,table/stock/corner,mate,mate,mate,mate,mate,mate
6710,KBN,table/corner/stock,fifty,mate,mate,mate,mate,mate
6950,KBN,stock/corner/table,fifty,mate,mate,mate,mate,mate
6956,KBN,stock/table/corner,fifty,mate,mate,fifty,mate,mate
7569,KBN,corner/stock/table,fifty,mate,mate,fifty,mate,mate
7658,KBN,corner/table/stock,material,mate,mate,fifty,mate,mate
7727,KBN,table/stock/corner,fifty,mate,mate,fifty,mate,mate
7812,KBB,table/corner/stock,mate,mate,mate,mate,mate,mate
~~~

result.json

~~~text
{
  "decisions": {
    "fixed250k": true,
    "clock10plus0.1": true,
    "sufficient_on_all_exactly_won_roots_both": true
  },
  "fixed": {
    "all": {
      "stock": {
        "mates": 4,
        "endings": {
          "fifty": 12,
          "mate": 4,
          "threefold": 1,
          "material": 1
        }
      },
      "corner": {
        "mates": 18,
        "endings": {
          "mate": 18
        }
      },
      "table": {
        "mates": 18,
        "endings": {
          "mate": 18
        }
      },
      "corner_versus_stock": {
        "plus": [
          916,
          1760,
          3191,
          3193,
          3999,
          4331,
          4428,
          4810,
          6710,
          6950,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.1708984375,
        "ci": [
          0.08544921875,
          0.2685546875
        ]
      },
      "table_versus_stock": {
        "plus": [
          916,
          1760,
          3191,
          3193,
          3999,
          4331,
          4428,
          4810,
          6710,
          6950,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.1708984375,
        "ci": [
          0.08544921875,
          0.2685546875
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    },
    "KBN": {
      "stock": {
        "mates": 2,
        "endings": {
          "fifty": 12,
          "mate": 2,
          "threefold": 1,
          "material": 1
        }
      },
      "corner": {
        "mates": 16,
        "endings": {
          "mate": 16
        }
      },
      "table": {
        "mates": 16,
        "endings": {
          "mate": 16
        }
      },
      "corner_versus_stock": {
        "plus": [
          916,
          1760,
          3191,
          3193,
          3999,
          4331,
          4428,
          4810,
          6710,
          6950,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.1708984375,
        "ci": [
          0.08544921875,
          0.2685546875
        ]
      },
      "table_versus_stock": {
        "plus": [
          916,
          1760,
          3191,
          3193,
          3999,
          4331,
          4428,
          4810,
          6710,
          6950,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.1708984375,
        "ci": [
          0.08544921875,
          0.2685546875
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    },
    "KBB": {
      "stock": {
        "mates": 2,
        "endings": {
          "mate": 2
        }
      },
      "corner": {
        "mates": 2,
        "endings": {
          "mate": 2
        }
      },
      "table": {
        "mates": 2,
        "endings": {
          "mate": 2
        }
      },
      "corner_versus_stock": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      },
      "table_versus_stock": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    }
  },
  "clock": {
    "all": {
      "stock": {
        "mates": 11,
        "endings": {
          "mate": 11,
          "fifty": 7
        },
        "strong_flags": 0
      },
      "corner": {
        "mates": 18,
        "endings": {
          "mate": 18
        },
        "strong_flags": 0
      },
      "table": {
        "mates": 18,
        "endings": {
          "mate": 18
        },
        "strong_flags": 0
      },
      "corner_versus_stock": {
        "plus": [
          3193,
          4331,
          4810,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.08544921875,
        "ci": [
          0.0244140625,
          0.15869140625
        ]
      },
      "table_versus_stock": {
        "plus": [
          3193,
          4331,
          4810,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.08544921875,
        "ci": [
          0.0244140625,
          0.15869140625
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    },
    "KBN": {
      "stock": {
        "mates": 9,
        "endings": {
          "mate": 9,
          "fifty": 7
        },
        "strong_flags": 0
      },
      "corner": {
        "mates": 16,
        "endings": {
          "mate": 16
        },
        "strong_flags": 0
      },
      "table": {
        "mates": 16,
        "endings": {
          "mate": 16
        },
        "strong_flags": 0
      },
      "corner_versus_stock": {
        "plus": [
          3193,
          4331,
          4810,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.08544921875,
        "ci": [
          0.0244140625,
          0.15869140625
        ]
      },
      "table_versus_stock": {
        "plus": [
          3193,
          4331,
          4810,
          6956,
          7569,
          7658,
          7727
        ],
        "minus": [],
        "pp": 0.08544921875,
        "ci": [
          0.0244140625,
          0.15869140625
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    },
    "KBB": {
      "stock": {
        "mates": 2,
        "endings": {
          "mate": 2
        },
        "strong_flags": 0
      },
      "corner": {
        "mates": 2,
        "endings": {
          "mate": 2
        },
        "strong_flags": 0
      },
      "table": {
        "mates": 2,
        "endings": {
          "mate": 2
        },
        "strong_flags": 0
      },
      "corner_versus_stock": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      },
      "table_versus_stock": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      },
      "corner_versus_table": {
        "plus": [],
        "minus": [],
        "pp": 0.0,
        "ci": [
          0.0,
          0.0
        ]
      }
    }
  },
  "timing": {
    "table": {
      "turns": 336,
      "wall_s": 2.058757908,
      "process_or_thread_cpu_s": 2.042234246,
      "CPU_to_wall": 0.9919739654984242,
      "turn_wall_ms": [
        2.0472,
        2.4914,
        5.8673,
        10.6022,
        12.3667
      ]
    },
    "stock": {
      "turns": 1820,
      "wall_s": 575.625087031,
      "process_or_thread_cpu_s": 571.11722966,
      "CPU_to_wall": 0.992168761451571,
      "turn_wall_ms": [
        0.1338,
        0.2955,
        237.1148,
        1236.9336,
        2495.2011
      ]
    },
    "corner": {
      "turns": 338,
      "wall_s": 146.301418778,
      "process_or_thread_cpu_s": 145.06145866,
      "CPU_to_wall": 0.9915246200046663,
      "turn_wall_ms": [
        0.222,
        0.3705,
        324.4203,
        1792.2105,
        2645.5969
      ]
    }
  },
  "checked": {
    "clocked_turns": 2494,
    "clocked_games": 54
  },
  "core_busy_quantiles": [
    0.9809,
    0.9821,
    0.9952,
    0.9994,
    1.0
  ],
  "fixed_sentinels": [
    916,
    5825,
    7727,
    7812
  ],
  "sha256": {
    "games.csv": "9eceee9064383b77eab4445c64de032c0281495f423f69d8fc571208e84f29a2",
    "times.csv": "a19ecdaf9cf52a031329e971b1340954013f17e67c5b08407ca15df8fbd1a7ec",
    "fixed.csv": "96c35f9e07476c9d4fe73c822286ab8cb45afbea174051e5e7a32e43231fbee2"
  }
}
~~~

fixed.csv

~~~text
g,class,strong_policy,mate,ending,postroot_plies,endfen,continuation
916,KBN,corner,1,mate,74,8/8/8/8/8/5bkn/8/7K w - - 74 157,e2d1 h5g4 d1c1 g4f4 c1d2 f4e4 d2c2 e4d4 c2b2 h6g4 b2c2 g4e3 c2b2 g8c4 b2b1 d4c3 b1a1 c4d5 a1b1 d5f7 b1a1 e3f5 a1b1 f5h6 b1a1 h6g4 a1b1 f7c4 b1a1 g4e3 a1b1 e3c2 b1c1 c4a2 c1d1 c2d4 d1e1 d4f5 e1e2 a2d5 e2d1 d5e4 d1c1 f5d4 c1d1 e4f5 d1c1 d4e2 c1d1 c3d3 d1e1 d3e3 e1d1 f5e4 d1e1 e4c2 e1f1 e2f4 f1e1 f4g2 e1f1 e3f3 f1g1 f3g3 g1f1 c2d3 f1g1 d3e2 g1h1 g2f4 h1g1 f4h3 g1h1 e2f3
916,KBN,stock,0,fifty,100,8/8/8/8/3K4/4n3/3k4/5b2 w - - 100 170,e2d1 g8c4 d1c2 h6f5 c2c3 c4f1 c3b2 h5g4 b2a1 g4f4 a1b1 f4e5 b1a1 f5e3 a1a2 e5d4 a2b3 f1c4 b3b2 c4b5 b2b3 b5c4 b3b2 c4e6 b2b1 d4c3 b1a1 e3g4 a1b1 e6b3 b1a1 g4f2 a1b1 b3e6 b1a1 e6c4 a1b1 f2g4 b1a1 g4e3 a1b1 c4e6 b1a1 e3c2 a1b1 e6c4 b1c1 c2e3 c1b1 c4f1 b1a1 c3c2 a1a2 f1c4 a2a1 c2b3 a1b1 c4b5 b1a1 e3c2 a1b1 b3c3 b1a2 b5c4 a2b1 c4d3 b1a2 c2e3 a2a1 d3c2 a1a2 c2d3 a2a1 d3c2 a1a2 c2b3 a2a1 e3g2 a1b1 b3c4 b1a1 c4d3 a1a2 d3f1 a2a1 c3d2 a1a2 g2h4 a2b3 h4g2 b3b4 g2e3 b4c5 e3g4 c5d4 f1g2 d4c5 g2f1 c5d4 g4e3
916,KBN,table,1,mate,56,8/8/2b5/8/8/8/5k2/5n1K w - - 56 148,e2d1 h5g4 d1c1 g4f3 c1d2 f3e4 d2c2 e4d4 c2b2 d4c4 b2a2 c4c3 a2a1 g8b3 a1b1 h6f5 b1a1 f5d4 a1b1 d4c2 b1c1 b3a2 c1d1 c2d4 d1e1 a2d5 e1d1 d5e4 d1c1 d4b3 c1d1 c3d3 d1e1 e4f3 e1f2 b3d4 f2f1 d3e3 f1e1 d4c2 e1f1 f3b7 f1g1 e3f3 g1f1 b7c8 f1g1 c2e3 g1h2 f3f2 h2h1 c8d7 h1h2 e3f1 h2h1 d7c6
1330,KBN,corner,1,mate,50,k7/8/NKB5/8/8/8/8/8 b - - 50 154,e8d7 c8b6 d7c6 b6a4 c6d6 f6f5 d6e7 f5e5 e7d7 c4d5 d7d8 e5e6 d8e8 a4c5 e8f8 e6f6 f8e8 d5c4 e8d8 f6e6 d8e8 c5d7 e8d8 c4d5 d8c7 d5h1 c7c8 e6d6 c8d8 h1e4 d8e8 e4g6 e8d8 d7c5 d8c8 g6d3 c8d8 d3b5 d8c8 b5d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
1330,KBN,stock,1,mate,46,k7/8/NK6/3B4/8/8/8/8 b - - 46 152,e8d7 c8b6 d7c6 b6a4 c6d6 f6f5 d6e7 f5e5 e7d7 c4d5 d7d8 e5d6 d8e8 d6e6 e8f8 e6f6 f8e8 a4c5 e8d8 f6e6 d8e8 c5d7 e8d8 e6d6 d8e8 d5c4 e8d8 c4f7 d8c8 d7c5 c8d8 c5b7 d8c8 d6c6 c8b8 f7c4 b8a8 c6b6 a8b8 c4e6 b8a8 b7c5 a8b8 c5a6 b8a8 e6d5
1330,KBN,table,1,mate,44,8/kBK5/2N5/8/8/8/8/8 b - - 44 151,e8d7 c4e6 d7c6 f6e5 c6c5 c8d6 c5c6 e6c4 c6c5 c4d5 c5b4 e5d4 b4a3 d4c3 a3a4 d5b3 a4a5 c3c4 a5b6 b3a4 b6c7 c4d5 c7d8 d5e6 d8c7 d6c4 c7c8 e6d6 c8d8 c4a5 d8c8 a4d7 c8b8 d6c6 b8a7 d7c8 a7b8 c6d7 b8a7 d7c7 a7a8 c8b7 a8a7 a5c6
1760,KBN,corner,1,mate,72,8/6b1/8/8/8/8/2k5/K1n5 w - - 72 116,c7d6 a7b8 d6d5 a6c5 d5d4 b8f4 d4d5 b5b6 d5c4 b6c6 c4b4 f4e5 b4c4 e5g7 c4b4 c5d3 b4b3 d3f2 b3c4 g7f6 c4b4 f6g7 b4c4 g7e5 c4b4 e5f4 b4c4 f4e3 c4b4 c6d5 b4a4 d5c4 a4a5 c4c5 a5a6 c5c6 a6a5 f2d3 a5a4 c6b6 a4b3 b6c5 b3c2 d3f2 c2c3 e3g5 c3b3 g5d2 b3c2 d2a5 c2b3 a5e1 b3a2 c5c4 a2b2 c4b4 b2c2 b4a3 c2c1 a3b3 c1b1 f2d3 b1a1 b3c2 a1a2 e1b4 a2a1 b4f8 a1a2 d3c1 a2a1 f8g7
1760,KBN,stock,0,fifty,100,8/8/8/8/8/3k4/1n6/4K1b1 w - - 100 130,c7d6 a7d4 d6d5 d4b2 d5e4 b5c4 e4e3 a6b4 e3e2 b2c1 e2e1 b4d3 e1f1 d3b2 f1e1 c4d4 e1f1 d4e3 f1g2 b2d3 g2g3 e3e4 g3g2 e4e3 g2g3 e3e4 g3g2 c1f4 g2g1 e4f3 g1f1 f4d2 f1g1 d2e3 g1h1 e3f4 h1g1 d3f2 g1f1 f2d3 f1g1 f4e3 g1h1 e3f2 h1h2 f2a7 h2h1 a7e3 h1h2 d3f4 h2h1 f4d3 h1h2 d3e5 h2h1 f3f2 h1h2 e5d7 h2h1 d7e5 h1h2 e3g5 h2h1 e5d3 h1h2 g5c1 h2h1 f2f1 h1h2 f1f2 h2h1 c1g5 h1h2 g5d2 h2h1 d3b2 h1h2 d2f4 h2h1 f2e2 h1g2 f4c1 g2g3 e2e3 g3g2 e3d4 g2f1 d4c4 f1e1 c4b4 e1e2 b4c5 e2e1 c1e3 e1e2 e3g1 e2d2 c5c4 d2e1 c4d3
1760,KBN,table,1,mate,54,8/8/8/8/3b4/8/2k5/K1n5 w - - 54 107,c7d6 a6c5 d6d5 a7b8 d5d4 b8f4 d4d5 b5b6 d5c4 b6c6 c4b4 f4c1 b4c3 c6d5 c3b4 c1e3 b4c3 e3d4 c3d2 d5e4 d2e2 c5b3 e2f1 e4f3 f1e1 d4b6 e1f1 b3d2 f1e1 f3e3 e1d1 e3d3 d1e1 b6a7 e1d1 a7f2 d1c1 d2c4 c1d1 c4b2 d1c1 d3c3 c1b1 b2d3 b1a1 c3b3 a1b1 f2c5 b1a1 b3c2 a1a2 d3c1 a2a1 c5d4
3141,KBN,corner,1,mate,28,7k/8/5BKN/8/8/8/8/8 b - - 28 92,g6f7 g3e2 f7g6 e2f4 g6f7 e5d5 f7e8 d5e6 e8f8 h4f6 f8e8 f4d5 e8f8 d5e7 f8e8 e7f5 e8f8 f6e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3141,KBN,stock,1,mate,22,7k/8/6KN/8/8/8/1B6/8 b - - 22 89,g6f7 e5f5 f7f8 f5e6 f8g7 e6e7 g7g6 e7f8 g6h6 f8f7 h6h7 g3f5 h7h8 h4e7 h8h7 e7a3 h7h8 f7g6 h8g8 f5h6 g8h8 a3b2
3141,KBN,table,1,mate,20,7k/8/5BKN/8/8/8/8/8 b - - 20 88,g6f7 h4f6 f7e8 e5e6 e8f8 g3f5 f8e8 f6g5 e8f8 g5e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3191,KBN,corner,1,mate,58,7k/8/6KN/8/8/8/1B6/8 b - - 58 106,f4f3 c5e7 f3e2 e7d6 e2f3 e4g3 f3f2 d4e4 f2g2 e4e3 g2h2 e3f3 h2g1 d6e5 g1h2 f3f2 h2h3 g3f5 h3g4 f5d6 g4h3 f2f3 h3h4 d6e4 h4h3 e4g5 h3h4 e5f6 h4h5 f6e7 h5h4 f3f4 h4h5 g5f7 h5g6 f7e5 g6h5 e5f7 h5g6 f7d6 g6h5 e7g5 h5g6 f4g4 g6h7 g4h5 h7g7 g5e7 g7h7 d6f5 h7g8 h5g6 g8h8 e7a3 h8g8 f5h6 g8h8 a3b2
3191,KBN,stock,0,threefold,100,8/8/8/4B3/8/5K2/8/3N2k1 b - - 100 127,f4f3 c5b4 f3e2 b4c3 e2f3 c3d2 f3e2 d2e3 e2f3 e4c5 f3g2 e3d2 g2f2 d4e4 f2g2 e4e3 g2g3 c5e6 g3g2 d2e1 g2f1 e1f2 f1g2 e6f4 g2f1 f2g3 f1g1 e3e2 g1h1 g3f2 h1h2 e2e3 h2h1 e3f3 h1h2 f2d4 h2h1 f4d3 h1h2 d3f2 h2g1 d4e3 g1h2 f2e4 h2h1 e3f2 h1h2 e4g3 h2h3 g3e2 h3h2 f2g3 h2h1 e2d4 h1g1 d4e6 g1h1 e6d4 h1g1 d4e6 g1h1 g3f4 h1g1 e6g5 g1h1 g5e6 h1g1 e6c5 g1h1 f4d2 h1g1 d2f4 g1h1 c5e4 h1g1 f4g5 g1h1 g5d2 h1g1 d2f4 g1h1 f4d6 h1g1 e4c3 g1h1 c3d5 h1g1 d5c3 g1h1 d6e5 h1g1 c3d1 g1f1 e5g3 f1g1 g3e5 g1f1 e5g3 f1g1 g3e5
3191,KBN,table,1,mate,50,8/8/8/8/8/NKB5/8/k7 b - - 50 102,f4f3 c5a3 f3e2 a3d6 e2f3 d4d3 f3g2 d3e2 g2g1 d6b8 g1g2 e4f2 g2g1 e2f3 g1f1 b8h2 f1e1 f2e4 e1d1 f3e3 d1c2 e4d2 c2b2 h2d6 b2c3 d6a3 c3c2 a3b4 c2d1 d2b3 d1c2 b3a5 c2d1 e3d3 d1c1 a5c4 c1d1 b4a5 d1c1 a5d2 c1b1 d3c3 b1a2 c3c2 a2a1 c2b3 a1b1 c4a3 b1a1 d2c3
3193,KBN,corner,1,mate,50,8/8/8/8/8/5NK1/6B1/6k1 b - - 50 88,f8g7 d6f5 g7g8 e6e7 g8h7 h5f7 h7h8 e7e6 h8h7 e6f6 h7h8 f5e7 h8h7 e7g6 h7h6 f7g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4d3 f3g3 d3e2 g3h4 g4f2 h4g3 f2e4 g3h4 f5f4 h4h3 f4g5 h3g2 g5g4 g2h2 e2f1 h2g1 f1h3 g1h1 g4g3 h1g1 e4d2 g1h1 h3g2 h1g1 d2f3
3193,KBN,stock,0,fifty,100,8/1N1B4/5k2/3K4/8/8/8/8 b - - 100 113,f8g7 e6e5 g7h6 h5g4 h6g6 g4c8 g6g7 c8e6 g7g6 e6g4 g6g7 e5f5 g7f8 f5f6 f8g8 g4c8 g8f8 d6b7 f8g8 c8f5 g8h8 f5g6 h8g8 g6h5 g8f8 h5g4 f8g8 b7d6 g8f8 d6f7 f8g8 g4e6 g8h7 e6f5 h7g8 f5g4 g8f8 f7d6 f8g8 g4d7 g8f8 d7c8 f8g8 c8e6 g8h7 e6c8 h7g8 c8d7 g8f8 d6b7 f8g8 d7f5 g8h8 f5d3 h8g8 d3e2 g8h7 e2g4 h7h8 f6f7 h8h7 g4f5 h7h8 f5e6 h8h7 e6f5 h7h8 f7f6 h8g8 b7d6 g8f8 d6b7 f8g8 b7d8 g8h8 d8c6 h8g8 c6a5 g8h8 f6e6 h8g7 a5b7 g7f8 e6d5 f8e7 f5c8 e7f6 d5d6 f6f7 d6e5 f7g7 e5d5 g7f6 c8e6 f6g5 d5e5 g5g6 e5d5 g6f6 e6d7
3193,KBN,table,1,mate,46,k7/8/NKB5/8/8/8/8/8 b - - 46 86,f8g7 d6f7 g7f8 e6f6 f8e8 f7e5 e8f8 h5g6 f8g8 e5f7 g8f8 g6h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3a6 c6c7 a6b5 c7d8 d7b6 d8c7 b6a4 c7d8 e6d6 d8c8 a4c5 c8d8 b5a4 d8c8 a4d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
3999,KBN,corner,1,mate,62,8/8/8/8/4B3/8/5K2/5N1k b - - 62 135,c7d7 d5e5 d7e7 g3f5 e7f7 g2d5 f7g6 d5g8 g6g5 f5d4 g5g6 d4e6 g6h5 g8f7 h5h6 e5f6 h6h7 e6f8 h7h6 f8g6 h6h7 f7c4 h7h6 c4g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4d3 f3g3 d3e4 g3h4 e4d5 h4g3 f5g5 g3h3 g5f4 h3h4 d5f7 h4h3 g4e3 h3h4 e3g2 h4h3 f4f3 h3h2 f7e6 h2g1 g2e3 g1h2 f3f2 h2h1 e6f5 h1h2 e3f1 h2h1 f5e4
3999,KBN,stock,0,fifty,100,8/1N6/3K2k1/8/8/7B/8/8 b - - 100 154,c7d7 g3f5 d7e8 d5e6 e8f8 g2d5 f8g8 e6f6 g8h7 d5e4 h7g8 e4d5 g8h7 d5f7 h7h8 f6e6 h8h7 e6f6 h7h8 f5d6 h8h7 f7d5 h7h8 d5e4 h8g8 d6f7 g8f8 e4f5 f8g8 f7d6 g8f8 d6b7 f8g8 f5e4 g8h8 b7d8 h8g8 e4f5 g8h8 f6g6 h8g8 f5e6 g8h8 e6f5 h8g8 d8e6 g8h8 e6g5 h8g8 f5e6 g8h8 g5f7 h8g8 g6f6 g8h7 e6f5 h7g8 f7d6 g8f8 f5c2 f8g8 c2e4 g8f8 e4f5 f8g8 d6b7 g8h8 b7d6 h8g8 d6b7 g8h8 f6g6 h8g8 f5e6 g8h8 g6f6 h8h7 e6g4 h7h8 g4f5 h8g8 f6e7 g8g7 f5c8 g7g6 e7e6 g6g5 e6e5 g5g6 e5e6 g6g5 e6e5 g5g6 c8f5 g6f7 f5h3 f7g7 e5e6 g7g6 e6d6
3999,KBN,table,1,mate,44,k1N5/2K5/2B5/8/8/8/8/8 b - - 44 126,c7d7 d5e5 d7e7 g2d5 e7f8 e5f6 f8e8 g3f5 e8d7 f6f7 d7c7 f7e6 c7b6 f5d4 b6a5 d4c2 a5b6 e6d6 b6b5 d5b3 b5a5 d6c5 a5a6 b3a4 a6a5 a4c6 a5a6 c2a3 a6a5 a3c4 a5a6 c5d6 a6a7 d6c7 a7a6 c6a4 a6a7 a4b5 a7a8 c4b6 a8a7 b6c8 a7a8 b5c6
4331,KBN,corner,1,mate,44,5n1K/5k2/5b2/8/8/8/8/8 w - - 44 85,g2h2 e4f3 h2h1 e2g3 h1h2 c5a7 h2h3 a7g1 h3h4 g3e4 h4h5 f3f4 h5g6 e4g5 g6g7 g1c5 g7f6 c5b4 f6g6 f4g4 g6f6 b4d6 f6g6 d6e7 g6h6 g4f5 h6g7 e7c5 g7h6 g5e6 h6h5 c5e7 h5h6 e7g5 h6h7 f5f6 h7g8 f6g6 g8h8 g6f7 h8h7 e6f8 h7h8 g5f6
4331,KBN,stock,0,fifty,100,8/8/8/8/8/3k4/5nK1/2b5 w - - 100 113,g2h2 e4f3 h2h1 e2f4 h1h2 c5e3 h2h1 f3e4 h1h2 e4f3 h2h1 f4d3 h1h2 f3e4 h2g2 e3c1 g2g3 c1f4 g3g2 f4c1 g2g3 c1f4 g3g2 f4d2 g2g3 d2c1 g3g2 e4e3 g2g3 e3e4 g3g2 c1f4 g2g1 e4f3 g1f1 f4h6 f1g1 d3b4 g1h1 h6f4 h1g1 b4c2 g1f1 f4d6 f1g1 c2e3 g1h1 d6f4 h1g1 f4g3 g1h1 e3g4 h1g1 g3e5 g1h1 g4e3 h1g1 e5g3 g1h1 e3g2 h1g1 g3f2 g1h1 f2c5 h1h2 c5d4 h2h1 d4e5 h1g1 g2e1 g1f1 e1g2 f1g1 e5d6 g1f1 d6f8 f1g1 f8d6 g1f1 g2e3 f1g1 e3d1 g1f1 d1b2 f1g1 d6f4 g1h1 f4c1 h1h2 f3e3 h2g2 b2d1 g2g3 d1f2 g3g2 f2g4 g2g3 g4f2 g3g2 e3d3
4331,KBN,table,1,mate,42,7K/8/6kn/8/8/8/1b6/8 w - - 42 84,g2h2 e4f3 h2h1 c5a7 h1h2 e2g3 h2h3 a7g1 h3h4 g3e4 h4h5 f3f4 h5g6 e4g5 g6g7 g1c5 g7f6 c5a3 f6g6 a3e7 g6h5 g5e4 h5g6 e4d6 g6h5 e7g5 h5g6 f4g4 g6h7 g4h5 h7g7 g5e7 g7h7 d6f5 h7g8 h5g6 g8h8 e7a3 h8g8 f5h6 g8h8 a3b2
4428,KBN,corner,1,mate,50,6k1/4N1B1/6K1/8/8/8/8/8 b - - 50 101,b8a8 f3d2 a8b8 d2f3 b8a8 f3d4 a8b8 d4b5 b8a8 b5c7 a8b8 c5f2 b8c8 f2a7 c8d8 c7d5 d8e8 c6d6 e8f7 d5e7 f7g7 a7e3 g7f6 e3d2 f6f7 d6d7 f7f6 d2f4 f6f7 f4g5 f7f8 d7e6 f8g7 g5e3 g7f8 e7f5 f8e8 f5d6 e8f8 e6f6 f8g8 e3h6 g8h7 d6f5 h7g8 f6g6 g8h8 h6g7 h8g8 f5e7
4428,KBN,stock,0,fifty,100,8/k5B1/2KN4/8/8/8/8/8 b - - 100 126,b8a8 f3e5 a8b8 e5f7 b8a8 c5g1 a8b8 g1e3 b8a8 e3c5 a8b8 c5d6 b8a8 d6c5 a8b8 c5e3 b8a8 f7h8 a8b8 e3d4 b8a8 h8f7 a8b8 f7d6 b8a8 c6b6 a8b8 d6f7 b8a8 b6c6 a8b8 d4f2 b8a8 f2g3 a8a7 g3c7 a7a6 f7h8 a6a7 c7a5 a7a6 a5e1 a6a7 e1b4 a7a8 b4c5 a8b8 h8f7 b8a8 f7d6 a8b8 d6b5 b8a8 b5c7 a8b8 c7e8 b8a8 e8d6 a8b8 c6d7 b8a8 c5b6 a8b8 d6e4 b8b7 b6c7 b7a7 e4c5 a7a8 c7g3 a8a7 d7c6 a7a8 c5e6 a8a7 e6c7 a7b8 g3d6 b8a7 d6c5 a7b8 c7e8 b8a8 e8g7 a8b8 c5f8 b8a7 c6c7 a7a6 c7d6 a6b5 d6d5 b5a6 d5c6 a6a7 g7e8 a7b8 e8d6 b8a7 f8g7
4428,KBN,table,1,mate,44,5N1k/5K2/8/8/8/2B5/8/8 b - - 44 98,b8a8 c5b6 a8b8 f3d4 b8a8 d4b5 a8b8 b5c7 b8c8 b6a7 c8d8 c7d5 d8e8 a7d4 e8d8 d4e5 d8c8 d5b6 c8d8 c6d6 d8e8 e5f6 e8f7 b6d5 f7f8 d6e6 f8e8 d5c7 e8f8 f6b2 f8g8 e6f6 g8f8 b2c1 f8g8 c7e6 g8h7 f6f7 h7h8 c1d2 h8h7 e6f8 h7h8 d2c3
4810,KBN,corner,1,mate,48,8/8/8/8/4B3/6KN/8/7k b - - 48 163,g7h7 f5f6 h7h8 e5g6 h8h7 c4e6 h7h6 e6g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4d3 f3g3 d3e2 g3h4 f5g6 h4h3 g6h5 h3g3 h5g5 g3h3 g4f2 h3g2 f2d3 g2h3 e2g4 h3g3 g5h5 g3h2 h5h4 h2g2 g4e2 g2h1 h4g3 h1g1 d3f4 g1h1 e2d3 h1g1 f4h3 g1h1 d3e4
4810,KBN,stock,0,fifty,100,2B5/1N4k1/8/5K2/8/8/8/8 b - - 100 189,g7h7 f5f6 h7h8 e5f7 h8h7 f7d6 h7h8 d6b7 h8h7 c4e6 h7h8 e6g4 h8h7 g4c8 h7h8 c8f5 h8g8 f6e5 g8f7 f5c8 f7g7 e5e4 g7f6 e4f4 f6e7 f4g5 e7f7 c8g4 f7g7 b7d8 g7f8 g5f6 f8g8 f6g6 g8f8 g6f6 f8g8 d8e6 g8h7 f6f5 h7g8 f5g6 g8h8 e6d8 h8g8 d8b7 g8h8 b7d8 h8g8 g4f5 g8f8 g6f6 f8g8 f6g6 g8f8 g6f6 f8g8 d8b7 g8h8 f6g6 h8g8 f5g4 g8h8 g4f5 h8g8 g6f6 g8h8 f6g5 h8g7 f5h3 g7f7 h3c8 f7g7 g5f5 g7f7 f5g5 f7g7 b7d8 g7f8 g5f6 f8g8 c8f5 g8h8 d8b7 h8g8 f5c8 g8h7 f6e6 h7g6 e6e5 g6g7 c8d7 g7f7 e5f5 f7g7 f5g5 g7f7 g5f5 f7g7 d7c8
4810,KBN,table,1,mate,42,8/8/8/8/8/5B2/5K2/5N1k b - - 42 160,g7h7 e5g6 h7g7 f5g5 g7h7 g5f6 h7h6 c4g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4a6 f3g3 a6e2 g3h4 g4e3 h4g3 e3d1 g3h4 f5f4 h4h3 d1e3 h3h4 e2d1 h4h3 d1g4 h3h2 f4f3 h2g1 f3g3 g1h1 g3f2 h1h2 e3f1 h2h1 g4f3
5825,KBB,corner,1,mate,28,8/8/8/8/4B3/1K6/1B6/1k6 b - - 28 101,b3c2 b5c4 c2d2 e7c5 d2e2 c4c3 e2f1 c3d3 f1e1 c6g2 e1d1 c5b4 d1c1 g2d5 c1d1 d5f3 d1c1 b4a3 c1b1 f3d5 b1a1 d3c3 a1b1 c3b3 b1a1 a3b2 a1b1 d5e4
5825,KBB,stock,1,mate,28,8/8/8/8/4B3/1K6/1B6/1k6 b - - 28 101,b3c2 b5c4 c2d2 e7c5 d2e2 c4c3 e2f1 c3d3 f1e1 c6g2 e1d1 c5b4 d1c1 g2d5 c1d1 d5f3 d1c1 b4a3 c1b1 f3d5 b1a1 d3c3 a1b1 c3b3 b1a1 a3b2 a1b1 d5e4
5825,KBB,table,1,mate,26,8/8/8/8/8/1K1B4/1B6/1k6 b - - 26 100,b3c2 b5b4 c2d2 e7c5 d2d3 c6g2 d3c2 g2f1 c2d2 b4b3 d2e1 f1a6 e1d2 c5f2 d2c1 f2e1 c1d1 e1b4 d1c1 a6e2 c1b1 b4a3 b1a1 a3b2 a1b1 e2d3
6710,KBN,corner,1,mate,78,8/8/8/3b4/8/8/5k2/5n1K w - - 78 98,d8e7 c4e5 e7e6 c5d4 e6e7 d4d5 e7f6 b5c4 f6e7 c4d3 e7f6 d5d6 f6g7 d6e7 g7g8 d3c4 g8g7 e7e6 g7g8 e6f6 g8h8 f6f7 h8h7 e5g4 h7h8 g4e3 h8h7 e3g4 h7h8 g4e5 h8h7 c4d3 h7h8 f7f6 h8g8 e5g6 g8h7 d3c4 h7h6 c4d3 h6h7 d3c4 h7h6 c4g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4b5 f3g3 b5c6 g3h3 f5f4 h3h4 c6e8 h4h3 g4e3 h3h4 e3g2 h4h3 f4f3 h3h2 e8d7 h2g1 g2e3 g1h2 f3f2 h2h1 d7e6 h1h2 e3f1 h2h1 e6d5
6710,KBN,stock,0,fifty,100,5K2/5n2/5k2/8/8/8/6b1/8 w - - 100 109,d8e7 c4a5 e7e6 a5b3 e6e5 c5c4 e5e4 c4c3 e4e5 c3b4 e5d5 b3a5 d5d4 a5b3 d4d5 b5c4 d5d6 b3a5 d6e5 b4c5 e5e4 c5b4 e4d4 a5b3 d4e4 b4a3 e4e3 c4f1 e3e4 f1c4 e4e3 c4g8 e3d3 g8h7 d3e3 a3b4 e3f3 h7f5 f3e3 b4c5 e3f4 f5g6 f4e5 g6d3 e5e6 d3c4 e6e5 b3a5 e5e4 c4d5 e4e3 a5c4 e3f4 c5d6 f4f5 d6e7 f5g6 e7e6 g6g7 d5e4 g7f8 c4d6 f8g7 e6f5 g7g8 f5f6 g8f8 e4a8 f8g8 a8c6 g8f8 d6f5 f8g8 f6e7 g8h7 e7f7 h7h8 f5d6 h8h7 c6g2 h7h8 g2f3 h8h7 f7f6 h7g8 f3d5 g8h7 d6f7 h7g8 f7g5 g8h8 d5c6 h8g8 g5f7 g8f8 f7g5 f8g8 g5f7 g8f8 c6g2
6710,KBN,table,1,mate,52,K7/8/nkb5/8/8/8/8/8 w - - 52 85,d8e7 c4d6 e7e6 b5d3 e6e5 d3f5 e5f6 c5d4 f6g7 d4e5 g7g8 e5f6 g8f8 d6f7 f8g8 f5b1 g8f8 b1h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3a6 c6c7 a6b5 c7d8 d7b6 d8c7 b6a4 c7d8 e6d6 d8c8 a4c5 c8d8 b5a4 d8c8 a4d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
6950,KBN,corner,1,mate,58,8/8/8/8/8/2n5/Kbk5/8 w - - 58 92,d1d2 d4b5 d2d3 c7b6 d3c4 b5c7 c4d3 b6e3 d3c2 f3e2 c2c3 e3b6 c3c4 b6e3 c4c3 e3b6 c3c4 e2d2 c4b3 d2d3 b3a2 b6e3 a2a3 d3c4 a3b2 c7d5 b2c2 d5c3 c2b2 c4d3 b2a3 c3d5 a3a4 d3c4 a4a5 d5c7 a5a4 e3d2 a4a3 c7a6 a3b2 a6b4 b2a3 b4d3 a3a4 d3c5 a4a3 d2c1 a3a2 c4c3 a2a1 c3c2 a1a2 c5e4 a2a1 c1b2 a1a2 e4c3
6950,KBN,stock,0,fifty,100,8/8/8/8/8/3k2K1/1n6/2b5 w - - 100 113,d1d2 d4e2 d2d3 e2g3 d3c4 c7f4 c4d4 g3h1 d4d5 f3g2 d5e4 f4h2 e4d3 h2g1 d3c4 g1a7 c4b5 a7e3 b5c4 h1g3 c4d5 e3f4 d5c4 g2f2 c4d3 f4e3 d3c4 g3f5 c4d5 f5e7 d5d6 e7c8 d6c6 c8b6 c6b5 f2e2 b5a5 e2d2 a5a6 d2d3 a6b5 d3c3 b5c6 c3c4 c6d6 e3c5 d6e5 c4d3 e5f4 c5a3 f4f3 a3c1 f3f2 b6a4 f2f3 a4b6 f3f2 d3e4 f2g2 c1f4 g2f1 e4f3 f1g1 b6a4 g1h1 a4b6 h1g1 b6c4 g1h1 c4e3 h1g1 e3c4 g1h1 f4g3 h1g1 c4b2 g1h1 g3f4 h1g1 f4d2 g1h1 f3e3 h1g2 e3f4 g2f2 f4e5 f2e2 d2c1 e2f3 e5d4 f3f2 d4c4 f2e1 c4d4 e1f1 d4e3 f1g2 e3e2 g2g3 e2d3
6950,KBN,table,1,mate,40,8/8/8/8/8/2b5/2k5/K1n5 w - - 40 83,d1d2 c7b6 d2c3 d4b5 c3c4 b5c7 c4d3 b6e3 d3c2 f3e2 c2c3 e3b6 c3c4 e2d2 c4b3 d2d3 b3a2 b6a5 a2a3 a5c3 a3a4 d3c4 a4a3 c7a6 a3a2 c4d3 a2a3 a6c5 a3a2 d3c2 a2a3 c3a5 a3a2 a5b4 a2a1 c5b3 a1a2 b3c1 a2a1 b4c3
6956,KBN,corner,1,mate,36,8/8/8/8/8/1k6/1b1n4/1K6 w - - 36 85,e1f1 e4f3 f1e1 d4b3 e1d1 b3d2 d1c1 f3e2 c1b2 e3c5 b2c3 e2e3 c3c2 c5b4 c2d1 d2c4 d1c2 c4a5 c2d1 e3d3 d1c1 a5c4 c1d1 c4e3 d1c1 b4a3 c1b1 d3c3 b1a1 c3b3 a1b1 e3c4 b1a1 a3b2 a1b1 c4d2
6956,KBN,stock,0,fifty,100,8/8/8/8/2n5/8/2k5/2b2K2 w - - 100 117,e1f1 e4f3 f1e1 e3f4 e1d1 f4h6 d1e1 h6e3 e1d1 e3f4 d1e1 d4c2 e1f1 f4g5 f1g1 g5f4 g1f1 c2d4 f1g1 d4e2 g1h1 e2c3 h1g1 c3a2 g1h1 a2c3 h1g1 c3d1 g1h1 d1f2 h1g1 f2d3 g1f1 f4h6 f1g1 d3c1 g1h1 c1e2 h1h2 h6g5 h2h1 g5d8 h1h2 d8c7 h2h1 e2f4 h1g1 f4d3 g1f1 c7g3 f1g1 g3f4 g1f1 d3b2 f1g1 f4c7 g1h1 b2d1 h1g1 c7d6 g1f1 d6f4 f1g1 d1e3 g1h1 f4b8 h1g1 b8g3 g1h1 e3c2 h1g1 c2e3 g1h1 e3d1 h1g1 g3f4 g1h1 d1b2 h1g1 f3e4 g1f2 e4d4 f2e2 f4h6 e2f1 d4e3 f1g1 e3d3 g1f2 h6e3 f2f3 e3c1 f3f2 c1f4 f2f3 f4c1 f3f2 b2c4 f2f1 d3c2
6956,KBN,table,1,mate,34,8/8/8/8/8/1kn5/1b6/K7 w - - 34 84,e1f1 e4f3 f1e1 d4b3 e1d1 b3d2 d1c1 f3e2 c1b2 e2d3 b2a3 d3c4 a3b2 d2e4 b2c2 e4f2 c2b2 e3d2 b2a3 d2c3 a3a2 c4b4 a2b1 b4b3 b1c1 c3b4 c1b1 b4a3 b1a1 f2d1 a1b1 d1c3 b1a1 a3b2
7569,KBN,corner,1,mate,92,8/8/8/8/8/6kn/6b1/6K1 w - - 92 108,f4f5 h5g3 f5f4 g3f1 f4e4 f1d2 e4d4 d2b1 d4e5 d1b3 e5f5 b3c2 f5e5 f7e7 e5d5 e7f6 d5d4 c2b3 d4e4 f6e6 e4d4 e6f5 d4e3 f5e5 e3d3 e5d5 d3e3 b3c2 e3f3 b1d2 f3e2 d2b1 e2f3 d5e5 f3e3 c2d1 e3d3 d1b3 d3e3 b3c2 e3f3 b1d2 f3g4 e5e6 g4f4 d2c4 f4g4 e6f6 g4f4 c2f5 f4f3 f6g5 f3e2 f5c2 e2e1 g5f4 e1e2 f4e4 e2f2 c4d2 f2e1 d2f3 e1e2 e4f4 e2f1 f4e3 f1g2 c2d3 g2g3 d3f5 g3g2 f3h4 g2g3 h4g6 g3g2 f5g4 g2f1 g6f4 f1e1 f4d3 e1f1 g4h3 f1g1 e3f3 g1h1 f3g3 h1g1 d3f4 g1h1 h3g2 h1g1 f4h3
7569,KBN,stock,0,fifty,100,8/8/8/4k3/8/8/K5n1/5b2 w - - 100 112,f4f5 d1f3 f5e5 f7g6 e5d4 f3g4 d4e4 g6f6 e4d4 h5f4 d4e4 f4g2 e4d4 g4f3 d4c3 f6e6 c3d4 e6d6 d4c4 d6e5 c4c3 f3e2 c3b3 e5e4 b3c2 e2f1 c2b3 e4e5 b3a2 f1d3 a2a1 e5e4 a1a2 e4e5 a2a1 e5e4 a1a2 e4d5 a2b3 d5d4 b3b2 d4c4 b2a1 c4c3 a1a2 d3c4 a2b1 c4d3 b1a1 d3f5 a1a2 f5e6 a2b1 e6f5 b1a1 g2e1 a1a2 e1g2 a2a1 f5c2 a1a2 c2d3 a2a1 d3e4 a1a2 e4c2 a2a1 c2d3 a1a2 g2f4 a2a1 c3d4 a1b2 f4g2 b2b3 d4d5 b3c3 d3f1 c3b3 d5e5 b3a2 e5e4 a2b3 f1e2 b3c2 e2b5 c2c3 b5a6 c3b2 e4e3 b2c2 a6f1 c2b3 e3d4 b3b2 f1b5 b2a1 d4e5 a1a2 b5f1
7569,KBN,table,1,mate,60,8/8/2b5/8/8/8/5k2/5n1K w - - 60 92,f4f5 d1a4 f5e4 f7e6 e4d3 e6d5 d3c3 a4b5 c3b2 b5c4 b2a1 d5d4 a1b2 h5f4 b2b1 d4c3 b1a1 c4b3 a1b1 f4d3 b1a1 d3b4 a1b1 b4c2 b1c1 b3a2 c1d1 c2d4 d1e1 a2d5 e1d1 d5e4 d1c1 d4b3 c1d1 c3d3 d1e1 e4f3 e1f2 b3d4 f2f1 d3e3 f1e1 d4c2 e1f1 f3b7 f1g1 e3f3 g1f1 b7c8 f1g1 c2e3 g1h2 f3f2 h2h1 c8d7 h1h2 e3f1 h2h1 d7c6
7658,KBN,corner,1,mate,48,8/8/2B5/8/8/6KN/8/7k b - - 48 76,h5h6 e3f5 h6h7 f4g5 h7h8 g5f6 h8h7 f5e7 h7h8 e7g6 h8h7 f7a2 h7h6 a2g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4d3 f3g3 d3e2 g3h4 g4f2 h4g3 f2d1 g3h4 f5f4 h4h3 d1e3 h3h4 e3g2 h4h3 f4f3 h3h2 g2f4 h2g1 f3g3 g1h1 e2b5 h1g1 f4h3 g1h1 b5c6
7658,KBN,stock,0,material,99,8/1NK5/8/8/6k1/8/8/8 w - - 0 102,h5h6 e3f5 h6h7 f4e5 h7h8 e5f6 h8h7 f7e6 h7h8 e6d5 h8h7 d5e6 h7h8 e6f7 h8h7 f5d6 h7h8 f7e6 h8h7 e6d5 h7h8 d5e6 h8h7 e6f5 h7h8 d6f7 h8g8 f5c8 g8f8 f7d6 f8g8 c8f5 g8f8 d6b7 f8g8 f5b1 g8h8 b7d8 h8g8 b1e4 g8f8 d8e6 f8g8 f6e7 g8h8 e7f6 h8g8 e4b1 g8h8 e6c7 h8g8 c7d5 g8h8 b1f5 h8g8 d5e7 g8h8 e7d5 h8g8 f5g6 g8h8 d5c7 h8g8 c7e6 g8h8 g6f5 h8g8 f5g6 g8h8 g6f5 h8g8 f5e4 g8h8 e6d8 h8g8 e4f5 g8h8 f5e4 h8g8 e4f5 g8h8 d8b7 h8g8 f5c8 g8h7 f6e6 h7g6 e6e5 g6g7 e5d5 g7f6 d5d6 f6f7 c8f5 f7f6 f5g4 f6g5 d6c7 g5g4
7658,KBN,table,1,mate,48,8/8/8/8/8/5B2/5K2/5N1k b - - 48 76,h5h6 e3f5 h6h7 f4e4 h7h8 e4e5 h8h7 e5f6 h7h8 f5e7 h8h7 e7g6 h7h6 f7g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4a6 f3g3 a6e2 g3h4 g4e3 h4g3 e3d1 g3h4 f5f4 h4h3 d1e3 h3h4 e2d1 h4h3 d1g4 h3h2 f4f3 h2g1 f3g3 g1h1 g3f2 h1h2 e3f1 h2h1 g4f3
7727,KBN,corner,1,mate,60,5N1k/5K2/8/8/3B4/8/8/8 b - - 60 156,e1f1 b3c1 f1f2 d3e4 f2g2 e4e3 g2g1 c1e2 g1f1 b4f8 f1g2 f8c5 g2h2 e3f2 h2h1 e2g3 h1h2 f2f3 h2h3 c5g1 h3h4 g3e4 h4h5 f3f4 h5g6 e4g5 g6g7 g1c5 g7f6 c5d6 f6g6 d6e5 g6h5 e5c3 h5g6 f4g4 g6h6 g4f5 h6h5 c3d4 h5h4 d4f2 h4h5 g5e6 h5h6 f2e3 h6h5 e6f4 h5h6 f5f6 h6h7 f4e6 h7g8 f6g6 g8h8 g6f7 h8h7 e6f8 h7h8 e3d4
7727,KBN,stock,0,fifty,100,8/8/8/8/3B4/5K2/4N2k/8 b - - 100 176,e1f1 b3d4 f1f2 b4d6 f2f1 d3e3 f1g2 e3f4 g2f2 d6c5 f2f1 f4f3 f1g1 d4f5 g1h1 f5d4 h1g1 f3g3 g1f1 c5b4 f1g1 g3f3 g1h1 d4e2 h1h2 b4d6 h2h1 d6e7 h1h2 e2d4 h2g1 e7d6 g1h1 d6a3 h1g1 a3c5 g1h2 d4f5 h2h1 f5g3 h1h2 c5b4 h2g1 b4d6 g1h2 d6e7 h2g1 g3f5 g1h2 e7b4 h2g1 b4d6 g1h1 f5d4 h1g1 d6b4 g1h1 d4f5 h1h2 b4e7 h2g1 e7d6 g1h1 f3g3 h1g1 d6b4 g1h1 f5d4 h1g1 b4a3 g1f1 g3f3 f1g1 a3c5 g1h2 d4e2 h2h1 c5e7 h1h2 e7a3 h2h1 a3c5 h1h2 c5b6 h2h1 e2f4 h1h2 b6f2 h2h1 f2c5 h1h2 c5a7 h2h1 a7b6 h1h2 b6f2 h2h1 f4e2 h1h2 f2d4
7727,KBN,table,1,mate,50,7k/8/6KN/8/8/8/1B6/8 b - - 50 151,e1f1 b3c5 f1f2 c5e4 f2f1 b4c5 f1g2 d3e2 g2h2 e2f2 h2h1 e4g3 h1h2 f2f3 h2h3 c5g1 h3h4 g3e4 h4h5 f3f4 h5g6 e4g5 g6g7 g1c5 g7f6 c5a3 f6g6 a3e7 g6h5 g5e4 h5g6 e4d6 g6h5 e7g5 h5g6 f4g4 g6h7 g4h5 h7g7 g5e7 g7h7 d6f5 h7g8 h5g6 g8h8 e7a3 h8g8 f5h6 g8h8 a3b2
7812,KBB,corner,1,mate,16,7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g5f6 e8d8 g4h3 d8e8 d6c7 e8f8 h3d7 f8g8 f6g6 g8f8 c7d6 f8g8 d7e6 g8h8 d6e5
7812,KBB,stock,1,mate,16,7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g5f6 e8d8 g4h3 d8e8 d6c7 e8f8 h3d7 f8g8 f6g6 g8f8 c7d6 f8g8 d7e6 g8h8 d6e5
7812,KBB,table,1,mate,16,7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g4e6 e8d8 g5f6 d8e8 d6c7 e8f8 e6d7 f8g8 f6g6 g8f8 c7d6 f8g8 d7e6 g8h8 d6e5
~~~

games.csv

~~~text
g,class,clock_start_s,strong_policy,core,strong_white,actual_mate,reason,flagged_color,attempts,start_monotonic_ns,stop_monotonic_ns,active_actor_cpu_ns,charged_wall_ns,per_core_ticks,endfen,moves
916,KBN,10,corner,0,0,1,mate,,48,30186715942979,30205946152248,18697867259,19205992046,"1824,0,3,37,0,0,0,72",K1n5/2k5/2b5/8/8/8/8/8 w - - 48 144,e2d3 h5g4 d3d4 g4f4 d4c5 f4e5 c5c6 g8d5 c6c7 d5e6 c7b6 e6d5 b6c7 d5e6 c7b6 h6f7 b6b5 e5d4 b5b6 d4c4 b6c6 e6g4 c6b6 g4d7 b6c7 d7e8 c7b6 c4b4 b6a6 b4c5 a6b7 c5b5 b7c7 e8c6 c7c8 b5b6 c8b8 c6d7 b8a8 f7d6 a8b8 d7b5 b8a8 b6c7 a8a7 d6c8 a7a8 b5c6
916,KBN,10,stock,0,0,1,mate,,46,30166997058801,30186561113725,19424404938,19542456016,"1886,0,1,9,0,0,0,69",K7/8/nk6/8/8/8/6b1/8 w - - 46 143,e2d3 g8e6 d3e4 h6f7 e4d4 h5g4 d4c5 e6d7 c5c4 d7c6 c4d4 g4f4 d4c5 c6g2 c5b4 f7g5 b4b5 g5e6 b5a5 f4e4 a5b5 e4d4 b5b6 d4c4 b6a5 g2c6 a5b6 c6d7 b6a5 c4c5 a5a6 e6d8 a6a5 d8b7 a5a6 c5c6 a6a7 b7c5 a7b8 c6b6 b8a8 d7h3 a8b8 c5a6 b8a8 h3g2
916,KBN,10,table,0,0,1,mate,,50,30206018290853,30213797440130,7624588814,7758909690,"751,0,2,9,0,0,0,23",8/8/8/8/8/5b2/5k2/5n1K w - - 50 145,e2d3 h5g4 d3e4 h6f5 e4e5 g8a2 e5e4 a2c4 e4e5 g4g5 e5e4 g5f6 e4f3 f6e5 f3g4 c4d3 g4h5 f5e3 h5g5 d3b1 g5h6 e5f6 h6h5 b1c2 h5h4 c2d1 h4g3 f6e5 g3f2 e3c2 f2g3 e5e4 g3h4 e4f4 h4h3 c2e3 h3h4 d1e2 h4h3 e2g4 h3h2 f4f3 h2g1 f3g3 g1h1 g3f2 h1h2 e3f1 h2h1 g4f3
1330,KBN,10,corner,2,1,1,mate,,50,30193356652285,30212660481951,18837844065,19279247420,"1839,0,1,37,0,0,0,64",1k6/1B1N4/1K6/8/8/8/8/8 b - - 50 154,e8d7 c8b6 d7c6 b6a4 c6d6 f6f5 d6e7 f5g6 e7d7 g6f7 d7d6 f7f6 d6d7 f6e5 d7e8 e5e6 e8f8 e6f6 f8e8 a4b6 e8d8 f6e6 d8e8 b6d7 e8d8 c4b5 d8e8 b5e2 e8d8 e6d6 d8e8 e2h5 e8d8 d7c5 d8c8 h5e2 c8d8 c5e6 d8c8 e2a6 c8b8 d6c6 b8a7 e6c5 a7b8 c6b6 b8a8 a6b7 a8b8 c5d7
1330,KBN,10,stock,2,1,1,mate,,52,30167311821102,30187489214741,20018993235,20151720263,"1950,0,2,12,0,0,0,65",k7/8/NKB5/8/8/8/8/8 b - - 52 155,e8d7 c8b6 d7c6 b6a4 c6d6 f6f5 d6e7 f5e5 e7d7 c4d5 d7e7 a4b6 e7f8 e5f6 f8e8 f6e5 e8e7 d5e6 e7f8 e5f6 f8e8 e6d5 e8d8 f6e6 d8e8 b6d7 e8d8 d5c6 d8c7 c6b5 c7d8 d7b6 d8c7 b6a4 c7d8 e6d6 d8c8 a4c5 c8d8 b5a4 d8c8 a4d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
1330,KBN,10,table,2,1,1,mate,,32,30187546986202,30193125579840,5531858123,5567365186,"538,0,0,2,0,0,0,20",k7/1B6/1KN5/8/8/8/8/8 b - - 32 145,e8d7 c4e6 d7c6 f6e5 c6b5 e5d4 b5c6 d4c4 c6c7 c4d5 c7d8 c8b6 d8c7 d5c5 c7b7 b6d5 b7a6 c5b4 a6a7 e6c8 a7b8 c8a6 b8a7 b4a5 a7b8 a5b6 b8a8 d5b4 a8b8 b4c6 b8a8 a6b7
1760,KBN,10,corner,0,0,1,mate,,38,30213939216583,30229542493606,15515223125,15587886020,"1505,0,1,5,0,0,1,53",5n1K/5k2/8/4b3/8/8/8/8 w - - 38 99,c7d6 a7b8 d6e6 b5c6 e6e7 a6c5 e7d8 b8c7 d8c8 c7d6 c8d8 c5e6 d8e8 e6f4 e8f7 d6e5 f7e7 c6c7 e7f7 c7d7 f7f8 e5f6 f8f7 f6e7 f7g8 d7e8 g8g7 e7g5 g7g8 f4e6 g8h7 e8f7 h7h8 g5f4 h8h7 e6f8 h7h8 f4e5
1760,KBN,10,stock,0,0,1,mate,,44,30229642250876,30247701110396,17936791888,18040464653,"1752,0,1,8,0,0,1,51",7K/8/5bkn/8/8/8/8/8 w - - 44 102,c7d6 a7d4 d6d5 d4b2 d5d6 a6b4 d6c7 b4a6 c7d6 b2a3 d6e5 b5c4 e5e6 c4d4 e6f6 d4d5 f6f7 d5e5 f7g6 a3e7 g6f7 e7f6 f7e8 e5e6 e8f8 a6c7 f8g8 e6f5 g8f7 f5g5 f7f8 g5g6 f8g8 c7e8 g8f8 e8d6 f8g8 f6e7 g8h8 d6f7 h8g8 f7h6 g8h8 e7f6
1760,KBN,10,table,0,0,1,mate,,44,30247773019469,30253409093253,5563060639,5619447003,"547,0,1,5,0,0,1,16",8/8/8/8/8/2n5/Kbk5/8 w - - 44 102,c7d6 a6c5 d6e5 a7b8 e5d4 b8f4 d4d5 b5b6 d5c4 b6c6 c4d4 c6d6 d4c4 f4e3 c4b4 d6d5 b4c3 e3d4 c3d2 d5e4 d2c2 e4e3 c2d1 d4c3 d1c2 c3a5 c2c1 e3d3 c1d1 c5a4 d1c1 a5d2 c1b1 d3c3 b1a2 d2c1 a2b1 c3d2 b1a2 d2c2 a2a1 c1b2 a1a2 a4c3
3141,KBN,10,corner,2,1,1,mate,,20,30212787339905,30220044332534,7196530973,7249640031,"705,0,0,4,0,0,0,20",7k/8/5BKN/8/8/8/8/8 b - - 20 88,g6f7 h4f6 f7e8 e5e6 e8f8 g3f5 f8e8 f6g5 e8f8 g5e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3141,KBN,10,stock,2,1,1,mate,,22,30222328876928,30229098958260,6693687479,6761991111,"655,0,0,6,0,0,0,21",7k/8/5BKN/8/8/8/8/8 b - - 22 89,g6f7 e5f5 f7f8 f5e6 f8g7 h4f6 g7g6 e6e7 g6h6 e7f7 h6h7 f6h4 h7h6 h4e7 h6h7 g3f5 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3141,KBN,10,table,2,1,1,mate,,20,30220094416822,30222237163350,2117881508,2137423945,"210,0,0,2,0,0,0,5",7k/8/5BKN/8/8/8/8/8 b - - 20 88,g6f7 h4f6 f7e8 e5e6 e8f8 g3f5 f8e8 f6g5 e8f8 g5e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3191,KBN,10,corner,0,1,1,mate,,44,30274401845203,30289556927578,15021416318,15132293413,"1464,0,4,8,0,0,1,45",7k/8/5BKN/8/8/8/8/8 b - - 44 99,f4f5 c5d6 f5g4 d4e3 g4f5 e4c5 f5g4 e3e4 g4g5 c5d7 g5g4 d7f6 g4g5 e4e5 g5g6 e5e6 g6g5 d6g3 g5h6 g3f4 h6g6 f4d2 g6g7 f6h5 g7g6 h5g3 g6g7 d2g5 g7f8 g5f6 f8g8 e6e7 g8h7 e7f7 h7h6 f6e7 h6h7 g3f5 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3191,KBN,10,stock,0,1,1,mate,,46,30259738273948,30274244507656,14360175239,14484755276,"1391,0,2,6,0,0,0,55",7k/8/5BKN/8/8/8/8/8 b - - 46 100,f4f5 c5d6 f5g4 d4e3 g4f5 d6c7 f5e6 e3d4 e6d7 c7f4 d7e6 e4g3 e6d7 d4d5 d7d8 d5d6 d8c8 d6c6 c8d8 f4d6 d8e8 c6d5 e8f7 d5e5 f7g6 d6e7 g6f7 e7f6 f7e8 e5e6 e8f8 g3f5 f8e8 f6h4 e8f8 h4e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
3191,KBN,10,table,0,1,1,mate,,40,30253455389392,30259549075410,6027680420,6081455602,"590,0,3,3,0,0,0,18",7k/8/5BKN/8/8/8/8/8 b - - 40 97,f4f5 c5d6 f5g4 d4e3 g4f5 e4c5 f5g4 d6f4 g4f5 e3f3 f5g6 f3g4 g6f6 f4c7 f6g6 c7d8 g6g7 c5b7 g7f7 g4f5 f7e8 f5e6 e8f8 d8f6 f8g8 e6f5 g8f8 b7d6 f8g8 f5g6 g8f8 f6d8 f8g8 d8e7 g8h8 d6f5 h8g8 f5h6 g8h8 e7f6
3193,KBN,10,corner,2,1,1,mate,,40,30237197683325,30250879679802,13587544038,13664224966,"1310,0,2,6,0,0,0,53",8/8/8/3B4/8/6KN/8/7k b - - 40 83,f8g7 d6f5 g7h8 h5f7 h8h7 e6f6 h7h8 f5e7 h8h7 e7g6 h7h6 f7g8 h6h5 g6e5 h5h4 g8d5 h4g3 e5d3 g3h2 f6g5 h2g3 d5a8 g3h3 a8f3 h3g3 f3g4 g3h2 g5h4 h2g2 g4e2 g2h2 d3f4 h2g1 h4g3 g1h1 e2c4 h1g1 f4h3 g1h1 c4d5
3193,KBN,10,stock,2,1,0,fifty,,100,30250986690081,30279611687764,28345040019,28572650065,"2756,0,7,19,0,0,0,95",8/8/7N/3K4/6B1/8/8/2k5 b - - 100 113,f8g7 e6e5 g7h7 e5f6 h7h8 f6f7 h8h7 h5g4 h7h8 f7f8 h8h7 f8f7 h7h8 g4c8 h8h7 c8f5 h7h6 f7f6 h6h5 f6e5 h5h4 e5f4 h4h5 f5c8 h5h6 f4e5 h6g6 c8d7 g6g7 d7f5 g7g8 e5f6 g8h8 f5h3 h8h7 h3f5 h7g8 f5e6 g8h7 d6f5 h7h8 f5h6 h8h7 h6f7 h7g8 e6c8 g8h7 c8f5 h7g8 f7d6 g8f8 f5c8 f8g8 c8g4 g8h7 g4e6 h7h6 e6f5 h6h5 f6e5 h5h4 e5f4 h4h5 f5g4 h5g6 f4e5 g6h6 e5f6 h6h7 d6f7 h7g8 g4f5 g8f8 f7d8 f8e8 d8b7 e8f8 f5c8 f8g8 c8f5 g8f8 f5c8 f8g8 f6e5 g8f8 e5e6 f8g7 e6d5 g7g6 d5c6 g6g5 c6d5 g5f4 b7d8 f4e3 c8g4 e3d2 d8f7 d2c1 f7h6
3193,KBN,10,table,2,1,1,mate,,42,30229155771996,30237086536835,7860681129,7914942449,"768,0,0,5,0,0,0,24",k7/8/NKB5/8/8/8/8/8 b - - 42 84,f8g7 d6f7 g7h7 e6f6 h7g8 h5g6 g8f8 g6h7 f8e8 f7e5 e8d8 f6e6 d8c7 e5d7 c7b7 h7d3 b7c6 d3a6 c6c7 a6b5 c7d8 d7b6 d8c7 b6a4 c7d8 e6d6 d8c8 a4c5 c8d8 b5a4 d8c8 a4d7 c8b8 d6c6 b8a7 c6c7 a7a8 c7b6 a8b8 c5a6 b8a8 d7c6
3999,KBN,10,corner,0,1,1,mate,,40,30303670778988,30316988588270,13235423770,13300942997,"1282,0,0,5,0,0,0,50",k7/8/NKB5/8/8/8/8/8 b - - 40 124,c7b6 d5d4 b6b5 g2d5 b5a4 d5c4 a4b4 g3e4 b4a3 d4c3 a3a4 e4d6 a4a5 c4b5 a5b6 c3b4 b6c7 d6f7 c7b6 b5e8 b6c7 b4a5 c7b7 e8a4 b7c7 a5a6 c7c8 a6b6 c8b8 a4d7 b8a8 f7g5 a8b8 g5e6 b8a8 e6c7 a8b8 c7a6 b8a8 d7c6
3999,KBN,10,stock,0,1,1,mate,,34,30289690805834,30303555766148,13774463920,13849933429,"1327,0,1,6,0,0,0,59",k1N5/2K5/2B5/8/8/8/8/8 b - - 34 121,c7b6 d5c4 b6a5 g2c6 a5b6 c4d5 b6c7 d5c5 c7b8 c5b6 b8c8 g3f5 c8d8 b6c5 d8c8 c5d6 c8b8 d6d7 b8a7 f5d6 a7b6 d6b7 b6a7 d7c7 a7a6 c6d7 a6a7 d7b5 a7a8 b7d6 a8a7 d6c8 a7a8 b5c6
3999,KBN,10,table,0,1,1,mate,,42,30317043719854,30325532963161,8412598191,8474369047,"815,0,1,5,0,0,0,33",k7/8/NKB5/8/8/8/8/8 b - - 42 125,c7b6 g2f1 b6a5 d5d4 a5b4 f1c4 b4a3 d4c3 a3a4 g3f5 a4a5 c3b3 a5b6 b3b4 b6c6 c4f7 c6b7 b4c5 b7b8 f5g7 b8c8 f7e8 c8d8 c5d6 d8c8 e8c6 c8b8 d6c5 b8a7 c5b5 a7b8 b5b6 b8c8 g7e6 c8b8 c6d7 b8a8 e6c5 a8b8 c5a6 b8a8 d7c6
4331,KBN,10,corner,2,0,1,mate,,32,30314503171867,30324805535610,10220106585,10288877902,"997,0,2,5,0,0,0,30",8/5kbK/5n2/8/8/8/8/8 w - - 32 79,g2h3 e4f3 h3h4 c5e7 h4h5 e2f4 h5h6 f3g4 h6g7 g4f5 g7f7 e7f6 f7e8 f5e6 e8f8 f6g5 f8e8 f4h5 e8f8 g5e7 f8g8 e6f6 g8h7 e7f8 h7g8 f6e7 g8h7 e7f7 h7h8 f8g7 h8h7 h5f6
4331,KBN,10,stock,2,0,0,fifty,,100,30279728917202,30307986615087,28078757510,28211416553,"2729,0,2,9,0,0,0,92",8/3K4/8/8/5b2/2n2k2/8/8 w - - 100 113,g2h3 e4f4 h3h4 e2g3 h4h3 f4f3 h3h2 c5f2 h2h3 g3e2 h3h2 e2c3 h2h1 f2a7 h1h2 a7c5 h2h3 c5e7 h3h2 c3e4 h2h1 e7d6 h1g1 e4c3 g1h1 d6c5 h1h2 c5f2 h2h1 c3e4 h1h2 f2g3 h2h1 g3c7 h1g1 e4c3 g1f1 c7b6 f1e1 b6e3 e1f1 c3e4 f1e1 e4f2 e1f1 e3g5 f1g1 g5e3 g1f1 e3c1 f1e1 c1f4 e1f1 f2d3 f1g1 f4d6 g1f1 d6f4 f1g1 d3b2 g1f1 b2d1 f1g1 d1e3 g1h1 e3c4 h1g1 c4e3 g1h1 f4g3 h1g1 e3d5 g1f1 g3f4 f1e1 d5c3 e1f1 f4e3 f1e1 e3c1 e1f1 c3d1 f1g1 d1b2 g1h2 f3e3 h2g3 e3e4 g3g4 b2a4 g4h5 e4f3 h5g6 c1f4 g6f7 f4c1 f7e6 c1f4 e6d7 a4c3
4331,KBN,10,table,2,0,1,mate,,36,30308045158013,30314369778910,6292466353,6313868152,"606,0,1,2,0,0,0,26",7K/5kb1/5n2/8/8/8/8/8 w - - 36 81,g2h3 e4f3 h3h4 c5e3 h4h5 f3f4 h5g6 f4e5 g6h5 e2g1 h5g6 e5e6 g6h5 e6f5 h5h4 e3f2 h4h5 g1e2 h5h6 f2d4 h6h7 f5f6 h7g8 d4c5 g8h7 e2g3 h7h6 c5f8 h6h7 f6f7 h7h8 g3e4 h8h7 e4f6 h7h8 f8g7
4428,KBN,10,corner,0,1,1,mate,,32,30325642958528,30336998219809,11292285923,11342605541,"1092,0,2,4,0,0,0,41",7k/8/5BKN/8/8/8/8/8 b - - 32 92,b8c8 c5d6 c8d8 f3h4 d8e8 c6c7 e8f7 c7d7 f7g7 d6f4 g7f6 d7d6 f6f7 f4g5 f7e8 d6e6 e8f8 h4f5 f8e8 g5f6 e8f8 f6e7 f8g8 e6f6 g8h7 f6f7 h7h8 f7g6 h8g8 f5h6 g8h8 e7f6
4428,KBN,10,stock,0,1,1,mate,,46,30337126464284,30356360131978,19089135672,19212380939,"1860,0,0,11,0,0,1,63",8/8/8/8/8/2B5/2K5/k1N5 b - - 46 99,b8c8 c5b6 c8b8 f3e5 b8c8 e5c4 c8b8 c4d6 b8a8 c6d5 a8b8 d5e6 b8a8 b6c5 a8b8 d6e8 b8b7 e6d6 b7a6 e8c7 a6a5 d6d5 a5a4 d5c4 a4a5 c5d4 a5a4 d4c3 a4a3 c7e6 a3a4 e6c5 a4a3 c4d3 a3a2 d3c2 a2a3 c3d2 a3a2 d2b4 a2a1 c5d3 a1a2 d3c1 a2a1 b4c3
4428,KBN,10,table,0,1,1,mate,,36,30356424966243,30362236766334,5756659801,5800604690,"562,0,1,4,0,0,0,18",7k/8/5BKN/8/8/8/8/8 b - - 36 94,b8c8 c5d6 c8d8 f3h4 d8c8 d6e5 c8d8 h4f5 d8e8 c6d6 e8d8 f5e7 d8e8 d6e6 e8d8 e5b8 d8e8 b8c7 e8f8 e7f5 f8e8 f5d6 e8f8 e6f6 f8g8 f6g6 g8f8 c7d8 f8g8 d8e7 g8h8 d6f5 h8g8 f5h6 g8h8 e7f6
4810,KBN,10,corner,2,1,1,mate,,30,30324925611281,30336541239614,11564541627,11602607271,"1121,0,1,2,0,0,0,40",k1N5/2K5/2B5/8/8/8/8/8 b - - 30 154,g7f8 f5f6 f8e8 c4d5 e8d8 d5c6 d8c8 f6e7 c8c7 e7e6 c7b6 e6d6 b6a5 d6c5 a5a6 e5f7 a6a7 c5b5 a7b8 b5b6 b8c8 c6b5 c8b8 f7d6 b8a8 b6c7 a8a7 d6c8 a7a8 b5c6
4810,KBN,10,stock,2,1,0,fifty,,100,30341331817323,30369254421324,27661557790,27870421226,"2708,0,4,11,0,0,0,77",3N3k/8/4B3/6K1/8/8/8/8 b - - 100 189,g7f8 c4e6 f8e7 e5f7 e7f8 f7d8 f8e7 d8b7 e7e8 f5f6 e8f8 e6h3 f8g8 h3g4 g8h8 g4f5 h8g8 f5c2 g8f8 c2h7 f8e8 h7f5 e8f8 b7d8 f8g8 f5e6 g8f8 e6c8 f8g8 c8f5 g8h8 f5e6 h8h7 d8b7 h7h6 e6g4 h6h7 b7d8 h7g8 g4f5 g8h8 f5e4 h8g8 e4d3 g8h8 d3f5 h8g8 f5e4 g8f8 d8e6 f8g8 e4d3 g8h8 e6c7 h8g8 d3g6 g8f8 g6e4 f8g8 e4d3 g8h8 c7e6 h8g8 d3f5 g8h8 f5e4 h8g8 e6c7 g8h8 e4g6 h8g8 g6f7 g8h7 c7e8 h7h6 e8d6 h6h7 f7g6 h7g8 g6f5 g8f8 d6b7 f8g8 f6e6 g8g7 e6e5 g7h6 f5d7 h6g5 d7c8 g5h4 e5f4 h4h5 c8f5 h5h6 f5e6 h6h7 f4g5 h7h8 b7d8
4810,KBN,10,table,2,1,1,mate,,30,30336594264281,30341194567184,4538314616,4590812786,"440,0,1,3,0,0,0,17",8/kBK5/2N5/8/8/8/8/8 b - - 30 154,g7f8 f5f6 f8e8 c4f7 e8d8 f6e6 d8c7 f7e8 c7d8 e8a4 d8c7 e5c4 c7c8 e6d6 c8d8 c4a5 d8c8 a4d7 c8b8 d6c6 b8a7 d7c8 a7b8 c6d7 b8a7 d7c7 a7a8 c8b7 a8a7 a5c6
5825,KBB,10,corner,0,1,1,mate,,26,30374843162567,30383731227738,8811156379,8879004246,"857,0,0,5,0,0,0,31",8/8/8/8/3BB3/1K6/8/k7 b - - 26 100,b3c2 b5c4 c2d2 e7c5 d2e2 c4c3 e2f1 c3d3 f1e1 c6g2 e1d1 c5f2 d1c1 d3c3 c1b1 g2d5 b1a1 c3b3 a1b1 d5f3 b1c1 f2e3 c1b1 f3e4 b1a1 e3d4
5825,KBB,10,stock,0,1,1,mate,,26,30366065200895,30374743856800,8626772023,8668305646,"845,0,1,3,0,0,0,23",8/8/8/8/3BB3/1K6/8/k7 b - - 26 100,b3c2 b5c4 c2d2 e7c5 d2e2 c4c3 e2f1 c3d3 f1e1 c6g2 e1d1 c5f2 d1c1 d3c3 c1b1 g2d5 b1a1 c3b3 a1b1 d5f3 b1c1 f2e3 c1b1 f3e4 b1a1 e3d4
5825,KBB,10,table,0,1,1,mate,,26,30362287611540,30365914956072,3575474815,3616570951,"351,0,0,3,0,0,0,11",8/8/8/3B4/3B4/8/2K5/k7 b - - 26 100,b3c2 b5b4 c2d2 e7c5 d2e2 b4c3 e2f1 c3d3 f1e1 c6g2 e1d1 c5f2 d1c1 d3c3 c1b1 f2c5 b1c1 g2f3 c1b1 c3b3 b1a1 b3c2 a1a2 f3d5 a2a1 c5d4
6710,KBN,10,corner,2,0,1,mate,,46,30377410657861,30396007421595,18467463290,18577964851,"1805,0,0,9,0,0,0,53",K1n5/2k5/2b5/8/8/8/8/8 w - - 46 82,d8e7 c4d6 e7e6 b5f1 e6d7 f1c4 d7e7 c5c6 e7f6 c6d5 f6e7 d5e5 e7d7 c4d5 d7c7 d6c4 c7d7 e5f6 d7e8 c4e5 e8d8 d5c6 d8c8 f6e7 c8c7 c6e8 c7b6 e7d6 b6b7 e8c6 b7c8 c6d7 c8b7 e5c4 b7a7 d6c7 a7a6 d7c6 a6a7 c6b5 a7a8 c4b6 a8a7 b6c8 a7a8 b5c6
6710,KBN,10,stock,2,0,1,mate,,74,30396098509038,30421318065986,24957798084,25186361708,"2422,0,4,17,0,0,0,94",8/8/8/8/8/5bkn/8/7K w - - 74 96,d8e7 c4a5 e7e6 a5b3 e6f5 b5f1 f5f4 c5b4 f4e4 b3a5 e4d5 a5c4 d5e4 b4c5 e4f5 c5d5 f5f6 d5d6 f6f7 c4e5 f7f6 e5c4 f6f7 c4e5 f7f6 f1d3 f6g5 d6e7 g5f4 e5c4 f4g3 e7f6 g3f4 d3f5 f4g3 f6g5 g3f3 f5d3 f3f2 g5g4 f2e1 d3c2 e1f2 c2f5 f2e1 f5c2 e1f2 c2d1 f2e1 d1f3 e1f1 g4f4 f1f2 c4b2 f2e1 f4e3 e1f1 b2d3 f1g1 e3f4 g1h2 f4g4 h2g1 g4g3 g1f1 f3g4 f1g1 g4e2 g1h1 d3f2 h1g1 f2h3 g1h1 e2f3
6710,KBN,10,table,2,0,1,mate,,42,30369313443280,30377258411743,7899888192,7933057861,"774,0,0,3,0,0,0,19",8/8/8/8/8/5n2/5kb1/7K w - - 42 80,d8e7 c4d6 e7e6 b5d3 e6e5 d3f5 e5f4 c5d4 f4f3 f5b1 f3f2 d4d3 f2f3 d6f7 f3f2 f7e5 f2g3 d3e3 g3h3 e3f4 h3g2 b1e4 g2f2 e4f3 f2e1 f4e3 e1f1 e5g6 f1g1 e3e2 g1h2 e2f2 h2h3 f3e2 h3h2 e2f1 h2h1 g6e5 h1h2 e5f3 h2h1 f1g2
6950,KBN,10,corner,0,0,1,mate,,42,30398218226396,30416276644595,17954039924,18039678155,"1724,0,2,7,0,0,0,79",8/8/5b2/8/8/nk6/8/K7 w - - 42 84,d1d2 d4b5 d2d3 c7b6 d3c4 b5c7 c4d3 b6e3 d3c4 f3e2 c4c3 e3a7 c3b4 e2d3 b4b3 a7b6 b3b4 b6e3 b4b3 e3d2 b3a4 d3c4 a4a3 c7a6 a3b2 a6b4 b2a3 b4d3 a3a4 d3b2 a4a3 c4c3 a3a2 b2c4 a2b1 c3b3 b1a1 d2g5 a1b1 c4a3 b1a1 g5f6
6950,KBN,10,stock,0,0,1,mate,,40,30383818556085,30398104226001,14204310514,14270612076,"1395,0,1,5,0,0,1,31",8/8/8/8/8/2b5/2k5/K1n5 w - - 40 83,d1d2 f3e4 d2c3 c7a5 c3c4 a5b6 c4c3 d4b5 c3b4 b5d6 b4a4 e4d3 a4b4 d3d2 b4b3 b6a5 b3a4 a5c3 a4b3 d2d3 b3a3 d6e4 a3a4 d3c4 a4a3 e4f2 a3a2 c4b4 a2b1 b4b3 b1c1 c3b4 c1b1 f2d3 b1a1 b3c2 a1a2 d3c1 a2a1 b4c3
6950,KBN,10,table,0,0,1,mate,,38,30416352217871,30423035244932,6636378084,6669947683,"637,0,1,3,0,0,0,29",8/8/8/8/8/nkb5/8/K7 w - - 38 82,d1d2 c7b6 d2c3 d4b5 c3c4 b5c7 c4d3 b6e3 d3c4 f3e2 c4c3 e3b6 c3c4 e2d2 c4b3 d2d3 b3b2 b6a5 b2c1 a5c3 c1d1 c7a8 d1c1 a8b6 c1d1 b6c4 d1c1 c3d2 c1b1 d3c3 b1a2 c3c2 a2a1 c2b3 a1b1 c4a3 b1a1 d2c3
6956,KBN,10,corner,2,0,1,mate,,34,30454312995926,30470040994027,15626771317,15713138019,"1517,0,0,7,0,0,0,55",8/8/8/8/8/nkb5/8/K7 w - - 34 84,e1f1 e4f3 f1e1 d4b3 e1d1 b3d2 d1c2 f3e2 c2b2 e3c5 b2c3 e2e3 c3c2 c5b4 c2d1 d2c4 d1c2 c4a5 c2c1 e3d3 c1d1 a5c4 d1c1 b4d2 c1b1 d3c3 b1a2 c3c2 a2a1 c2b3 a1b1 c4a3 b1a1 d2c3
6956,KBN,10,stock,2,0,0,fifty,,100,30421435060102,30449848089558,28195466488,28367524167,"2730,0,1,14,0,0,0,111",8/8/8/8/n7/3k4/8/2b1K3 w - - 100 117,e1f1 d4f5 f1g2 e4f4 g2h2 f4f3 h2h3 e3f2 h3h2 f5g3 h2h3 f2c5 h3h4 c5e3 h4h3 g3f5 h3h2 e3f2 h2h3 f2a7 h3h2 f5e7 h2h1 e7f5 h1h2 a7f2 h2h3 f5d4 h3h2 f2g3 h2g1 g3f2 g1f1 f2g3 f1g1 d4f5 g1f1 f5e3 f1g1 g3d6 g1h1 e3f5 h1g1 d6f4 g1h1 f4g3 h1g1 g3f2 g1h2 f2d4 h2h3 f5g3 h3h4 d4f6 h4h3 g3e2 h3h2 f6c3 h2h1 c3d4 h1h2 d4f6 h2h3 f6e7 h3h2 e7c5 h2h1 e2f4 h1h2 f4d5 h2h1 d5b4 h1h2 b4d5 h2h1 c5f2 h1h2 d5b4 h2h3 b4d3 h3h2 d3b2 h2h3 f2e3 h3h4 f3e4 h4h5 e4f5 h5h4 e3c1 h4h3 f5e4 h3g2 b2a4 g2g1 c1e3 g1f1 e4d3 f1e1 e3c1
6956,KBN,10,table,2,0,1,mate,,34,30449934482542,30454170518352,4194568320,4225356949,"406,0,0,3,0,0,0,17",8/8/8/8/8/1kn5/1b6/K7 w - - 34 84,e1f1 e4f3 f1e1 d4b3 e1d1 b3d2 d1c2 f3e2 c2b2 e2d3 b2a3 d3c4 a3b2 d2e4 b2c2 e4f2 c2b2 e3d2 b2c2 d2c3 c2c1 c4b3 c1b1 c3a5 b1c1 a5b4 c1b1 b4a3 b1a1 f2d1 a1b1 d1c3 b1a1 a3b2
7569,KBN,10,corner,0,0,1,mate,,42,30423228097525,30438993488781,15691939841,15749090373,"1530,0,1,4,0,0,1,46",2n5/Kbk5/8/8/8/8/8/8 w - - 42 83,f4e3 f7e6 e3e4 d1g4 e4d4 e6d6 d4c4 d6e5 c4b4 e5d4 b4b5 g4d7 b5b6 d4d5 b6c7 h5f6 c7d8 d5e6 d8c7 f6e8 c7b7 e6d5 b7b6 d7c6 b6a5 d5c5 a5a6 c6d7 a6b7 c5b5 b7a7 e8d6 a7b8 b5b6 b8a8 b6c7 a8a7 d7c8 a7a8 c8b7 a8a7 d6c8
7569,KBN,10,stock,0,0,0,fifty,,100,30439101673229,30468214674298,28859244572,29067520262,"2809,0,1,17,0,0,0,100",8/8/8/1b6/8/4k3/6n1/K7 w - - 100 112,f4e3 f7f6 e3e4 h5g3 e4d5 g3f5 d5e4 f5h4 e4d5 d1f3 d5d6 h4f5 d6d7 f3h5 d7d8 f6e6 d8c7 e6e7 c7b6 e7d7 b6c5 d7e6 c5c4 e6e5 c4c5 h5f3 c5b6 e5d6 b6b5 f3e2 b5b4 f5h4 b4c3 d6e5 c3d2 e2f1 d2e1 f1b5 e1d2 e5d4 d2c2 b5f1 c2d2 f1b5 d2c2 h4f3 c2b2 f3e1 b2b3 b5c6 b3b4 c6d7 b4b3 d7b5 b3b4 b5d7 b4b3 e1d3 b3c2 d7a4 c2d2 d3f4 d2c1 d4c3 c1b1 f4d3 b1a2 d3e1 a2b1 a4d1 b1c1 d1f3 c1b1 f3e4 b1a2 e1c2 a2b1 c2e1 b1a1 e1g2 a1a2 e4d3 a2a3 d3b5 a3a2 b5f1 a2b1 c3d2 b1b2 d2e3 b2b3 g2h4 b3b2 f1b5 b2a2 e3d3 a2b1 d3e3 b1a1 h4g2
7569,KBN,10,table,0,0,1,mate,,48,30468288921443,30477293355450,8827481210,8986103953,"863,0,0,14,0,0,0,32",8/8/8/8/8/6k1/4n1b1/6K1 w - - 48 86,f4e3 f7e6 e3e4 h5f6 e4f4 d1b3 f4g5 b3c2 g5h6 f6e8 h6h5 c2f5 h5h4 e6e5 h4g5 e8d6 g5h6 e5f6 h6h5 d6f7 h5h4 f6e5 h4g3 e5e4 g3f2 f5g4 f2f1 f7e5 f1f2 e4f4 f2e1 f4e3 e1f1 e5d3 f1g2 e3f4 g2h2 f4f3 h2g1 g4h3 g1h1 f3g3 h1g1 d3c1 g1h1 h3g2 h1g1 c1e2
7658,KBN,10,corner,2,1,1,mate,,48,30470133959906,30488158177095,17845603951,17998683101,"1728,0,1,14,0,0,0,69",8/8/8/8/8/6K1/4N1B1/6k1 b - - 48 76,h5h6 e3f5 h6h7 f4g5 h7h8 g5f6 h8h7 f7b3 h7h8 f5e7 h8h7 e7g6 h7h6 b3g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4f1 f3g3 f1e2 g3h4 g4f6 h4g3 f6e4 g3h4 f5f4 h4h3 f4g5 h3h2 e2f1 h2g1 f1h3 g1h1 g5g4 h1h2 e4c3 h2g1 g4g3 g1h1 h3g2 h1g1 c3e2
7658,KBN,10,stock,2,1,0,fifty,,100,30496922834460,30526023302944,28736259706,29051631197,"2778,0,4,25,0,0,0,121",2B5/1N6/8/3K4/8/8/4k3/8 b - - 100 102,h5h6 e3f5 h6h7 f4e5 h7h8 e5f6 h8h7 f7e6 h7h8 e6c8 h8g8 f6e7 g8h7 e7f6 h7g8 f5d6 g8f8 c8f5 f8g8 f5e4 g8h8 d6f7 h8g8 f7d8 g8f8 d8e6 f8g8 e4c2 g8h8 c2b1 h8g8 b1f5 g8h8 e6d8 h8g8 d8b7 g8f8 f5e6 f8e8 e6g4 e8f8 b7d6 f8g8 g4h5 g8h8 f6f7 h8h7 d6f5 h7h8 h5e2 h8h7 e2c4 h7h8 c4b3 h8h7 b3e6 h7h8 f7e7 h8h7 e7f6 h7h8 e6b3 h8h7 f5d6 h7h8 b3c4 h8h7 c4f7 h7h6 d6f5 h6h7 f6e7 h7h8 e7d6 h8h7 d6c6 h7h8 c6d7 h8h7 d7c6 h7h8 c6d5 h8h7 d5c4 h7h8 f7e6 h8h7 f5d6 h7g7 d6b7 g7f6 c4d5 f6g5 d5c4 g5f4 c4d4 f4f3 e6c8 f3e2 d4d5
7658,KBN,10,table,2,1,1,mate,,48,30488210711862,30496788881118,8513292007,8563484781,"830,0,2,3,0,0,0,26",8/8/8/8/8/5B2/5K2/5N1k b - - 48 76,h5h6 e3f5 h6h7 f4e4 h7h8 e4e5 h8h7 e5f6 h7h8 f5e7 h8h7 e7g6 h7h6 f7g8 h6h5 g6e5 h5h4 f6f5 h4g3 e5g4 g3g2 g8c4 g2f3 c4a6 f3g3 a6e2 g3h4 g4e3 h4g3 e3d1 g3h4 f5f4 h4h3 d1e3 h3h4 e2d1 h4h3 d1g4 h3h2 f4f3 h2g1 f3g3 g1h1 g3f2 h1h2 e3f1 h2h1 g4f3
7727,KBN,10,corner,0,1,1,mate,,48,30513121131495,30530442818403,17018537091,17298666642,"1649,0,2,14,0,0,0,76",8/8/8/8/8/NKB5/8/k7 b - - 48 150,e1f2 b3d2 f2g3 d3e3 g3g4 e3e4 g4g5 b4e7 g5g4 d2f1 g4h3 e7d6 h3g2 f1e3 g2f2 e3c4 f2e1 e4f3 e1d1 f3e3 d1c2 c4d2 c2c3 d6c5 c3c2 c5d4 c2c1 e3d3 c1d1 d4f2 d1c1 d2c4 c1d1 c4e3 d1c1 d3c3 c1b1 c3b3 b1c1 f2e1 c1b1 e1d2 b1a1 e3c2 a1b1 c2a3 b1a1 d2c3
7727,KBN,10,stock,0,1,0,fifty,,100,30484803007061,30512965889101,27960493532,28110590845,"2698,0,1,12,0,0,0,115",8/8/6K1/1N6/1B6/8/8/3k4 b - - 100 176,e1f2 b3d4 f2g3 d3e4 g3g4 b4d2 g4h4 d4e6 h4g3 d2e1 g3g4 e1f2 g4h3 e4f3 h3h2 f2g3 h2h1 g3f2 h1h2 e6f4 h2h1 f4e2 h1h2 f2g3 h2h1 e2d4 h1g1 g3f2 g1h2 d4f5 h2h1 f5d4 h1h2 d4e2 h2h3 f2e1 h3h2 e1g3 h2h1 g3f2 h1h2 e2g3 h2h3 g3h5 h3h2 f2b6 h2h1 h5g3 h1h2 g3e2 h2h3 b6d8 h3h2 d8h4 h2h3 h4e1 h3h2 e2d4 h2h1 e1h4 h1g1 h4g3 g1f1 g3h4 f1g1 h4g3 g1f1 d4f5 f1g1 g3e5 g1f1 e5d4 f1e1 d4c3 e1d1 f5d4 d1c1 f3e4 c1b1 c3b4 b1a2 e4e5 a2b1 e5f6 b1c1 f6g6 c1b2 g6g7 b2c1 g7g6 c1b2 g6g7 b2a2 b4a5 a2b2 d4b5 b2c2 g7g6 c2d1 a5b4
7727,KBN,10,table,0,1,1,mate,,48,30477361651574,30484591425714,7175251669,7213989652,"701,0,1,3,0,0,0,21",6k1/6B1/5NK1/8/8/8/8/8 b - - 48 150,e1f2 b3d2 f2g3 d3e3 g3g4 b4d6 g4f5 d2c4 f5g4 c4b6 g4h3 e3f3 h3h4 d6f4 h4h5 b6d5 h5h4 d5f6 h4h3 f6e4 h3h4 f4g3 h4h5 f3f4 h5g6 g3h4 g6h5 h4d8 h5g6 e4d6 g6h6 f4f5 h6h5 d6e8 h5h6 d8g5 h6h7 f5f6 h7g8 g5h6 g8h7 f6g5 h7g8 g5g6 g8h8 h6g7 h8g8 e8f6
7812,KBB,10,corner,2,1,1,mate,,16,30527550331462,30531143519411,3575077999,3588139473,"349,0,1,1,0,0,0,9",7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g5f6 e8d8 g4h3 d8e8 d6c7 e8f8 h3d7 f8g8 f6g6 g8h8 c7d6 h8g8 d7e6 g8h8 d6e5
7812,KBB,10,stock,2,1,1,mate,,16,30531260152893,30534536996920,3265574497,3271280570,"319,0,0,0,0,0,0,9",7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g5f6 e8d8 g4h3 d8e8 d6c7 e8f8 h3d7 f8g8 f6g6 g8h8 c7d6 h8g8 d7e6 g8h8 d6e5
7812,KBB,10,table,2,1,1,mate,,16,30526080529825,30527411264949,1324498094,1326854868,"126,0,0,0,0,0,0,6",7k/8/4B1K1/4B3/8/8/8/8 b - - 16 98,d8e8 g4e6 e8d8 g5f6 d8e8 d6c7 e8f8 e6d7 f8g8 f6g6 g8h8 c7d6 h8g8 d7e6 g8h8 d6e5
~~~

times.csv

~~~text
g,class,clock_start_s,strong_policy,ply,core,white_to_move,actor,intended_move,bank_before_ns,start_monotonic_ns,stop_monotonic_ns,bank_after_ns,btime_ms,wtime_ms,actor_cpu_ns,actor_leader_run_ns,actor_leader_wait_ns,actor_leader_slices,parent_leader_run_ns,parent_leader_wait_ns,parent_leader_slices
916,KBN,10,corner,0,0,1,stock,e2d3,10000000000,30186716193543,30187054648192,9761545351,10000,10000,338058926,127700,4143732,2,523802,3501043,12
916,KBN,10,corner,1,0,0,corner,h5g4,10000000000,30187055069351,30188212361210,8942708141,10000,9761,1156758844,155612,0,1,903709,4940039,16
916,KBN,10,corner,2,0,1,stock,d3d4,9761545351,30188212932374,30188520371671,9554106054,8942,9761,306833346,109963,2986997,2,1010649,2918825,15
916,KBN,10,corner,3,0,0,corner,g4f4,8942708141,30188520829054,30189055291002,8508246193,8942,9554,534150052,123294,0,1,718089,3105253,13
916,KBN,10,corner,4,0,1,stock,d4c5,9554106054,30189055648546,30189402448239,9307306361,8508,9554,346459371,91186,3976,1,681848,4191293,9
916,KBN,10,corner,5,0,0,corner,f4e5,8508246193,30189402873104,30189740572300,8270546997,8508,9307,337439920,88442,4687,1,660465,4998087,7
916,KBN,10,corner,6,0,1,stock,c5c6,9307306361,30189741170473,30192226733442,6921743392,8270,9307,2477927743,106709,6059,1,804370,2688902,9
916,KBN,10,corner,7,0,0,corner,g8d5,8270546997,30192227265357,30192483832403,8113979951,8270,6921,256228864,107631,7221,1,917028,4574455,8
916,KBN,10,corner,8,0,1,stock,c6c7,6921743392,30192484263407,30192736502147,6769504652,8113,6921,251980275,91727,4016,1,477132,3615764,9
916,KBN,10,corner,9,0,0,corner,d5e6,8113979951,30192736950938,30193285901127,7665029762,8113,6769,524857117,92538,4727,1,786492,2911124,7
916,KBN,10,corner,10,0,1,stock,c7b6,6769504652,30193286429656,30193593273033,6562661275,7665,6769,197739720,105687,6029,1,841827,5426566,6
916,KBN,10,corner,11,0,0,corner,e6d5,7665029762,30193593743185,30193839041599,7519731348,7665,6562,160528787,104346,6229,1,715305,26769819,8
916,KBN,10,corner,12,0,1,stock,b6c7,6562661275,30193839519493,30194344497858,6157682910,7519,6562,398882812,140730,6400,1,749918,3532480,8
916,KBN,10,corner,13,0,0,corner,d5e6,7519731348,30194345028310,30195074863791,6889895867,7519,6157,694826729,110524,6550,1,760817,2813237,8
916,KBN,10,corner,14,0,1,stock,c7b6,6157682910,30195075246192,30195729182137,5603746965,6889,6157,616195446,88542,3505,1,619745,4636778,6
916,KBN,10,corner,15,0,0,corner,h6f7,6889895867,30195729536537,30196721235281,5998197123,6889,5603,944918250,114971,0,1,606965,3004602,7
916,KBN,10,corner,16,0,1,stock,b6b5,5603746965,30196721856158,30196877516936,5548086187,5998,5603,155020509,92488,0,1,1078829,6142725,15
916,KBN,10,corner,17,0,0,corner,e5d4,5998197123,30196877973518,30197085868310,5890302331,5998,5548,205620800,156554,0,1,782528,6292909,6
916,KBN,10,corner,18,0,1,stock,b5b6,5548086187,30197086426614,30197307437283,5427075518,5890,5548,216943827,99548,5228,1,931230,5432735,9
916,KBN,10,corner,19,0,0,corner,d4c4,5890302331,30197307961577,30197529089641,5769174267,5890,5427,220654075,141210,6610,1,973010,3847180,11
916,KBN,10,corner,20,0,1,stock,b6c6,5427075518,30197529653964,30197906003421,5150726061,5769,5427,375671906,104856,0,1,1029499,6118918,11
916,KBN,10,corner,21,0,0,corner,e6g4,5769174267,30197906455907,30198533286695,5242343479,5769,5150,625429263,96885,5368,1,660044,5406926,4
916,KBN,10,corner,22,0,1,stock,c6b6,5150726061,30198533781354,30198737506868,5047000547,5242,5150,195972837,151777,8272,1,827223,6026261,6
916,KBN,10,corner,23,0,0,corner,g4d7,5242343479,30198737938653,30199919446814,4160835318,5242,5047,1178888868,95242,5208,1,742659,2323837,6
916,KBN,10,corner,24,0,1,stock,b6c7,5047000547,30199919866310,30201435444346,3631422511,4160,5047,1509858503,96524,4316,1,492875,3993738,3
916,KBN,10,corner,25,0,0,corner,d7e8,4160835318,30201436074718,30201866155092,3830754944,4160,3631,429884575,115823,0,1,194510,3923234,3
916,KBN,10,corner,26,0,1,stock,c7b6,3631422511,30201866596913,30202048231320,3549788104,3830,3631,181459603,129273,5288,1,590421,5264264,3
916,KBN,10,corner,27,0,0,corner,c4b4,3830754944,30202048869414,30202635307018,3344317340,3830,3549,585620070,116534,8953,1,831821,2948239,5
916,KBN,10,corner,28,0,1,stock,b6a6,3549788104,30202635759214,30202852375177,3433172141,3344,3549,216419333,100790,0,1,628326,4205314,5
916,KBN,10,corner,29,0,0,corner,b4c5,3344317340,30202852768094,30203243608254,3053477180,3344,3433,381149914,96384,4918,1,755498,3097431,6
916,KBN,10,corner,30,0,1,stock,a6b7,3433172141,30203244095773,30203652067508,3125200406,3053,3433,403878124,90045,0,1,402531,3906438,4
916,KBN,10,corner,31,0,0,corner,c5b5,3053477180,30203652564441,30204177931451,2628110170,3053,3125,525071078,148301,0,1,681516,3434835,4
916,KBN,10,corner,32,0,1,stock,b7c7,3125200406,30204178446641,30204376851434,3026795613,2628,3125,198073441,153990,0,1,793974,5644852,4
916,KBN,10,corner,33,0,0,corner,e8c6,2628110170,30204377403139,30204588530574,2516982735,2628,3026,210833658,118847,7832,1,781045,2427222,4
916,KBN,10,corner,34,0,1,stock,c7c8,3026795613,30204588992906,30204858685060,2857103459,2516,3026,268024281,98877,5048,1,828605,4134069,5
916,KBN,10,corner,35,0,0,corner,b5b6,2516982735,30204859262534,30205040341890,2435903379,2516,2857,176113625,117395,7562,1,915387,5879822,5
916,KBN,10,corner,36,0,1,stock,c8b8,2857103459,30205042159999,30205193289533,2805973925,2435,2857,150816577,100480,5338,1,669899,5708136,5
916,KBN,10,corner,37,0,0,corner,c6d7,2435903379,30205193857332,30205435007524,2294753187,2435,2805,240727592,99509,5849,1,955755,2368314,6
916,KBN,10,corner,38,0,1,stock,b8a8,2805973925,30205435584707,30205538400101,2803158531,2294,2805,102340263,148161,6680,1,1025520,4231093,9
916,KBN,10,corner,39,0,0,corner,f7d6,2294753187,30205538957084,30205688161119,2245549152,2294,2803,148663674,116093,6159,1,1077859,4878478,10
916,KBN,10,corner,40,0,1,stock,a8b8,2803158531,30205688781367,30205779997968,2811941930,2245,2803,90738804,100050,5057,1,1098009,3093255,36
916,KBN,10,corner,41,0,0,corner,d7b5,2245549152,30205780456213,30205928666713,2197338652,2245,2811,145897464,98387,5328,1,1191182,4928743,37
916,KBN,10,corner,42,0,1,stock,b8a8,2811941930,30205929213110,30205938813676,2902341364,2197,2811,9333174,117184,5018,1,780294,2638887,12
916,KBN,10,corner,43,0,0,corner,b6c7,2197338652,30205939323037,30205942669551,2293992138,2197,2902,3226844,103505,5368,1,549129,3083550,1
916,KBN,10,corner,44,0,1,stock,a8a7,2902341364,30205943191361,30205944067221,3001465504,2293,2902,646422,101923,5058,2,838213,0,65
916,KBN,10,corner,45,0,0,corner,d6c8,2293992138,30205944275983,30205944827488,2393440633,2293,3001,479716,93720,0,1,223924,479716,1
916,KBN,10,corner,46,0,1,stock,a7a8,3001465504,30205945006605,30205945451601,3101020508,2393,3001,237954,87060,0,2,444074,65017,66
916,KBN,10,corner,47,0,0,corner,b5c6,2393440633,30205945600003,30205946053190,2492987446,2393,3101,384283,116734,0,1,160169,384283,1
916,KBN,10,stock,0,0,1,stock,e2d3,10000000000,30166997367662,30167358270922,9739096740,10000,10000,360169496,165036,7112431,2,1083857,6196124,11
916,KBN,10,stock,1,0,0,stock,g8e6,10000000000,30167358649507,30167870997868,9587651639,10000,9739,508246156,170885,3655,1,823297,4942034,12
916,KBN,10,stock,2,0,1,stock,d3e4,9739096740,30167871480879,30168371655583,9338922036,9587,9739,491495887,105928,5398,1,763876,4576048,9
916,KBN,10,stock,3,0,0,stock,h6f7,9587651639,30168372115530,30168631623841,9428143328,9587,9338,259163071,90565,4006,1,399145,3738628,9
916,KBN,10,stock,4,0,1,stock,e4d4,9338922036,30168632226752,30168935089113,9136059675,9428,9338,298870841,102893,6881,1,500237,3607191,10
916,KBN,10,stock,5,0,0,stock,h5g4,9428143328,30168935621228,30169714888609,8748875947,9428,9136,774688459,136845,6439,1,893172,4191864,8
916,KBN,10,stock,6,0,1,stock,d4c5,9136059675,30169715231942,30169957776853,8993514764,8748,9136,234745190,89633,4547,1,767055,4658259,10
916,KBN,10,stock,7,0,0,stock,e6d7,8748875947,30169958250831,30170406825880,8400300898,8748,8993,444343458,104186,6840,1,857979,0,23
916,KBN,10,stock,8,0,1,stock,c5c4,8993514764,30170407225948,30170693410997,8807329715,8400,8993,285725836,146168,4787,1,923937,4596438,11
916,KBN,10,stock,9,0,0,stock,d7c6,8400300898,30170694015329,30171139788319,8054527908,8400,8807,443726761,127841,7962,1,2578367,5794485,12
916,KBN,10,stock,10,0,1,stock,c4d4,8807329715,30171140215116,30172455313421,7592231410,8054,8807,1314577249,89713,4938,1,406637,3664527,5
916,KBN,10,stock,11,0,0,stock,g4f4,8054527908,30172455729653,30172964052422,7646205139,8054,7592,507651067,94941,5609,1,1009116,4128799,13
916,KBN,10,stock,12,0,1,stock,d4c5,7592231410,30172964522594,30173253437666,7403316338,7646,7592,288476756,95883,5789,1,865080,3352482,8
916,KBN,10,stock,13,0,0,stock,c6g2,7646205139,30173254045864,30173555521761,7444729242,7646,7403,301038526,112067,7441,1,947784,5812702,5
916,KBN,10,stock,14,0,1,stock,c5b4,7403316338,30173556116420,30175611344936,5448087822,7444,7403,2030522373,94521,5268,1,213318,3756565,4
916,KBN,10,stock,15,0,0,stock,f7g5,7444729242,30175611788098,30175915993101,7240524239,7444,5448,303619497,96354,6490,1,964079,4068701,10
916,KBN,10,stock,16,0,1,stock,b4b5,5448087822,30175916494380,30176352541287,5112040915,7240,5448,435528540,94712,5228,1,968214,3372251,15
916,KBN,10,stock,17,0,0,stock,g5e6,7240524239,30176353084138,30178280899928,5412708449,7240,5112,1915521613,105778,5969,1,804500,2767058,13
916,KBN,10,stock,18,0,1,stock,b5a5,5112040915,30178281320837,30178458784830,5034576922,5412,5112,176898586,96214,5037,1,930357,2554611,15
916,KBN,10,stock,19,0,0,stock,f4e4,5412708449,30178459266389,30178830945940,5141028898,5412,5034,371108750,117275,0,1,944980,4733973,8
916,KBN,10,stock,20,0,1,stock,a5b5,5034576922,30178831355782,30179115996493,4849936211,5141,5034,283857847,96615,4426,1,725199,4514546,8
916,KBN,10,stock,21,0,0,stock,e4d4,5141028898,30179116666053,30180656988898,3700706053,5141,4849,1532166780,122232,0,1,1115585,3245231,11
916,KBN,10,stock,22,0,1,stock,b5b6,4849936211,30180657400623,30180862382803,4744954031,3700,4849,204578624,94872,5608,1,759675,2471437,9
916,KBN,10,stock,23,0,0,stock,d4c4,3700706053,30180862768358,30181379966987,3283507424,3700,4744,505591043,92398,4046,1,708407,5103594,6
916,KBN,10,stock,24,0,1,stock,b6a5,4744954031,30181380394586,30182830711544,3394637073,3283,4744,1447802996,95743,5107,1,543561,3477498,4
916,KBN,10,stock,25,0,0,stock,g2c6,3283507424,30182831121336,30183946589495,2268039265,3283,3394,1107968824,96544,5809,1,576310,4738590,3
916,KBN,10,stock,26,0,1,stock,a5b6,3394637073,30183947086136,30184063334450,3378388759,2268,3394,115976399,102954,7000,1,784269,4776767,8
916,KBN,10,stock,27,0,0,stock,c6d7,2268039265,30184063797621,30184503757322,1928079564,2268,3378,439776382,102232,5579,1,622870,4051054,4
916,KBN,10,stock,28,0,1,stock,b6a5,3378388759,30184504168737,30184625955983,3356601513,1928,3378,121664554,89784,4266,1,248471,3755593,3
916,KBN,10,stock,29,0,0,stock,c4c5,1928079564,30184626382490,30184889940621,1764521433,1928,3356,263306951,88261,4417,1,636662,5490171,8
916,KBN,10,stock,30,0,1,stock,a5a6,3356601513,30184890497113,30185096720471,3250378155,1764,3356,205928314,118096,6470,1,800906,5349080,4
916,KBN,10,stock,31,0,0,stock,e6d8,1764521433,30185097132116,30185384322901,1577330648,1764,3250,286945555,98236,4016,1,610662,2737695,4
916,KBN,10,stock,32,0,1,stock,a6a5,3250378155,30185384758041,30185552718879,3182417317,1577,3250,167751130,98346,5378,1,618815,3117030,4
916,KBN,10,stock,33,0,0,stock,d8b7,1577330648,30185553250994,30185834240114,1396341528,1577,3182,277009133,114141,6029,1,837618,2586028,5
916,KBN,10,stock,34,0,1,stock,a5a6,3182417317,30185834761542,30185970313232,3146865627,1396,3182,135149302,102613,0,1,852903,5302712,6
916,KBN,10,stock,35,0,0,stock,c5c6,1396341528,30185970949322,30186101156809,1366134041,1396,3146,129884055,123895,0,1,923108,5049433,6
916,KBN,10,stock,36,0,1,stock,a6a7,3146865627,30186101756685,30186199074775,3149547537,1366,3146,97033466,112127,6069,1,857660,6095644,11
916,KBN,10,stock,37,0,0,stock,b7c5,1366134041,30186199481062,30186318552119,1347062984,1366,3149,118748467,96734,0,1,707446,4480274,13
916,KBN,10,stock,38,0,1,stock,a7b8,3149547537,30186319735166,30186420362680,3148920023,1347,3149,99739873,99869,5298,1,1558978,4621666,24
916,KBN,10,stock,39,0,0,stock,c6b6,1347062984,30186420781967,30186543132598,1324712353,1347,3148,122001777,99599,0,1,749908,3219494,30
916,KBN,10,stock,40,0,1,stock,b8a8,3148920023,30186543550221,30186553017712,3239452532,1324,3148,9322840,97846,4346,1,539995,4300556,10
916,KBN,10,stock,41,0,0,stock,d7h3,1324712353,30186553695845,30186558657426,1419750772,1324,3239,4846200,90625,0,1,782798,4747904,2
916,KBN,10,stock,42,0,1,stock,a8b8,3239452532,30186558983233,30186559413115,3339022650,1419,3239,374398,92588,4647,2,365225,252577,1
916,KBN,10,stock,43,0,0,stock,c5a6,1419750772,30186559565983,30186560101043,1519215712,1419,3339,361187,74231,0,1,359298,74231,66
916,KBN,10,stock,44,0,1,stock,b8a8,3339022650,30186560227431,30186560468231,3438781850,1519,3339,196933,134961,0,1,135693,196933,1
916,KBN,10,stock,45,0,0,stock,h3g2,1519215712,30186560589081,30186561042659,1618762134,1519,3438,303796,68042,0,2,305433,53991,66
916,KBN,10,table,0,0,1,stock,e2d3,10000000000,30206018606204,30206272032863,9846573341,10000,10000,252735629,168752,5828766,2,1198507,4966199,11
916,KBN,10,table,1,0,0,table,h5g4,10000000000,30206272718158,30206280180786,10092537372,10000,9846,7424366,8126894,41983,1,8126894,41983,1
916,KBN,10,table,2,0,1,stock,d3e4,9846573341,30206280511340,30206780806911,9446277770,10092,9846,498636237,131627,0,1,1022016,7485859,13
916,KBN,10,table,3,0,0,table,h6f5,10092537372,30206781215492,30206787863342,10185889522,10092,9446,6651043,7188484,34151,1,7188484,34151,1
916,KBN,10,table,4,0,1,stock,e4e5,9446277770,30206788240496,30207156123700,9178394566,10185,9446,355764744,91797,0,1,1136846,7760468,7
916,KBN,10,table,5,0,0,table,g8a2,10185889522,30207158316108,30207165690144,10278515486,10185,9178,7350646,9557959,27772,1,9557959,27772,1
916,KBN,10,table,6,0,1,stock,e5e4,9178394566,30207165884765,30207558179039,8886100292,10278,9178,384029755,89864,0,1,772862,6126830,15
916,KBN,10,table,7,0,0,table,a2c4,10278515486,30207558745807,30207567012668,10370248625,10278,8886,8238601,8847619,31017,1,8847619,31017,1
916,KBN,10,table,8,0,1,stock,e4e5,8886100292,30207567246758,30207831752016,8721595034,10370,8886,260627428,96043,4708565,2,449900,4752140,4
916,KBN,10,table,9,0,0,table,g4g5,10370248625,30207832416370,30207840587597,10462077398,10370,8721,8145814,8542686,27841,1,8542686,27841,1
916,KBN,10,table,10,0,1,stock,e5e4,8721595034,30207840773986,30208074351540,8588017480,10462,8721,229594368,76134,0,1,498463,7224819,7
916,KBN,10,table,11,0,0,table,g5f6,10462077398,30208074796045,30208082140938,10554732505,10462,8588,7319791,7774529,27040,1,7774529,27040,1
916,KBN,10,table,12,0,1,stock,e4f3,8588017480,30208082396380,30208418683614,8351730246,10554,8588,335825751,153228,0,1,702929,5530651,13
916,KBN,10,table,13,0,0,table,f6e5,10554732505,30208419197182,30208427096714,10646832973,10554,8351,7873076,8397268,29734,1,8397268,29734,1
916,KBN,10,table,14,0,1,stock,f3g4,8351730246,30208427350273,30208855517319,8023563200,10646,8351,423989606,85818,4615416,2,744530,4701234,8
916,KBN,10,table,15,0,0,table,c4d3,10646832973,30208856241072,30208867531754,10735542291,10646,8023,11266178,11490603,27992,1,11490603,27992,1
916,KBN,10,table,16,0,1,stock,g4h5,8023563200,30208867764212,30209091207933,7900119479,10735,8023,223130313,92558,0,1,531453,4232184,8
916,KBN,10,table,17,0,0,table,f5e3,10735542291,30209091561762,30209099004902,10828099151,10735,7900,7423315,7787688,21873,1,7787688,21873,1
916,KBN,10,table,18,0,1,stock,h5g5,7900119479,30209099199222,30209323158195,7776160506,10828,7900,216983920,79058,4726321,2,417074,4805379,7
916,KBN,10,table,19,0,0,table,d3b1,10828099151,30209323701107,30209332779861,10919020397,10828,7776,9054369,9607694,27911,1,9607694,27911,1
916,KBN,10,table,20,0,1,stock,g5h6,7776160506,30209333045729,30209536769506,7672436729,10919,7776,199721483,104686,2854589,2,604502,6952182,8
916,KBN,10,table,21,0,0,table,e5f6,10919020397,30209537436768,30209544937240,11011519925,10919,7672,7478296,8155407,24447,1,8155407,24447,1
916,KBN,10,table,22,0,1,stock,h6h5,7672436729,30209545131806,30211660636322,5656932213,11011,7672,2073612415,99799,0,1,320440,2867908,6
916,KBN,10,table,23,0,0,table,b1c2,11011519925,30211661084983,30211667242232,11105362676,11011,5656,6133491,6676952,26319,1,6676952,26319,1
916,KBN,10,table,24,0,1,stock,h5h4,5656932213,30211667414159,30211821447601,5602898771,11105,5656,150185504,78207,0,1,378196,4584279,10
916,KBN,10,table,25,0,0,table,c2d1,11105362676,30211821834860,30211828199249,11198998287,11105,5602,6344985,6741176,20922,1,6741176,20922,1
916,KBN,10,table,26,0,1,stock,h4g3,5602898771,30211828351196,30212096660906,5434589061,11198,5602,267471217,72648,0,1,509299,3651878,8
916,KBN,10,table,27,0,0,table,f6e5,11198998287,30212097275255,30212107583713,11288689829,11198,5434,10281280,10908285,29904,1,10908285,29904,1
916,KBN,10,table,28,0,1,stock,g3f2,5434589061,30212107836541,30212337835972,5304589630,11288,5434,223831260,98697,4099166,2,542248,6177456,9
916,KBN,10,table,29,0,0,table,e3c2,11288689829,30212338246987,30212342818084,11384118732,11288,5304,4550429,4972889,22764,1,4972889,22764,1
916,KBN,10,table,30,0,1,stock,f2g3,5304589630,30212342971874,30212507190167,5240371337,11384,5304,164075178,78638,0,1,282982,5028653,4
916,KBN,10,table,31,0,0,table,e5e4,11384118732,30212507572519,30212512742862,11478948389,11384,5240,5161581,5555028,25438,1,5555028,25438,1
916,KBN,10,table,32,0,1,stock,g3h4,5240371337,30212512936992,30212853693687,4999614642,11478,5240,336694440,78357,0,1,376212,3065914,7
916,KBN,10,table,33,0,0,table,e4f4,11478948389,30212854274075,30212862784874,11570437590,11478,4999,8485209,9078524,28673,1,9078524,28673,1
916,KBN,10,table,34,0,1,stock,h4h3,4999614642,30212863053676,30213072512918,4890155400,11570,4999,201045279,102944,0,1,459916,4944327,4
916,KBN,10,table,35,0,0,table,c2e3,11570437590,30213073008870,30213077467328,11665979132,11570,4890,4436017,4942393,25148,1,4942393,25148,1
916,KBN,10,table,36,0,1,stock,h3h4,4890155400,30213077617873,30213300607411,4767165862,11665,4890,203808566,82012,2340252,2,498274,2382294,5
916,KBN,10,table,37,0,0,table,d1e2,11665979132,30213302113584,30213307823194,11760269522,11665,4767,5685543,7202746,27351,1,7202746,27351,1
916,KBN,10,table,38,0,1,stock,h4h3,4767165862,30213308111966,30213490741462,4684536366,11760,4767,182379771,86018,0,1,299136,3885797,5
916,KBN,10,table,39,0,0,table,e2g4,11760269522,30213491238706,30213497690566,11853817662,11760,4684,6424786,6933234,29834,1,6933234,29834,1
916,KBN,10,table,40,0,1,stock,h3h2,4684536366,30213498053239,30213631225726,4651363879,11853,4684,132821019,92288,5898560,2,684561,5943838,7
916,KBN,10,table,41,0,0,table,f4f3,11853817662,30213631646065,30213638002027,11947461700,11853,4651,6326184,6757327,32579,1,6757327,32579,1
916,KBN,10,table,42,0,1,stock,h2g1,4651363879,30213638233873,30213769576605,4620021147,11947,4651,129396212,82894,0,1,635495,7294784,33
916,KBN,10,table,43,0,0,table,f3g3,11947461700,30213770003964,30213774936692,12042528972,11947,4620,4913741,5351454,21953,1,5351454,21953,1
916,KBN,10,table,44,0,1,stock,g1h1,4620021147,30213775131713,30213780234226,4714918634,12042,4620,5025698,91216,4781584,2,264484,4872800,3
916,KBN,10,table,45,0,0,table,g3f2,12042528972,30213780445602,30213788371797,12134602777,12042,4714,7907968,8124051,19549,1,8124051,19549,1
916,KBN,10,table,46,0,1,stock,h1h2,4714918634,30213788533999,30213789171683,4814280950,12134,4714,577041,129754,0,1,174380,577041,1
916,KBN,10,table,47,0,0,table,e3f1,12134602777,30213789306074,30213794351841,12229557010,12134,4814,5046869,5228400,0,0,5228400,0,0
916,KBN,10,table,48,0,1,stock,h2h1,4814280950,30213794467194,30213794642606,4914105538,12229,4814,128822,69403,59419,2,123324,128822,1
916,KBN,10,table,49,0,0,table,g4f3,12229557010,30213794736937,30213797309175,12326984772,12229,4914,2573580,2705557,0,0,2705557,0,0
1330,KBN,10,corner,0,2,0,stock,e8d7,10000000000,30193356962749,30193607843287,9849119462,10000,10000,197227054,178937,0,1,1003117,40227085,15
1330,KBN,10,corner,1,2,1,corner,c8b6,10000000000,30193608334570,30194124927120,9583407450,9849,10000,368727311,174771,5648,1,698359,6938212,14
1330,KBN,10,corner,2,2,0,stock,d7c6,9849119462,30194125384433,30194929487711,9145016184,9849,9583,727305959,104767,5287,1,631924,2477806,6
1330,KBN,10,corner,3,2,1,corner,b6a4,9583407450,30194929875660,30195178080987,9435202123,9145,9583,247949732,82633,4657,1,614767,2012973,6
1330,KBN,10,corner,4,2,0,stock,c6d6,9145016184,30195178609927,30195594299162,8829326949,9145,9435,375443227,111587,32539,1,673504,5216082,3
1330,KBN,10,corner,5,2,1,corner,f6f5,9435202123,30195594627743,30196392073656,8737756210,8829,9435,750669225,97065,4176,1,632256,0,23
1330,KBN,10,corner,6,2,0,stock,d6e7,8829326949,30196392533333,30196707137162,8614723120,8829,8737,302519635,137595,5308,1,859844,3298591,9
1330,KBN,10,corner,7,2,1,corner,f5g6,8737756210,30196707543949,30197811453687,7733846472,8614,8737,1099889589,114751,3746,1,726783,4356169,7
1330,KBN,10,corner,8,2,0,stock,e7d7,8614723120,30197811858812,30198157100277,8369481655,8614,7733,344719704,216202,4677,1,781596,3895321,9
1330,KBN,10,corner,9,2,1,corner,g6f7,7733846472,30198157486484,30198487358654,7503974302,8369,7733,329497482,89554,4216,1,672331,2373031,9
1330,KBN,10,corner,10,2,0,stock,d7d6,8369481655,30198487849557,30199091054664,7866276548,8369,7503,590832208,91948,5768,1,815417,4028540,7
1330,KBN,10,corner,11,2,1,corner,f7f6,7503974302,30199091584085,30201166815433,5528742954,7866,7503,2067475357,142482,0,1,728558,4364871,5
1330,KBN,10,corner,12,2,0,stock,d6d7,7866276548,30201167410893,30201826113676,7307573765,7866,5528,654700612,113379,7742,1,937860,4436018,8
1330,KBN,10,corner,13,2,1,corner,f6e5,5528742954,30201826699401,30202107175140,5348267215,7307,5528,279959556,115442,6309,1,922379,5166808,11
1330,KBN,10,corner,14,2,0,stock,d7e8,7307573765,30202107602409,30204138188470,5376987704,7307,5348,2029837673,95893,23075,1,518935,4250181,2
1330,KBN,10,corner,15,2,1,corner,e5e6,5348267215,30204138776720,30204512605539,5074438396,5376,5348,373504836,115011,7972,1,882516,5055543,5
1330,KBN,10,corner,16,2,0,stock,e8f8,5376987704,30204513203963,30204659487022,5330704645,5376,5074,146052650,123064,8342,1,798460,2633238,4
1330,KBN,10,corner,17,2,1,corner,e6f6,5074438396,30204659923484,30205182103373,4652258507,5330,5074,521722424,122884,0,1,702870,4080548,4
1330,KBN,10,corner,18,2,0,stock,f8e8,5330704645,30205182542921,30205870251504,4742996062,5330,4652,683703156,115732,0,1,662479,5455849,4
1330,KBN,10,corner,19,2,1,corner,a4b6,4652258507,30205870706314,30206720378367,3902586454,4742,4652,849410025,98327,5158,1,688036,5100470,4
1330,KBN,10,corner,20,2,0,stock,e8d8,4742996062,30206721333745,30207163091919,4401237888,4742,3902,437693904,117165,8102,1,1281062,2514341,8
1330,KBN,10,corner,21,2,1,corner,f6e6,3902586454,30207163781170,30207421297028,3745070596,4401,3902,254682907,93019,4407,1,799673,4083583,4
1330,KBN,10,corner,22,2,0,stock,d8e8,4401237888,30207421922503,30207598972966,4324187425,4401,3745,176896466,90545,5778,1,758762,5960773,3
1330,KBN,10,corner,23,2,1,corner,b6d7,3745070596,30207599646273,30207798857661,3645859208,4324,3745,198631533,140270,8011,1,1218417,4156842,7
1330,KBN,10,corner,24,2,0,stock,e8d8,4324187425,30207799425570,30208202540213,4021072782,4324,3645,402842691,104866,5168,1,771391,4440045,4
1330,KBN,10,corner,25,2,1,corner,c4b5,3645859208,30208203238397,30209087434241,2861663364,4021,3645,883811089,118346,6640,1,1020111,4594855,5
1330,KBN,10,corner,26,2,0,stock,d8e8,4021072782,30209087854499,30209256176211,3952751070,4021,2861,168178600,97145,4798,1,543401,4020177,3
1330,KBN,10,corner,27,2,1,corner,b5e2,2861663364,30209256724030,30209808917057,2409470337,3952,2861,551866201,100450,4617,1,797590,3132774,6
1330,KBN,10,corner,28,2,0,stock,e8d8,3952751070,30209809494193,30209949291694,3912953569,3952,2409,139586614,98587,5458,1,742127,2377878,5
1330,KBN,10,corner,29,2,1,corner,e6d6,2409470337,30209949706787,30210108348305,2350828819,3912,2409,158489003,96965,4557,1,522680,2158510,3
1330,KBN,10,corner,30,2,0,stock,d8e8,3912953569,30210108910026,30210358779297,3763084298,3912,2350,242628107,99409,5698,1,860523,2878224,4
1330,KBN,10,corner,31,2,1,corner,e2h5,2350828819,30210359193258,30210738180260,2071841817,3763,2350,378702035,98597,4276,1,602149,4663087,4
1330,KBN,10,corner,32,2,0,stock,e8d8,3763084298,30210738611405,30210946255284,3655440419,3763,2071,203811665,99208,5348,1,586615,5244405,4
1330,KBN,10,corner,33,2,1,corner,d7c5,2071841817,30210947829208,30211085724192,2033946833,3655,2071,137751184,105117,0,1,1690802,4170803,3
1330,KBN,10,corner,34,2,0,stock,d8c8,3655440419,30211086317149,30211256919943,3584837625,3655,2033,170435127,190565,0,1,739423,5679584,4
1330,KBN,10,corner,35,2,1,corner,h5e2,2033946833,30211257271519,30211402920781,1988297571,3584,2033,145507616,90585,3916,1,472725,2620720,4
1330,KBN,10,corner,36,2,0,stock,c8d8,3584837625,30211403332597,30211553027369,3535142853,3584,1988,149511610,100059,4286,1,574327,4536168,4
1330,KBN,10,corner,37,2,1,corner,c5e6,1988297571,30211553530301,30211773741222,1868086650,3535,1988,219957100,96033,5027,1,736278,2330757,5
1330,KBN,10,corner,38,2,0,stock,d8c8,3535142853,30211774159387,30211910665825,3498636415,3535,1868,136290366,100750,4507,1,606194,5714335,8
1330,KBN,10,corner,39,2,1,corner,e2a6,1868086650,30211911088256,30212154601780,1724573126,3498,1868,239420411,94511,4427,1,645762,4773301,5
1330,KBN,10,corner,40,2,0,stock,c8b8,3498636415,30212155037532,30212278150537,3475523410,3498,1724,122740939,103084,4207,1,784631,4830036,9
1330,KBN,10,corner,41,2,1,corner,d6c6,1724573126,30212278572748,30212409969196,1693176678,3475,1724,130882846,103193,3466,1,812454,5281800,11
1330,KBN,10,corner,42,2,0,stock,b8a7,3475523410,30212410400201,30212516387437,3469536174,3475,1693,105593984,104577,5368,1,902381,5463411,42
1330,KBN,10,corner,43,2,1,corner,e6c5,1693176678,30212517006393,30212644715249,1665467822,3469,1693,127305787,96043,4857,1,1000145,2855781,39
1330,KBN,10,corner,44,2,0,stock,a7b8,3469536174,30212645149158,30212649319605,3565365727,3469,1665,4056853,167760,4086,1,533425,2651546,4
1330,KBN,10,corner,45,2,1,corner,c6b6,1665467822,30212649589709,30212657893560,1757163971,3565,1665,8155567,80640,2694,1,402471,2310758,27
1330,KBN,10,corner,46,2,0,stock,b8a8,3565365727,30212658154210,30212658525806,3664994131,3565,1757,324514,78928,2093,1,279627,232707,1
1330,KBN,10,corner,47,2,1,corner,a6b7,1757163971,30212658635460,30212659127466,1856671965,3664,1757,349385,75854,0,2,283319,61172,66
1330,KBN,10,corner,48,2,0,stock,a8b8,3664994131,30212659327765,30212659495546,3764826350,3664,1856,128852,71527,0,1,208772,128852,1
1330,KBN,10,corner,49,2,1,corner,c5d7,1856671965,30212659595566,30212660341301,1955926230,3764,1856,463694,70045,0,2,411562,57646,66
1330,KBN,10,stock,0,2,0,stock,e8d7,10000000000,30167312254039,30167614791826,9797462213,10000,10000,294726739,190434,3607052,2,724221,3332712,14
1330,KBN,10,stock,1,2,1,stock,c8b6,10000000000,30167615223290,30168069754533,9645468757,9797,10000,453967035,159387,4643849,2,949619,4389288,12
1330,KBN,10,stock,2,2,0,stock,d7c6,9797462213,30168070154180,30168878306075,9089310318,9797,9645,796657879,95482,4146,1,647005,5698903,5
1330,KBN,10,stock,3,2,1,stock,b6a4,9645468757,30168878820183,30169317541358,9306747582,9089,9645,438096727,96775,5608,1,1114512,5011197,5
1330,KBN,10,stock,4,2,0,stock,c6d6,9089310318,30169319052385,30170929905087,7578457616,9089,9306,1606854310,98987,5769,1,1798364,0,21
1330,KBN,10,stock,5,2,1,stock,f6f5,9306747582,30170930344714,30171276433403,9060658893,7578,9306,345839725,99328,4487,1,667858,5513226,6
1330,KBN,10,stock,6,2,0,stock,d6e7,7578457616,30171277007991,30172161780412,6793685195,7578,9060,884581405,111316,6079,1,728718,2847818,3
1330,KBN,10,stock,7,2,1,stock,f5e5,9060658893,30172162175492,30172622527023,8700307362,6793,9060,452873378,92838,4417,1,541548,5697690,4
1330,KBN,10,stock,8,2,0,stock,e7d7,6793685195,30172623075262,30172989989103,6526771354,6793,8700,366579889,110976,7000,1,848375,4788535,5
1330,KBN,10,stock,9,2,1,stock,c4d5,8700307362,30172990539616,30174232227100,7558619878,6526,8700,1237470905,111316,6690,1,886802,5272136,7
1330,KBN,10,stock,10,2,0,stock,d7e7,6526771354,30174232582901,30174473395257,6385958998,6526,7558,233064822,90525,4487,1,505305,3279313,4
1330,KBN,10,stock,11,2,1,stock,a4b6,7558619878,30174473863576,30175587338082,6545145372,6385,7558,1104958581,95292,4096,1,830087,6816159,12
1330,KBN,10,stock,12,2,0,stock,e7f8,6385958998,30175587908464,30176194271219,5879596243,6385,6545,606084499,144175,7311,1,777048,3918507,4
1330,KBN,10,stock,13,2,1,stock,e5f6,6545145372,30176194653160,30176933105228,5906693304,5879,6545,727170552,181010,3705,1,592815,5123374,5
1330,KBN,10,stock,14,2,0,stock,f8e8,5879596243,30176933643722,30177092064171,5821175794,5879,5906,154567234,140470,0,1,710399,2358910,3
1330,KBN,10,stock,15,2,1,stock,f6e5,5906693304,30177092620572,30177691848363,5407465513,5821,5906,595268164,144085,0,1,977069,7232610,6
1330,KBN,10,stock,16,2,0,stock,e8e7,5821175794,30177692442891,30178145769658,5467849027,5821,5407,449210198,123084,0,1,750438,3559481,6
1330,KBN,10,stock,17,2,1,stock,d5e6,5407465513,30178146298949,30179276355227,4377409235,5467,5407,1126086664,115282,0,1,735589,5700414,4
1330,KBN,10,stock,18,2,0,stock,e7f8,5467849027,30179276933801,30179689180385,5155602443,5467,4377,411986037,121080,0,1,805623,3068227,4
1330,KBN,10,stock,19,2,1,stock,e5f6,4377409235,30179689745349,30180458526256,3708628328,5155,4377,764295282,96714,4687,1,773025,2118020,5
1330,KBN,10,stock,20,2,0,stock,f8e8,5155602443,30180459068866,30180968600539,4746070770,5155,3708,497816800,126529,0,1,737271,4931828,5
1330,KBN,10,stock,21,2,1,stock,e6d5,3708628328,30180969108708,30181521768783,3255968253,4746,3708,548750835,114290,0,1,743129,2886256,5
1330,KBN,10,stock,22,2,0,stock,e8d8,4746070770,30181522163583,30181745733126,4622501227,4746,3255,223298713,101010,0,1,639956,5861354,6
1330,KBN,10,stock,23,2,1,stock,f6e6,3255968253,30181746145852,30182186852680,2915261425,4622,3255,440498910,104175,4988,1,585815,5699903,4
1330,KBN,10,stock,24,2,0,stock,d8e8,4622501227,30182187337724,30182450851078,4458987873,4622,2915,263244169,99648,5729,1,711642,4531230,6
1330,KBN,10,stock,25,2,1,stock,b6d7,2915261425,30182451252678,30182624505496,2842008607,4458,2915,173032111,96824,3776,1,598232,4608616,6
1330,KBN,10,stock,26,2,0,stock,e8d8,4458987873,30182625005492,30182878588274,4305405091,4458,2842,253370608,98487,5298,1,681117,2865265,4
1330,KBN,10,stock,27,2,1,stock,d5c6,2842008607,30182878962403,30183894336137,1926634873,4305,2842,1015031630,98106,4296,1,575357,4897707,5
1330,KBN,10,stock,28,2,0,stock,d8c7,4305405091,30183894851667,30184146312990,4153943768,4305,1926,251243956,98657,4908,1,706374,5018637,4
1330,KBN,10,stock,29,2,1,stock,c6b5,1926634873,30184146907017,30184526957826,1646584064,4153,1926,375791563,116454,6159,1,804760,4919329,5
1330,KBN,10,stock,30,2,0,stock,c7d8,4153943768,30184527360578,30184834906626,3946397720,4153,1646,303701385,99458,3916,1,566824,4512302,4
1330,KBN,10,stock,31,2,1,stock,d7b6,1646584064,30184835473212,30185044232093,1537825183,3946,1646,208565314,118928,6209,1,731102,4355488,4
1330,KBN,10,stock,32,2,0,stock,d8c7,3946397720,30185044775404,30185267622408,3823550716,3946,1537,222567452,104395,6109,1,703671,3087516,4
1330,KBN,10,stock,33,2,1,stock,b6a4,1537825183,30185268032380,30185741824170,1164033393,3823,1537,469814002,101932,4086,1,256524,3820330,5
1330,KBN,10,stock,34,2,0,stock,c7d8,3823550716,30185742357086,30185915847393,3750060409,3823,1164,173280612,117676,0,1,882607,5640235,4
1330,KBN,10,stock,35,2,1,stock,e6d6,1164033393,30185916336213,30186047226119,1133143487,3750,1164,130683911,101201,5157,1,496070,3517718,5
1330,KBN,10,stock,36,2,0,stock,d8c8,3750060409,30186047771854,30186177505603,3720326660,3750,1133,125945231,160850,5257,1,656328,4038485,3
1330,KBN,10,stock,37,2,1,stock,a4c5,1133143487,30186178032721,30186424392560,986783648,3720,1133,242419681,109964,6220,1,708728,5809387,4
1330,KBN,10,stock,38,2,0,stock,c8d8,3720326660,30186424892166,30186571135325,3674083501,3720,986,146068564,98638,4817,1,646574,2987497,4
1330,KBN,10,stock,39,2,1,stock,b5a4,986783648,30186571855211,30186684907082,973731777,3674,986,112867751,95612,5268,1,876417,3975751,4
1330,KBN,10,stock,40,2,0,stock,d8c8,3674083501,30186685572937,30186832949128,3626707310,3674,973,147088142,178906,8183,1,932904,2204218,7
1330,KBN,10,stock,41,2,1,stock,a4d7,973731777,30186833360111,30187003838760,903253128,3626,973,166629249,101672,4547,1,821325,2496695,6
1330,KBN,10,stock,42,2,0,stock,c8b8,3626707310,30187004274121,30187139390264,3591591167,3626,903,134758925,100480,4857,1,522669,3599721,8
1330,KBN,10,stock,43,2,1,stock,d6c6,903253128,30187139962869,30187260283438,882932559,3591,903,120003668,144385,6410,1,866512,3841120,7
1330,KBN,10,stock,44,2,0,stock,b8a7,3591591167,30187260846609,30187370157654,3582280122,3591,882,108958514,121642,6409,1,895840,2995399,34
1330,KBN,10,stock,45,2,1,stock,c6c7,882932559,30187370563911,30187468515894,884980576,3582,882,95248719,120059,3816,1,701737,7271268,29
1330,KBN,10,stock,46,2,0,stock,a7a8,3582280122,30187469072685,30187475650520,3675702287,3582,884,6410041,120510,5899,1,712466,2770243,12
1330,KBN,10,stock,47,2,1,stock,c7b6,884980576,30187475960303,30187486203643,974737236,3675,884,9955585,117556,3515,1,586382,0,65
1330,KBN,10,stock,48,2,0,stock,a8b8,3675702287,30187486466646,30187487047674,3775121259,3675,974,507156,92568,4206,1,286237,400998,1
1330,KBN,10,stock,49,2,1,stock,c5a6,974737236,30187487211498,30187487935570,1074013164,3775,974,527149,86880,2774,2,413094,0,65
1330,KBN,10,stock,50,2,0,stock,b8a8,3775121259,30187488130451,30187488355417,3874896293,3775,1074,161491,83404,0,1,120780,161491,1
1330,KBN,10,stock,51,2,1,stock,d7c6,1074013164,30187488494435,30187489124155,1173383444,3874,1074,411373,85136,0,2,409572,65297,66
1330,KBN,10,table,0,2,0,stock,e8d7,10000000000,30187547279991,30187842120094,9805159897,10000,10000,294083160,159438,5137685,2,1253821,4318874,14
1330,KBN,10,table,1,2,1,table,c4e6,10000000000,30187843212666,30187847440491,10095772175,9805,10000,4229971,5332506,86919,1,5332506,86919,1
1330,KBN,10,table,2,2,0,stock,d7c6,9805159897,30187847701991,30188524327265,9228534623,9805,10095,675658431,80400,4223231,2,582599,4303631,12
1330,KBN,10,table,3,2,1,table,f6e5,10095772175,30188525410192,30188530635777,10190546590,9228,10095,5210944,6302553,16575,1,6302553,16575,1
1330,KBN,10,table,4,2,0,stock,c6b5,9228534623,30188530804199,30190264754829,7594583993,9228,10190,1725869436,74551,0,1,450201,5198335,7
1330,KBN,10,table,5,2,1,table,e5d4,10190546590,30190265168817,30190271988684,10283726723,7594,10190,6793755,7273701,28603,1,7273701,28603,1
1330,KBN,10,table,6,2,0,stock,b5c6,7594583993,30190272262503,30190639162449,7327684047,7594,10283,362888411,84636,0,1,569530,3762903,7
1330,KBN,10,table,7,2,1,table,d4c4,10283726723,30190639735595,30190645297172,10378165146,7327,10283,5536300,6119881,26960,1,6119881,26960,1
1330,KBN,10,table,8,2,0,stock,c6c7,7327684047,30190645542459,30190862602724,7210623782,7327,10378,216715213,84596,2404167,2,571823,2475133,14
1330,KBN,10,table,9,2,1,table,c4d5,10378165146,30190863015331,30190867849081,10473331396,7210,10378,4836226,5258315,0,0,5258315,0,0
1330,KBN,10,table,10,2,0,stock,c7d8,7210623782,30190868089530,30191121756780,7056956532,7210,10473,253390585,84817,0,1,337022,3908631,11
1330,KBN,10,table,11,2,1,table,c8b6,10473331396,30191122211188,30191126345223,10569197361,7056,10473,4136211,4603688,21903,1,4603688,21903,1
1330,KBN,10,table,12,2,0,stock,d8c7,7056956532,30191126554366,30191439248872,6844262026,7056,10569,308598762,82803,5668627,2,607655,5449700,7
1330,KBN,10,table,13,2,1,table,d5c5,10569197361,30191439637673,30191442857432,10665977602,6844,10569,3221346,3620932,23094,1,3620932,23094,1
1330,KBN,10,table,14,2,0,stock,c7b7,6844262026,30191443028167,30191971833882,6415456311,6844,10665,528637620,75473,0,1,483252,4972769,4
1330,KBN,10,table,15,2,1,table,b6d5,10665977602,30191972263614,30191979880421,10758360795,6415,10665,7595072,7846888,24416,1,7846888,24416,1
1330,KBN,10,table,16,2,0,stock,b7a6,6415456311,30191980091126,30192189598740,6305948697,6415,10758,209322844,85648,0,1,211095,3936243,3
1330,KBN,10,table,17,2,1,table,c5b4,10758360795,30192190016594,30192197979007,10850398382,6305,10758,7966055,8437158,0,0,8437158,0,0
1330,KBN,10,table,18,2,0,stock,a6a7,6305948697,30192198241780,30192484310592,6119879885,6305,10850,278442062,96975,0,1,415049,5756949,4
1330,KBN,10,table,19,2,1,table,e6c8,10850398382,30192484793984,30192493622050,10941570316,6119,10850,8806579,9299004,24326,1,9299004,24326,1
1330,KBN,10,table,20,2,0,stock,a7b8,6119879885,30192493843831,30192759458867,5954264849,6119,10941,261694926,95693,0,1,474286,6157918,7
1330,KBN,10,table,21,2,1,table,c8a6,10941570316,30192759961447,30192763566082,11037965681,5954,10941,3606711,4120217,24387,1,4120217,24387,1
1330,KBN,10,table,22,2,0,stock,b8a7,5954264849,30192763798218,30192933350693,5884712374,5954,11037,165412254,89022,4122371,2,625722,4211393,10
1330,KBN,10,table,23,2,1,table,b4a5,11037965681,30192933923899,30192939085709,11132803871,5884,11037,5140039,5722638,23825,1,5722638,23825,1
1330,KBN,10,table,24,2,0,stock,a7b8,5884712374,30192939255192,30193096784439,5827183127,5884,11132,156985019,82953,0,1,702179,4746030,26
1330,KBN,10,table,25,2,1,table,a5b6,11132803871,30193097175663,30193103970532,11226009002,5827,11132,6773566,7209606,24426,1,7209606,24426,1
1330,KBN,10,table,26,2,0,stock,b8a8,5827183127,30193104210491,30193112537018,5918856600,5827,11226,8213243,87010,0,1,308912,3788652,14
1330,KBN,10,table,27,2,1,table,d5b4,11226009002,30193112802645,30193118046748,11320764899,5918,11226,5229071,5500516,16424,1,5500516,16424,1
1330,KBN,10,table,28,2,0,stock,a8b8,5918856600,30193118190132,30193118687655,6018359077,5918,11320,419136,77105,0,1,154681,419136,1
1330,KBN,10,table,29,2,1,table,b4c6,11320764899,30193118824630,30193123089109,11416500420,6018,11320,4265614,4468526,0,0,4468526,0,0
1330,KBN,10,table,30,2,0,stock,b8a8,6018359077,30193123204882,30193123382347,6118181612,6018,11416,131646,72828,58818,2,124536,131646,1
1330,KBN,10,table,31,2,1,table,a6b7,11416500420,30193123477860,30193125525078,11514453202,6118,11416,2047915,2179472,0,0,2179472,0,0
1760,KBN,10,corner,0,0,1,stock,c7d6,10000000000,30213939418385,30214251839919,9787578466,10000,10000,311851698,378455,4670538,2,796709,4041059,12
1760,KBN,10,corner,1,0,0,corner,a7b8,10000000000,30214252236181,30214580513810,9771722371,10000,9787,327191443,126328,3896,1,611133,3437018,14
1760,KBN,10,corner,2,0,1,stock,d6e6,9787578466,30214580925045,30214873439704,9595063807,9771,9787,292126311,74031,4697,1,762006,3044753,14
1760,KBN,10,corner,3,0,0,corner,b5c6,9771722371,30214873869697,30215187622631,9557969437,9771,9595,313407361,79369,3976,1,668226,6008865,7
1760,KBN,10,corner,4,0,1,stock,e6e7,9595063807,30215188146385,30215765399940,9117810252,9557,9595,572909894,75002,4977,1,670582,3746329,11
1760,KBN,10,corner,5,0,0,corner,a6c5,9557969437,30215765974639,30216363235797,9060708279,9557,9117,596616350,89453,5949,1,1112912,5886532,10
1760,KBN,10,corner,6,0,1,stock,e7d8,9117810252,30216363613512,30216596587444,8984836320,9060,9117,232657938,73900,4417,1,667165,4280236,5
1760,KBN,10,corner,7,0,0,corner,b8c7,9060708279,30216596989285,30217096399940,8661297624,9060,8984,495377587,76895,4336,1,697960,2895850,8
1760,KBN,10,corner,8,0,1,stock,d8c8,8984836320,30217096832247,30217468611945,8713056622,8661,8984,369305015,79188,5057,1,765200,2959015,5
1760,KBN,10,corner,9,0,0,corner,c7d6,8661297624,30217469058573,30217865183285,8365172912,8661,8713,395759363,77145,4096,1,777841,2825105,8
1760,KBN,10,corner,10,0,1,stock,c8d8,8713056622,30217865584746,30218207053349,8471588019,8365,8713,337431753,78047,4887,1,722166,2309075,10
1760,KBN,10,corner,11,0,0,corner,c5e6,8365172912,30218207455000,30218926351913,7746275999,8365,8471,714431297,78717,0,1,691210,4501556,7
1760,KBN,10,corner,12,0,1,stock,d8e8,8471588019,30218926887955,30219270443880,8228032094,7746,8471,343065437,87591,6910,1,955466,4988873,10
1760,KBN,10,corner,13,0,0,corner,e6f4,7746275999,30219270876117,30219631407243,7485744873,7746,8228,354712819,80039,0,1,692843,6852583,12
1760,KBN,10,corner,14,0,1,stock,e8f7,8228032094,30219631912549,30219948476609,8011468034,7485,8228,316130658,116474,6840,1,900684,3938095,12
1760,KBN,10,corner,15,0,0,corner,d6e5,7485744873,30219948911920,30222019243427,5515413366,7485,8011,2058503372,81833,0,1,561146,3095559,6
1760,KBN,10,corner,16,0,1,stock,f7e7,8011468034,30222019716214,30222272959022,7858225226,5515,8011,249227734,113159,0,1,806042,4291423,10
1760,KBN,10,corner,17,0,0,corner,c6c7,5515413366,30222273355726,30223559135311,4329633781,5515,7858,1284445104,76734,0,1,595229,2600079,7
1760,KBN,10,corner,18,0,1,stock,e7f7,7858225226,30223559517223,30225714853588,5802888861,4329,7858,2154628543,72739,5218,1,532903,4379104,8
1760,KBN,10,corner,19,0,0,corner,c7d7,4329633781,30225715406203,30226167586708,3977453276,4329,5802,451605411,98798,0,1,948013,4592081,8
1760,KBN,10,corner,20,0,1,stock,f7f8,5802888861,30226168054407,30226566928060,5504015208,3977,5802,394326610,79519,5038,1,319236,3835862,8
1760,KBN,10,corner,21,0,0,corner,e5f6,3977453276,30226567329730,30227059303506,3585479500,3977,5504,491619284,79318,0,1,601498,4623948,5
1760,KBN,10,corner,22,0,1,stock,f8f7,5504015208,30227059698786,30227509237271,5154476723,3585,5504,441979564,105728,4527,1,594216,4171403,5
1760,KBN,10,corner,23,0,0,corner,f6e7,3585479500,30227509640393,30227867092946,3328026947,3585,5154,357166548,80821,3965,1,576769,2222696,5
1760,KBN,10,corner,24,0,1,stock,f7g8,5154476723,30227867483609,30228109823333,5012136999,3328,5154,242073783,77616,0,1,604380,4516429,4
1760,KBN,10,corner,25,0,0,corner,d7e8,3328026947,30228110186675,30228424382380,3113831242,3328,5012,305933519,81762,0,1,736799,3892437,5
1760,KBN,10,corner,26,0,1,stock,g8g7,5012136999,30228424788477,30228621604513,4915320963,3113,5012,196530538,77175,4377,1,666635,3105573,6
1760,KBN,10,corner,27,0,0,corner,e7g5,3113831242,30228622172351,30228884844743,2951158850,3113,4915,262188143,98116,0,1,842418,3442786,7
1760,KBN,10,corner,28,0,1,stock,g7g8,4915320963,30228885372952,30229031896628,4868797287,2951,4915,146200339,89914,5989,1,948856,2517405,9
1760,KBN,10,corner,29,0,0,corner,f4e6,2951158850,30229032319741,30229212450920,2871027671,2951,4868,179689498,81932,0,1,662087,3640982,16
1760,KBN,10,corner,30,0,1,stock,g8h7,4868797287,30229213011779,30229345799074,4836009992,2871,4868,132341234,117295,6820,1,985730,2836142,20
1760,KBN,10,corner,31,0,0,corner,e8f7,2871027671,30229346193734,30229524030965,2793190440,2871,4836,177382003,79308,0,1,805770,5763799,15
1760,KBN,10,corner,32,0,1,stock,h7h8,4836009992,30229524438094,30229531003256,4929444830,2793,4836,6362612,81872,58026,1,593827,3389708,14
1760,KBN,10,corner,33,0,0,corner,g5f4,2793190440,30229531284146,30229540354505,2884120081,2793,4929,8969470,62002,3175,1,365326,4628576,7
1760,KBN,10,corner,34,0,1,stock,h8h7,4929444830,30229540586743,30229540996386,5029035187,2884,4929,362632,57476,2613,1,250333,291616,1
1760,KBN,10,corner,35,0,0,corner,e6f8,2884120081,30229541174061,30229541656433,2983637709,2884,5029,337360,55834,2433,2,354712,0,65
1760,KBN,10,corner,36,0,1,stock,h7h8,5029035187,30229541776693,30229541925506,5128886374,2983,5029,107661,50776,0,1,126679,107661,1
1760,KBN,10,corner,37,0,0,corner,f4e5,2983637709,30229542022451,30229542432554,3083227606,2983,5128,267239,44426,0,2,274699,36394,66
1760,KBN,10,stock,0,0,1,stock,c7d6,10000000000,30229642479679,30229953763941,9788715738,10000,10000,310946279,110976,1296564,3,775736,0,19
1760,KBN,10,stock,1,0,0,stock,a7d4,10000000000,30229954144891,30230235677042,9818467849,10000,9788,280813101,128162,4807,1,913975,5542940,11
1760,KBN,10,stock,2,0,1,stock,d6d5,9788715738,30230236053305,30230862590136,9262178907,9818,9788,621987045,80009,4517,1,288413,0,20
1760,KBN,10,stock,3,0,0,stock,d4b2,9818467849,30230863070434,30231128410302,9653127981,9818,9262,261381931,77506,5669,1,751230,0,21
1760,KBN,10,stock,4,0,1,stock,d5d6,9262178907,30231128800776,30231359637386,9131342297,9653,9262,230450974,73239,5148,1,721007,3101006,9
1760,KBN,10,stock,5,0,0,stock,a6b4,9653127981,30231360167028,30231734337785,9378957224,9653,9131,362305719,75723,5759,1,437650,3719950,9
1760,KBN,10,stock,6,0,1,stock,d6c7,9131342297,30231734708600,30232065779964,8900270933,9378,9131,322217885,96394,4066,1,581387,5169302,9
1760,KBN,10,stock,7,0,0,stock,b4a6,9378957224,30232066291870,30232762603476,8782645618,9378,8900,692038788,73600,5188,1,802027,5594456,11
1760,KBN,10,stock,8,0,1,stock,c7d6,8900270933,30232763005818,30233757867209,8005409542,8782,8900,994305931,73099,4267,1,787223,4894041,12
1760,KBN,10,stock,9,0,0,stock,b2a3,8782645618,30233758241789,30234169845154,8471042253,8782,8005,411155781,73720,4187,1,716950,5653234,7
1760,KBN,10,stock,10,0,1,stock,d6e5,8005409542,30234170341797,30234501446147,7774305192,8471,8005,329868051,88692,5739,1,936085,5531503,13
1760,KBN,10,stock,11,0,0,stock,b5c4,8471042253,30234501976880,30235714363061,7358656072,8471,7774,1211970352,87451,6079,1,848294,5893933,8
1760,KBN,10,stock,12,0,1,stock,e5e6,7774305192,30235714779684,30236190313688,7398771188,7358,7774,467453354,76824,4377,1,935086,5113549,10
1760,KBN,10,stock,13,0,0,stock,c4d4,7358656072,30236190677011,30237162420631,6486912452,7358,7398,971401198,163674,4306,1,552084,5123313,8
1760,KBN,10,stock,14,0,1,stock,e6f6,7398771188,30237162838005,30237525561232,7136047961,6486,7398,362502658,74070,4347,1,598191,5056194,6
1760,KBN,10,stock,15,0,0,stock,d4d5,6486912452,30237525973578,30237765373686,6347512344,6486,7136,239227866,72288,4126,1,563200,5915055,5
1760,KBN,10,stock,16,0,1,stock,f6f7,7136047961,30237765809879,30238096952956,6904904884,6347,7136,327216253,81972,0,1,631020,2189787,6
1760,KBN,10,stock,17,0,0,stock,d5e5,6347512344,30238097344281,30238733375703,5811480922,6347,6904,635166740,75663,0,1,654476,2659117,7
1760,KBN,10,stock,18,0,1,stock,f7g6,6904904884,30238733953197,30240674288485,5064569596,5811,6904,1924756834,91967,0,1,826002,6046962,5
1760,KBN,10,stock,19,0,0,stock,a3e7,5811480922,30240674879489,30242365145887,4221214524,5811,5064,1674961108,97085,0,1,949054,5119278,7
1760,KBN,10,stock,20,0,1,stock,g6f7,5064569596,30242365549108,30243066898832,4463219872,4221,5064,698373756,79599,0,1,691931,5455429,7
1760,KBN,10,stock,21,0,0,stock,e7f6,4221214524,30243067394502,30243333396779,4055212247,4221,4463,265778770,93239,0,1,693155,4607804,4
1760,KBN,10,stock,22,0,1,stock,f7e8,4463219872,30243333801603,30244482374516,3414646959,4055,4463,1148202833,76383,0,1,560037,6197195,4
1760,KBN,10,stock,23,0,0,stock,e5e6,4055212247,30244482790598,30245042324471,3595678374,4055,3414,551808583,78597,0,1,750380,5208461,9
1760,KBN,10,stock,24,0,1,stock,e8f8,3414646959,30245042737168,30245224726371,3332657756,3595,3414,181813902,82643,0,1,563020,5214950,4
1760,KBN,10,stock,25,0,0,stock,a6c7,3595678374,30245225158006,30245426698058,3494138322,3595,3332,201400424,78467,4807,1,548178,2722632,3
1760,KBN,10,stock,26,0,1,stock,f8g8,3332657756,30245427036645,30245730785775,3128908626,3494,3332,303535452,71417,0,1,505324,4965078,4
1760,KBN,10,stock,27,0,0,stock,e6f5,3494138322,30245731312352,30245940422476,3385028198,3494,3128,208797870,91577,0,1,797799,4647304,8
1760,KBN,10,stock,28,0,1,stock,g8f7,3128908626,30245941036554,30246153418951,3016526229,3385,3128,212145044,98327,0,1,820645,2964983,4
1760,KBN,10,stock,29,0,0,stock,f5g5,3385028198,30246153836255,30246416847580,3222016873,3385,3016,262270148,81212,0,1,593355,6173010,4
1760,KBN,10,stock,30,0,1,stock,f7f8,3016526229,30246417210013,30246660220425,2873515817,3222,3016,242735472,80390,4476,1,580004,2681461,5
1760,KBN,10,stock,31,0,0,stock,g5g6,3222016873,30246660613723,30246871092904,3111537692,3222,2873,210259569,80870,0,1,571264,3386021,4
1760,KBN,10,stock,32,0,1,stock,f8g8,2873515817,30246871431491,30246986504497,2858442811,3111,2873,114859591,79699,0,1,530422,4569037,5
1760,KBN,10,stock,33,0,0,stock,c7e8,3111537692,30246986915282,30247177633399,3020819575,3111,2858,190439870,81261,0,1,667788,5087590,6
1760,KBN,10,stock,34,0,1,stock,g8f8,2858442811,30247178232756,30247277412814,2859262753,3020,2858,98785963,85798,0,1,967702,5763760,16
1760,KBN,10,stock,35,0,0,stock,e8d6,3020819575,30247277960523,30247410925788,2987854310,3020,2859,128113096,82853,5228,1,1762968,5909517,19
1760,KBN,10,stock,36,0,1,stock,f8g8,2859262753,30247411327178,30247509269660,2861320271,2987,2859,97359329,81892,0,1,860834,4672301,15
1760,KBN,10,stock,37,0,0,stock,f6e7,2987854310,30247509706193,30247687680120,2909880383,2987,2861,177220044,168291,4657,1,912224,2325169,23
1760,KBN,10,stock,38,0,1,stock,g8h8,2861320271,30247688136283,30247692432838,2957023716,2909,2861,4218274,81752,0,1,194790,3862423,4
1760,KBN,10,stock,39,0,0,stock,d6f7,2909880383,30247692660919,30247698173694,3004367608,2909,2957,4979584,67450,2884,2,637376,0,65
1760,KBN,10,stock,40,0,1,stock,h8g8,2957023716,30247698538169,30247699182964,3056378921,3004,2957,562829,71777,0,1,387949,562829,1
1760,KBN,10,stock,41,0,0,stock,f7h6,3004367608,30247699418376,30247699994718,3103791266,3004,3056,503732,66229,0,2,395089,503732,1
1760,KBN,10,stock,42,0,1,stock,g8h8,3056378921,30247700213895,30247700436378,3156156438,3103,3056,150644,64125,0,1,208021,150644,1
1760,KBN,10,stock,43,0,0,stock,e7f6,3103791266,30247700601395,30247701013752,3203378909,3103,3156,349261,59779,0,1,233829,349261,1
1760,KBN,10,table,0,0,1,stock,c7d6,10000000000,30247773304475,30248132914889,9740389586,10000,10000,355518686,128872,3118673,2,928816,2363666,13
1760,KBN,10,table,1,0,0,table,a6c5,10000000000,30248133306895,30248138455775,10094851120,10000,9740,5092408,5494227,58587,1,5494227,58587,1
1760,KBN,10,table,2,0,1,stock,d6e5,9740389586,30248138610326,30248849670989,9129328923,10094,9740,710457866,57375,0,1,440980,5388769,11
1760,KBN,10,table,3,0,0,table,a7b8,10094851120,30248850314862,30248859251747,10185914235,10094,9129,8911486,9566393,28602,1,9566393,28602,1
1760,KBN,10,table,4,0,1,stock,e5d4,9129328923,30248859471045,30249118329370,8970470598,10185,9129,258538758,74512,4463929,2,526197,4538441,10
1760,KBN,10,table,5,0,0,table,b8f4,10185914235,30249118669298,30249124668330,10279915203,10185,8970,5981373,6330284,19209,1,6330284,19209,1
1760,KBN,10,table,6,0,1,stock,d4d5,8970470598,30249124849661,30249367220717,8828099542,10279,8970,238388110,57576,0,1,433937,7151119,8
1760,KBN,10,table,7,0,0,table,b5b6,10279915203,30249367607336,30249374247607,10373274932,10279,8828,6620888,7016278,21482,1,7016278,21482,1
1760,KBN,10,table,8,0,1,stock,d5c4,8828099542,30249374476379,30249709281670,8593294251,10373,8828,323271373,65347,9112536,3,589151,9177102,11
1760,KBN,10,table,9,0,0,table,b6c6,10373274932,30249709844911,30249720480766,10462639077,10373,8593,10607496,11183255,31587,1,11183255,31587,1
1760,KBN,10,table,10,0,1,stock,c4d4,8593294251,30249720789527,30250028152512,8385931266,10462,8593,303478028,83274,0,1,500707,7213342,4
1760,KBN,10,table,11,0,0,table,c6d6,10462639077,30250028557987,30250035694376,10555502688,10462,8385,7113132,7902330,28432,1,7902330,28432,1
1760,KBN,10,table,12,0,1,stock,d4c4,8385931266,30250036479819,30250255402017,8267009068,10555,8385,218582737,67210,0,1,664973,3518339,8
1760,KBN,10,table,13,0,0,table,f4e3,10555502688,30250255926711,30250262902990,10648526409,10555,8267,6949588,7486228,29575,1,7486228,29575,1
1760,KBN,10,table,14,0,1,stock,c4b4,8267009068,30250263056749,30250550144678,8079921139,10648,8267,276877151,66098,4888313,2,414300,5450421,10
1760,KBN,10,table,15,0,0,table,d6d5,10648526409,30250550675621,30250558833465,10740368565,10648,8079,8134095,8677686,26850,1,8677686,26850,1
1760,KBN,10,table,16,0,1,stock,b4c3,8079921139,30250559070028,30250818594271,7920396896,10740,8079,258874314,70545,0,1,590102,4930686,9
1760,KBN,10,table,17,0,0,table,e3d4,10740368565,30250819266705,30250824943203,10834692067,10740,7920,5655578,6338266,22794,1,6338266,22794,1
1760,KBN,10,table,18,0,1,stock,c3d2,7920396896,30250825098064,30251129332566,7716162394,10834,7920,304024182,62914,6875708,2,335941,6903299,9
1760,KBN,10,table,19,0,0,table,d5e4,10834692067,30251129706855,30251136547321,10927851601,10834,7716,6818292,7203056,24096,1,7203056,24096,1
1760,KBN,10,table,20,0,1,stock,d2c2,7716162394,30251136723034,30251365592709,7587292719,10927,7716,228672302,79178,0,1,353847,3287625,5
1760,KBN,10,table,21,0,0,table,e4e3,10927851601,30251365988380,30251371386782,11022453199,10927,7587,5373437,5780004,27531,1,5780004,27531,1
1760,KBN,10,table,22,0,1,stock,c2d1,7587292719,30251371588523,30251696161301,7362719941,11022,7587,320399615,65558,0,1,601154,4622987,11
1760,KBN,10,table,23,0,0,table,d4c3,11022453199,30251696625103,30251701444401,11117633901,11022,7362,4794042,5269101,27762,1,5269101,27762,1
1760,KBN,10,table,24,0,1,stock,d1c2,7362719941,30251701638992,30251926941904,7237417029,11117,7362,221340350,64076,2301844,2,446504,6360450,7
1760,KBN,10,table,25,0,0,table,c3a5,11117633901,30251927497444,30251934933710,11210197635,11117,7237,7407902,7977311,33310,1,7977311,33310,1
1760,KBN,10,table,26,0,1,stock,c2c1,7237417029,30251935250313,30252370285355,6902381987,11210,7237,431038115,92388,0,1,645494,4746151,7
1760,KBN,10,table,27,0,0,table,e3d3,11210197635,30252370859392,30252382185568,11298871459,11210,6902,11297034,11885562,1500909,2,11885562,1500909,2
1760,KBN,10,table,28,0,1,stock,c1d1,6902381987,30252383924144,30252568905172,6817400959,11298,6902,182896247,100780,3981310,2,436652,4082090,5
1760,KBN,10,table,29,0,0,table,c5a4,11298871459,30252569292561,30252574472847,11393691173,11298,6817,5156002,5554146,26880,1,5554146,26880,1
1760,KBN,10,table,30,0,1,stock,d1c1,6817400959,30252574660287,30252813621479,6678439767,11393,6817,238547816,104326,0,1,353157,5338765,4
1760,KBN,10,table,31,0,0,table,a5d2,11393691173,30252814006184,30252818842366,11488854991,11393,6678,4838458,5234129,26769,1,5234129,26769,1
1760,KBN,10,table,32,0,1,stock,c1b1,6678439767,30252819044838,30252996057364,6601427241,11488,6678,173018440,67210,4930016,2,465775,4952559,9
1760,KBN,10,table,33,0,0,table,d3c3,11488854991,30252996571052,30253004259449,11581166594,11488,6601,7664274,8191942,26209,1,8191942,26209,1
1760,KBN,10,table,34,0,1,stock,b1a2,6601427241,30253004478867,30253176487896,6529418212,11581,6601,171553888,78006,0,1,661419,6715057,19
1760,KBN,10,table,35,0,0,table,d2c1,11581166594,30253177159471,30253181584838,11676741227,11581,6529,4402388,5084035,25498,1,5084035,25498,1
1760,KBN,10,table,36,0,1,stock,a2b1,6529418212,30253181737126,30253348569238,6462586100,11676,6529,166331831,64206,0,1,638876,2246532,33
1760,KBN,10,table,37,0,0,table,c3d2,11676741227,30253348994424,30253352367949,11773367702,11676,6462,3347083,3783154,28793,1,3783154,28793,1
1760,KBN,10,table,38,0,1,stock,b1a2,6462586100,30253352542309,30253395205035,6519923374,11773,6462,42493838,64457,0,1,330803,3462977,6
1760,KBN,10,table,39,0,0,table,d2c2,11773367702,30253395578934,30253399201461,11869745175,11773,6519,3624958,4009773,22884,1,4009773,22884,1
1760,KBN,10,table,40,0,1,stock,a2a1,6519923374,30253399391936,30253399908649,6619406661,11869,6519,417283,62293,354990,2,179427,417283,1
1760,KBN,10,table,41,0,0,table,c1b2,11869745175,30253400144331,30253405415794,11964473712,11869,6619,5273037,5387268,0,0,5387268,0,0
1760,KBN,10,table,42,0,1,stock,a1a2,6619406661,30253405559278,30253405736984,6719228955,11964,6619,125988,61431,64557,2,152738,125988,1
1760,KBN,10,table,43,0,0,table,a4c3,11964473712,30253405874420,30253409024090,12061324042,11964,6719,3150770,3329086,0,0,3329086,0,0
3141,KBN,10,corner,0,2,0,stock,g6f7,10000000000,30212787531631,30213316323994,9571207637,10000,10000,498431060,117064,5197775,2,697763,4943025,11
3141,KBN,10,corner,1,2,1,corner,h4f6,10000000000,30213316853436,30215962450330,7454403106,9571,10000,2640974879,208341,5298,1,905529,2690333,12
3141,KBN,10,corner,2,2,0,stock,f7e8,9571207637,30215962886162,30216274575000,9359518799,9571,7454,307764922,144626,5838,1,655819,5717019,4
3141,KBN,10,corner,3,2,1,corner,e5e6,7454403106,30216274987627,30216849156880,6980233853,9359,7454,569796634,76624,4307,1,771681,4902094,9
3141,KBN,10,corner,4,2,0,stock,e8f8,9359518799,30216849520153,30217114545816,9194493136,9359,6980,261209965,69293,3846,1,516160,2390757,4
3141,KBN,10,corner,5,2,1,corner,g3f5,6980233853,30217114952023,30217770306125,6424879751,9194,6980,654806829,69424,5147,1,710879,4939530,5
3141,KBN,10,corner,6,2,0,stock,f8e8,9194493136,30217770692593,30218090737645,8974448084,9194,6424,319765143,99428,4106,1,633947,5178536,5
3141,KBN,10,corner,7,2,1,corner,f6g5,6424879751,30218091141389,30218489063970,6126957170,8974,6424,397678686,77015,5167,1,621937,4739741,4
3141,KBN,10,corner,8,2,0,stock,e8f8,8974448084,30218489513663,30218758486673,8805475074,8974,6126,268513224,76374,5318,1,882448,2381743,6
3141,KBN,10,corner,9,2,1,corner,g5e7,6126957170,30218758996696,30219191892108,5794061758,8805,6126,432147520,76043,5278,1,1316144,4888453,7
3141,KBN,10,corner,10,2,0,stock,f8g8,8805475074,30219192443854,30219421517454,8676401474,8805,5794,227690812,92127,6550,1,873635,4313566,13
3141,KBN,10,corner,11,2,1,corner,e6f6,5794061758,30219422028178,30219715105134,5600984802,8676,5794,292452949,83725,6720,1,1051828,4311883,16
3141,KBN,10,corner,12,2,0,stock,g8h7,8676401474,30219715609469,30219892495028,8599515915,8676,5600,176120019,85478,0,1,1140029,4396690,39
3141,KBN,10,corner,13,2,1,corner,f6f7,5600984802,30219892951200,30220039018744,5554917258,8599,5600,145513338,78627,0,1,823005,3071743,34
3141,KBN,10,corner,14,2,0,stock,h7h8,8599515915,30220039425232,30220041220568,8697720579,8599,5554,1730402,78958,0,1,436942,1730402,1
3141,KBN,10,corner,15,2,1,corner,f7g6,5554917258,30220041438545,30220042680563,5653675240,8697,5554,1055331,113009,0,2,451397,94621,66
3141,KBN,10,corner,16,2,0,stock,h8g8,8697720579,30220042864097,30220043245849,8797338827,8697,5653,336472,50195,0,1,194610,336472,1
3141,KBN,10,corner,17,2,1,corner,f5h6,5653675240,30220043372939,30220043666207,5753381972,8797,5653,256342,45868,0,2,170084,256342,1
3141,KBN,10,corner,18,2,0,stock,g8h8,8797338827,30220043797754,30220043936592,8897199989,8797,5753,98827,44566,0,1,169223,98827,1
3141,KBN,10,corner,19,2,1,corner,e7f6,5753381972,30220044055480,30220044277472,5853159980,8897,5753,187619,43304,0,1,46089,187619,1
3141,KBN,10,stock,0,2,0,stock,g6f7,10000000000,30222329074273,30222817531578,9611542695,10000,10000,480794380,125307,2841099,2,705993,2608201,12
3141,KBN,10,stock,1,2,1,stock,e5f5,10000000000,30222817978206,30223273389437,9644588769,9611,10000,451401551,139558,5976336,2,758250,5715778,10
3141,KBN,10,stock,2,2,0,stock,f7f8,9611542695,30223273944848,30223773518199,9211969344,9611,9644,495471080,87982,6850,1,941596,5925591,7
3141,KBN,10,stock,3,2,1,stock,f5e6,9644588769,30223773940441,30224188171844,9330357366,9211,9644,413851418,75743,4256,1,766434,5942015,7
3141,KBN,10,stock,4,2,0,stock,f8g7,9211969344,30224188583911,30224615210599,8885342656,9211,9330,426087184,75112,5027,1,889167,3287815,4
3141,KBN,10,stock,5,2,1,stock,h4f6,9330357366,30224615619030,30225490092998,8555883398,8885,9330,870484852,73850,3876,1,679833,4264552,5
3141,KBN,10,stock,6,2,0,stock,g7g6,8885342656,30225490626876,30226109664009,8366305523,8885,8555,618659788,72578,4938,1,878220,5269522,4
3141,KBN,10,stock,7,2,1,stock,e6e7,8555883398,30226110232318,30226805425797,7960689919,8366,8555,687667595,77346,4967,1,774505,5644791,4
3141,KBN,10,stock,8,2,0,stock,g6h6,8366305523,30226806022979,30227128867635,8143460867,8366,7960,315109894,85748,6931,1,868786,5854444,5
3141,KBN,10,stock,9,2,1,stock,e7f7,7960689919,30227129271107,30227529027189,7660933837,8143,7960,395761669,77866,4206,1,719044,2609043,5
3141,KBN,10,stock,10,2,0,stock,h6h7,8143460867,30227529417793,30227744564283,8028314377,8143,7660,214767147,77566,0,1,744661,2585477,7
3141,KBN,10,stock,11,2,1,stock,f6h4,7660933837,30227744990930,30228186257496,7319667271,8028,7660,425570821,75794,0,1,894395,5894916,10
3141,KBN,10,stock,12,2,0,stock,h7h6,8028314377,30228186634669,30228407273902,7907675144,8028,7319,214816708,78346,0,1,869759,7067673,17
3141,KBN,10,stock,13,2,1,stock,h4e7,7319667271,30228407640199,30228773845232,7053462238,7907,7319,365203905,74140,0,1,1256275,4361406,21
3141,KBN,10,stock,14,2,0,stock,h6h7,7907675144,30228774235765,30228966590954,7815319955,7907,7053,188111239,75823,0,1,964381,9404701,33
3141,KBN,10,stock,15,2,1,stock,g3f5,7053462238,30228967027085,30229086335126,7034154197,7815,7053,118990180,77365,4216,1,737835,4855244,27
3141,KBN,10,stock,16,2,0,stock,h7h8,7815319955,30229086690308,30229095763191,7906247072,7815,7034,8963453,94201,4096,1,445555,5189943,4
3141,KBN,10,stock,17,2,1,stock,f7g6,7034154197,30229096070630,30229097145569,7133079258,7906,7034,1018209,59208,2845,1,74161,936497,1
3141,KBN,10,stock,18,2,0,stock,h8g8,7906247072,30229097300580,30229097804504,8005743148,7906,7133,357679,52949,2443,2,339992,0,65
3141,KBN,10,stock,19,2,1,stock,f5h6,7133079258,30229097914118,30229098196340,7232797036,8005,7133,245957,45658,0,1,116363,245957,1
3141,KBN,10,stock,20,2,0,stock,g8h8,8005743148,30229098283771,30229098571161,8105455758,8005,7232,145981,43464,0,2,258913,34171,66
3141,KBN,10,stock,21,2,1,stock,e7f6,7232797036,30229098656439,30229098900344,7332553131,8105,7232,206789,40100,0,1,90645,206789,1
3141,KBN,10,table,0,2,0,stock,g6f7,10000000000,30220094619085,30220599420515,9595198570,10000,10000,500776367,107612,5791129,2,736927,5054821,10
3141,KBN,10,table,1,2,1,table,h4f6,10000000000,30220599829998,30220604376550,10095453448,9595,10000,4491921,4911387,56374,1,4911387,56374,1
3141,KBN,10,table,2,2,0,stock,f7e8,9595198570,30220604519784,30220870473473,9429244881,9595,10095,265763349,55613,0,1,313758,3482626,4
3141,KBN,10,table,3,2,1,table,e5e6,10095453448,30220871115704,30220876162644,10190406508,9429,10095,5021882,5673134,27771,1,5673134,27771,1
3141,KBN,10,table,4,2,0,stock,e8f8,9429244881,30220876358297,30221155015862,9250587316,9429,10190,278461173,63625,3588664,2,378785,7641481,4
3141,KBN,10,table,5,2,1,table,g3f5,10190406508,30221155394708,30221161603137,10284198079,9250,10190,6182363,6571013,28763,1,6571013,28763,1
3141,KBN,10,table,6,2,0,stock,f8e8,9250587316,30221161812951,30221483245569,9029154698,9250,10284,317586736,61462,0,1,397553,6186430,5
3141,KBN,10,table,7,2,1,table,f6g5,10284198079,30221483617445,30221489558433,10378257091,9029,10284,5917068,6298657,26249,1,6298657,26249,1
3141,KBN,10,table,8,2,0,stock,e8f8,9029154698,30221489732313,30221750139925,8868747086,9029,10378,256460868,61281,0,1,462582,2245590,6
3141,KBN,10,table,9,2,1,table,g5e7,10378257091,30221750538511,30221756371828,10472423774,8868,10378,5803308,6212518,31457,1,6212518,31457,1
3141,KBN,10,table,10,2,0,stock,f8g8,8868747086,30221756547431,30221999963708,8725330809,8868,10472,238976832,64618,7397075,2,844069,7461693,12
3141,KBN,10,table,11,2,1,table,e6f6,10472423774,30222000484768,30222008625947,10564282595,8725,10472,8114837,8586190,28893,1,8586190,28893,1
3141,KBN,10,table,12,2,0,stock,g8h7,8725330809,30222008867579,30222213976932,8620221456,8725,10564,202544801,74310,0,1,1033953,7577564,41
3141,KBN,10,table,13,2,1,table,f6f7,10564282595,30222214381808,30222219492995,10659171408,8620,10564,5112708,5529520,23756,1,5529520,23756,1
3141,KBN,10,table,14,2,0,stock,h7h8,8620221456,30222219673655,30222221079979,8718815132,8620,10659,1347821,55302,0,1,168451,1347821,1
3141,KBN,10,table,15,2,1,table,f7g6,10659171408,30222221211596,30222227947162,10752435842,8718,10659,6736941,6913424,0,0,6913424,0,0
3141,KBN,10,table,16,2,0,stock,h8g8,8718815132,30222228099860,30222228434591,8818480401,8718,10752,283963,55642,228321,2,101171,283963,1
3141,KBN,10,table,17,2,1,table,f5h6,10752435842,30222228532968,30222234199676,10846769134,8818,10752,5668026,5806583,0,0,5806583,0,0
3141,KBN,10,table,18,2,0,stock,g8h8,8818480401,30222234324273,30222234478253,8918326421,8818,10846,109914,50916,58998,2,130595,109914,1
3141,KBN,10,table,19,2,1,table,e7f6,10846769134,30222234572734,30222237092234,10944249634,8918,10846,2520630,2651816,0,0,2651816,0,0
3191,KBN,10,corner,0,0,0,stock,f4f5,10000000000,30274402198421,30274925234483,9576963938,10000,10000,505498967,123574,5714506,2,1044527,5474547,11
3191,KBN,10,corner,1,0,1,corner,c5d6,10000000000,30274927467829,30275396206655,9631261174,9576,10000,468106448,276804,4329809,2,2824374,3893369,14
3191,KBN,10,corner,2,0,0,stock,f5g4,9576963938,30275396679532,30275773647533,9299995937,9576,9631,376438557,113850,0,1,919222,3336919,12
3191,KBN,10,corner,3,0,1,corner,d4e3,9631261174,30275774166429,30276287640951,9217786652,9299,9631,513173065,88893,5959,1,776768,5725692,5
3191,KBN,10,corner,4,0,0,stock,g4f5,9299995937,30276288292885,30276675384034,9012904788,9299,9217,386665126,81612,6309,1,522138,3594563,10
3191,KBN,10,corner,5,0,1,corner,e4c5,9217786652,30276675865304,30276905952685,9087699271,9012,9217,229880514,86269,6119,1,637601,3952727,5
3191,KBN,10,corner,6,0,0,stock,f5g4,9012904788,30276906477059,30277268361115,8751020732,9012,9087,359385645,73409,5218,1,997840,6066881,9
3191,KBN,10,corner,7,0,1,corner,e3e4,9087699271,30277268763657,30277532187674,8924275254,8751,9087,255110173,76974,4547,1,589411,3119654,7
3191,KBN,10,corner,8,0,0,stock,g4g5,8751020732,30277532607762,30278317593711,8066034783,8751,8924,781076506,68743,4757,1,556490,3300043,4
3191,KBN,10,corner,9,0,1,corner,c5d7,8924275254,30278318175010,30278681146532,8661303732,8066,8924,362002058,161531,8313,1,843278,5618022,7
3191,KBN,10,corner,10,0,0,stock,g5g4,8066034783,30278681660600,30278993813698,7853881685,8066,8661,309781908,90676,4586,1,864739,5781766,11
3191,KBN,10,corner,11,0,1,corner,d7f6,8661303732,30278994173165,30279551626547,8203850350,7853,8661,557211963,71586,4758,1,555278,5712903,6
3191,KBN,10,corner,12,0,0,stock,g4g5,7853881685,30279552066114,30279840711284,7665236515,7853,8203,288448161,74241,4687,1,196805,3829574,8
3191,KBN,10,corner,13,0,1,corner,e4e5,8203850350,30279841121257,30280108060780,8036910827,7665,8203,266744012,74391,4126,1,565804,2762502,6
3191,KBN,10,corner,14,0,0,stock,g5g6,7665236515,30280108481208,30280450607038,7423110685,7665,8036,334602749,75543,4747,1,659846,3416036,6
3191,KBN,10,corner,15,0,1,corner,e5e6,8036910827,30280451116199,30280709199311,7878827715,7423,8036,255343155,77195,5288,1,805579,7180742,11
3191,KBN,10,corner,16,0,0,stock,g6g5,7423110685,30280709921832,30281364956549,6868075968,7423,7878,652852239,78767,0,1,918020,6077417,4
3191,KBN,10,corner,17,0,1,corner,d6g3,7878827715,30281365341524,30283199642128,6144527111,6868,7878,1800542236,76604,3756,1,552363,2541803,4
3191,KBN,10,corner,18,0,0,stock,g5h6,6868075968,30283200263647,30283634603702,6533735913,6868,6144,434081216,97416,0,1,465425,3737977,5
3191,KBN,10,corner,19,0,1,corner,g3f4,6144527111,30283635042308,30284811904657,5067664762,6533,6144,1172815234,78757,4818,1,794786,4840522,6
3191,KBN,10,corner,20,0,0,stock,h6g6,6533735913,30284812456472,30284992316787,6453875598,6533,5067,179549150,78047,0,1,607085,3546141,4
3191,KBN,10,corner,21,0,1,corner,f4d2,5067664762,30284992722774,30285251845787,4908541749,6453,5067,255145128,79479,4406,1,916707,3133745,6
3191,KBN,10,corner,22,0,0,stock,g6g7,6453875598,30285252466475,30285667327537,6139014536,6453,4908,414536728,92959,0,1,732481,3535585,7
3191,KBN,10,corner,23,0,1,corner,f6h5,4908541749,30285667797699,30286194068876,4482270572,6139,4908,525871575,82113,0,1,672503,4192015,5
3191,KBN,10,corner,24,0,0,stock,g7g6,6139014536,30286194582884,30286415450512,6018146908,6139,4482,216955600,93960,6960,1,748658,5255541,6
3191,KBN,10,corner,25,0,1,corner,h5g3,4482270572,30286415982207,30286577359584,4420893195,6018,4482,160598561,93129,6229,1,684931,3850705,3
3191,KBN,10,corner,26,0,0,stock,g6g7,6018146908,30286577890127,30286843063155,5852973880,6018,4420,264942223,90455,6880,1,737170,5982575,4
3191,KBN,10,corner,27,0,1,corner,d2g5,4420893195,30286843412848,30287382787266,3981518777,5852,4420,535792686,81561,4457,1,528940,4463680,4
3191,KBN,10,corner,28,0,0,stock,g7f8,5852973880,30287383211070,30287610531609,5725653341,5852,3981,227111273,82002,4677,1,605933,4677979,4
3191,KBN,10,corner,29,0,1,corner,g5f6,3981518777,30287611079748,30287858457410,3834141115,5725,3981,243342778,80430,5418,1,772663,4793552,6
3191,KBN,10,corner,30,0,0,stock,f8g8,5725653341,30287858875024,30288052954552,5631573813,5725,3834,193796338,81311,4918,1,674998,5014100,6
3191,KBN,10,corner,31,0,1,corner,e6e7,3834141115,30288053349051,30288453350744,3534139422,5631,3834,399736761,81031,4717,1,630340,2531727,5
3191,KBN,10,corner,32,0,0,stock,g8h7,5631573813,30288453921337,30288603345700,5582149450,5631,3534,149078636,98227,7972,1,884718,5919001,5
3191,KBN,10,corner,33,0,1,corner,e7f7,3534139422,30288603781050,30288805583508,3432336964,5582,3534,201541481,82934,5258,1,664901,4936130,5
3191,KBN,10,corner,34,0,0,stock,h7h6,5582149450,30288806033982,30288978178308,5510005124,5582,3432,171641057,82874,5138,1,808204,5854023,9
3191,KBN,10,corner,35,0,1,corner,f6e7,3432336964,30288978808570,30289190468052,3320677482,5510,3432,211127199,79388,5308,1,1133142,5077816,11
3191,KBN,10,corner,36,0,0,stock,h6h7,5510005124,30289191006797,30289337173650,5463838271,5510,3320,145417464,97295,7361,1,1259217,4863506,26
3191,KBN,10,corner,37,0,1,corner,g3f5,3320677482,30289338733011,30289539064254,3220346239,5463,3320,199704767,98788,0,1,2153810,5243934,27
3191,KBN,10,corner,38,0,0,stock,h7h8,5463838271,30289539456140,30289545426355,5557868056,5463,3220,5860040,87981,0,1,486588,4544750,6
3191,KBN,10,corner,39,0,1,corner,f7g6,3220346239,30289545716809,30289554616754,3311446294,5557,3220,8809543,77646,0,1,369761,6024829,4
3191,KBN,10,corner,40,0,0,stock,h8g8,5557868056,30289554881209,30289555300436,5657448829,5557,3311,370172,52578,3075,1,282242,305877,1
3191,KBN,10,corner,41,0,1,corner,f5h6,3311446294,30289555430170,30289555970728,3410905736,5657,3311,342328,54492,0,2,405357,42584,66
3191,KBN,10,corner,42,0,0,stock,g8h8,5657448829,30289556109155,30289556255724,5757302260,5657,3410,104986,49523,2234,1,104727,47561,1
3191,KBN,10,corner,43,0,1,corner,e7f6,3410905736,30289556353320,30289556854729,3510404327,5757,3410,279912,46770,0,2,350829,37606,66
3191,KBN,10,stock,0,0,0,stock,f4f5,10000000000,30259738474839,30260166128692,9672346147,10000,10000,423621183,113539,4407,1,682565,0,18
3191,KBN,10,stock,1,0,1,stock,c5d6,10000000000,30260166533047,30261015571066,9250961981,9672,10000,826396102,138406,4808,1,995147,0,20
3191,KBN,10,stock,2,0,0,stock,f5g4,9672346147,30261015963623,30261292711856,9495597914,9672,9250,276411666,94271,0,1,677029,4038716,11
3191,KBN,10,stock,3,0,1,stock,d4e3,9250961981,30261293133286,30261531722152,9112373115,9495,9250,238359643,79017,2828461,2,587858,2747910,4
3191,KBN,10,stock,4,0,0,stock,g4f5,9495597914,30261532073747,30261891283362,9236388299,9495,9112,357965197,66510,3893108,2,382180,4697889,10
3191,KBN,10,stock,5,0,1,stock,d6c7,9112373115,30261891847475,30262451487035,8652733555,9236,9112,550922360,88843,6620,1,947204,2213,23
3191,KBN,10,stock,6,0,0,stock,f5e6,9236388299,30262451980132,30262779112177,9009256254,9236,8652,314193038,74461,26029,1,789651,3893098,12
3191,KBN,10,stock,7,0,1,stock,e3d4,8652733555,30262779860095,30263111027684,8421565966,9009,8652,322117832,84796,7181,1,1088936,3973068,7
3191,KBN,10,stock,8,0,0,stock,e6d7,9009256254,30263111530596,30263357434511,8863352339,9009,8421,245508609,80991,5368,1,728787,4354396,6
3191,KBN,10,stock,9,0,1,stock,c7f4,8421565966,30263357870192,30263718802834,8160633324,8863,8421,360393377,130905,4858,1,841967,5953342,9
3191,KBN,10,stock,10,0,0,stock,d7e6,8863352339,30263719192787,30264186206172,8496338954,8863,8160,466693864,76905,4667,1,672684,4696927,5
3191,KBN,10,stock,11,0,1,stock,e4g3,8160633324,30264186728062,30264532026279,7915335107,8496,8160,340345037,79349,6199,1,1263717,4097543,9
3191,KBN,10,stock,12,0,0,stock,e6d7,8496338954,30264532423373,30264839225741,8289536586,8496,7915,295268813,139738,5478,1,645743,3406002,6
3191,KBN,10,stock,13,0,1,stock,d4d5,7915335107,30264839624016,30265956349041,6898610082,8289,7915,1116261543,78347,4286,1,784070,4231333,11
3191,KBN,10,stock,14,0,0,stock,d7d8,8289536586,30265957039292,30266444593836,7901982042,8289,6898,486768310,90615,7291,1,886474,2833768,5
3191,KBN,10,stock,15,0,1,stock,d5d6,6898610082,30266444968325,30266878733937,6564844470,7901,6898,430971020,74732,4637,1,670772,2917163,11
3191,KBN,10,stock,16,0,0,stock,d8c8,7901982042,30266879189338,30267251718220,7629453160,7901,6564,372227340,76014,5318,1,734295,4701824,7
3191,KBN,10,stock,17,0,1,stock,d6c6,6564844470,30267252151357,30267509937088,6407058739,7629,6564,257453640,79238,4867,1,402572,3727281,6
3191,KBN,10,stock,18,0,0,stock,c8d8,7629453160,30267510320470,30267803324078,7436449552,7629,6407,289028319,77436,0,1,647365,5678402,6
3191,KBN,10,stock,19,0,1,stock,f4d6,6407058739,30267803818326,30268095000492,6215876573,7436,6407,290790405,78117,4977,1,752593,4057693,6
3191,KBN,10,stock,20,0,0,stock,d8e8,7436449552,30268095509222,30268301405459,7330553315,7436,6215,205535585,90164,0,1,847844,4490128,12
3191,KBN,10,stock,21,0,1,stock,c6d5,6215876573,30268301844716,30268529505880,6088215409,7330,6215,223385374,80911,4937,1,862386,5939842,11
3191,KBN,10,stock,22,0,0,stock,e8f7,7330553315,30268529955312,30268973729265,6986779362,7330,6088,441097374,79949,4897,1,674216,5930448,5
3191,KBN,10,stock,23,0,1,stock,d5e5,6088215409,30268974361670,30269231362588,5931214491,6986,6088,256616872,101722,7611,1,980875,9155360,6
3191,KBN,10,stock,24,0,0,stock,f7g6,6986779362,30269232109835,30269699162870,6619726327,6986,5931,466511322,96744,7020,1,567183,3750916,15
3191,KBN,10,stock,25,0,1,stock,d6e7,5931214491,30269699565973,30269874224668,5856555796,6619,5931,174154636,140800,4096,1,580476,4215048,4
3191,KBN,10,stock,26,0,0,stock,g6f7,6619726327,30269874827279,30270429011877,6165541729,6619,5856,550030693,80660,4998,1,1110167,5057315,6
3191,KBN,10,stock,27,0,1,stock,e7f6,5856555796,30270429689620,30271066097287,5320148129,6165,5856,623743972,120850,6430,1,927333,2143398,5
3191,KBN,10,stock,28,0,0,stock,f7e8,6165541729,30271066623994,30271502991946,5829173777,6165,5320,436228610,82053,0,1,643980,5376402,3
3191,KBN,10,stock,29,0,1,stock,e5e6,5320148129,30271503348409,30271737350963,5186145575,5829,5320,233677469,79699,3755,1,577882,4595426,4
3191,KBN,10,stock,30,0,0,stock,e8f8,5829173777,30271737802758,30271901533261,5765443274,5829,5186,163454287,89373,5589,1,576069,6077107,3
3191,KBN,10,stock,31,0,1,stock,g3f5,5186145575,30271902049703,30272148458060,5039737218,5765,5186,242538926,90275,5458,1,677600,5814254,4
3191,KBN,10,stock,32,0,0,stock,f8e8,5765443274,30272148885639,30272562457004,5451871909,5765,5039,412513223,80780,5689,1,623420,3829374,5
3191,KBN,10,stock,33,0,1,stock,f6h4,5039737218,30272562883502,30272885249610,4817371110,5451,5039,318983748,80359,4357,1,581527,4991727,4
3191,KBN,10,stock,34,0,0,stock,e8f8,5451871909,30272885722287,30273079136041,5358458155,5451,4817,193048533,81712,5428,1,811682,2153623,6
3191,KBN,10,stock,35,0,1,stock,h4e7,4817371110,30273079550611,30273407989338,4588932383,5358,4817,328110295,80670,4717,1,751821,4319375,6
3191,KBN,10,stock,36,0,0,stock,f8g8,5358458155,30273408621413,30273564343899,5302735669,5358,4588,155352385,84276,0,1,944098,3321326,8
3191,KBN,10,stock,37,0,1,stock,e6f6,4588932383,30273564889164,30273850037969,4403783578,5302,4588,284497588,95342,6239,1,1069726,2969680,9
3191,KBN,10,stock,38,0,0,stock,g8h7,5302735669,30273850836572,30273993252575,5260319666,5302,4403,141806583,97636,0,1,1382684,5173839,26
3191,KBN,10,stock,39,0,1,stock,f6f7,4403783578,30273993953382,30274225895754,4271841206,5260,4403,231107657,92688,7451,1,1507477,5900784,38
3191,KBN,10,stock,40,0,0,stock,h7h8,5260319666,30274226408200,30274233976014,5352751852,5260,4271,7415192,95002,0,1,646354,5589069,8
3191,KBN,10,stock,41,0,1,stock,f7g6,4271841206,30274234281520,30274241631559,4364491167,5352,4271,7218000,72188,3725,1,418183,5622087,6
3191,KBN,10,stock,42,0,0,stock,h8g8,5352751852,30274241930165,30274242449030,5452232987,5352,4364,447508,66560,3585,1,321509,365776,1
3191,KBN,10,stock,43,0,1,stock,f5h6,4364491167,30274242618454,30274243305961,4463803660,5452,4364,493321,64627,2834,2,414584,0,65
3191,KBN,10,stock,44,0,0,stock,g8h8,5452232987,30274243457287,30274243653640,5552036634,5452,4463,134351,57256,0,1,162091,134351,1
3191,KBN,10,stock,45,0,1,stock,e7f6,4463803660,30274243823994,30274244419564,4563208090,5552,4463,374437,57726,0,2,442902,44106,66
3191,KBN,10,table,0,0,0,stock,f4f5,10000000000,30253455591074,30253906969878,9648621196,10000,10000,447402412,102022,4716707,2,690462,4035260,11
3191,KBN,10,table,1,0,1,table,c5d6,10000000000,30253907360382,30253912393509,10094966873,9648,10000,4972889,5373667,62774,1,5373667,62774,1
3191,KBN,10,table,2,0,0,stock,f5g4,9648621196,30253912620618,30254278182597,9383059217,9648,10094,365117051,58708,0,1,654958,3378380,12
3191,KBN,10,table,3,0,1,table,d4e3,10094966873,30254278702324,30254287236786,10186432411,9383,10094,7412779,7945253,1124708,2,7945253,1124708,2
3191,KBN,10,table,4,0,0,stock,g4f5,9383059217,30254287434502,30254675525634,9094968085,9383,10186,384010622,63244,0,1,582791,4566673,9
3191,KBN,10,table,5,0,1,table,e4c5,10186432411,30254676118992,30254684272334,10278279069,9094,10186,8124091,8226343,32258,1,8226343,32258,1
3191,KBN,10,table,6,0,0,stock,f5g4,9094968085,30254684493064,30255049599556,8829861593,9094,10278,360902930,77947,3479040,2,615668,3547923,10
3191,KBN,10,table,7,0,1,table,d6f4,10278279069,30255050135898,30255059263648,10369151319,8829,10278,9130683,9741454,0,0,9741454,0,0
3191,KBN,10,table,8,0,0,stock,g4f5,8829861593,30255059488454,30255421569762,8567780285,8829,10369,360504653,83744,0,1,663211,5637770,13
3191,KBN,10,table,9,0,1,table,e3f3,10369151319,30255422041518,30255426722848,10464469989,8567,10369,4682446,5164956,38688,1,5164956,38688,1
3191,KBN,10,table,10,0,0,stock,f5g6,8567780285,30255426894735,30255883038425,8211636595,8567,10464,444829337,56075,5053579,2,390079,5109654,7
3191,KBN,10,table,11,0,1,table,f3g4,10464469989,30255883442149,30255890409007,10557503131,8211,10464,6943910,7358428,25538,1,7358428,25538,1
3191,KBN,10,table,12,0,0,stock,g6f6,8211636595,30255890606883,30256142547272,8059696206,8211,10557,251768390,57787,0,1,356101,5393707,4
3191,KBN,10,table,13,0,1,table,f4c7,10557503131,30256142958227,30256150009160,10650452198,8059,10557,7026333,7447521,26970,1,7447521,26970,1
3191,KBN,10,table,14,0,0,stock,f6g6,8059696206,30256150188148,30256868462570,7441421784,8059,10650,709003977,60570,0,1,446958,5811741,5
3191,KBN,10,table,15,0,1,table,c7d8,10650452198,30256868889779,30256879493995,10739847982,7441,10650,10579153,11016987,28432,1,11016987,28432,1
3191,KBN,10,table,16,0,0,stock,g6g7,7441421784,30256879756578,30257074358476,7346819886,7441,10739,194344147,75103,4172845,2,499775,4247948,5
3191,KBN,10,table,17,0,1,table,c5b7,10739847982,30257074766356,30257080836153,10833778185,7346,10739,6048985,6467470,22383,1,6467470,22383,1
3191,KBN,10,table,18,0,0,stock,g7f7,7346819886,30257080961961,30257330259217,7197522630,7346,10833,248139286,57827,2984973,2,309461,7038871,6
3191,KBN,10,table,19,0,1,table,g4f5,10833778185,30257330629030,30257335372924,10929034291,7197,10833,4745841,5126398,21503,1,5126398,21503,1
3191,KBN,10,table,20,0,0,stock,f7e8,7197522630,30257335550499,30257986604691,6646468438,7197,10929,650743668,61041,4396319,2,373337,4457360,5
3191,KBN,10,table,21,0,1,table,f5e6,10929034291,30257986999371,30257992153922,11023879740,6646,10929,5128942,5533265,28432,1,5533265,28432,1
3191,KBN,10,table,22,0,0,stock,e8f8,6646468438,30257992396805,30258314071096,6424794147,6646,11023,321465011,73750,0,1,439456,7599869,4
3191,KBN,10,table,23,0,1,table,d8f6,11023879740,30258314438665,30258319157476,11119160929,6424,11023,4720522,5098236,21222,1,5098236,21222,1
3191,KBN,10,table,24,0,0,stock,f8g8,6424794147,30258319328021,30258635137238,6208984930,6424,11119,308679806,88712,4584580,2,377584,4673292,10
3191,KBN,10,table,25,0,1,table,e6f5,11119160929,30258635847910,30258642043938,11212964901,6208,11119,6168063,6889700,30335,1,6889700,30335,1
3191,KBN,10,table,26,0,0,stock,g8f8,6208984930,30258642275124,30258949881064,6001378990,6208,11212,307299526,63915,0,1,427358,5727505,5
3191,KBN,10,table,27,0,1,table,b7d6,11212964901,30258950267892,30258956862275,11306370518,6001,11212,6572115,6969158,24897,1,6969158,24897,1
3191,KBN,10,table,28,0,0,stock,f8g8,6001378990,30258957131848,30259161938596,5896572242,6001,11306,204446911,65809,2811414,2,482809,6869459,4
3191,KBN,10,table,29,0,1,table,f5g6,11306370518,30259162400767,30259171958689,11396812596,5896,11306,9536057,10063444,24316,1,10063444,24316,1
3191,KBN,10,table,30,0,0,stock,g8f8,5896572242,30259172217415,30259355601655,5813188002,5896,11396,179319641,77706,3714752,2,616319,3792458,8
3191,KBN,10,table,31,0,1,table,f6d8,11396812596,30259356060030,30259362810126,11490062500,5813,11396,6727867,6776500,24597,1,6776500,24597,1
3191,KBN,10,table,32,0,0,stock,f8g8,5813188002,30259362974261,30259523652424,5752509839,5813,11490,157386835,62113,0,1,569483,5034421,29
3191,KBN,10,table,33,0,1,table,d8e7,11490062500,30259524100904,30259529707251,11584456153,5752,11490,5583801,5673605,24577,1,5673605,24577,1
3191,KBN,10,table,34,0,0,stock,g8h8,5752509839,30259529871937,30259534030481,5848351295,5752,11584,4045105,59739,0,1,179407,4045105,1
3191,KBN,10,table,35,0,1,table,d6f5,11584456153,30259534242898,30259540081041,11678618010,5848,11584,5841104,6141903,6690,1,6141903,6690,1
3191,KBN,10,table,36,0,0,stock,h8g8,5848351295,30259540214992,30259540602771,5947963516,5848,11678,334489,59970,0,1,144616,334489,1
3191,KBN,10,table,37,0,1,table,f5h6,11678618010,30259540701258,30259546162107,11773157161,5947,11678,5462259,5602348,0,0,5602348,0,0
3191,KBN,10,table,38,0,0,stock,g8h8,5947963516,30259546288987,30259546460183,6047792320,5947,11773,122513,56505,0,1,135382,122513,1
3191,KBN,10,table,39,0,1,table,e7f6,11773157161,30259546555275,30259548960358,11870752078,6047,11773,2406270,2540130,0,0,2540130,0,0
3193,KBN,10,corner,0,2,0,stock,f8g7,10000000000,30237197989453,30237499889910,9798099543,10000,10000,297814527,139848,5920133,2,1023520,5644431,12
3193,KBN,10,corner,1,2,1,corner,d6f5,10000000000,30237500347575,30237770924393,9829423182,9798,10000,270157695,167080,4867,1,700845,3234406,11
3193,KBN,10,corner,2,2,0,stock,g7h8,9798099543,30237771281407,30238038458743,9630922207,9798,9829,266761327,64837,4256,1,714737,4627183,10
3193,KBN,10,corner,3,2,1,corner,h5f7,9829423182,30238038861135,30238541721657,9426562660,9630,9829,502104511,69183,4617,1,682418,5482530,7
3193,KBN,10,corner,4,2,0,stock,h8h7,9630922207,30238542221325,30238886243509,9386900023,9630,9426,343647959,70666,4256,1,844188,5680935,10
3193,KBN,10,corner,5,2,1,corner,e6f6,9426562660,30238886658019,30239551741056,8861479623,9386,9426,661132023,88171,4497,1,689848,5214380,6
3193,KBN,10,corner,6,2,0,stock,h7h8,9386900023,30239552317599,30239886583610,9152634012,9386,8861,331312784,81542,6490,1,617001,3566310,10
3193,KBN,10,corner,7,2,1,corner,f5e7,8861479623,30239887075375,30240222193045,8626361953,9152,8861,334846690,72528,5328,1,739184,4761544,4
3193,KBN,10,corner,8,2,0,stock,h8h7,9152634012,30240222911069,30240493373905,8982171176,9152,8626,262328242,85517,5328,1,960854,4928012,5
3193,KBN,10,corner,9,2,1,corner,e7g6,8626361953,30240493786753,30241662663985,7557484721,8982,8626,1162435169,69003,5208,1,797129,2104630,8
3193,KBN,10,corner,10,2,0,stock,h7h6,8982171176,30241663101238,30242260414851,8484857563,8982,7557,596660781,73539,4928,1,961205,4894222,14
3193,KBN,10,corner,11,2,1,corner,f7g8,7557484721,30242261572749,30242521940770,7397116700,8484,7557,259668884,84526,0,1,1363716,2427381,6
3193,KBN,10,corner,12,2,0,stock,h6h5,8484857563,30242522341888,30242745898486,8361300965,8484,7397,207154102,71276,0,1,790039,5682648,10
3193,KBN,10,corner,13,2,1,corner,g6e5,7397116700,30242746408887,30243313096503,6930429084,8361,7397,562774777,87330,0,1,736989,5591692,5
3193,KBN,10,corner,14,2,0,stock,h5h4,8361300965,30243313431553,30243711995154,8062737364,8361,6930,394358387,67400,4056,1,730570,2478157,11
3193,KBN,10,corner,15,2,1,corner,g8d5,6930429084,30243712396934,30244048535626,6694290392,8062,6930,335807560,72968,0,1,677019,3606731,7
3193,KBN,10,corner,16,2,0,stock,h4g3,8062737364,30244049090826,30244266515138,7945313052,8062,6694,217020773,89093,0,1,930198,2914699,9
3193,KBN,10,corner,17,2,1,corner,e5d3,6694290392,30244267027514,30245372984697,5688333209,7945,6694,1096698763,76705,0,1,894484,5029764,5
3193,KBN,10,corner,18,2,0,stock,g3h2,7945313052,30245373478596,30245714537264,7704254384,7945,5688,340799647,85608,0,1,665453,6518430,5
3193,KBN,10,corner,19,2,1,corner,f6g5,5688333209,30245715094367,30246861664909,4641762667,7704,5688,1145946780,85658,0,1,889910,4906550,9
3193,KBN,10,corner,20,2,0,stock,h2g3,7704254384,30246862205167,30247568408240,7098051311,7704,4641,705627057,75433,5158,1,759963,5688207,8
3193,KBN,10,corner,21,2,1,corner,d5a8,4641762667,30247568855569,30248307488978,4003129258,7098,4641,738215291,73319,4447,1,641186,3027647,5
3193,KBN,10,corner,22,2,0,stock,g3h3,7098051311,30248308139010,30248497763472,7008426849,7098,4003,189365258,74642,0,1,260999,3860880,4
3193,KBN,10,corner,23,2,1,corner,a8f3,4003129258,30248498245322,30248729561215,3871813365,7008,4003,231095838,77446,0,1,692443,5755107,4
3193,KBN,10,corner,24,2,0,stock,h3g3,7008426849,30248730091278,30248943943964,6894574163,7008,3871,213506646,83304,7140,1,778171,5792772,4
3193,KBN,10,corner,25,2,1,corner,f3g4,3871813365,30248944357392,30249169906200,3746264557,6894,3871,225345077,73469,4267,1,514970,3530668,5
3193,KBN,10,corner,26,2,0,stock,g3h2,6894574163,30249170312358,30249357353647,6807532874,6894,3746,186466624,73901,4707,1,591462,5586635,5
3193,KBN,10,corner,27,2,1,corner,g5h4,3746264557,30249357681567,30249681897738,3522048386,6807,3746,323970908,95723,4317,1,502090,2183327,4
3193,KBN,10,corner,28,2,0,stock,h2g2,6807532874,30249682304635,30249889510706,6700326803,6807,3522,206807432,74010,4517,1,713345,5592844,7
3193,KBN,10,corner,29,2,1,corner,g4e2,3522048386,30249890004554,30250114018968,3398033972,6700,3522,223721436,76895,5468,1,762387,5885881,6
3193,KBN,10,corner,30,2,0,stock,g2h2,6700326803,30250114424864,30250290814450,6623937217,6700,3398,175919177,76033,4577,1,761946,5468719,13
3193,KBN,10,corner,31,2,1,corner,d3f4,3398033972,30250291130793,30250483720224,3305444541,6623,3398,186211215,66228,3836,1,651304,9128818,14
3193,KBN,10,corner,32,2,0,stock,h2g1,6623937217,30250484144858,30250664621759,6543460316,6623,3305,179959197,81782,4497,1,621667,3747841,25
3193,KBN,10,corner,33,2,1,corner,h4g3,3305444541,30250665064460,30250854110975,3216398026,6543,3305,188520641,73199,5949,1,871062,2820197,16
3193,KBN,10,corner,34,2,0,stock,g1h1,6543460316,30250854508729,30250859040787,6638928258,6543,3216,4464070,72669,4336,1,427828,4368307,1
3193,KBN,10,corner,35,2,1,corner,e2c4,3216398026,30250859382317,30250877445204,3298335139,6638,3216,17808268,62103,0,2,637923,44667,66
3193,KBN,10,corner,36,2,0,stock,h1g1,6638928258,30250877727556,30250878166742,6738489072,6638,3298,388149,81081,0,1,300608,388149,1
3193,KBN,10,corner,37,2,1,corner,f4h3,3298335139,30250878283326,30250878793298,3397825167,6738,3298,362607,51717,0,2,301504,38027,66
3193,KBN,10,corner,38,2,0,stock,g1h1,6738489072,30250878900388,30250879036361,6838353099,6738,3397,96333,41111,0,1,113730,96333,1
3193,KBN,10,corner,39,2,1,corner,c4d5,3397825167,30250879127637,30250879530869,3497421935,6838,3397,261433,39859,0,2,266395,31767,66
3193,KBN,10,stock,0,2,0,stock,f8g7,10000000000,30250986944781,30251277764233,9809180548,10000,10000,290431174,112978,5959,1,788978,4756065,12
3193,KBN,10,stock,1,2,1,stock,e6e5,10000000000,30251278293043,30251724056006,9654237037,9809,10000,444200921,146158,6970,1,1110530,6204096,14
3193,KBN,10,stock,2,2,0,stock,g7h7,9809180548,30251724567410,30252035530702,9598217256,9809,9654,310436329,78457,6269,1,971739,3318341,17
3193,KBN,10,stock,3,2,1,stock,e5f6,9654237037,30252036186681,30252330939578,9459484140,9598,9654,294108812,83565,7000,1,750020,3682283,8
3193,KBN,10,stock,4,2,0,stock,h7h8,9598217256,30252331330782,30252697774388,9331773650,9598,9459,365977575,71837,5479,1,781015,4578491,7
3193,KBN,10,stock,5,2,1,stock,f6f7,9459484140,30252698320123,30254442454711,7815349552,9331,9459,1736278347,83234,6520,1,1059312,5544803,10
3193,KBN,10,stock,6,2,0,stock,h8h7,9331773650,30254442936892,30254705304729,9169405813,9331,7815,262097203,69995,4887,1,733536,4970936,5
3193,KBN,10,stock,7,2,1,stock,h5g4,7815349552,30254705808463,30255624859872,6996298143,9169,7815,907394579,79459,6009,1,664741,2073003,5
3193,KBN,10,stock,8,2,0,stock,h7h8,9169405813,30255625250767,30255877364746,9017291834,9169,6996,251769048,71297,5107,1,698634,2650704,6
3193,KBN,10,stock,9,2,1,stock,f7f8,6996298143,30255877788740,30256434615991,6539470892,9017,6996,552736378,72799,4757,1,829880,6091718,9
3193,KBN,10,stock,10,2,0,stock,h8h7,9017291834,30256435054597,30256720871073,8831475358,9017,6539,281675922,72968,0,1,671741,4945668,6
3193,KBN,10,stock,11,2,1,stock,f8f7,6539470892,30256721203891,30257132947712,6227727071,8831,6539,400532645,67170,3415,1,559154,2693629,7
3193,KBN,10,stock,12,2,0,stock,h7h8,8831475358,30257133339207,30257427270848,8637543717,8831,6227,293614841,69844,0,1,639984,6343745,9
3193,KBN,10,stock,13,2,1,stock,g4c8,6227727071,30257427861170,30258301696201,5453892040,8637,6227,873351094,76985,0,1,1032880,4137142,9
3193,KBN,10,stock,14,2,0,stock,h8h7,8637543717,30258302102608,30258594863788,8444782537,8637,5453,291871388,69404,0,1,1043166,5898891,9
3193,KBN,10,stock,15,2,1,stock,c8f5,5453892040,30258596216198,30258920154802,5229953436,8444,5453,323605316,90946,0,1,484051,3782974,7
3193,KBN,10,stock,16,2,0,stock,h7h6,8444782537,30258920640127,30259206973338,8258449326,8444,5229,277724226,75242,0,1,889386,3298110,12
3193,KBN,10,stock,17,2,1,stock,f7f6,5229953436,30259207448407,30259444308279,5093093564,8258,5229,236511947,73179,0,1,800004,4552572,9
3193,KBN,10,stock,18,2,0,stock,h6h5,8258449326,30259444669720,30259732502735,8070616311,8258,5093,283605492,83725,4847,1,616138,3229298,12
3193,KBN,10,stock,19,2,1,stock,f6e5,5093093564,30259732934590,30260063206688,4862821466,8070,5093,326250830,76504,0,1,724662,3030291,10
3193,KBN,10,stock,20,2,0,stock,h5h4,8070616311,30260063689810,30260699379808,7534926313,8070,4862,631458594,108752,5929,1,629349,4164583,4
3193,KBN,10,stock,21,2,1,stock,e5f4,4862821466,30260699895809,30260854156383,4808560892,7534,4862,153819199,119128,11867,2,791709,3926398,8
3193,KBN,10,stock,22,2,0,stock,h4h5,7534926313,30260854544162,30261075523517,7413946958,7534,4808,208932446,70395,4777,1,692221,5381288,10
3193,KBN,10,stock,23,2,1,stock,f5c8,4808560892,30261075918166,30262096526933,3887952125,7413,4808,1012699270,92368,4186,1,705222,3947519,5
3193,KBN,10,stock,24,2,0,stock,h5h6,7413946958,30262096952669,30262299272269,7311627358,7413,3887,198002559,76824,5659,1,780224,2936822,10
3193,KBN,10,stock,25,2,1,stock,f4e5,3887952125,30262299766398,30262422078164,3865640359,7311,3887,118460565,77405,5268,1,678132,4108550,9
3193,KBN,10,stock,26,2,0,stock,h6g6,7311627358,30262422481587,30262618672514,7215436431,7311,3865,191807600,75672,4848,1,1124038,5432345,11
3193,KBN,10,stock,27,2,1,stock,c8d7,3865640359,30262619803976,30263055076547,3530367788,7215,3865,431082621,75042,0,1,1351087,4148279,8
3193,KBN,10,stock,28,2,0,stock,g6g7,7215436431,30263056330202,30263309989412,7061777221,7215,3530,249535889,76795,6800,1,685452,3555124,12
3193,KBN,10,stock,29,2,1,stock,d7f5,3530367788,30263310389541,30264485605076,2455152253,7061,3530,1160035995,77926,4387,1,634546,5532635,6
3193,KBN,10,stock,30,2,0,stock,g7g8,7061777221,30264486108148,30265107670263,6540215106,7061,2455,604243137,75112,6770,1,757689,2806998,5
3193,KBN,10,stock,31,2,1,stock,e5f6,2455152253,30265108108398,30265298519052,2364741599,6540,2455,189954187,75643,3925,1,368238,3931155,11
3193,KBN,10,stock,32,2,0,stock,g8h8,6540215106,30265298930117,30265518938264,6420206959,6540,2364,219723719,72148,4927,1,676460,4965968,9
3193,KBN,10,stock,33,2,1,stock,f5h3,2364741599,30265519336370,30265961837700,2022240269,6420,2364,442256296,75323,4637,1,623591,4541515,10
3193,KBN,10,stock,34,2,0,stock,h8h7,6420206959,30265962169065,30266237717969,6244658055,6420,2022,274417289,70064,4457,1,648487,6528210,9
3193,KBN,10,stock,35,2,1,stock,h3f5,2022240269,30266238114421,30266413177438,1947177252,6244,2022,174731615,72949,4367,1,702860,6230185,8
3193,KBN,10,stock,36,2,0,stock,h7g8,6244658055,30266413647881,30266599590924,6158715012,6244,1947,185716940,95493,4657,1,676741,2224749,7
3193,KBN,10,stock,37,2,1,stock,f5e6,1947177252,30266600102548,30266828729785,1818550015,6158,1947,224698693,77095,4607,1,340198,3773119,9
3193,KBN,10,stock,38,2,0,stock,g8h7,6158715012,30266829129041,30267090968618,5996875435,6158,1818,261664645,74081,5548,1,550360,2770003,4
3193,KBN,10,stock,39,2,1,stock,d6f5,1818550015,30267091372561,30267877224705,1132697871,5996,1818,785436217,74672,4646,1,688607,4508496,11
3193,KBN,10,stock,40,2,0,stock,h7h8,5996875435,30267877917470,30268065484613,5909308292,5996,1132,187192237,114161,0,1,1084748,6079641,8
3193,KBN,10,stock,41,2,1,stock,f5h6,1132697871,30268066027224,30268459524543,839200552,5909,1132,393044768,89473,5909,1,809778,5830589,8
3193,KBN,10,stock,42,2,0,stock,h8h7,5909308292,30268459943139,30269111371440,5357879991,5909,839,647475247,102363,5148,1,687225,3920239,10
3193,KBN,10,stock,43,2,1,stock,h6f7,839200552,30269112141982,30269182732400,868610134,5357,839,70402631,92899,7301,1,270834,3715743,3
3193,KBN,10,stock,44,2,0,stock,h7g8,5357879991,30269183247450,30269451697991,5189429450,5357,868,268078036,80750,0,1,855347,6519266,6
3193,KBN,10,stock,45,2,1,stock,e6c8,868610134,30269452275113,30269557794044,863091203,5189,868,105327090,91647,6479,1,414869,3575464,5
3193,KBN,10,stock,46,2,0,stock,g8h7,5189429450,30269558250146,30269841832743,5005846853,5189,863,283263699,76424,5118,1,748647,5646194,6
3193,KBN,10,stock,47,2,1,stock,c8f5,863091203,30269842237738,30270090919348,714409593,5005,863,248417461,76794,3986,1,636388,1949739,8
3193,KBN,10,stock,48,2,0,stock,h7g8,5005846853,30270091362981,30270732121402,4465088432,5005,714,632943166,75963,4927,1,751851,4559242,8
3193,KBN,10,stock,49,2,1,stock,f7d6,714409593,30270732776201,30270799766181,747419613,4465,714,66469627,93069,7521,1,1417254,3076520,4
3193,KBN,10,stock,50,2,0,stock,g8f8,4465088432,30270802295512,30271042154106,4325229838,4465,747,239459660,223734,0,1,2624836,5692974,7
3193,KBN,10,stock,51,2,1,stock,f5c8,747419613,30271042661585,30271186258232,703822966,4325,747,143353873,135973,5158,1,724090,5157955,5
3193,KBN,10,stock,52,2,0,stock,f8g8,4325229838,30271186844338,30271343664315,4268409861,4325,703,156413106,92197,8423,1,966173,5023225,7
3193,KBN,10,stock,53,2,1,stock,c8g4,703822966,30271344213897,30271526274152,621762711,4268,703,181682282,94281,6339,1,518332,3640041,7
3193,KBN,10,stock,54,2,0,stock,g8h7,4268409861,30271527233817,30271653166487,4242477191,4268,621,125766994,119929,5338,1,1120502,4628575,4
3193,KBN,10,stock,55,2,1,stock,g4e6,621762711,30271653580225,30271723238871,652104065,4242,621,69485572,80290,4026,1,563943,2297898,6
3193,KBN,10,stock,56,2,0,stock,h7h6,4242477191,30271723811106,30271903862598,4162425699,4242,652,176103285,92448,7451,1,840213,4052746,6
3193,KBN,10,stock,57,2,1,stock,e6f5,652104065,30271904295386,30272071265006,585134445,4162,652,166674094,78817,5559,1,544262,3554232,6
3193,KBN,10,stock,58,2,0,stock,h6h5,4162425699,30272071676151,30272287560668,4046541182,4162,585,215668540,97806,4697,1,599094,4192084,5
3193,KBN,10,stock,59,2,1,stock,f6e5,585134445,30272288202849,30272425842230,547495064,4046,585,137248262,89614,6389,1,540247,3660511,6
3193,KBN,10,stock,60,2,0,stock,h5h4,4046541182,30272426237611,30272575836001,3996942792,4046,547,149363359,78518,4997,1,608157,5650210,7
3193,KBN,10,stock,61,2,1,stock,e5f4,547495064,30272576221477,30272655198538,568518003,3996,547,78746555,76665,4356,1,406274,0,14
3193,KBN,10,stock,62,2,0,stock,h4h5,3996942792,30272655764084,30272855087353,3897619523,3996,568,195392752,78868,5548,1,798911,4066147,8
3193,KBN,10,stock,63,2,1,stock,f5g4,568518003,30272855436655,30272961729222,562225436,3897,568,105832064,73931,4186,1,519064,3711477,6
3193,KBN,10,stock,64,2,0,stock,h5g6,3897619523,30272962470691,30273242495990,3717594224,3897,562,276237013,81171,6370,1,855548,5414738,3
3193,KBN,10,stock,65,2,1,stock,f4e5,562225436,30273243083729,30273297068275,608240890,3717,562,53828448,74381,5048,1,727006,4793972,9
3193,KBN,10,stock,66,2,0,stock,g6h6,3717594224,30273297466190,30273419835382,3695225032,3717,608,122144119,79378,4557,1,602589,2424197,10
3193,KBN,10,stock,67,2,1,stock,e5f6,608240890,30273420209772,30273491005913,637444749,3695,608,70642963,77746,3656,1,316393,3666760,6
3193,KBN,10,stock,68,2,0,stock,h6h7,3695225032,30273491384689,30273750497996,3536111725,3695,637,255143165,80189,4457,1,605052,4505041,6
3193,KBN,10,stock,69,2,1,stock,d6f7,637444749,30273750921489,30274096058957,392307281,3536,637,341257679,80430,4687,1,625303,4950756,5
3193,KBN,10,stock,70,2,0,stock,h7g8,3536111725,30274096556049,30275272056807,2460610967,3536,392,1175151727,79699,4977,1,791500,3332763,5
3193,KBN,10,stock,71,2,1,stock,g4f5,392307281,30275272883071,30275502092301,263098051,2460,392,225382122,83835,6820,1,971761,2983391,11
3193,KBN,10,stock,72,2,0,stock,g8f8,2460610967,30275502656605,30275640848094,2422419478,2460,263,137861684,109934,0,1,906251,5374108,7
3193,KBN,10,stock,73,2,1,stock,f7d8,263098051,30275641374891,30275754378722,250094220,2422,263,112592921,100600,7191,1,908875,2477517,10
3193,KBN,10,stock,74,2,0,stock,f8e8,2422419478,30275754919100,30276183777709,2093560869,2422,250,423303827,96584,8052,1,814044,6562811,7
3193,KBN,10,stock,75,2,1,stock,d8b7,250094220,30276184496914,30276273183528,261407606,2093,250,88424537,84116,5518,1,711302,3372281,6
3193,KBN,10,stock,76,2,0,stock,e8f8,2093560869,30276273675113,30276593918454,1873317528,2093,261,311081862,118407,6569,1,717148,2172201,7
3193,KBN,10,stock,77,2,1,stock,f5c8,261407606,30276594514616,30276744858823,211063399,1873,261,150089927,103094,0,1,768106,5513526,4
3193,KBN,10,stock,78,2,0,stock,f8g8,1873317528,30276745270198,30277060473536,1658114190,1873,211,315033240,84786,5689,1,618162,2614420,6
3193,KBN,10,stock,79,2,1,stock,c8f5,211063399,30277060858511,30277183712403,188209507,1658,211,120104221,79949,4888,1,523291,5588086,5
3193,KBN,10,stock,80,2,0,stock,g8f8,1658114190,30277184150918,30277518901122,1423363986,1658,188,334166971,80710,5779,1,363793,3739680,6
3193,KBN,10,stock,81,2,1,stock,f5c8,188209507,30277519387800,30277625779506,181817801,1423,188,106189047,87531,5227,1,600234,4477040,7
3193,KBN,10,stock,82,2,0,stock,f8g8,1423363986,30277626285933,30277914111759,1235538160,1423,181,287614950,84195,7091,1,761086,5597631,6
3193,KBN,10,stock,83,2,1,stock,f6e5,181817801,30277914475533,30278016675954,179617380,1235,181,102010161,80169,4567,1,496471,5401378,5
3193,KBN,10,stock,84,2,0,stock,g8f8,1235538160,30278017201139,30278174810031,1177929268,1235,179,157419578,83545,7190,1,725923,2680038,6
3193,KBN,10,stock,85,2,1,stock,e5e6,179617380,30278175168307,30278276505057,178280630,1177,179,100967116,80210,4056,1,490701,4710588,5
3193,KBN,10,stock,86,2,0,stock,f8g7,1177929268,30278277071674,30278762565792,792435150,1177,178,479853387,99278,8162,1,847855,4519883,8
3193,KBN,10,stock,87,2,1,stock,e6d5,178280630,30278763116325,30278863311663,178085292,792,178,97307315,84626,5468,1,811591,7341568,6
3193,KBN,10,stock,88,2,0,stock,g7g6,792435150,30278863728166,30278964177910,791985406,792,178,100193252,85347,6940,1,665131,4109591,5
3193,KBN,10,stock,89,2,1,stock,d5c6,178085292,30278964909524,30279065201452,177793364,791,178,100061304,95933,7892,1,880424,5405505,5
3193,KBN,10,stock,90,2,0,stock,g6g5,791985406,30279065970943,30279235912451,722043898,791,177,166069783,99939,9324,1,1130366,5875716,4
3193,KBN,10,stock,91,2,1,stock,c6d5,177793364,30279236433740,30279336824076,177403028,722,177,100191608,87640,5258,1,531984,3439541,4
3193,KBN,10,stock,92,2,0,stock,g5f4,722043898,30279337227739,30279392577762,766693875,722,177,55146625,85598,0,1,630220,6770130,6
3193,KBN,10,stock,93,2,1,stock,b7d8,177403028,30279393132662,30279475400505,195135185,766,177,82109339,90085,0,1,693346,2868239,9
3193,KBN,10,stock,94,2,0,stock,f4e3,766693875,30279475789337,30279526636960,815846252,766,195,47838037,83604,0,1,582041,6956798,23
3193,KBN,10,stock,95,2,1,stock,c8g4,195135185,30279527126802,30279598165669,224096318,815,195,70783852,84236,4637,1,723852,4653943,34
3193,KBN,10,stock,96,2,0,stock,e3d2,815846252,30279598544516,30279604992114,909398654,815,224,6340009,80150,5268,1,474117,5339546,11
3193,KBN,10,stock,97,2,1,stock,d8f7,224096318,30279605222088,30279610545456,318772950,909,224,5209564,61812,2414,1,335028,2702732,31
3193,KBN,10,stock,98,2,0,stock,d2c1,909398654,30279610709241,30279611125323,1008982572,909,318,371524,73800,2724,1,177996,281860,1
3193,KBN,10,stock,99,2,1,stock,f7h6,318772950,30279611227165,30279611632752,418367363,1008,318,261239,54271,0,2,278166,43585,66
3193,KBN,10,table,0,2,0,stock,f8g7,10000000000,30229155978044,30229457919699,9798058345,10000,10000,301562346,130063,4358003,2,794337,3727491,12
3193,KBN,10,table,1,2,1,table,d6f7,10000000000,30229458305016,30229464675315,10093629701,9798,10000,6312468,6708690,59528,1,6708690,59528,1
3193,KBN,10,table,2,2,0,stock,g7h7,9798058345,30229465013291,30229709078341,9653993295,9798,10093,243663707,54221,0,1,725333,6987695,9
3193,KBN,10,table,3,2,1,table,e6f6,10093629701,30229709463557,30229714625089,10188468169,9653,10093,5164665,5561647,29284,1,5561647,29284,1
3193,KBN,10,table,4,2,0,stock,h7g8,9653993295,30229714922144,30230509907450,8959007989,9653,10188,790708228,66659,5022664,2,491992,5089323,7
3193,KBN,10,table,5,2,1,table,h5g6,10188468169,30230510422811,30230516624669,10282266311,8959,10188,6176485,6701919,27571,1,6701919,27571,1
3193,KBN,10,table,6,2,0,stock,g8f8,8959007989,30230516824949,30230944147118,8631685820,8959,10282,427089036,53460,0,1,411793,7174725,5
3193,KBN,10,table,7,2,1,table,g6h7,10282266311,30230944519255,30230949672283,10377113283,8631,10282,5130354,5512574,24497,1,5512574,24497,1
3193,KBN,10,table,8,2,0,stock,f8e8,8631685820,30230949860225,30231184143971,8497402074,8631,10377,234015553,53539,0,1,443191,6141632,12
3193,KBN,10,table,9,2,1,table,f7e5,10377113283,30231184537270,30231189968916,10471681637,8497,10377,5434367,5838030,24607,1,5838030,24607,1
3193,KBN,10,table,10,2,0,stock,e8d8,8497402074,30231190163677,30231408440266,8379125485,8497,10471,217912539,51207,0,1,517141,5847004,9
3193,KBN,10,table,11,2,1,table,f6e6,10471681637,30231408976909,30231415453999,10565204547,8379,10471,6479707,7030209,26679,1,7030209,26679,1
3193,KBN,10,table,12,2,0,stock,d8c7,8379125485,30231415630423,30231881093452,8013662456,8379,10565,461368345,53669,4347807,2,421088,4370961,9
3193,KBN,10,table,13,2,1,table,e5d7,10565204547,30231881477947,30231887180528,10659501966,8013,10565,5681065,6076305,24467,1,6076305,24467,1
3193,KBN,10,table,14,2,0,stock,c7b7,8013662456,30231887493977,30232323947657,7677208776,8013,10659,424082427,55492,0,1,716118,4506112,10
3193,KBN,10,table,15,2,1,table,h7d3,10659501966,30232324354666,30232330323375,10753533257,7677,10659,5948315,6290956,23335,1,6290956,23335,1
3193,KBN,10,table,16,2,0,stock,b7c6,7677208776,30232330499719,30234445827939,5661880556,7677,10753,2107680706,53770,0,1,273837,5501598,3
3193,KBN,10,table,17,2,1,table,d3a6,10753533257,30234446197392,30234452273114,10847457535,5661,10753,6051488,6465506,26700,1,6465506,26700,1
3193,KBN,10,table,18,2,0,stock,c6c7,5661880556,30234452439753,30234969621796,5244698513,5661,10847,516724313,55583,3545750,2,326888,3563967,4
3193,KBN,10,table,19,2,1,table,a6b5,10847457535,30234970016906,30234975101677,10942372764,5244,10847,5063855,5468799,24266,1,5468799,24266,1
3193,KBN,10,table,20,2,0,stock,c7d8,5244698513,30234975284680,30235557809383,4762173810,5244,10942,578402192,61141,0,1,327789,5093499,5
3193,KBN,10,table,21,2,1,table,d7b6,10942372764,30235558186867,30235563698847,11036860784,4762,10942,5514327,5903587,25328,1,5903587,25328,1
3193,KBN,10,table,22,2,0,stock,d8c7,4762173810,30235563917744,30235878521272,4547570282,4762,11036,314269301,56074,4059897,2,382651,4084013,4
3193,KBN,10,table,23,2,1,table,b6a4,11036860784,30235878905246,30235882819147,11132946883,4547,11036,3915672,4310792,864880,2,4310792,864880,2
3193,KBN,10,table,24,2,0,stock,c7d8,4547570282,30235883859452,30236172022640,4359407094,4547,11132,280528415,55923,4090803,2,366638,4146726,4
3193,KBN,10,table,25,2,1,table,e6d6,11132946883,30236172671099,30236177233189,11228384793,4359,11132,4536488,5195291,29935,1,5195291,29935,1
3193,KBN,10,table,26,2,0,stock,d8c8,4359407094,30236177402923,30236356608283,4280201734,4359,11228,175410110,60179,0,1,293427,6602400,3
3193,KBN,10,table,27,2,1,table,a4c5,11228384793,30236357173117,30236365680615,11319877295,4280,11228,8479801,9057172,31087,1,9057172,31087,1
3193,KBN,10,table,28,2,0,stock,c8d8,4280201734,30236365937349,30236597722719,4148416364,4280,11319,231590615,78868,0,1,437943,6063306,5
3193,KBN,10,table,29,2,1,table,b5a4,11319877295,30236598141054,30236603787796,11414230553,4148,11319,5648488,6077287,23685,1,6077287,23685,1
3193,KBN,10,table,30,2,0,stock,d8c8,4148416364,30236603972892,30236773219539,4079169717,4148,11414,166381144,79318,4012356,2,382500,4052105,6
3193,KBN,10,table,31,2,1,table,a4d7,11414230553,30236773616283,30236784173620,11503673216,4079,11414,6888762,7296541,3670256,2,7296541,3670256,2
3193,KBN,10,table,32,2,0,stock,c8b8,4079169717,30236784485827,30236934225829,4029429715,4079,11503,149367445,81011,0,1,552024,3515615,6
3193,KBN,10,table,33,2,1,table,d6c6,11503673216,30236934599738,30236939854864,11598418090,4029,11503,5257063,5642177,24247,1,5642177,24247,1
3193,KBN,10,table,34,2,0,stock,b8a7,4029429715,30236940079189,30237060200977,4009307927,4029,11598,119800486,55273,0,1,376720,7920677,32
3193,KBN,10,table,35,2,1,table,c6c7,11598418090,30237060594034,30237065553718,11693458406,4009,11598,4939310,5344073,22824,1,5344073,22824,1
3193,KBN,10,table,36,2,0,stock,a7a8,4009307927,30237065786617,30237069297214,4105797330,4009,11693,3430138,63896,2201604,2,307368,2216717,8
3193,KBN,10,table,37,2,1,table,c7b6,11693458406,30237069463012,30237075656721,11787264697,4105,11693,6183525,6353008,11327,1,6353008,11327,1
3193,KBN,10,table,38,2,0,stock,a8b8,4105797330,30237075790441,30237076147275,4205440496,4105,11787,307218,47841,0,1,142753,307218,1
3193,KBN,10,table,39,2,1,table,c5a6,11787264697,30237076250539,30237081369551,11882145685,4205,11787,5120329,5265095,2285610,1,5265095,2285610,1
3193,KBN,10,table,40,2,0,stock,b8a8,4205440496,30237083833985,30237084023859,4305250622,4205,11882,120260,54091,66169,2,233128,120260,1
3193,KBN,10,table,41,2,1,table,d7c6,11882145685,30237084131580,30237086470336,11979806929,4305,11882,2340071,2458227,0,0,2458227,0,0
3999,KBN,10,corner,0,0,0,stock,c7b6,10000000000,30303671065866,30304223759509,9547306357,10000,10000,548606328,164235,0,1,871539,4937427,12
3999,KBN,10,corner,1,0,1,corner,d5d4,10000000000,30304224330954,30304773033783,9551297171,9547,10000,548236694,177595,0,1,732853,3669014,15
3999,KBN,10,corner,2,0,0,stock,b6b5,9547306357,30304773379690,30305196577656,9224108391,9547,9551,415539308,77596,4226,1,663709,2543535,11
3999,KBN,10,corner,3,0,1,corner,g2d5,9551297171,30305197129281,30305617233684,9231192768,9224,9551,419795619,98718,6990,1,832991,2725096,7
3999,KBN,10,corner,4,0,0,stock,b5a4,9224108391,30305617717747,30305881854885,9059971253,9224,9231,263670684,95232,6340,1,878842,2131710,10
3999,KBN,10,corner,5,0,1,corner,d5c4,9231192768,30305882379410,30306309056840,8904515338,9059,9231,426266771,103425,5668,1,881496,5465755,8
3999,KBN,10,corner,6,0,0,stock,a4b4,9059971253,30306309460113,30306603121005,8866310361,9059,8904,292058789,83044,4156,1,728677,3135588,11
3999,KBN,10,corner,7,0,1,corner,g3e4,8904515338,30306603515024,30307136165652,8471864710,8866,8904,528684397,81422,4326,1,685672,4364612,8
3999,KBN,10,corner,8,0,0,stock,b4a3,8866310361,30307136512881,30307498512336,8604310906,8866,8471,358028701,76114,4216,1,659374,3386382,9
3999,KBN,10,corner,9,0,1,corner,d4c3,8471864710,30307499032564,30308192609372,7878287902,8604,8471,693297817,104025,6280,1,742968,4813772,5
3999,KBN,10,corner,10,0,0,stock,a3a4,8604310906,30308193262910,30308437080436,8460493380,8604,7878,243516688,103254,7411,1,802406,2610455,4
3999,KBN,10,corner,11,0,1,corner,e4d6,7878287902,30308437481075,30309688384611,6727384366,8460,7878,1246087355,98807,8493,1,617291,2376996,4
3999,KBN,10,corner,12,0,0,stock,a4a5,8460493380,30309688833742,30309976931565,8272395557,8460,6727,287756671,88162,4747,1,707385,3046945,8
3999,KBN,10,corner,13,0,1,corner,c4b5,6727384366,30309977336060,30310343599722,6461120704,8272,6727,362359964,85447,3986,1,553095,2536444,4
3999,KBN,10,corner,14,0,0,stock,a5b6,8272395557,30310344179950,30311240597951,7475977556,8272,6461,895671835,104095,0,1,396270,3834491,12
3999,KBN,10,corner,15,0,1,corner,c3b4,6461120704,30311241095085,30311573176209,6229039580,7475,6461,331885787,100780,0,1,666535,2906396,4
3999,KBN,10,corner,16,0,0,stock,b6c7,7475977556,30311573587034,30311906094615,7243469975,7475,6229,332291233,87290,0,1,541418,2415423,3
3999,KBN,10,corner,17,0,1,corner,d6f7,6229039580,30311906510267,30312497675729,5737874118,7243,6229,590894190,87390,0,1,641716,5510872,7
3999,KBN,10,corner,18,0,0,stock,c7b6,7243469975,30312498138250,30312804468844,7037139381,7243,5737,306152430,99428,6139,1,612434,5719548,4
3999,KBN,10,corner,19,0,1,corner,b5e8,5737874118,30312804901101,30313376887762,5265887457,7037,5737,571591373,88482,5078,1,691700,2967798,5
3999,KBN,10,corner,20,0,0,stock,b6c7,7037139381,30313377300209,30313626687410,6887752180,7037,5265,249149090,87551,4216,1,632294,2583714,4
3999,KBN,10,corner,21,0,1,corner,b4a5,5265887457,30313627118304,30314088379514,4904626247,6887,5265,460911229,91847,0,1,576129,4879640,4
3999,KBN,10,corner,22,0,0,stock,c7b7,6887752180,30314088813333,30314353224134,6723341379,6887,4904,264178754,83124,4847,1,646334,3065274,6
3999,KBN,10,corner,23,0,1,corner,e8a4,4904626247,30314353559235,30314617924232,4740261250,6723,4904,263091700,81782,0,1,492393,2442965,4
3999,KBN,10,corner,24,0,0,stock,b7c7,6723341379,30314618456388,30314922120614,6519677153,6723,4740,303094568,101171,6229,1,710139,5404663,4
3999,KBN,10,corner,25,0,1,corner,a5a6,4740261250,30314922623857,30315256517222,4506367885,6519,4740,326012321,128001,5518,1,710379,5203683,5
3999,KBN,10,corner,26,0,0,stock,c7c8,6519677153,30315256961687,30315440949383,6435689457,6519,4506,180193463,88713,4466,1,583661,2919446,5
3999,KBN,10,corner,27,0,1,corner,a6b6,4506367885,30315441303212,30315787683691,4259987406,6435,4506,342520484,80199,4507,1,559144,2582253,6
3999,KBN,10,corner,28,0,0,stock,c8b8,6435689457,30315788066213,30315965680038,6358075632,6435,4259,177227670,80880,4697,1,289683,3827711,6
3999,KBN,10,corner,29,0,1,corner,a4d7,4259987406,30315966270481,30316269123183,4057134704,6358,4259,298862724,86469,5658,1,888325,5601887,6
3999,KBN,10,corner,30,0,0,stock,b8a8,6358075632,30316269500858,30316439154559,6288421931,6358,4057,164231261,88522,5167,1,722177,3942893,12
3999,KBN,10,corner,31,0,1,corner,f7g5,4057134704,30316439677410,30316659818791,3936993323,6288,4057,219616971,125197,5878,1,1026131,4144393,17
3999,KBN,10,corner,32,0,0,stock,a8b8,6288421931,30316660196786,30316826285236,6222333481,6288,3936,165611698,86789,4217,1,626738,3691808,41
3999,KBN,10,corner,33,0,1,corner,g5e6,3936993323,30316826685705,30316980509509,3883169519,6222,3936,153300907,124005,4166,1,783372,5149392,32
3999,KBN,10,corner,34,0,0,stock,b8a8,6222333481,30316981057439,30316983757446,6319633474,6222,3883,2063419,104706,6820,1,595568,2443927,2
3999,KBN,10,corner,35,0,1,corner,e6c7,3883169519,30316984052578,30316985638038,3981584059,6319,3883,1359950,86309,4336,2,257573,0,65
3999,KBN,10,corner,36,0,0,stock,a8b8,6319633474,30316985850937,30316986418846,6419065565,6319,3981,503952,75032,0,1,225667,503952,1
3999,KBN,10,corner,37,0,1,corner,c7a6,3981584059,30316986578585,30316987345972,4080816672,6419,3981,568590,70825,0,2,410190,55122,66
3999,KBN,10,corner,38,0,0,stock,b8a8,6419065565,30316987501385,30316987716697,6518850253,6419,4080,146930,68613,0,1,165617,146930,1
3999,KBN,10,corner,39,0,1,corner,d7c6,4080816672,30316987888213,30316988498135,4180206750,6518,4080,385455,68933,0,2,454327,54331,66
3999,KBN,10,stock,0,0,0,stock,c7b6,10000000000,30289691015878,30290204336622,9586679256,10000,10000,509326388,135592,4884006,2,733694,4655396,12
3999,KBN,10,stock,1,0,1,stock,d5c4,10000000000,30290204722438,30290524331265,9780391173,9586,10000,318398480,153729,3123580,2,869757,3057542,15
3999,KBN,10,stock,2,0,0,stock,b6a5,9586679256,30290524708079,30290975775508,9235611827,9586,9780,450450532,100099,0,1,637042,3295757,7
3999,KBN,10,stock,3,0,1,stock,g2c6,9780391173,30290976352551,30291998532706,8858211018,9235,9780,1018154793,101251,6810,1,624151,7136637,7
3999,KBN,10,stock,4,0,0,stock,a5b6,9235611827,30291999069969,30292730223094,8604458702,9235,8858,723219607,98016,6510,1,799934,4795104,8
3999,KBN,10,stock,5,0,1,stock,c4d5,8858211018,30292730693728,30293761410384,7927494362,8604,8858,1030492109,107050,5518,1,647398,5158065,4
3999,KBN,10,stock,6,0,0,stock,b6c7,8604458702,30293761846576,30294200550930,8265754348,8604,7927,438463883,85137,4327,1,583521,6037387,4
3999,KBN,10,stock,7,0,1,stock,d5c5,7927494362,30294200980722,30294949796294,7278678790,8265,7927,740713994,84546,5038,1,791500,2898705,6
3999,KBN,10,stock,8,0,0,stock,c7b8,8265754348,30294950214059,30295526221402,7789747005,8265,7278,572158575,85577,4847,1,599716,5668196,4
3999,KBN,10,stock,9,0,1,stock,c5b6,7278678790,30295526729000,30295744721374,7160686416,7789,7278,217742900,79208,5117,1,731512,5135141,8
3999,KBN,10,stock,10,0,0,stock,b8c8,7789747005,30295745161883,30295992725847,7642183041,7789,7160,247098063,82283,5078,1,833832,2733469,10
3999,KBN,10,stock,11,0,1,stock,g3f5,7160686416,30295993310792,30297993583711,5260413497,7642,7160,1992437395,102263,7281,1,910567,2525838,13
3999,KBN,10,stock,12,0,0,stock,c8d8,7642183041,30297994122247,30298446394181,7289911107,7642,5260,448384715,99127,7932,1,818702,5754976,5
3999,KBN,10,stock,13,0,1,stock,b6c5,5260413497,30298446982511,30298821142762,4986253246,7289,5260,369806543,104235,6270,1,774966,4830056,3
3999,KBN,10,stock,14,0,0,stock,d8c8,7289911107,30298821888727,30299275794349,6936005485,7289,4986,453540242,111526,0,1,931610,6109164,4
3999,KBN,10,stock,15,0,1,stock,c5d6,4986253246,30299276265884,30300712645424,3649873706,6936,4986,1426023025,93399,0,1,594689,6166800,9
3999,KBN,10,stock,16,0,0,stock,c8b8,6936005485,30300713100073,30301012251901,6736853657,6936,3649,295164923,90105,0,1,671292,2913057,4
3999,KBN,10,stock,17,0,1,stock,d6d7,3649873706,30301012781172,30301359253416,3403401462,6736,3649,346221436,90245,0,1,754516,3217711,6
3999,KBN,10,stock,18,0,0,stock,b8a7,6736853657,30301359847885,30301697257221,6499444321,6736,3403,336267936,87560,0,1,834495,5027831,10
3999,KBN,10,stock,19,0,1,stock,f5d6,3403401462,30301697713082,30301884919952,3316194592,6499,3403,186880032,113209,0,1,609058,2287974,4
3999,KBN,10,stock,20,0,0,stock,a7b6,6499444321,30301885479238,30302171515818,6313407741,6499,3316,285525551,105378,0,1,735627,6518776,5
3999,KBN,10,stock,21,0,1,stock,d6b7,3316194592,30302171897698,30302396339528,3191752762,6313,3316,220194702,84206,0,1,590612,4472853,10
3999,KBN,10,stock,22,0,0,stock,b6a7,6313407741,30302396769110,30302607463987,6202712864,6313,3191,209685493,87009,0,1,730900,3231040,7
3999,KBN,10,stock,23,0,1,stock,d7c7,3191752762,30302607918827,30302820029561,3079642028,6202,3191,211746430,125016,0,1,794716,4081118,7
3999,KBN,10,stock,24,0,0,stock,a7a6,6202712864,30302820419454,30302993254667,6129877651,6202,3079,172385285,86939,0,1,701437,3582104,14
3999,KBN,10,stock,25,0,1,stock,c6d7,3079642028,30302993755876,30303173938254,2999459650,6129,3079,179837403,86039,0,1,823008,6243825,13
3999,KBN,10,stock,26,0,0,stock,a6a7,6129877651,30303174393615,30303337377949,6066893317,6129,2999,158934159,103835,0,1,809685,9257131,31
3999,KBN,10,stock,27,0,1,stock,d7b5,2999459650,30303337814953,30303523903321,2913371282,6066,2999,185657687,89423,4918,1,966852,6052269,36
3999,KBN,10,stock,28,0,0,stock,a7a8,6066893317,30303524346384,30303549057008,6142182693,6066,2913,24555544,87691,4387,1,458024,3536316,11
3999,KBN,10,stock,29,0,1,stock,b7d6,2913371282,30303549459600,30303553524256,3009306626,6142,2913,3970824,80210,3936,1,481819,2435674,3
3999,KBN,10,stock,30,0,0,stock,a8a7,6142182693,30303553768211,30303554146617,6241804287,6142,3009,330153,64897,2494,1,263703,252086,1
3999,KBN,10,stock,31,0,1,stock,d6c8,3009306626,30303554266436,30303554756509,3108816553,6241,3009,323823,59288,1883,2,317373,0,65
3999,KBN,10,stock,32,0,0,stock,a7a8,6241804287,30303555039822,30303555188855,6341655254,6241,3108,108262,54582,0,1,290984,108262,1
3999,KBN,10,stock,33,0,1,stock,b5c6,3108816553,30303555286281,30303555691517,3208411317,6341,3108,263033,54882,0,2,273047,44807,66
3999,KBN,10,table,0,0,0,stock,c7b6,10000000000,30317043942107,30317572071237,9571870870,10000,10000,527766391,136965,957839,3,736117,0,18
3999,KBN,10,table,1,0,1,table,g2f1,10000000000,30317572479007,30317577541017,10094937990,9571,10000,5033870,5453126,29354,1,5453126,29354,1
3999,KBN,10,table,2,0,0,stock,b6a5,9571870870,30317577666674,30317926117489,9323420055,9571,10094,348119843,82693,6279669,2,415529,6332007,9
3999,KBN,10,table,3,0,1,table,d5d4,10094937990,30317926498799,30317930992347,10190444442,9323,10094,4495276,4887492,22704,1,4887492,22704,1
3999,KBN,10,table,4,0,0,stock,a5b4,9323420055,30317931205906,30318425955501,8928670460,9323,10190,493716978,64526,0,1,427358,5556559,10
3999,KBN,10,table,5,0,1,table,f1c4,10190444442,30318426460897,30318432064294,10284841045,8928,10190,5581146,6096925,23816,1,6096925,23816,1
3999,KBN,10,table,6,0,0,stock,b4a3,8928670460,30318432203222,30318817499471,8643374211,8928,10284,373660565,67110,3736354,2,433747,7808980,6
3999,KBN,10,table,7,0,1,table,d4c3,10284841045,30318817919439,30318823929695,10378830789,8643,10284,5989327,6420911,22713,1,6420911,22713,1
3999,KBN,10,table,8,0,0,stock,a3a4,8643374211,30318824089424,30319270839943,8296623692,8643,10378,439152276,66229,0,1,366447,3911085,8
3999,KBN,10,table,9,0,1,table,g3f5,10378830789,30319271230777,30319278237973,10471823593,8296,10378,6985672,7387852,23485,1,7387852,23485,1
3999,KBN,10,table,10,0,0,stock,a4a5,8296623692,30319278442108,30320764669923,6910395877,8296,10471,1478690532,71496,0,1,414309,5555798,4
3999,KBN,10,table,11,0,1,table,c3b3,10471823593,30320765106285,30320772343244,10564586634,6910,10471,7213252,7660148,25939,1,7660148,25939,1
3999,KBN,10,table,12,0,0,stock,a5b6,6910395877,30320772519998,30321083877407,6699038468,6910,10564,311186476,72418,3444970,2,526405,3481724,5
3999,KBN,10,table,13,0,1,table,b3b4,10564586634,30321084494069,30321092785475,10656295228,6699,10564,8266083,8682184,27611,1,8682184,27611,1
3999,KBN,10,table,14,0,0,stock,b6c6,6699038468,30321093136269,30321673899020,6218275717,6699,10656,580519727,75022,0,1,574116,6862198,7
3999,KBN,10,table,15,0,1,table,c4f7,10656295228,30321674300610,30321683217915,10747377923,6218,10656,8892197,9304602,27641,1,9304602,27641,1
3999,KBN,10,table,16,0,0,stock,c6b7,6218275717,30321683426707,30321902666887,6099035537,6218,10747,218884685,70705,0,1,539835,4574014,7
3999,KBN,10,table,17,0,1,table,b4c5,10747377923,30321903254725,30321914549765,10836082883,6099,10747,11267371,11868107,31156,1,11868107,31156,1
3999,KBN,10,table,18,0,0,stock,b7b8,6099035537,30321914814500,30322122500547,5991349490,6099,10836,205743635,96064,5139007,2,457030,5185517,5
3999,KBN,10,table,19,0,1,table,f5g7,10836082883,30322122996278,30322133563359,10925515802,5991,10836,10539675,11046351,30235,1,11046351,30235,1
3999,KBN,10,table,20,0,0,stock,b8c8,5991349490,30322133796808,30323864247699,4360898599,5991,10925,1709852920,101200,4563719,2,462020,4684838,10
3999,KBN,10,table,21,0,1,table,f7e8,10925515802,30323864660796,30323870557007,11019619591,4360,10925,5898320,6353259,0,0,6353259,0,0
3999,KBN,10,table,22,0,0,stock,c8d8,4360898599,30323870723756,30324197191902,4134430453,4360,11019,326245603,96554,0,1,343353,5276402,5
3999,KBN,10,table,23,0,1,table,c5d6,11019619591,30324198671964,30324204645581,11113645974,4134,11019,5946211,7437506,31717,1,7437506,31717,1
3999,KBN,10,table,24,0,0,stock,d8c8,4134430453,30324205023085,30324629870369,3809583169,4134,11113,420722535,79128,0,1,564714,6975677,3
3999,KBN,10,table,25,0,1,table,e8c6,11113645974,30324630303356,30324635715124,11208234206,3809,11113,5415600,5859512,39939,1,5859512,39939,1
3999,KBN,10,table,26,0,0,stock,c8b8,3809583169,30324635980651,30324882679838,3662883982,3809,11208,246401773,83195,3943733,2,416832,4012747,5
3999,KBN,10,table,27,0,1,table,d6c5,11208234206,30324883280997,30324893328161,11298187042,3662,11208,10024116,10636649,27641,1,10636649,27641,1
3999,KBN,10,table,28,0,0,stock,b8a7,3662883982,30324893666547,30325074619244,3581931285,3662,11298,180730206,122783,0,1,544332,6345697,4
3999,KBN,10,table,29,0,1,table,c5b5,11298187042,30325075218179,30325085173015,11388232206,3581,11298,9924066,10535207,33871,1,10535207,33871,1
3999,KBN,10,table,30,0,0,stock,a7b8,3581931285,30325085439974,30325240259387,3527111872,3581,11388,154540082,105868,6511094,2,530541,6557654,5
3999,KBN,10,table,31,0,1,table,b5b6,11388232206,30325240835899,30325250250278,11478817827,3527,11388,9386826,9975494,30645,1,9975494,30645,1
3999,KBN,10,table,32,0,0,stock,b8c8,3527111872,30325250478639,30325387707560,3489882951,3527,11478,133311807,90074,0,1,486135,5521478,7
3999,KBN,10,table,33,0,1,table,g7e6,11478817827,30325388170242,30325397001760,11569986309,3489,11478,8810474,8963833,22774,1,8963833,22774,1
3999,KBN,10,table,34,0,0,stock,c8b8,3489882951,30325397210381,30325504274108,3482819224,3489,11569,106729933,80280,0,1,529700,6794127,17
3999,KBN,10,table,35,0,1,table,c6d7,11569986309,30325504682638,30325510906599,11663762348,3482,11569,6201923,6621209,24196,1,6621209,24196,1
3999,KBN,10,table,36,0,0,stock,b8a8,3482819224,30325511080349,30325516053992,3577845581,3482,11663,4885018,72568,0,1,217514,4885018,1
3999,KBN,10,table,37,0,1,table,e6c5,11663762348,30325516269243,30325522384192,11757647399,3577,11663,6117016,6374971,0,0,6374971,0,0
3999,KBN,10,table,38,0,0,stock,a8b8,3577845581,30325522546084,30325522982946,3677408719,3577,11757,374549,74281,0,1,174971,374549,1
3999,KBN,10,table,39,0,1,table,c5a6,11757647399,30325523105760,30325529494858,11851258301,3677,11757,6391255,6561239,0,0,6561239,0,0
3999,KBN,10,table,40,0,0,stock,b8a8,3677408719,30325529661267,30325529892172,3777177814,3677,11851,175913,102293,0,1,175902,175913,1
3999,KBN,10,table,41,0,1,table,d7c6,11851258301,30325530071590,30325532876752,11948453139,3777,11851,2807068,3029670,0,0,3029670,0,0
4331,KBN,10,corner,0,2,1,stock,g2h3,10000000000,30314503367319,30314774279963,9829087356,10000,10000,269416069,96373,4992099,2,857338,4358643,15
4331,KBN,10,corner,1,2,0,corner,e4f3,10000000000,30314774708184,30315045019208,9829688976,10000,9829,269324608,197284,5132718,2,814825,4884327,11
4331,KBN,10,corner,2,2,1,stock,h3h4,9829087356,30315045354139,30315318518080,9655923415,9829,9829,261103825,65848,4096,1,623080,2554401,8
4331,KBN,10,corner,3,2,0,corner,c5e7,9829688976,30315318924177,30315779361587,9469251566,9829,9655,460000873,69544,4006,1,751044,4963385,10
4331,KBN,10,corner,4,2,1,stock,h4h5,9655923415,30315779886152,30316045568054,9490241513,9469,9655,264926759,83154,6369,1,1251318,3971285,13
4331,KBN,10,corner,5,2,0,corner,e2f4,9469251566,30316046294170,30316388347798,9227197938,9469,9490,341688563,167530,42082,1,1045560,5441819,11
4331,KBN,10,corner,6,2,1,stock,h5h6,9490241513,30316388734206,30316757134128,9221841591,9227,9490,368178218,70756,4687,1,585914,3152663,6
4331,KBN,10,corner,7,2,0,corner,f3g4,9227197938,30316757516029,30318316345046,7768368921,9227,9221,1558626370,67060,4296,1,549619,2381724,8
4331,KBN,10,corner,8,2,1,stock,h6g7,9221841591,30318316739706,30318570565132,9068016165,7768,9221,249537690,69624,5128,1,618653,3145092,6
4331,KBN,10,corner,9,2,0,corner,g4f5,7768368921,30318570919341,30319251875310,7187412952,7768,9068,680620473,67540,4407,1,684642,4973119,4
4331,KBN,10,corner,10,2,1,stock,g7f7,9068016165,30319252297532,30319912709847,8507603850,7187,9068,656545556,70906,4486,1,462198,3612700,4
4331,KBN,10,corner,11,2,0,corner,e7f6,7187412952,30319913204326,30320322004830,6878612448,7187,8507,408490031,80801,5838,1,706464,2672097,9
4331,KBN,10,corner,12,2,1,stock,f7e8,8507603850,30320322354824,30320810711205,8119247469,6878,8507,488108735,66269,4757,1,567927,5562794,4
4331,KBN,10,corner,13,2,0,corner,f5e6,6878612448,30320811233546,30321169501056,6620344938,6878,8119,358016895,83855,6790,1,744049,4644429,12
4331,KBN,10,corner,14,2,1,stock,e8f8,8119247469,30321169922557,30321370162687,8019007339,6620,8119,196953630,69263,4848,1,578052,5981154,4
4331,KBN,10,corner,15,2,0,corner,f6g5,6620344938,30321370627562,30321987447548,6103524952,6620,8019,609148954,78708,6239,1,640216,5217975,4
4331,KBN,10,corner,16,2,1,stock,f8e8,8019007339,30321987850400,30322221259277,7885598462,6103,8019,220465715,71286,5118,1,562410,4049151,4
4331,KBN,10,corner,17,2,0,corner,f4h5,6103524952,30322221824602,30322628353145,5796996409,6103,7885,406291390,82753,6130,1,758491,6046201,4
4331,KBN,10,corner,18,2,1,stock,e8f8,7885598462,30322628737860,30322973255680,7641080642,5796,7885,344218237,72549,4386,1,620336,3153815,5
4331,KBN,10,corner,19,2,0,corner,g5e7,5796996409,30322973661817,30323268278339,5602379887,5796,7641,286857686,92998,4067,1,570871,2207714,4
4331,KBN,10,corner,20,2,1,stock,f8g8,7641080642,30323268858696,30323547322183,7462617155,5602,7641,276811532,84055,0,1,2122067,3145943,7
4331,KBN,10,corner,21,2,0,corner,e6f6,5602379887,30323547864063,30323852089639,5398154311,5602,7462,303565907,87300,0,1,1030648,4137062,7
4331,KBN,10,corner,22,2,1,stock,g8h7,7462617155,30323852595865,30324043846206,7371366814,5398,7462,189561136,85898,0,1,1358017,8388715,15
4331,KBN,10,corner,23,2,0,corner,e7f8,5398154311,30324044404049,30324336727680,5205830680,5398,7371,288831506,89533,0,1,1388077,8990783,20
4331,KBN,10,corner,24,2,1,stock,h7g8,7371366814,30324337293005,30324524333869,7284325950,5205,7371,185181110,89724,0,1,1414637,7433321,32
4331,KBN,10,corner,25,2,0,corner,f6e7,5205830680,30324525002558,30324773791551,5057041687,5205,7284,248046386,76093,5469,1,1333269,2881309,32
4331,KBN,10,corner,26,2,1,stock,g8h7,7284325950,30324774185821,30324792677164,7365834607,5057,7284,18335125,73479,0,1,524342,5843648,7
4331,KBN,10,corner,27,2,0,corner,e7f7,5057041687,30324793069981,30324803506838,5146604830,5057,7365,10330612,69744,4036,1,479105,2829671,4
4331,KBN,10,corner,28,2,1,stock,h7h8,7365834607,30324803828048,30324804185903,7465476752,5146,7365,306928,56875,3465,1,344133,233519,1
4331,KBN,10,corner,29,2,0,corner,f8g7,5146604830,30324804312482,30324804760341,5246156971,5146,7465,284693,47691,1903,2,302783,0,65
4331,KBN,10,corner,30,2,1,stock,h8h7,7465476752,30324804870366,30324805007741,7565339377,5246,7465,98167,41582,1893,1,137936,48433,1
4331,KBN,10,corner,31,2,0,corner,h5f6,5246156971,30324805099668,30324805473918,5345782721,5246,7565,233206,39288,0,2,264055,30816,66
4331,KBN,10,stock,0,2,1,stock,g2h3,10000000000,30279729113075,30279970081863,9859031212,10000,10000,240627789,92819,3257730,2,759311,2623244,15
4331,KBN,10,stock,1,2,0,stock,e4f4,10000000000,30279970534720,30280742369348,9328165372,10000,9859,771138678,124926,5424823,2,905954,5094481,11
4331,KBN,10,stock,2,2,1,stock,h3h4,9859031212,30280742763648,30280991377459,9710417401,9328,9859,248104188,70155,4717,1,840403,5141541,11
4331,KBN,10,stock,3,2,0,stock,e2g3,9328165372,30280991788234,30281264946783,9155006823,9328,9710,272841680,70475,4667,1,699623,4098165,10
4331,KBN,10,stock,4,2,1,stock,h4h3,9710417401,30281265389785,30281552622995,9523184191,9155,9710,286959510,68482,4367,1,693506,2517876,7
4331,KBN,10,stock,5,2,0,stock,f4f3,9155006823,30281553037895,30282313223889,8494820829,9155,9523,739777579,73449,4577,1,853230,2856272,10
4331,KBN,10,stock,6,2,1,stock,h3h2,9523184191,30282313780170,30282579928914,9357035447,8494,9523,265718913,71897,5288,1,968795,2118210,9
4331,KBN,10,stock,7,2,0,stock,c5f2,8494820829,30282580383463,30283058958089,8116246203,8494,9357,478302089,71026,4687,1,600767,3502706,5
4331,KBN,10,stock,8,2,1,stock,h2h3,9357035447,30283059417766,30283290911031,9225542182,8116,9357,231293878,70305,4156,1,636850,4338022,4
4331,KBN,10,stock,9,2,0,stock,g3e2,8116246203,30283291278500,30284426844619,7080680084,8116,9225,1135011206,70656,4487,1,889015,4612962,11
4331,KBN,10,stock,10,2,1,stock,h3h2,9225542182,30284427346469,30284795284943,8957603708,7080,9225,367665717,81622,5839,1,754757,4539963,6
4331,KBN,10,stock,11,2,0,stock,e2c3,7080680084,30284795862646,30285572657137,6403885593,7080,8957,772580332,85628,7421,1,1051617,3969582,11
4331,KBN,10,stock,12,2,1,stock,h2h1,8957603708,30285573044907,30285833831481,8796817134,6403,8957,256725158,186528,4026,1,693626,3047681,10
4331,KBN,10,stock,13,2,0,stock,f2a7,6403885593,30285834283677,30286128042826,6210126444,6403,8796,293477095,59749,4888,1,699045,5642228,9
4331,KBN,10,stock,14,2,1,stock,h1h2,8796817134,30286128541642,30286461318664,8564040112,6210,8796,328696647,83795,6390,1,754533,3342928,6
4331,KBN,10,stock,15,2,0,stock,a7c5,6210126444,30286461710980,30287249839519,5521997905,6210,8564,784007421,103174,5779,1,801014,2144700,9
4331,KBN,10,stock,16,2,1,stock,h2h3,8564040112,30287250232297,30287533093743,8381178666,5521,8564,282464615,73770,0,1,769208,5852902,8
4331,KBN,10,stock,17,2,0,stock,c5e7,5521997905,30287533802813,30288253497777,4902302941,5521,8381,715603508,114571,0,1,1134902,6146741,13
4331,KBN,10,stock,18,2,1,stock,h3h2,8381178666,30288253934099,30288648508654,8086604111,4902,8381,390627626,73539,4217,1,664312,5964308,7
4331,KBN,10,stock,19,2,0,stock,c3e4,4902302941,30288648884255,30288978360225,4672826971,4902,8086,325522534,69183,4677,1,600656,3019966,11
4331,KBN,10,stock,20,2,1,stock,h2h1,8086604111,30288978803487,30289257868399,7907539199,4672,8086,278829611,80320,5558,1,655139,5084866,6
4331,KBN,10,stock,21,2,0,stock,e7d6,4672826971,30289258372412,30289496619875,4534579508,4672,7907,237541362,85558,6379,1,1176636,5492144,11
4331,KBN,10,stock,22,2,1,stock,h1g1,7907539199,30289497145631,30289742446905,7762237925,4534,7907,245045822,86129,5939,1,756166,2738946,10
4331,KBN,10,stock,23,2,0,stock,e4c3,4534579508,30289742880704,30290427096318,3950363894,4534,7762,683742555,75382,4948,1,642408,4996345,5
4331,KBN,10,stock,24,2,1,stock,g1h1,7762237925,30290427484528,30290646181465,7643540988,3950,7762,218409403,67911,4026,1,656191,4430199,9
4331,KBN,10,stock,25,2,0,stock,d6c5,3950363894,30290646611749,30291129935887,3567039756,3950,7643,479084071,73440,5077,1,660636,5223203,6
4331,KBN,10,stock,26,2,1,stock,h1h2,7643540988,30291130441794,30291365815931,7508166851,3567,7643,235061119,84826,6330,1,791500,5439546,6
4331,KBN,10,stock,27,2,0,stock,c5f2,3567039756,30291366271552,30292076613772,2956697536,3567,7508,709761915,113649,6079,1,759934,5569148,7
4331,KBN,10,stock,28,2,1,stock,h2h1,7508166851,30292077023936,30292417438709,7267752078,2956,7508,339277768,76414,4536,1,678800,3712981,9
4331,KBN,10,stock,29,2,0,stock,c3e4,2956697536,30292417984645,30292674778127,2799904054,2956,7267,251994940,76555,0,1,749397,6019171,5
4331,KBN,10,stock,30,2,1,stock,h1h2,7267752078,30292675144064,30292868575687,7174320455,2799,7267,193083515,74561,3756,1,616841,4757097,10
4331,KBN,10,stock,31,2,0,stock,f2g3,2799904054,30292869052550,30293063925124,2705031480,2799,7174,194545464,73009,5188,1,877498,2832677,9
4331,KBN,10,stock,32,2,1,stock,h2h1,7174320455,30293064342598,30293368711868,6969951185,2705,7174,303865101,78407,0,1,777792,3658278,11
4331,KBN,10,stock,33,2,0,stock,g3c7,2705031480,30293369467357,30293562392169,2612106668,2705,6969,192283156,97475,0,1,1288033,2533189,11
4331,KBN,10,stock,34,2,1,stock,h1g1,6969951185,30293562776103,30293779496641,6853230647,2612,6969,215302586,70685,0,1,593965,6412948,5
4331,KBN,10,stock,35,2,0,stock,e4c3,2612106668,30293779884281,30293966180578,2525810371,2612,6853,185998434,76665,4627,1,638563,3967750,7
4331,KBN,10,stock,36,2,1,stock,g1f1,6853230647,30293966594337,30294974505661,5945319323,2525,6853,1007530600,76404,4117,1,710972,5301479,9
4331,KBN,10,stock,37,2,0,stock,c7b6,2525810371,30294974892209,30295139229000,2461473580,2525,5945,164086055,76965,5368,1,613214,4988252,7
4331,KBN,10,stock,38,2,1,stock,f1e1,5945319323,30295139636730,30295536850265,5648105788,2461,5945,393003128,97225,4286,1,641556,4236711,7
4331,KBN,10,stock,39,2,0,stock,b6e3,2461473580,30295537213248,30296467377433,1631309395,2461,5648,926317250,69574,4556,1,465003,2677214,3
4331,KBN,10,stock,40,2,1,stock,e1f1,5648105788,30296467842107,30296760367832,5455580063,1631,5648,292273410,77635,5629,1,751430,4049973,5
4331,KBN,10,stock,41,2,0,stock,c3e4,1631309395,30296760779558,30296877589163,1614499790,1631,5455,116514373,74391,4997,1,678179,3101637,11
4331,KBN,10,stock,42,2,1,stock,f1e1,5455580063,30296878070132,30297471191272,4962458923,1614,5455,592719778,85728,5198,1,859152,5812983,11
4331,KBN,10,stock,43,2,0,stock,e4f2,1614499790,30297471782757,30297815777391,1370505156,1614,4962,343779288,68632,5999,1,734756,4108049,3
4331,KBN,10,stock,44,2,1,stock,e1f1,4962458923,30297816186443,30297969517075,4909128291,1370,4962,153086535,74711,4276,1,377001,3715593,12
4331,KBN,10,stock,45,2,0,stock,e3g5,1370505156,30297969877404,30298370086705,1070295855,1370,4909,399991090,74541,4777,1,555789,6008254,10
4331,KBN,10,stock,46,2,1,stock,f1g1,4909128291,30298370837968,30298590678769,4789287490,1070,4909,219429412,89534,6700,1,1136566,5035493,10
4331,KBN,10,stock,47,2,0,stock,g5e3,1070295855,30298591204735,30298717103575,1044397015,1070,4789,125493606,91817,7071,1,906253,4648044,9
4331,KBN,10,stock,48,2,1,stock,g1f1,4789287490,30298717572776,30299675181927,3931678339,1044,4789,949676875,85948,4317,1,720788,2311759,10
4331,KBN,10,stock,49,2,0,stock,e3c1,1044397015,30299675879150,30299858805971,961470194,1044,3931,182664160,78878,6499,1,933324,3969291,8
4331,KBN,10,stock,50,2,1,stock,f1e1,3931678339,30299859202925,30300251363433,3639517831,961,3931,391892999,78997,4016,1,641698,4688655,8
4331,KBN,10,stock,51,2,0,stock,c1f4,961470194,30300251784051,30300562923326,750330919,961,3639,306997021,79149,5257,1,790089,4093557,9
4331,KBN,10,stock,52,2,1,stock,e1f1,3639517831,30300563444866,30300781312546,3521650151,750,3639,217605572,91707,0,1,761094,4557750,6
4331,KBN,10,stock,53,2,0,stock,f2d3,750330919,30300781707046,30300904395766,727642199,750,3521,122455803,98447,4677,1,598063,2174424,7
4331,KBN,10,stock,54,2,1,stock,f1g1,3521650151,30300904824377,30301083777928,3442696600,727,3521,177958118,79499,0,1,625024,3957414,7
4331,KBN,10,stock,55,2,0,stock,f4d6,727642199,30301084259207,30301245559695,666341711,727,3442,161112977,77716,0,1,406487,3741662,9
4331,KBN,10,stock,56,2,1,stock,g1f1,3442696600,30301246046733,30301489546666,3299196667,666,3442,243315807,77976,0,1,646897,5951289,6
4331,KBN,10,stock,57,2,0,stock,d6f4,666341711,30301489954706,30301578224647,678071770,666,3299,87678209,77465,4667,1,960673,5910197,5
4331,KBN,10,stock,58,2,1,stock,f1g1,3299196667,30301580166991,30301718723595,3260640063,678,3299,133655134,154471,4597,1,4601093,6539206,7
4331,KBN,10,stock,59,2,0,stock,d3b2,678071770,30301719182892,30301798331040,698923622,678,3260,75257552,77536,4998,1,673657,4698814,8
4331,KBN,10,stock,60,2,1,stock,g1f1,3260640063,30301798875403,30302033953586,3125561880,698,3260,234743960,89714,5798,1,848606,5000611,9
4331,KBN,10,stock,61,2,0,stock,b2d1,698923622,30302034339533,30302146778548,686484607,698,3125,112162388,77866,4297,1,641797,5540616,10
4331,KBN,10,stock,62,2,1,stock,f1g1,3125561880,30302147116153,30302334136284,3038541749,686,3125,186835242,70846,4066,1,501219,4938237,9
4331,KBN,10,stock,63,2,0,stock,d1e3,686484607,30302334530754,30302412199945,708815416,686,3038,77501506,80079,4356,1,540768,5346547,4
4331,KBN,10,stock,64,2,1,stock,g1h1,3038541749,30302412568566,30302509522882,3041587433,708,3038,96698107,75082,3665,1,602949,3330879,7
4331,KBN,10,stock,65,2,0,stock,e3c4,708815416,30302509948017,30302902486776,416276657,708,3041,392261534,82393,4957,1,673084,5923768,8
4331,KBN,10,stock,66,2,1,stock,h1g1,3041587433,30302902872182,30303039116108,3005343507,416,3041,136049745,79739,4016,1,557723,5017626,6
4331,KBN,10,stock,67,2,0,stock,c4e3,416276657,30303039493833,30303238145303,317625187,416,3005,198438656,75914,3845,1,566794,4387416,7
4331,KBN,10,stock,68,2,1,stock,g1h1,3005343507,30303238537159,30303364291382,2979589284,317,3005,125548829,79038,3856,1,575739,5355319,3
4331,KBN,10,stock,69,2,0,stock,f4g3,317625187,30303364630059,30303468771339,313483907,317,2979,103991768,71707,4377,1,464263,3231431,6
4331,KBN,10,stock,70,2,1,stock,h1g1,2979589284,30303469168002,30303637003440,2911753846,313,2979,167370875,79258,4006,1,555367,6313150,6
4331,KBN,10,stock,71,2,0,stock,e3d5,313483907,30303637643827,30303819219328,231908406,313,2911,181363932,317134,5959,1,777980,5976036,5
4331,KBN,10,stock,72,2,1,stock,g1f1,2911753846,30303819705736,30303928940691,2902518891,231,2911,109009384,109062,5809,1,736980,4158144,5
4331,KBN,10,stock,73,2,0,stock,g3f4,231908406,30303929342502,30304061508080,199742828,231,2902,131869708,85247,0,1,633987,2605607,8
4331,KBN,10,stock,74,2,1,stock,f1e1,2902518891,30304061970421,30304249498562,2814990750,199,2902,187296632,85888,0,1,705903,6027051,6
4331,KBN,10,stock,75,2,0,stock,d5c3,199742828,30304250018910,30304363456368,186305370,199,2814,113288918,95102,0,1,615568,5979160,5
4331,KBN,10,stock,76,2,1,stock,e1f1,2814990750,30304363825169,30304641579498,2637236421,186,2814,277510284,82624,4727,1,626064,4062501,7
4331,KBN,10,stock,77,2,0,stock,f4e3,186305370,30304642083101,30304747438255,180950216,186,2637,101576565,80931,5117,1,583350,5790329,4
4331,KBN,10,stock,78,2,1,stock,f1e1,2637236421,30304747985663,30304932671197,2552550887,180,2637,184431819,79729,30776,1,811821,3888692,6
4331,KBN,10,stock,79,2,0,stock,e3c1,180950216,30304933226136,30305035420145,178756207,180,2552,102003931,93980,6159,1,677632,2621932,5
4331,KBN,10,stock,80,2,1,stock,e1f1,2552550887,30305035973121,30305301689126,2386834882,178,2552,257619686,103545,25037,1,853475,3998706,7
4331,KBN,10,stock,81,2,0,stock,c3d1,178756207,30305302100631,30305402428790,178428048,178,2386,100178710,85728,0,1,499384,5854495,5
4331,KBN,10,stock,82,2,1,stock,f1g1,2386834882,30305402850911,30306067182801,1822502992,178,2386,664178905,79228,5668,1,594947,5039859,4
4331,KBN,10,stock,83,2,0,stock,d1b2,178428048,30306067515438,30306167708427,178235059,178,1822,100060723,72107,3886,1,423311,4377541,5
4331,KBN,10,stock,84,2,1,stock,g1h2,1822502992,30306168114804,30306486985786,1603632010,178,1822,318601119,79208,4506,1,341509,3774361,6
4331,KBN,10,stock,85,2,0,stock,f3e3,178235059,30306487371152,30306575962657,189643554,178,1603,88228725,83003,4768,1,714056,4501546,5
4331,KBN,10,stock,86,2,1,stock,h2g3,1603632010,30306576338829,30306653699024,1626271815,189,1603,76054227,81232,4256,1,766994,4381998,7
4331,KBN,10,stock,87,2,0,stock,e3e4,189643554,30306654137690,30306761350687,182430557,189,1626,107057500,80340,4938,1,574588,5740925,4
4331,KBN,10,stock,88,2,1,stock,g3g4,1626271815,30306761754701,30307280573295,1207453221,182,1626,518601885,80760,4006,1,596390,2131560,7
4331,KBN,10,stock,89,2,0,stock,b2a4,182430557,30307281016798,30307386901088,176546267,182,1207,103120179,131046,2625717,2,517121,6986814,4
4331,KBN,10,stock,90,2,1,stock,g4h5,1207453221,30307387303750,30307562998825,1131758146,176,1207,175499113,87781,4617,1,625151,4519123,5
4331,KBN,10,stock,91,2,0,stock,e4f3,176546267,30307563355318,30307662682222,177219363,176,1131,99135092,78177,4687,1,488739,4525321,3
4331,KBN,10,stock,92,2,1,stock,h5g6,1131758146,30307663161990,30307724927143,1169992993,177,1131,61647834,88952,0,1,619685,4842124,3
4331,KBN,10,stock,93,2,0,stock,c1f4,177219363,30307725304988,30307825448774,177075577,177,1169,99067703,79960,4536,1,569438,2574000,4
4331,KBN,10,stock,94,2,1,stock,g6f7,1169992993,30307825969653,30307886384357,1209578289,177,1169,60210229,85137,0,1,724461,6029435,18
4331,KBN,10,stock,95,2,0,stock,f4c1,177075577,30307886771226,30307958522227,205324576,177,1209,71293469,78878,4687,1,826073,5118296,19
4331,KBN,10,stock,96,2,1,stock,f7e6,1209578289,30307959085159,30307972553750,1296109698,205,1209,13149625,99990,5618,1,863070,4773341,41
4331,KBN,10,stock,97,2,0,stock,c1f4,205324576,30307973011114,30307984582658,293753032,205,1296,8644055,85948,5167,1,709870,5524812,44
4331,KBN,10,stock,98,2,1,stock,e6d7,1296109698,30307984965661,30307985626169,1395449190,293,1296,578363,77365,0,1,413036,558463,2
4331,KBN,10,stock,99,2,0,stock,a4c3,293753032,30307985879998,30307986498773,393134257,293,1395,408848,74962,0,2,518906,55983,66
4331,KBN,10,table,0,2,1,stock,g2h3,10000000000,30308045345283,30308400164892,9745180391,10000,10000,354383319,84025,369952,1,782301,1992993,21
4331,KBN,10,table,1,2,0,table,e4f3,10000000000,30308400518601,30308407962953,10092555648,10000,9745,7395633,7804033,50786,1,7804033,50786,1
4331,KBN,10,table,2,2,1,stock,h3h4,9745180391,30308408161770,30308647472326,9605869835,10092,9745,239090916,52238,3816885,2,358504,3841521,7
4331,KBN,10,table,3,2,0,table,c5e3,10092555648,30308647990361,30308659900511,10180645498,10092,9605,11888818,12418107,24236,1,12418107,24236,1
4331,KBN,10,table,4,2,1,stock,h4h5,9605869835,30308660136754,30308892424894,9473581695,10180,9605,232038708,56123,0,1,355131,3871265,8
4331,KBN,10,table,5,2,0,table,f3f4,10180645498,30308892815518,30308899155128,10274305888,10180,9473,6295502,6696831,45758,1,6696831,45758,1
4331,KBN,10,table,6,2,1,stock,h5g6,9473581695,30308899376069,30309186625472,9286332292,10274,9473,286967423,57255,4574335,2,490332,4631590,8
4331,KBN,10,table,7,2,0,table,f4e5,10274305888,30309187072320,30309194706197,10366672011,10274,9286,7608571,8064912,28303,1,8064912,28303,1
4331,KBN,10,table,8,2,1,stock,g6h5,9286332292,30309194986766,30310423277093,8158041965,10366,9286,1224136698,69774,4954883,2,431913,5024657,4
4331,KBN,10,table,9,2,0,table,e2g1,10366672011,30310423636330,30310430126793,10460181548,10366,8158,6473908,6843330,17717,1,6843330,17717,1
4331,KBN,10,table,10,2,1,stock,h5g6,8158041965,30310430272451,30311074610774,7613703642,10460,8158,644078586,51657,0,1,384293,5730740,6
4331,KBN,10,table,11,2,0,table,e5e6,10460181548,30311075020947,30311080776691,10554425804,10460,7613,5730079,6150626,27942,1,6150626,27942,1
4331,KBN,10,table,12,2,1,stock,g6h5,7613703642,30311080971352,30311333031330,7461643664,10554,7613,251923130,60099,2975870,2,318314,7027835,4
4331,KBN,10,table,13,2,0,table,e6f5,10554425804,30311333476115,30311340090703,10647811216,10554,7461,6593667,7048386,23525,1,7048386,23525,1
4331,KBN,10,table,14,2,1,stock,h5h4,7461643664,30311340258253,30312032466524,6869435393,10647,7461,691992244,54120,3695023,2,356663,3749143,5
4331,KBN,10,table,15,2,0,table,e3f2,10647811216,30312032920012,30312038601166,10742130062,10647,6869,5654447,6119611,30335,1,6119611,30335,1
4331,KBN,10,table,16,2,1,stock,h4h5,6869435393,30312038801986,30312636977112,6371260267,10742,6869,597912193,70836,5144525,2,390883,5215361,4
4331,KBN,10,table,17,2,0,table,g1e2,10742130062,30312637375548,30312642805726,10836699884,10742,6371,5409140,5818551,23094,1,5818551,23094,1
4331,KBN,10,table,18,2,1,stock,h5h6,6371260267,30312642952876,30313141460630,5972752513,10836,6371,494709869,54151,0,1,279056,5048953,4
4331,KBN,10,table,19,2,0,table,f2d4,10836699884,30313141845165,30313147495722,10931049327,10836,5972,5628907,6022885,24477,1,6022885,24477,1
4331,KBN,10,table,20,2,1,stock,h6h7,5972752513,30313147809050,30313517169296,5703392267,10931,5972,365523442,62573,0,1,489070,4192595,4
4331,KBN,10,table,21,2,0,table,f5f6,10931049327,30313517641201,30313524491311,11024199217,10931,5703,6821477,7303036,31266,1,7303036,31266,1
4331,KBN,10,table,22,2,1,stock,h7g8,5703392267,30313524682868,30313833930190,5494144945,11024,5703,309039099,81362,0,1,385835,3321436,5
4331,KBN,10,table,23,2,0,table,d4c5,11024199217,30313834331430,30313840622407,11117908240,11024,5494,6126640,6538675,166168,1,6538675,166168,1
4331,KBN,10,table,24,2,1,stock,g8h7,5494144945,30313840875145,30314004189046,5430831044,11117,5494,162612114,103494,3027246,2,462791,7146822,4
4331,KBN,10,table,25,2,0,table,e2g3,11117908240,30314004815693,30314015819077,11206904856,11117,5430,10979191,11617543,26970,1,11617543,26970,1
4331,KBN,10,table,26,2,1,stock,h7h6,5430831044,30314016048861,30314189114304,5357765601,11206,5430,169121357,71707,0,1,323082,3955041,8
4331,KBN,10,table,27,2,0,table,c5f8,11206904856,30314189509245,30314195787713,11300626388,11206,5357,6251437,6657102,30526,1,6657102,30526,1
4331,KBN,10,table,28,2,1,stock,h6h7,5357765601,30314196194742,30314344206429,5309753914,11300,5357,146002556,66560,0,1,603499,5377664,39
4331,KBN,10,table,29,2,0,table,f6f7,11300626388,30314344661279,30314353702150,11391585517,11300,5309,9021629,9486353,21162,1,9486353,21162,1
4331,KBN,10,table,30,2,1,stock,h7h8,5309753914,30314353919364,30314358076491,5405596787,11391,5309,4089802,58407,0,1,231024,4089802,1
4331,KBN,10,table,31,2,0,table,g3e4,11391585517,30314358237341,30314362008150,11487814708,11391,5405,3773691,3980729,4166,1,3980729,4166,1
4331,KBN,10,table,32,2,1,stock,h8h7,5405596787,30314362116262,30314362444082,5505268967,11487,5405,281259,42954,0,1,115082,281259,1
4331,KBN,10,table,33,2,0,table,e4f6,11487814708,30314362539795,30314367256799,11583097704,11487,5505,4718330,4852210,0,0,4852210,0,0
4331,KBN,10,table,34,2,1,stock,h7h8,5505268967,30314367371400,30314367516247,5605124120,11583,5505,101832,43905,0,1,120229,101832,1
4331,KBN,10,table,35,2,0,table,f8g7,11583097704,30314367612901,30314369702877,11681007728,11583,5605,2090739,2223537,0,0,2223537,0,0
4428,KBN,10,corner,0,0,0,stock,b8c8,10000000000,30325643149654,30325885376129,9857773525,10000,10000,241872137,122703,4406,1,674394,4523559,9
4428,KBN,10,corner,1,0,1,corner,c5d6,10000000000,30325885829196,30326332461304,9653367892,9857,10000,445800891,137875,4808,1,935145,5815436,12
4428,KBN,10,corner,2,0,0,stock,c8d8,9857773525,30326332888543,30326709488287,9581173781,9857,9653,375601966,75913,4337,1,863687,3010301,10
4428,KBN,10,corner,3,0,1,corner,f3h4,9653367892,30326710043767,30329275226564,7188185095,9581,9653,2549731435,87049,6801,1,839142,5814384,6
4428,KBN,10,corner,4,0,0,stock,d8e8,9581173781,30329275693832,30329510659054,9446208559,9581,7188,232851941,112257,5839,1,976046,1616292,18
4428,KBN,10,corner,5,0,1,corner,c6c7,7188185095,30329511067164,30329951727101,6847525158,9446,7188,440355828,73550,4988,1,681305,0,20
4428,KBN,10,corner,6,0,0,stock,e8f7,9446208559,30329952181710,30330219912129,9278478140,9446,6847,267401171,73990,4006,1,537642,3718849,7
4428,KBN,10,corner,7,0,1,corner,c7d7,6847525158,30330220466047,30330906979216,6261011989,9278,6847,678173523,89473,7041,1,636580,3402837,4
4428,KBN,10,corner,8,0,0,stock,f7g7,9278478140,30330907357031,30331146172686,9139662485,9278,6261,235030599,67350,4186,1,499545,4551280,3
4428,KBN,10,corner,9,0,1,corner,d6f4,6261011989,30331146624631,30331748535135,5759101485,9139,6261,598114084,81141,5428,1,653335,5214069,4
4428,KBN,10,corner,10,0,0,stock,g7f6,9139662485,30331749055262,30332219868498,8768849249,9139,5759,466827616,86199,6500,1,960534,2828049,6
4428,KBN,10,corner,11,0,1,corner,d7d6,5759101485,30332220288996,30332644651816,5434738665,8768,5759,424127184,77515,0,1,478635,3712338,6
4428,KBN,10,corner,12,0,0,stock,f6f7,8768849249,30332645113295,30332934992897,8578969647,8768,5434,289624318,77486,0,1,662458,2886577,6
4428,KBN,10,corner,13,0,1,corner,f4g5,5434738665,30332935364642,30333237725517,5232377790,8578,5434,302199359,75022,4166,1,513185,4522066,4
4428,KBN,10,corner,14,0,0,stock,f7e8,8578969647,30333238187708,30333697819808,8219337547,8578,5232,459395143,70846,4496,1,679343,5712052,4
4428,KBN,10,corner,15,0,1,corner,d6e6,5232377790,30333698298954,30334109962855,4920713889,8219,5232,411348249,78437,5007,1,659074,5524803,4
4428,KBN,10,corner,16,0,0,stock,e8f8,8219337547,30334110274380,30334764151204,7665460723,8219,4920,653145402,113639,8313,1,536371,5543250,5
4428,KBN,10,corner,17,0,1,corner,h4f5,4920713889,30334764649729,30335215638603,4569725015,7665,4920,450678367,113460,7280,1,697391,3194015,4
4428,KBN,10,corner,18,0,0,stock,f8e8,7665460723,30335216033112,30335409620022,7571873813,7665,4569,193216904,70675,4277,1,135392,3871266,3
4428,KBN,10,corner,19,0,1,corner,g5f6,4569725015,30335410068693,30335654296522,4425497186,7571,4569,243920546,77796,5479,1,955366,5813523,4
4428,KBN,10,corner,20,0,0,stock,e8f8,7571873813,30335654852352,30335860844161,7465882004,7571,4425,205518196,94100,6380,1,880875,5033068,5
4428,KBN,10,corner,21,0,1,corner,f6e7,4425497186,30335861313692,30336101523927,4285286951,7465,4425,239938605,78727,5899,1,712783,2561211,5
4428,KBN,10,corner,22,0,0,stock,f8g8,7465882004,30336101945447,30336312170178,7355657273,7465,4285,209765470,275381,4407,1,840994,5753464,9
4428,KBN,10,corner,23,0,1,corner,e6f6,4285286951,30336312656425,30336555359442,4142583934,7355,4285,242237622,115673,6299,1,925603,3193193,17
4428,KBN,10,corner,24,0,0,stock,g8h7,7355657273,30336555704597,30336741441989,7269919881,7355,4142,185258992,88392,4126,1,801897,4182761,42
4428,KBN,10,corner,25,0,1,corner,f6f7,4142583934,30336741864400,30336989857588,3994590746,7269,4142,243729019,81452,0,1,969221,6162384,33
4428,KBN,10,corner,26,0,0,stock,h7h8,7269919881,30336990280811,30336992122604,7368078088,7269,3994,1772274,75473,4597,1,452315,1672936,1
4428,KBN,10,corner,27,0,1,corner,f7g6,3994590746,30336992342613,30336995968433,4090964926,7368,3994,3456400,61692,0,2,482336,44726,66
4428,KBN,10,corner,28,0,0,stock,h8g8,7368078088,30336996170906,30336996556743,7467692251,7368,4090,341590,54051,3064,1,170905,274900,1
4428,KBN,10,corner,29,0,1,corner,f5h6,4090964926,30336996660037,30336997260545,4190364418,7467,4090,453236,48092,0,2,280869,37216,66
4428,KBN,10,corner,30,0,0,stock,g8h8,7467692251,30336997387405,30336997528856,7567550800,7467,4190,101481,46439,0,1,135272,101481,1
4428,KBN,10,corner,31,0,1,corner,e7f6,4190364418,30336997623397,30336998144156,4289843659,7567,4190,296375,44587,0,2,350551,35333,66
4428,KBN,10,stock,0,0,0,stock,b8c8,10000000000,30337127514233,30337371490526,9856023707,10000,10000,243593502,154210,0,1,1648740,4504390,9
4428,KBN,10,stock,1,0,1,stock,c5b6,10000000000,30337371905146,30338500069139,8971836007,9856,10000,1119829588,158286,0,1,734204,4124213,11
4428,KBN,10,stock,2,0,0,stock,c8b8,9856023707,30338500500483,30339147948399,9308575791,9856,8971,635659041,74661,0,1,754473,3500733,8
4428,KBN,10,stock,3,0,1,stock,f3e5,8971836007,30339148347355,30339494467086,8725716276,9308,8971,344980656,71307,4416,1,832970,4106126,11
4428,KBN,10,stock,4,0,0,stock,b8c8,9308575791,30339494889497,30339971158167,8932307121,9308,8725,472280665,385856,5258,1,731572,4693502,8
4428,KBN,10,stock,5,0,1,stock,e5c4,8725716276,30339971541270,30340566463664,8230793882,8932,8725,590931103,72628,4126,1,659905,4344111,6
4428,KBN,10,stock,6,0,0,stock,c8b8,8932307121,30340567048769,30341013113447,8586242443,8932,8230,445825334,75212,6981,1,786041,4843977,5
4428,KBN,10,stock,7,0,1,stock,c4d6,8230793882,30341013471963,30341290523858,8053741987,8586,8230,276772879,71877,3806,1,613966,2418798,9
4428,KBN,10,stock,8,0,0,stock,b8a8,8586242443,30341290988322,30341566551708,8410679057,8586,8053,271516541,76164,5939,1,752953,0,19
4428,KBN,10,stock,9,0,1,stock,c6d5,8053741987,30341566989342,30342117810809,7602920520,8410,8053,550434301,73960,4767,1,741546,4896355,6
4428,KBN,10,stock,10,0,0,stock,a8b8,8410679057,30342118359479,30342435981022,8193057514,8410,7602,313597254,91266,7822,1,926382,5522399,7
4428,KBN,10,stock,11,0,1,stock,d5e6,7602920520,30342436646867,30342834050632,7305516755,8193,7602,396553421,94611,5028,1,955996,3219133,10
4428,KBN,10,stock,12,0,0,stock,b8a8,8193057514,30342834917547,30343095195119,8032779942,8193,7305,259920855,75763,6470,1,1173302,4979869,6
4428,KBN,10,stock,13,0,1,stock,b6c5,7305516755,30343095726333,30343601065988,6900177100,8032,7305,497665692,77575,5619,1,910540,4133637,7
4428,KBN,10,stock,14,0,0,stock,a8b8,8032779942,30343601468320,30343804266537,7929981725,8032,6900,202477100,77796,5358,1,703410,2427101,11
4428,KBN,10,stock,15,0,1,stock,d6e8,6900177100,30343804631834,30344639848822,6164960112,7929,6900,827539002,69423,0,1,915876,3371800,6
4428,KBN,10,stock,16,0,0,stock,b8b7,7929981725,30344640369670,30346183837935,6486513460,7929,6164,1535754970,76985,0,1,660054,3631097,11
4428,KBN,10,stock,17,0,1,stock,e6d6,6164960112,30346184251202,30347378308325,5070902989,6486,6164,1189351871,79458,0,1,509431,3749764,4
4428,KBN,10,stock,18,0,0,stock,b7a6,6486513460,30347378869914,30347690990016,6274393358,6486,5070,311732079,88482,0,1,914005,5128872,12
4428,KBN,10,stock,19,0,1,stock,e8c7,5070902989,30347691607479,30348002955337,4859555131,6274,5070,310811054,90635,0,1,1003429,4395808,12
4428,KBN,10,stock,20,0,0,stock,a6a5,6274393358,30348003435024,30348209731064,6168097318,6274,4859,202457855,90365,0,1,627126,4564590,4
4428,KBN,10,stock,21,0,1,stock,d6d5,4859555131,30348210138804,30348404626318,4765067617,6168,4859,194056819,75102,4477,1,754775,5748466,9
4428,KBN,10,stock,22,0,0,stock,a5a4,6168097318,30348405174337,30348606280815,6066990840,6168,4765,200823533,77335,5809,1,805221,2721440,14
4428,KBN,10,stock,23,0,1,stock,d5c4,4765067617,30348606650107,30349300520770,4171196954,6066,4765,689629945,94481,4297,1,755237,5212537,7
4428,KBN,10,stock,24,0,0,stock,a4a5,6066990840,30349301400355,30349797356076,5671035119,6066,4171,492055516,92829,8833,1,1119699,2468593,5
4428,KBN,10,stock,25,0,1,stock,c5d4,4171196954,30349797768823,30351118347655,2950618122,5671,4171,1308615441,164165,5038,1,624570,6022015,4
4428,KBN,10,stock,26,0,0,stock,a5a4,5671035119,30351118821883,30351370048993,5519808009,5671,2950,247361832,79749,6861,1,728425,5058126,8
4428,KBN,10,stock,27,0,1,stock,d4c3,2950618122,30351370627518,30352410920726,2010324914,5519,2950,1032767409,76764,4156,1,693245,5213728,7
4428,KBN,10,stock,28,0,0,stock,a4a3,5519808009,30352411414895,30353531425078,4499797826,5519,2010,1119677051,70465,5669,1,754107,4500184,4
4428,KBN,10,stock,29,0,1,stock,c7e6,2010324914,30353531971134,30353676943547,1965352501,4499,2010,144690789,100029,5018,1,793011,3864596,11
4428,KBN,10,stock,30,0,0,stock,a3a4,4499797826,30353677373600,30354683413096,3593758330,4499,1965,1004702465,75643,4807,1,563351,2535342,4
4428,KBN,10,stock,31,0,1,stock,e6c5,1965352501,30354683814666,30354929575371,1819591796,3593,1965,239412353,71617,4306,1,591894,4074208,6
4428,KBN,10,stock,32,0,0,stock,a4a3,3593758330,30354930002259,30355210862204,3412898385,3593,1819,277039644,84987,5959,1,577873,5885100,4
4428,KBN,10,stock,33,0,1,stock,c4d3,1819591796,30355211393969,30355494856370,1636129395,3412,1819,283185031,92718,5688,1,774786,4463610,5
4428,KBN,10,stock,34,0,0,stock,a3a2,3412898385,30355495516577,30355646840046,3361574916,3412,1636,151131537,78217,5848,1,824069,4379904,4
4428,KBN,10,stock,35,0,1,stock,d3c2,1636129395,30355647188026,30355860097925,1523219496,3361,1636,212624899,77576,3876,1,584532,4717709,6
4428,KBN,10,stock,36,0,0,stock,a2a3,3361574916,30355860575319,30355973583043,3348567192,3361,1523,112640161,87680,6670,1,825662,3306713,7
4428,KBN,10,stock,37,0,1,stock,c3d2,1523219496,30355973981458,30356115529916,1481671038,3348,1523,141228404,76264,0,1,695676,6020062,8
4428,KBN,10,stock,38,0,0,stock,a3a2,3348567192,30356115958827,30356220095802,3344430217,3348,1481,100206080,102342,0,1,708497,4040428,25
4428,KBN,10,stock,39,0,1,stock,d2b4,1481671038,30356220478684,30356348603826,1453545896,3344,1481,127822892,79268,4016,1,668107,3401966,27
4428,KBN,10,stock,40,0,0,stock,a2a1,3344430217,30356348980419,30356353388348,3440022288,3344,1453,4298925,71898,0,1,470430,3021558,10
4428,KBN,10,stock,41,0,1,stock,c5d3,1453545896,30356353581767,30356358024248,1549103415,3440,1453,4347405,52818,2524,1,278477,2351438,11
4428,KBN,10,stock,42,0,0,stock,a1a2,3440022288,30356358200731,30356358649552,3539573467,3440,1549,401609,52799,0,1,187209,401609,1
4428,KBN,10,stock,43,0,1,stock,d3c1,1549103415,30356358813928,30356359284241,1648633102,3539,1549,326008,52789,0,2,346295,41412,66
4428,KBN,10,stock,44,0,0,stock,a2a1,3539573467,30356359388877,30356359530519,3639431825,3539,1648,102172,46960,0,1,111066,102172,1
4428,KBN,10,stock,45,0,1,stock,b4c3,1648633102,30356359617860,30356360063726,1748187236,3639,1648,302989,44828,0,2,262896,36615,66
4428,KBN,10,table,0,0,0,stock,b8c8,10000000000,30356425246602,30356787128119,9738118483,10000,10000,361480618,135972,7209116,2,948474,2396455,10
4428,KBN,10,table,1,0,1,table,c5d6,10000000000,30356787522869,30356792779767,10094743102,9738,10000,5200509,5605212,58257,1,5605212,58257,1
4428,KBN,10,table,2,0,0,stock,c8d8,9738118483,30356792944163,30357268714577,9362348069,9738,10094,471828855,57396,0,1,446123,6373520,11
4428,KBN,10,table,3,0,1,table,f3h4,10094743102,30357269139182,30357275719468,10188162816,9362,10094,6554449,6989117,28733,1,6989117,28733,1
4428,KBN,10,table,4,0,0,stock,d8c8,9362348069,30357275935792,30358378235785,8360048076,9362,10188,1098248122,80911,0,1,603640,4065025,13
4428,KBN,10,table,5,0,1,table,d6e5,10188162816,30358378644917,30358383382098,10283425635,8360,10188,4739731,5160919,301100,2,5160919,301100,2
4428,KBN,10,table,6,0,0,stock,c8d8,8360048076,30358383889687,30358722336068,8121601695,8360,10283,333915296,62363,4053818,2,342141,4116181,6
4428,KBN,10,table,7,0,1,table,h4f5,10283425635,30358722728214,30358728597107,10377556742,8121,10283,5845591,6247581,24897,1,6247581,24897,1
4428,KBN,10,table,8,0,0,stock,d8e8,8121601695,30358728790456,30359133475642,7816916509,8121,10377,404495867,58677,0,1,360247,7212821,4
4428,KBN,10,table,9,0,1,table,c6d6,10377556742,30359133909470,30359141178747,10470287465,7816,10377,7248004,7691626,24136,1,7691626,24136,1
4428,KBN,10,table,10,0,0,stock,e8d8,7816916509,30359141497874,30359605363342,7453051041,7816,10470,452754915,62724,2446540,2,486426,6503763,4
4428,KBN,10,table,11,0,1,table,f5e7,10470287465,30359605965542,30359611865071,10564387936,7453,10470,5902175,6514519,28843,1,6514519,28843,1
4428,KBN,10,table,12,0,0,stock,d8e8,7453051041,30359612085761,30359985137761,7179999041,7453,10564,372838686,61551,3866569,2,257014,3928120,4
4428,KBN,10,table,13,0,1,table,d6e6,10564387936,30359985530377,30359992036553,10657881760,7179,10564,6483963,6886944,24577,1,6886944,24577,1
4428,KBN,10,table,14,0,0,stock,e8d8,7179999041,30359992228029,30360430812618,6841414452,7179,10657,438371786,62212,0,1,368290,3772358,4
4428,KBN,10,table,15,0,1,table,e5b8,10657881760,30360431204063,30360438249304,10750836519,6841,10657,7019824,7422625,27851,1,7422625,27851,1
4428,KBN,10,table,16,0,0,stock,d8e8,6841414452,30360438595482,30360814322861,6565687073,6841,10750,362414778,65778,5345525,2,532336,5411303,5
4428,KBN,10,table,17,0,1,table,b8c7,10750836519,30360814700556,30360819176286,10846360789,6565,10750,4443700,4831238,33840,1,4831238,33840,1
4428,KBN,10,table,18,0,0,stock,e8f8,6565687073,30360819332359,30361311944804,6173074628,6565,10846,488776983,56514,0,1,400568,4668054,4
4428,KBN,10,table,19,0,1,table,e7f5,10846360789,30361312431381,30361319794978,10938997192,6173,10846,7338478,7755139,27802,1,7755139,27802,1
4428,KBN,10,table,20,0,0,stock,f8e8,6173074628,30361319990961,30361507444574,6085621015,6173,10938,187295587,65818,3928902,2,341829,3994720,4
4428,KBN,10,table,21,0,1,table,f5d6,10938997192,30361507902318,30361516695592,11030203918,6085,10938,8767270,9233786,28723,1,9233786,28723,1
4428,KBN,10,table,22,0,0,stock,e8f8,6085621015,30361516954029,30361698970277,6003604767,6085,11030,181845068,75713,0,1,408641,7058340,4
4428,KBN,10,table,23,0,1,table,e6f6,11030203918,30361699419729,30361704078814,11125544833,6003,11030,4634774,5092807,26851,1,5092807,26851,1
4428,KBN,10,table,24,0,0,stock,f8g8,6003604767,30361704338993,30361868597034,5939346726,6003,11125,163940726,63896,3602604,2,449050,3666500,5
4428,KBN,10,table,25,0,1,table,f6g6,11125544833,30361868969942,30361875333311,11219181464,5939,11125,6345536,6726455,19730,1,6726455,19730,1
4428,KBN,10,table,26,0,0,stock,g8f8,5939346726,30361875513260,30362048958274,5865901712,5939,11219,172987396,60170,0,1,516681,4488857,11
4428,KBN,10,table,27,0,1,table,c7d8,11219181464,30362049340756,30362053732145,11314790075,5865,11219,4383039,4774894,24316,1,4774894,24316,1
4428,KBN,10,table,28,0,0,stock,f8g8,5865901712,30362053908800,30362208335132,5811475380,5865,11314,153881909,61592,0,1,633596,6091288,26
4428,KBN,10,table,29,0,1,table,d8e7,11314790075,30362208771605,30362214796458,11408765222,5811,11314,6027502,6474109,28543,1,6474109,28543,1
4428,KBN,10,table,30,0,0,stock,g8h8,5811475380,30362215025050,30362221839864,5904660566,5811,11408,6714337,65428,4917787,2,292626,4983215,10
4428,KBN,10,table,31,0,1,table,d6f5,11408765222,30362222070810,30362227936545,11502899487,5904,11408,5868505,6161222,13831,1,6161222,13831,1
4428,KBN,10,table,32,0,0,stock,h8g8,5904660566,30362228120109,30362228473408,6004307267,5904,11502,299427,55323,0,1,122723,299427,1
4428,KBN,10,table,33,0,1,table,f5h6,11502899487,30362228576282,30362233756010,11597719759,6004,11502,5180989,5325024,0,0,5325024,0,0
4428,KBN,10,table,34,0,0,stock,g8h8,6004307267,30362233872064,30362234029259,6104150072,6004,11597,109713,50835,58878,2,123435,109713,1
4428,KBN,10,table,35,0,1,table,e7f6,11597719759,30362234203380,30362236677901,11695245238,6104,11597,2475693,2688501,0,0,2688501,0,0
4810,KBN,10,corner,0,2,0,stock,g7f8,10000000000,30324925964609,30325274454104,9751510505,10000,10000,348055661,208762,0,1,953553,6039591,9
4810,KBN,10,corner,1,2,1,corner,f5f6,10000000000,30325275010485,30325608460184,9766550301,9751,10000,333044597,204095,0,1,932310,4987461,12
4810,KBN,10,corner,2,2,0,stock,f8e8,9751510505,30325608963867,30326022770020,9437704352,9751,9766,413368434,106999,5228,1,906672,2899766,11
4810,KBN,10,corner,3,2,1,corner,c4d5,9766550301,30326023192231,30328039417354,7850325178,9437,9766,2007953448,101241,4506,1,659174,4662115,5
4810,KBN,10,corner,4,2,0,stock,e8d8,9437704352,30328039789650,30328358049790,9219444212,9437,7850,317879130,89724,4677,1,734888,4093186,11
4810,KBN,10,corner,5,2,1,corner,d5c6,7850325178,30328358523067,30329464325451,6844522794,9219,7850,1105449118,101412,5287,1,787683,5328860,7
4810,KBN,10,corner,6,2,0,stock,d8c8,9219444212,30329464912008,30330168607448,8615748772,9219,6844,703284099,119468,6379,1,966670,2930532,13
4810,KBN,10,corner,7,2,1,corner,f6e7,6844522794,30330169034326,30330726762618,6386794502,8615,6844,557358761,101181,6009,1,603129,2813678,4
4810,KBN,10,corner,8,2,0,stock,c8c7,8615748772,30330727179301,30331123594107,8319333966,8615,6386,390779320,99308,4426,1,621566,4700453,4
4810,KBN,10,corner,9,2,1,corner,e7e6,6386794502,30331124198421,30331972977554,5638015369,8319,6386,848572701,112728,5959,1,339487,3640922,4
4810,KBN,10,corner,10,2,0,stock,c7b6,8319333966,30331973379475,30332472731177,7919982264,8319,5638,499089843,99028,4166,1,639404,2493540,6
4810,KBN,10,corner,11,2,1,corner,e6d6,5638015369,30332473175371,30332907543383,5303647357,7919,5638,427752295,103345,4777,1,666104,2675281,5
4810,KBN,10,corner,12,2,0,stock,b6a5,7919982264,30332908185613,30333218190512,7709977365,7919,5303,308225898,102122,4887,1,319168,3679079,4
4810,KBN,10,corner,13,2,1,corner,d6c5,5303647357,30333218583620,30333871082503,4751148474,7709,5303,652084430,98217,0,1,636448,5424193,5
4810,KBN,10,corner,14,2,0,stock,a5a6,7709977365,30333871594148,30334102605860,7578965653,7709,4751,230835769,101191,5478,1,723319,4250772,4
4810,KBN,10,corner,15,2,1,corner,e5f7,4751148474,30334103020670,30334740459201,4213709943,7578,4751,637230383,104806,4697,1,600687,4726591,4
4810,KBN,10,corner,16,2,0,stock,a6a7,7578965653,30334741007630,30334936473338,7483499945,7578,4213,191495055,116704,6520,1,749589,2853458,5
4810,KBN,10,corner,17,2,1,corner,c5b5,4213709943,30334936920867,30335211615520,4039015290,7483,4213,272652112,101241,4326,1,626454,2932305,4
4810,KBN,10,corner,18,2,0,stock,a7b8,7483499945,30335212085822,30335449707573,7345878194,7483,4039,237271519,103985,5008,1,389994,3782212,7
4810,KBN,10,corner,19,2,1,corner,b5b6,4039015290,30335450136834,30335702123219,3887028905,7345,4039,251619713,108182,0,1,769168,5859983,6
4810,KBN,10,corner,20,2,0,stock,b8c8,7345878194,30335702687592,30335917229390,7231336396,7345,3887,213797958,153980,6029,1,1146131,5120309,10
4810,KBN,10,corner,21,2,1,corner,c6b5,3887028905,30335917852331,30336136467280,3768413956,7231,3887,216074955,125467,7812,1,1299506,7797753,16
4810,KBN,10,corner,22,2,0,stock,c8b8,7231336396,30336136997473,30336322466520,7145867349,7231,3768,184859675,103354,5037,1,1119302,2865354,40
4810,KBN,10,corner,23,2,1,corner,f7d6,3768413956,30336322951205,30336532191277,3659173884,7145,3768,208657276,112638,5859,1,1044833,4887161,32
4810,KBN,10,corner,24,2,0,stock,b8a8,7145867349,30336532611826,30336535346203,7243132972,7145,3659,2666858,102252,4237,1,452876,2507621,1
4810,KBN,10,corner,25,2,1,corner,b6c7,3659173884,30336535571009,30336539123711,3755621182,7243,3659,3381822,89423,3816,2,437116,0,65
4810,KBN,10,corner,26,2,0,stock,a8a7,7243132972,30336539320265,30336539692421,7342760816,7243,3755,329301,78407,0,1,209713,329301,1
4810,KBN,10,corner,27,2,1,corner,d6c8,3755621182,30336539980201,30336540508711,3855092672,7342,3755,389156,96224,0,2,459040,80100,66
4810,KBN,10,corner,28,2,0,stock,a7a8,7342760816,30336540620078,30336540803392,7442577502,7342,3855,141371,68482,0,1,118777,144756,1
4810,KBN,10,corner,29,2,1,corner,b5c6,3855092672,30336540902650,30336541180095,3954815227,7442,3855,240969,65958,0,1,137415,240969,1
4810,KBN,10,stock,0,2,0,stock,g7f8,10000000000,30341332077913,30341639121902,9792956011,10000,10000,298971373,170594,3798397,2,449620,3559881,10
4810,KBN,10,stock,1,2,1,stock,c4e6,10000000000,30341639660086,30342431076521,9308583565,9792,10000,790802811,191987,4527,1,1092761,3908531,11
4810,KBN,10,stock,2,2,0,stock,f8e7,9792956011,30342431633143,30342869498945,9455090209,9792,9308,437274922,137945,7201,1,1102923,4184613,12
4810,KBN,10,stock,3,2,1,stock,e5f7,9308583565,30342870212612,30343206905802,9071890375,9455,9308,330760509,98497,5248,1,1280381,5641176,7
4810,KBN,10,stock,4,2,0,stock,e7f8,9455090209,30343207458368,30343480606604,9281941973,9455,9071,269169240,144956,5879,1,866543,4354096,8
4810,KBN,10,stock,5,2,1,stock,f7d8,9071890375,30343481054694,30344042080537,8610864532,9281,9071,560604365,100851,4617,1,841734,0,20
4810,KBN,10,stock,6,2,0,stock,f8e7,9281941973,30344042710879,30344343257860,9081394992,9281,8610,300247654,112858,4958,1,905583,5151240,9
4810,KBN,10,stock,7,2,1,stock,d8b7,8610864532,30344343671017,30344598173472,8456362077,9081,8610,254174788,130475,3575,1,714517,4159385,7
4810,KBN,10,stock,8,2,0,stock,e7e8,9081394992,30344598588182,30344992429227,8787553947,9081,8456,393508745,100289,4126,1,715017,5256092,6
4810,KBN,10,stock,9,2,1,stock,f5f6,8456362077,30344993011717,30345214706056,8334667738,8787,8456,219689976,100620,5578,1,927222,2841830,8
4810,KBN,10,stock,10,2,0,stock,e8f8,8787553947,30345215125593,30345610417696,8492261844,8787,8334,395070375,98697,4276,1,615598,4743086,4
4810,KBN,10,stock,11,2,1,stock,e6h3,8334667738,30345610841840,30346088171759,7957337819,8492,8334,469603151,100840,4767,1,800025,5007411,9
4810,KBN,10,stock,12,2,0,stock,f8g8,8492261844,30346088578958,30346329219729,8351621073,8492,7957,236790924,100229,3946,1,591011,3301886,9
4810,KBN,10,stock,13,2,1,stock,h3g4,7957337819,30346329638615,30346650646022,7736330412,8351,7957,320430617,146168,3886,1,969538,4931197,15
4810,KBN,10,stock,14,2,0,stock,g8h8,8351621073,30346651200020,30346911760810,8191060283,8351,7736,256408986,118526,0,1,1059782,4791929,13
4810,KBN,10,stock,15,2,1,stock,g4f5,7736330412,30346912168369,30347180136336,7568362445,8191,7736,267721683,92648,0,1,378001,3787060,14
4810,KBN,10,stock,16,2,0,stock,h8g8,8191060283,30347180551347,30347390886174,8080725456,8191,7568,207610156,101562,4527,1,974583,3334654,12
4810,KBN,10,stock,17,2,1,stock,f5c2,7568362445,30347391289467,30347618787854,7440864058,8080,7568,227231471,99609,0,1,646455,4706351,8
4810,KBN,10,stock,18,2,0,stock,g8f8,8080725456,30347619203565,30347969420277,7830508744,8080,7440,350024645,103113,0,1,571913,4793982,5
4810,KBN,10,stock,19,2,1,stock,c2h7,7440864058,30347970024570,30348347769839,7163118789,7830,7440,377350805,139669,0,1,976435,5910408,9
4810,KBN,10,stock,20,2,0,stock,f8e8,7830508744,30348348214644,30348571922204,7706801184,7830,7163,223514706,102492,4738,1,460618,3649044,5
4810,KBN,10,stock,21,2,1,stock,h7f5,7163118789,30348572352878,30350572654942,5262816725,7706,7163,1993923869,98307,4156,1,403932,6472677,4
4810,KBN,10,stock,22,2,0,stock,e8f8,7706801184,30350573087298,30350777328917,7602559565,7706,5262,203956434,100079,5809,1,729227,2784824,6
4810,KBN,10,stock,23,2,1,stock,b7d8,5262816725,30350777770067,30351207718555,4932868237,7602,5262,425797754,104205,0,1,779323,2226551,7
4810,KBN,10,stock,24,2,0,stock,f8g8,7602559565,30351208314806,30351416296776,7494577595,7602,4932,194058681,166318,0,1,1429732,3686039,10
4810,KBN,10,stock,25,2,1,stock,f5e6,4932868237,30351416879187,30352114027894,4335719530,7494,4932,693065325,104746,0,1,784039,5894554,7
4810,KBN,10,stock,26,2,0,stock,g8f8,7494577595,30352114431017,30352361401389,7347607223,7494,4335,243055371,97716,4387,1,651471,5504643,6
4810,KBN,10,stock,27,2,1,stock,e6c8,4335719530,30352362108456,30353078531588,3719296398,7347,4335,712320026,100099,5228,1,1060432,5742337,7
4810,KBN,10,stock,28,2,0,stock,f8g8,7347607223,30353079140128,30353541838694,6984908657,7347,3719,455980019,121361,7401,1,979922,4690919,7
4810,KBN,10,stock,29,2,1,stock,c8f5,3719296398,30353542360494,30353884658813,3476998079,6984,3719,338186533,102462,4627,1,775598,5491012,7
4810,KBN,10,stock,30,2,0,stock,g8h8,6984908657,30353885089857,30354155448246,6814550268,6984,3476,270103559,104456,4587,1,662368,2774940,6
4810,KBN,10,stock,31,2,1,stock,f5e6,3476998079,30354155880953,30354924347109,2808531923,6814,3476,760980403,125117,4887,1,738793,3912327,10
4810,KBN,10,stock,32,2,0,stock,h8h7,6814550268,30354924951142,30355156709432,6682791978,6814,2808,227734809,124556,6630,1,955886,2885034,8
4810,KBN,10,stock,33,2,1,stock,d8b7,2808531923,30355157164382,30356167498099,1898198206,6682,2808,1004312048,106179,5318,1,640737,2683304,9
4810,KBN,10,stock,34,2,0,stock,h7h6,6682791978,30356167982553,30356348420713,6602353818,6682,1898,180172766,108492,0,1,727594,3959037,10
4810,KBN,10,stock,35,2,1,stock,e6g4,1898198206,30356348941101,30356640439458,1706699849,6602,1898,291210208,104355,0,1,791721,3057301,11
4810,KBN,10,stock,36,2,0,stock,h6h7,6602353818,30356640958775,30356815196206,6528116387,6602,1706,173981718,109403,0,1,714716,3004543,8
4810,KBN,10,stock,37,2,1,stock,b7d8,1706699849,30356815637446,30356916891140,1705446155,6528,1706,101032123,133269,0,1,684620,4339665,11
4810,KBN,10,stock,38,2,0,stock,h7g8,6528116387,30356917300241,30357197296631,6348119997,6528,1705,279707411,217394,4557,1,674548,2444447,10
4810,KBN,10,stock,39,2,1,stock,g4f5,1705446155,30357197804661,30357410219214,1593031602,6348,1705,212210718,104917,5538,1,685953,6043897,5
4810,KBN,10,stock,40,2,0,stock,g8h8,6348119997,30357410979190,30357629367298,6229731889,6348,1593,210871687,124636,7071,1,1564823,4849825,8
4810,KBN,10,stock,41,2,1,stock,f5e4,1593031602,30357629912393,30357734342796,1588601199,6229,1593,104130786,105437,5368,1,825541,5933753,7
4810,KBN,10,stock,42,2,0,stock,h8g8,6229731889,30357734762663,30358046904159,6017590393,6229,1588,308364001,103014,4717,1,556829,5139478,8
4810,KBN,10,stock,43,2,1,stock,e4d3,1588601199,30358047297207,30358221041977,1514856429,6017,1588,173157804,105638,5237,1,958530,4435157,8
4810,KBN,10,stock,44,2,0,stock,g8h8,6017590393,30358221468444,30358565473955,5773584882,6017,1514,343727896,107711,4566,1,679162,2391248,10
4810,KBN,10,stock,45,2,1,stock,d3f5,1514856429,30358565960813,30359033461205,1147356037,5773,1514,467309982,109874,4928,1,655327,5881695,6
4810,KBN,10,stock,46,2,0,stock,h8g8,5773584882,30359033965659,30359335697680,5571852861,5773,1147,297836350,96194,4947,1,751530,5908104,9
4810,KBN,10,stock,47,2,1,stock,f5e4,1147356037,30359336308142,30359522852980,1060811199,5571,1147,182355838,106449,4747,1,1300510,3565920,7
4810,KBN,10,stock,48,2,0,stock,g8f8,5571852861,30359524217239,30359991994255,5204075845,5571,1060,464047265,255591,3591248,2,337102,3865928,4
4810,KBN,10,stock,49,2,1,stock,d8e6,1060811199,30359992359421,30360111828964,1041341656,5204,1060,118674656,100330,0,1,1307839,3641784,9
4810,KBN,10,stock,50,2,0,stock,f8g8,5204075845,30360112279278,30360522692085,4893663038,5204,1041,406549809,109643,0,1,436622,3716575,10
4810,KBN,10,stock,51,2,1,stock,e4d3,1041341656,30360523159313,30360697349233,967151736,4893,1041,161532758,108562,0,1,657422,4835434,6
4810,KBN,10,stock,52,2,0,stock,g8h8,4893663038,30360697893427,30360840492188,4851064277,4893,967,142291963,128161,0,1,828206,6060471,11
4810,KBN,10,stock,53,2,1,stock,e6c7,967151736,30360841125836,30360956440699,951836873,4851,967,115013521,104506,5047,1,893422,2666138,8
4810,KBN,10,stock,54,2,0,stock,h8g8,4851064277,30360956883701,30361143691993,4764255985,4851,951,186402240,118928,0,1,827483,3123951,11
4810,KBN,10,stock,55,2,1,stock,d3g6,951836873,30361144111670,30361341150666,854797877,4764,951,196850685,108001,0,1,250394,3844486,6
4810,KBN,10,stock,56,2,0,stock,g8f8,4764255985,30361341543112,30361489776638,4716022459,4764,854,144062477,106348,4367,1,896447,2316005,11
4810,KBN,10,stock,57,2,1,stock,g6e4,854797877,30361490399679,30361624275467,820922089,4716,854,131227241,131626,0,1,979783,5593575,7
4810,KBN,10,stock,58,2,0,stock,f8g8,4716022459,30361624931037,30361767115677,4673837819,4716,820,141965350,110845,5638,1,856809,2924704,7
4810,KBN,10,stock,59,2,1,stock,e4d3,820922089,30361767530337,30362253899298,434553128,4673,820,486223379,106909,4297,1,502400,4316259,5
4810,KBN,10,stock,60,2,0,stock,g8h8,4673837819,30362254255722,30362417931952,4610161589,4673,434,163438758,101902,5198,1,602840,5612834,7
4810,KBN,10,stock,61,2,1,stock,c7e6,434553128,30362418444679,30362469412183,483585624,4610,434,50814701,108722,5098,1,645113,5391594,5
4810,KBN,10,stock,62,2,0,stock,h8g8,4610161589,30362469833684,30362613229095,4566766178,4610,483,141996838,105828,5338,1,594598,7231799,6
4810,KBN,10,stock,63,2,1,stock,d3f5,483585624,30362613654442,30362803117648,394122418,4566,483,189276137,125087,4527,1,589288,2179872,8
4810,KBN,10,stock,64,2,0,stock,g8h8,4566766178,30362803534922,30362939822480,4530478620,4566,394,136035065,109203,4327,1,645332,4305614,6
4810,KBN,10,stock,65,2,1,stock,f5e4,394122418,30362940290641,30363032931556,401481503,4530,394,92467364,110766,4616,1,419806,3550657,5
4810,KBN,10,stock,66,2,0,stock,h8g8,4530478620,30363033351935,30363642779330,4021051225,4530,401,602240058,128672,5177,1,759603,2494863,8
4810,KBN,10,stock,67,2,1,stock,e6c7,401481503,30363643199308,30363860585445,284095366,4021,401,213096359,108091,4486,1,841395,4650709,8
4810,KBN,10,stock,68,2,0,stock,g8h8,4021051225,30363863834372,30364426432132,3558453465,4021,284,558770177,197054,0,1,3594662,4159316,4
4810,KBN,10,stock,69,2,1,stock,e4g6,284095366,30364426814544,30364591270781,219639129,3558,284,164262022,103294,0,1,503231,5185206,4
4810,KBN,10,stock,70,2,0,stock,h8g8,3558453465,30364591697629,30364910146812,3340004282,3558,219,318108924,139398,0,1,793655,4297361,8
4810,KBN,10,stock,71,2,1,stock,g6f7,219639129,30364910730094,30365036042503,194326720,3340,219,125024348,137676,0,1,828565,5247039,7
4810,KBN,10,stock,72,2,0,stock,g8h7,3340004282,30365036537603,30365233625723,3242916162,3340,194,196866620,111747,5308,1,717720,3314815,9
4810,KBN,10,stock,73,2,1,stock,c7e8,194326720,30365234029807,30365344478678,183877849,3242,194,110289081,109253,0,1,499528,5967402,6
4810,KBN,10,stock,74,2,0,stock,h7h6,3242916162,30365344928481,30365492221997,3195622646,3242,183,147099250,111857,5568,1,669510,2920146,6
4810,KBN,10,stock,75,2,1,stock,e8d6,183877849,30365492631359,30365595983942,180525266,3195,183,103178975,155602,0,1,611843,3313494,9
4810,KBN,10,stock,76,2,0,stock,h6h7,3195622646,30365596603479,30365728648221,3163577904,3195,180,121057413,168261,7662,1,874094,3163049,5
4810,KBN,10,stock,77,2,1,stock,f7g6,180525266,30365729872471,30365832387111,178010626,3163,180,98673013,141041,0,1,1356583,5949376,6
4810,KBN,10,stock,78,2,0,stock,h7g8,3163577904,30365833040628,30366079660760,3016957772,3163,178,238552191,128883,7621,1,901003,2791575,9
4810,KBN,10,stock,79,2,1,stock,g6f5,178010626,30366080100017,30366144610678,213499965,3016,178,64369326,103575,4286,1,202049,3746820,6
4810,KBN,10,stock,80,2,0,stock,g8f8,3016957772,30366145037606,30366357965134,2904030244,3016,213,212736176,107019,4637,1,596310,2821109,7
4810,KBN,10,stock,81,2,1,stock,d6b7,213499965,30366358360235,30366479689178,192171022,2904,213,121135414,108342,4116,1,519745,5485074,4
4810,KBN,10,stock,82,2,0,stock,f8g8,2904030244,30366480286031,30367510616892,1973699383,2904,192,1030082459,134791,7441,1,440888,3534883,6
4810,KBN,10,stock,83,2,1,stock,f6e6,192171022,30367511050410,30367620348951,182872481,1973,192,109096295,111977,5057,1,587695,4782986,4
4810,KBN,10,stock,84,2,0,stock,g8g7,1973699383,30367620812103,30367907323530,1787187956,1973,182,284189817,108592,7070,1,720904,3045314,6
4810,KBN,10,stock,85,2,1,stock,e6e5,182872481,30367907776807,30367991641650,199007638,1787,182,83690941,113780,4636,1,605452,4061961,4
4810,KBN,10,stock,86,2,0,stock,g7h6,1787187956,30367992257220,30368214508505,1664936671,1787,199,221995670,115332,5538,1,459335,3585950,7
4810,KBN,10,stock,87,2,1,stock,f5d7,199007638,30368214971187,30368328198991,185779834,1664,199,112933627,116033,4687,1,697632,4862264,6
4810,KBN,10,stock,88,2,0,stock,h6g5,1664936671,30368328800381,30368467956203,1625780849,1664,185,138674211,132537,8012,1,907074,3016981,6
4810,KBN,10,stock,89,2,1,stock,d7c8,185779834,30368468535389,30368573826459,180488764,1625,185,105103087,114551,5498,1,650260,3302647,5
4810,KBN,10,stock,90,2,0,stock,g5h4,1625780849,30368574238005,30368835482808,1464536046,1625,180,261079760,112648,0,1,583902,5755296,5
4810,KBN,10,stock,91,2,1,stock,e5f4,180488764,30368835889987,30368938142505,178236246,1464,180,102055098,147941,4887,1,552865,3915011,5
4810,KBN,10,stock,92,2,0,stock,h4h5,1464536046,30368938566509,30369003008007,1500094548,1464,178,64273812,114000,4897,1,587656,5283933,4
4810,KBN,10,stock,93,2,1,stock,c8f5,178236246,30369003411450,30369103631841,178015855,1500,178,100019590,110585,4306,1,542991,4430039,4
4810,KBN,10,stock,94,2,0,stock,h5h6,1500094548,30369104281272,30369168974717,1535401103,1500,178,64459279,135021,7671,1,466065,3533181,27
4810,KBN,10,stock,95,2,1,stock,f5e6,178015855,30369169380723,30369238047578,209349000,1535,178,68419219,109754,4217,1,636106,2462574,28
4810,KBN,10,stock,96,2,0,stock,h6h7,1535401103,30369238456099,30369246302588,1627554614,1535,209,7696716,113619,4868,1,541926,5396451,19
4810,KBN,10,stock,97,2,1,stock,f4g5,209349000,30369246601154,30369253035713,302914441,1627,209,6325036,99459,2433,1,390532,5253728,12
4810,KBN,10,stock,98,2,0,stock,h7h8,1627554614,30369253293578,30369253723571,1727124621,1627,302,315070,94661,2885,1,280509,204455,1
4810,KBN,10,stock,99,2,1,stock,b7d8,302914441,30369253888527,30369254348815,402454153,1727,302,312528,92627,2624,2,407526,0,65
4810,KBN,10,table,0,2,0,stock,g7f8,10000000000,30336594497730,30336884591540,9809906190,10000,10000,289788215,204495,5752272,2,677493,5079798,9
4810,KBN,10,table,1,2,1,table,f5f6,10000000000,30336885038458,30336891767578,10093270880,9809,10000,6697132,7153913,34852,1,7153913,34852,1
4810,KBN,10,table,2,2,0,stock,f8e8,9809906190,30336892080415,30337329394287,9472592318,9809,10093,421670148,152758,0,1,281962,3917665,11
4810,KBN,10,table,3,2,1,table,c4f7,10093270880,30337329829207,30337336399789,10186700298,9472,10093,6547998,6992582,24597,1,6992582,24597,1
4810,KBN,10,table,4,2,0,stock,e8d8,9472592318,30337336575021,30337694612379,9214554960,9472,10186,357576926,83755,0,1,622179,3424158,12
4810,KBN,10,table,5,2,1,table,f6e6,10186700298,30337695214598,30337702188227,10279726669,9214,10186,6948657,7560901,27651,1,7560901,27651,1
4810,KBN,10,table,6,2,0,stock,d8c7,9214554960,30337702402587,30338054819386,8962138161,9214,10279,348361650,92558,5508859,2,609307,5601417,12
4810,KBN,10,table,7,2,1,table,f7e8,10279726669,30338055296189,30338059608081,10375414777,8962,10279,4315178,4803056,27971,1,4803056,27971,1
4810,KBN,10,table,8,2,0,stock,c7d8,8962138161,30338059862280,30338400676605,8721323836,8962,10375,337024604,94260,0,1,391054,8133584,4
4810,KBN,10,table,9,2,1,table,e8a4,10375414777,30338401176001,30338405204871,10471385907,8721,10375,4031805,4541446,29644,1,4541446,29644,1
4810,KBN,10,table,10,2,0,stock,d8c7,8721323836,30338405398660,30339379525652,7847196844,8721,10471,957397048,84325,0,1,389399,2603424,7
4810,KBN,10,table,11,2,1,table,e5c4,10471385907,30339380100571,30339386230940,10565255538,7847,10471,6108844,6199499,23435,1,6199499,23435,1
4810,KBN,10,table,12,2,0,stock,c7c8,7847196844,30339386377359,30339922151654,7411422549,7847,10565,531868087,145146,5545183,2,361840,5690329,5
4810,KBN,10,table,13,2,1,table,e6d6,10565255538,30339922542247,30339928656172,10659141613,7411,10565,6090838,6491495,25518,1,6491495,25518,1
4810,KBN,10,table,14,2,0,stock,c8d8,7411422549,30339928877883,30340350164948,7090135484,7411,10659,420888131,82413,0,1,479616,7118390,8
4810,KBN,10,table,15,2,1,table,c4a5,10659141613,30340350615330,30340355953306,10753803637,7090,10659,5340178,5834223,21082,1,5834223,21082,1
4810,KBN,10,table,16,2,0,stock,d8c8,7090135484,30340356155087,30340605804216,6940486355,7090,10753,249433546,85337,3772368,2,348680,3857705,5
4810,KBN,10,table,17,2,1,table,a4d7,10753803637,30340606284714,30340611047460,10849040891,6940,10753,4738430,5229843,25838,1,5229843,25838,1
4810,KBN,10,table,18,2,0,stock,c8b8,6940486355,30340611207950,30340805845729,6845848576,6940,10849,194330706,82813,0,1,444274,4790336,6
4810,KBN,10,table,19,2,1,table,d6c6,10849040891,30340806342131,30340811398134,10943984888,6845,10849,5058507,5565894,30095,1,5565894,30095,1
4810,KBN,10,table,20,2,0,stock,b8a7,6845848576,30340811626044,30340992725567,6764749053,6845,10943,180444196,92187,4285424,2,832034,4377611,18
4810,KBN,10,table,21,2,1,table,d7c8,10943984888,30340993254988,30340997828241,11039411635,6764,10943,4549318,5088031,26229,1,5088031,26229,1
4810,KBN,10,table,22,2,0,stock,a7b8,6764749053,30340997983442,30341169978107,6692754388,6764,11039,166287091,85137,0,1,715189,6015374,32
4810,KBN,10,table,23,2,1,table,c6d7,11039411635,30341170426687,30341174198291,11135640031,6692,11039,3773790,4235069,21362,1,4235069,21362,1
4810,KBN,10,table,24,2,0,stock,b8a7,6692754388,30341174393834,30341180097926,6787050296,6692,11135,5639193,77676,0,1,232797,5605473,3
4810,KBN,10,table,25,2,1,table,d7c7,11135640031,30341180275902,30341184093065,11231822868,6787,11135,3818778,4000879,12058,1,4000879,12058,1
4810,KBN,10,table,26,2,0,stock,a7a8,6787050296,30341184267045,30341184599842,6886717499,6787,11231,279197,75763,0,1,173038,279197,1
4810,KBN,10,table,27,2,1,table,c8b7,11231822868,30341184815765,30341189595356,11327043277,6886,11231,4780823,5037095,0,0,5037095,0,0
4810,KBN,10,table,28,2,0,stock,a8a7,6886717499,30341189714905,30341189918619,6986513785,6886,11327,154190,94421,0,1,129974,154190,1
4810,KBN,10,table,29,2,1,table,a5c6,11327043277,30341190037857,30341194407705,11422673429,6986,11327,4371412,4528746,0,0,4528746,0,0
5825,KBB,10,corner,0,0,0,stock,b3c2,10000000000,30374843376036,30375351560500,9591815536,10000,10000,507706531,138457,0,1,752262,4646973,13
5825,KBB,10,corner,1,0,1,corner,b5c4,10000000000,30375351990542,30375788365510,9663625032,9591,10000,435953120,146038,4436,1,818541,3585679,13
5825,KBB,10,corner,2,0,0,stock,c2d2,9591815536,30375788789344,30376285178087,9195426793,9591,9663,489487948,79178,5208,1,599134,3106224,5
5825,KBB,10,corner,3,0,1,corner,e7c5,9663625032,30376285675881,30377260924564,8788376349,9195,9663,967683838,105978,5318,1,688125,2173082,5
5825,KBB,10,corner,4,0,0,stock,d2e2,9195426793,30377261260336,30378070591500,8486095629,9195,8788,797568825,72979,5108,1,757601,2646358,12
5825,KBB,10,corner,5,0,1,corner,c4c3,8788376349,30378070941743,30379152719174,7806598918,8486,8788,1077133900,79378,3526,1,531292,4935564,5
5825,KBB,10,corner,6,0,0,stock,e2f1,8486095629,30379153149868,30379496712015,8242533482,8486,7806,343294673,79488,5729,1,629488,2739648,5
5825,KBB,10,corner,7,0,1,corner,c3d3,7806598918,30379497113055,30380219119408,7184592565,8242,7806,700770821,77566,4287,1,605364,2765666,4
5825,KBB,10,corner,8,0,0,stock,f1e1,8242533482,30380219532205,30380454902009,8107163678,8242,7184,231512213,79539,5548,1,552534,4832149,3
5825,KBB,10,corner,9,0,1,corner,c6g2,7184592565,30380455262167,30380786392738,6953461994,8107,7184,330940378,77536,3856,1,500847,4614194,3
5825,KBB,10,corner,10,0,0,stock,e1d1,8107163678,30380786810453,30381029467725,7964506406,8107,6953,242408525,79619,5749,1,622168,5080169,4
5825,KBB,10,corner,11,0,1,corner,c5f2,6953461994,30381029983836,30381440115736,6643330094,7964,6953,409864714,83694,4858,1,710491,5884038,4
5825,KBB,10,corner,12,0,0,stock,d1c1,7964506406,30381440506961,30381830297276,7674716091,7964,6643,385848378,78707,4987,1,562829,3385912,4
5825,KBB,10,corner,13,0,1,corner,d3c3,6643330094,30381830684434,30382232122850,6341891678,7674,6643,400968274,109464,4196,1,595378,5164835,5
5825,KBB,10,corner,14,0,0,stock,c1b1,7674716091,30382232476188,30382428682867,7578509412,7674,6341,195966266,71196,4888,1,575329,3410147,5
5825,KBB,10,corner,15,0,1,corner,g2d5,6341891678,30382429090847,30382855822641,6015159884,7578,6341,424977514,82783,3325,1,763099,2790183,6
5825,KBB,10,corner,16,0,0,stock,b1a1,7578509412,30382856240686,30383064598406,7470151692,7578,6015,207924385,78828,4777,1,518246,6618745,14
5825,KBB,10,corner,17,0,1,corner,c3b3,6015159884,30383064997954,30383369011030,5811146808,7470,6015,303431038,79208,3546,1,840813,2878425,15
5825,KBB,10,corner,18,0,0,stock,a1b1,7470151692,30383369421343,30383557107985,7382465050,7470,5811,186076301,75512,0,1,831661,3747952,44
5825,KBB,10,corner,19,0,1,corner,d5f3,5811146808,30383557492971,30383724393191,5744246588,7382,5811,166222275,80440,0,1,703255,2868399,39
5825,KBB,10,corner,20,0,0,stock,b1c1,7382465050,30383724815603,30383727343131,7479937522,7382,5744,2452419,79098,0,1,448389,2464868,1
5825,KBB,10,corner,21,0,1,corner,f2e3,5744246588,30383727530040,30383729586013,5842190615,7479,5744,1999313,57917,0,1,243723,1999313,1
5825,KBB,10,corner,22,0,0,stock,c1b1,7479937522,30383729763729,30383730124098,7579577153,7479,5842,319287,52999,0,1,231405,319287,1
5825,KBB,10,corner,23,0,1,corner,f3e4,5842190615,30383730228754,30383730545127,5941874242,7579,5842,279958,47541,0,1,143293,279958,1
5825,KBB,10,corner,24,0,0,stock,b1a1,7579577153,30383730637425,30383730789512,7679425066,7579,5941,96203,45227,0,1,128432,96203,1
5825,KBB,10,corner,25,0,1,corner,e3d4,5941874242,30383730877724,30383731181278,6041570688,7679,5941,269282,45338,0,1,144105,269282,1
5825,KBB,10,stock,0,0,0,stock,b3c2,10000000000,30366065410158,30366631963041,9533447117,10000,10000,561730540,129233,5068,1,797400,2255004,14
5825,KBB,10,stock,1,0,1,stock,b5c4,10000000000,30366632366234,30367076560403,9655805831,9533,10000,440163618,141291,4687,1,716451,3220335,13
5825,KBB,10,stock,2,0,0,stock,c2d2,9533447117,30367077142102,30367538030956,9172558263,9533,9655,460634389,77645,5248,1,734596,0,19
5825,KBB,10,stock,3,0,1,stock,e7c5,9655805831,30367538468560,30368524246516,8770027875,9172,9655,978063433,74140,5338,1,660888,0,19
5825,KBB,10,stock,4,0,0,stock,d2e2,9172558263,30368524816468,30369339133903,8458240828,9172,8770,813914207,91797,7311,1,875838,3056400,12
5825,KBB,10,stock,5,0,1,stock,c4c3,8770027875,30369339669453,30370438854521,7770842807,8458,8770,1098845913,116604,5788,1,750139,4160788,5
5825,KBB,10,stock,6,0,0,stock,e2f1,8458240828,30370439254278,30370750361814,8247133292,8458,7770,310252434,76163,4397,1,613565,4567975,5
5825,KBB,10,stock,7,0,1,stock,c3d3,7770842807,30370750811726,30371387071736,7234582797,8247,7770,635945548,79518,5498,1,704082,5059308,4
5825,KBB,10,stock,8,0,0,stock,f1e1,8247133292,30371387489631,30371590183786,8144439137,8247,7234,198889179,81081,5218,1,566033,4398712,3
5825,KBB,10,stock,9,0,1,stock,c6g2,7234582797,30371590575461,30371915795862,7009362396,8144,7234,324985233,79578,4357,1,586764,0,18
5825,KBB,10,stock,10,0,0,stock,e1d1,8144439137,30371916241127,30372153807848,8006872416,8144,7009,237286102,81552,5168,1,433748,3647993,4
5825,KBB,10,stock,11,0,1,stock,c5f2,7009362396,30372154195357,30372538372443,6725185310,8006,7009,383891096,81491,5639,1,587597,5676739,4
5825,KBB,10,stock,12,0,0,stock,d1c1,8006872416,30372538789716,30372906727979,7738934153,8006,6725,360218869,80571,4917,1,596530,5098216,4
5825,KBB,10,stock,13,0,1,stock,d3c3,6725185310,30372907141657,30373264510310,6467816657,7738,6725,357073144,82012,5068,1,627958,4745109,5
5825,KBB,10,stock,14,0,0,stock,c1b1,7738934153,30373264949697,30373491964205,7611919645,7738,6467,224292667,81682,5268,1,800615,5331154,6
5825,KBB,10,stock,15,0,1,stock,g2d5,6467816657,30373492372125,30373837369377,6222819405,7611,6467,344672348,79779,4697,1,647974,3504678,6
5825,KBB,10,stock,16,0,0,stock,b1a1,7611919645,30373837787892,30374027711609,7521995928,7611,6222,189133951,82322,0,1,1522112,6168543,13
5825,KBB,10,stock,17,0,1,stock,c3b3,6222819405,30374028335201,30374336095723,6015058883,7521,6222,305520815,79188,4617,1,862276,4957506,15
5825,KBB,10,stock,18,0,0,stock,a1b1,7521995928,30374336506037,30374528733297,7429768668,7521,6015,190916253,108432,0,1,924569,6825724,42
5825,KBB,10,stock,19,0,1,stock,d5f3,6015058883,30374529171842,30374721648605,5922582120,7429,6015,190187025,82553,0,1,930409,4604450,40
5825,KBB,10,stock,20,0,0,stock,b1c1,7429768668,30374722090806,30374738408386,7513451088,7429,5922,16185848,86088,0,1,554337,5908535,3
5825,KBB,10,stock,21,0,1,stock,f2e3,5922582120,30374738765761,30374741639256,6019708625,7513,5922,2804614,68312,3475,1,381940,2705536,1
5825,KBB,10,stock,22,0,0,stock,c1b1,7513451088,30374742002609,30374742549416,7612904281,7513,6019,393837,64867,4246,2,565484,0,65
5825,KBB,10,stock,23,0,1,stock,f3e4,6019708625,30374742664769,30374743095552,6119277842,7612,6019,389401,51557,0,1,122503,389401,1
5825,KBB,10,stock,24,0,0,stock,b1a1,7612904281,30374743217455,30374743364244,7712757492,7612,6119,107160,49465,0,2,163734,107160,1
5825,KBB,10,stock,25,0,1,stock,e3d4,6119277842,30374743457203,30374743798183,6218936862,7712,6119,274399,46369,0,1,131006,274399,1
5825,KBB,10,table,0,0,0,stock,b3c2,10000000000,30362287853402,30362814034539,9573818863,10000,10000,521709119,116624,4499944,2,721628,3817755,13
5825,KBB,10,table,1,0,1,table,b5b4,10000000000,30362814365624,30362819154518,10095211106,9573,10000,4790998,5131105,28392,1,5131105,28392,1
5825,KBB,10,table,2,0,0,stock,c2d2,9573818863,30362819336440,30363328937159,9164218144,9573,10095,502022797,55103,0,1,380790,4666112,7
5825,KBB,10,table,3,0,1,table,e7c5,10095211106,30363329284578,30363334280166,10190215518,9164,10095,4976094,5333698,21352,1,5333698,21352,1
5825,KBB,10,table,4,0,0,stock,d2e2,9164218144,30363334450070,30363598528319,9000139895,9164,10190,260326617,67240,5492184,2,274229,5559424,3
5825,KBB,10,table,5,0,1,table,b4c3,10190215518,30363599050399,30363611417145,10277848772,9000,10190,11477503,12619176,893263,1,12619176,893263,1
5825,KBB,10,table,6,0,0,stock,e2f1,9000139895,30363612962745,30363908026722,8805075918,9000,10277,287289274,152668,0,1,1176335,2998885,4
5825,KBB,10,table,7,0,1,table,c3d3,10277848772,30363908515172,30363913247736,10373116208,8805,10277,4711189,5212126,23435,1,5212126,23435,1
5825,KBB,10,table,8,0,0,stock,f1e1,8805075918,30363913401636,30364410415240,8408062314,8805,10373,496706187,60830,0,1,321130,6611784,4
5825,KBB,10,table,9,0,1,table,c6g2,10373116208,30364410825753,30364415333041,10468608920,8408,10373,4508647,4929694,23555,1,4929694,23555,1
5825,KBB,10,table,10,0,0,stock,e1d1,8408062314,30364415485969,30364766996243,8156552040,8408,10468,344026420,61732,4459403,2,308602,4521135,5
5825,KBB,10,table,11,0,1,table,c5f2,10468608920,30364767467337,30364771819683,10564256574,8156,10468,4354277,4836966,24958,1,4836966,24958,1
5825,KBB,10,table,12,0,0,stock,d1c1,8156552040,30364771993903,30365221928823,7806617120,8156,10564,445960018,59830,0,1,396951,3990844,5
5825,KBB,10,table,13,0,1,table,d3c3,10564256574,30365222320649,30365226843490,10659733733,7806,10564,4525873,4929285,27571,1,4929285,27571,1
5825,KBB,10,table,14,0,0,stock,c1b1,7806617120,30365227063890,30365436435602,7697245408,7806,10659,209164559,70084,4873762,2,386054,4943846,5
5825,KBB,10,table,15,0,1,table,f2c5,10659733733,30365436817222,30365441327935,10755223020,7697,10659,4488918,4880062,23965,1,4880062,23965,1
5825,KBB,10,table,16,0,0,stock,b1c1,7697245408,30365441489526,30365689590792,7549144142,7697,10755,247250691,63094,0,1,905178,6511525,8
5825,KBB,10,table,17,0,1,table,g2f3,10755223020,30365691444022,30365697875907,10848791135,7549,10755,6405105,8270749,30927,1,8270749,30927,1
5825,KBB,10,table,18,0,0,stock,c1b1,7549144142,30365698094794,30365887405769,7459833167,7549,10848,185929123,87481,5871009,2,1501388,7722561,32
5825,KBB,10,table,19,0,1,table,c3b3,10848791135,30365888346405,30365893625797,10943511743,7459,10848,5256402,5588918,25929,1,5588918,25929,1
5825,KBB,10,table,20,0,0,stock,b1a1,7459833167,30365893988499,30365898676977,7555144689,7459,10943,4482808,506405,0,1,377343,4482808,1
5825,KBB,10,table,21,0,1,table,b3c2,10943511743,30365898916285,30365904626621,11037801407,7555,10943,5712472,6140170,0,0,6140170,0,0
5825,KBB,10,table,22,0,0,stock,a1a2,7555144689,30365904947441,30365905381710,7654710420,7555,11037,372796,70996,0,1,334850,372796,1
5825,KBB,10,table,23,0,1,table,f3d5,11037801407,30365905489851,30365910874080,11132417178,7654,11037,5386456,5540216,0,0,5540216,0,0
5825,KBB,10,table,24,0,0,stock,a2a1,7654710420,30365911048200,30365911254940,7754503680,7654,11132,146599,72038,0,1,186568,146599,1
5825,KBB,10,table,25,0,1,table,c5d4,11132417178,30365911360317,30365914852126,11228925369,7754,11132,3493873,3644738,0,0,3644738,0,0
6710,KBN,10,corner,0,2,1,stock,d8e7,10000000000,30377410872252,30378796136172,8714736080,10000,10000,1381190014,92139,5496679,2,803529,4868723,13
6710,KBN,10,corner,1,2,0,corner,c4d6,10000000000,30378796534498,30379458376251,9438158247,10000,8714,661363212,240889,4998,1,842229,0,21
6710,KBN,10,corner,2,2,1,stock,e7e6,8714736080,30379458713746,30379886247960,8387201866,9438,8714,423543959,81381,4237,1,622835,5207709,12
6710,KBN,10,corner,3,2,0,corner,b5f1,9438158247,30379886570052,30380259991238,9164737061,9438,8387,361471638,56985,4137,1,770489,5333467,11
6710,KBN,10,corner,4,2,1,stock,e6d7,8387201866,30380260518787,30381064118175,7683602478,9164,8387,792300405,78947,6771,1,820905,3368145,11
6710,KBN,10,corner,5,2,0,corner,f1c4,9164737061,30381064507857,30383519734395,6809510523,9164,7683,2444031900,66850,4717,1,790809,0,25
6710,KBN,10,corner,6,2,1,stock,d7e7,7683602478,30383520164899,30385218983956,6084783421,6809,7683,1690335822,69884,6219,1,348980,3736164,8
6710,KBN,10,corner,7,2,0,corner,c5c6,6809510523,30385219386798,30385402308808,6726588513,6809,6084,182631492,69604,4296,1,673825,4501196,15
6710,KBN,10,corner,8,2,1,stock,e7f6,6084783421,30385402708997,30386096122946,5491369472,6726,6084,693054888,89103,4767,1,582050,5173488,6
6710,KBN,10,corner,9,2,0,corner,c6d5,6726588513,30386096486308,30386434963217,6488111604,6726,5491,334266942,65939,4226,1,665512,3410779,6
6710,KBN,10,corner,10,2,1,stock,f6e7,5491369472,30386435350094,30386667856600,5358862966,6488,5491,232165163,69814,4827,1,871359,4549969,5
6710,KBN,10,corner,11,2,0,corner,d5e5,6488111604,30386668246632,30386838195041,6418163195,6488,5358,169645866,66649,4557,1,382671,3649184,5
6710,KBN,10,corner,12,2,1,stock,e7d7,5358862966,30386838688708,30387018636638,5278915036,6418,5358,179645398,101211,6379,1,777639,5176502,12
6710,KBN,10,corner,13,2,0,corner,c4d5,6418163195,30387019007081,30387383729552,6153440724,6418,5278,362443527,67210,0,1,600487,6996698,7
6710,KBN,10,corner,14,2,1,stock,d7c7,5278915036,30387384157941,30387531224439,5231848538,6153,5278,146827366,70015,4206,1,357112,3744156,14
6710,KBN,10,corner,15,2,0,corner,d6c4,6153440724,30387531576935,30387780198861,6004818798,6153,5231,248364109,64736,0,1,589080,4424671,8
6710,KBN,10,corner,16,2,1,stock,c7d7,5231848538,30387780576845,30387956940659,5155484724,6004,5231,174074454,71086,0,1,593736,5326858,7
6710,KBN,10,corner,17,2,0,corner,e5f6,6004818798,30387957285203,30389692550158,4369553843,6004,5155,1734842275,67040,0,1,499596,2718135,4
6710,KBN,10,corner,18,2,1,stock,d7e8,5155484724,30389692970697,30389839560001,5108895420,4369,5155,146318339,71026,0,1,704562,6881251,6
6710,KBN,10,corner,19,2,0,corner,c4e5,4369553843,30389840303642,30390407457333,3902400152,4369,5108,566866874,176403,4917,1,401798,3476607,6
6710,KBN,10,corner,20,2,1,stock,e8d8,5108895420,30390407866595,30390838428100,4778333915,3902,5108,422912362,72358,5288,1,696100,4029412,8
6710,KBN,10,corner,21,2,0,corner,d5c6,3902400152,30390838841518,30391151348758,3689892912,3902,4778,312222311,71366,5118,1,675648,5043494,6
6710,KBN,10,corner,22,2,1,stock,d8c8,4778333915,30391151732091,30391552441243,4477624763,3689,4778,400509138,70715,5238,1,559876,4127278,4
6710,KBN,10,corner,23,2,0,corner,f6e7,3689892912,30391552871206,30392039171413,3303592705,3689,4477,482409571,122272,7221,1,696410,2961138,5
6710,KBN,10,corner,24,2,1,stock,c8c7,4477624763,30392039674885,30392519544991,4097754657,3303,4477,460088766,108963,5938,1,680744,4182751,4
6710,KBN,10,corner,25,2,0,corner,c6e8,3303592705,30392519962365,30393268971970,2654583100,3303,4097,748753222,91056,4657,1,628368,3903874,4
6710,KBN,10,corner,26,2,1,stock,c7b6,4097754657,30393269366460,30393582532595,3884588522,2654,4097,312947033,71747,4987,1,595719,2536224,7
6710,KBN,10,corner,27,2,0,corner,e7d6,2654583100,30393582938402,30393850500912,2487020590,2654,3884,267350576,72268,4647,1,584071,4951016,4
6710,KBN,10,corner,28,2,1,stock,b6b7,3884588522,30393850995411,30393970012907,3865571026,2487,3884,118817798,71787,6179,1,668768,4897957,4
6710,KBN,10,corner,29,2,0,corner,e8c6,2487020590,30393970511701,30394121833616,2435698675,2487,3865,151055974,82844,7391,1,739434,5355920,6
6710,KBN,10,corner,30,2,1,stock,b7c8,3865571026,30394122177079,30394381075479,3706672626,2435,3865,258585408,68682,4167,1,630972,5725912,5
6710,KBN,10,corner,31,2,0,corner,c6d7,2435698675,30394381472962,30394723917195,2193254442,2435,3706,342214108,84657,4486,1,711171,2397037,6
6710,KBN,10,corner,32,2,1,stock,c8b7,3706672626,30394724305585,30394844995441,3685982770,2193,3706,120473650,151516,4477,1,477869,3513282,8
6710,KBN,10,corner,33,2,0,corner,e5c4,2193254442,30394845390801,30395051431348,2087213895,2193,3685,205837618,75873,0,1,577292,2609884,4
6710,KBN,10,corner,34,2,1,stock,b7a7,3685982770,30395051863243,30395224804901,3613041112,2087,3685,172436892,73350,0,1,698132,4137353,5
6710,KBN,10,corner,35,2,0,corner,d6c7,2087213895,30395225169045,30395420622559,1991760381,2087,3613,187856608,74190,0,1,631843,6462481,8
6710,KBN,10,corner,36,2,1,stock,a7a6,3613041112,30395421202185,30395535928715,3598314582,1991,3613,114416520,88983,7140,1,961085,2686558,6
6710,KBN,10,corner,37,2,0,corner,d7c6,1991760381,30395536626637,30395709075550,1919311468,1991,3598,172040100,89373,0,1,980743,3375556,8
6710,KBN,10,corner,38,2,1,stock,a6a7,3598314582,30395709557510,30395823693700,3584178392,1919,3598,113643145,84887,0,1,948487,6443303,19
6710,KBN,10,corner,39,2,0,corner,c6b5,1919311468,30395824300526,30395969868281,1873743713,1919,3584,144857548,75393,0,1,761525,3699359,21
6710,KBN,10,corner,40,2,1,stock,a7a8,3584178392,30395970265284,30395976295498,3678148178,1873,3584,5911079,76304,0,1,491193,5763308,3
6710,KBN,10,corner,41,2,0,corner,c4b6,1873743713,30395976690277,30396004885107,1945548883,1873,3678,25528284,80320,4346,1,762759,6872062,23
6710,KBN,10,corner,42,2,1,stock,a8a7,3678148178,30396005276572,30396005804941,3777619809,1945,3678,414899,74141,4297,1,421519,317584,1
6710,KBN,10,corner,43,2,0,corner,b6c8,1945548883,30396005994223,30396006531125,2045011981,1945,3777,389186,53158,2804,2,428854,0,65
6710,KBN,10,corner,44,2,1,stock,a7a8,3777619809,30396006653167,30396006841809,3877431167,2045,3777,146899,44496,2383,1,132558,91807,1
6710,KBN,10,corner,45,2,0,corner,b5c6,2045011981,30396006954708,30396007362707,2144603982,2045,3877,260952,43264,0,2,291573,34111,66
6710,KBN,10,stock,0,2,1,stock,d8e7,10000000000,30396098702807,30397491063408,8707639399,10000,10000,1388125516,103996,5580104,2,936137,5029754,13
6710,KBN,10,stock,1,2,0,stock,c4a5,10000000000,30397491465739,30397970786415,9620679324,10000,8707,478934453,116664,4406,1,742457,4177653,12
6710,KBN,10,stock,2,2,1,stock,e7e6,8707639399,30397971153063,30398346905335,8431887127,9620,8707,375495079,64997,3946,1,549891,4768504,11
6710,KBN,10,stock,3,2,0,stock,a5b3,9620679324,30398347310942,30398714790405,9353199861,9620,8431,363547370,67310,4447,1,665653,4581475,5
6710,KBN,10,stock,4,2,1,stock,e6f5,8431887127,30398715164564,30398925021347,8322030344,9353,8431,205940368,67311,4466,1,620896,4738049,9
6710,KBN,10,stock,5,2,0,stock,b5f1,9353199861,30398925419062,30400051641078,8326977845,9353,8322,1107045460,69093,4246,1,723010,0,21
6710,KBN,10,stock,6,2,1,stock,f5f4,8322030344,30400052064641,30400326914403,8147180582,8326,8322,274436690,69835,5678,1,336020,3833379,9
6710,KBN,10,stock,7,2,0,stock,c5b4,8326977845,30400327309844,30402592600295,6161687394,8326,8147,2260153325,67861,4507,1,656099,5700185,11
6710,KBN,10,stock,8,2,1,stock,f4e4,8147180582,30402593011709,30402888206575,7951985716,6161,8147,294724926,70024,0,1,876508,2953957,15
6710,KBN,10,stock,9,2,0,stock,b3a5,6161687394,30402888599342,30403222520853,5927765883,6161,7951,333377445,68262,4487,1,914554,3283259,14
6710,KBN,10,stock,10,2,1,stock,e4d5,7951985716,30403223212637,30404092691860,7182506493,5927,7951,858199123,69975,0,1,994622,4789035,16
6710,KBN,10,stock,11,2,0,stock,a5c4,5927765883,30404093194161,30404356490548,5764469496,5927,7182,263025849,82293,0,1,750000,2818254,10
6710,KBN,10,stock,12,2,1,stock,d5e4,7182506493,30404356848322,30404656656340,6982698475,5764,7182,295799729,68292,0,1,694468,3156850,16
6710,KBN,10,stock,13,2,0,stock,b4c5,5764469496,30404657059383,30405492922089,5028606790,5764,6982,827762314,71026,0,1,1115116,2942330,12
6710,KBN,10,stock,14,2,1,stock,e4f5,6982698475,30405493519161,30407448913957,5127303679,5028,6982,1937014699,65538,0,1,787106,2501842,6
6710,KBN,10,stock,15,2,0,stock,c5d5,5028606790,30407449400424,30407959405679,4618601535,5028,5127,505820405,98097,0,1,875656,2602994,11
6710,KBN,10,stock,16,2,1,stock,f5f6,5127303679,30407959829192,30408312455913,4874676958,4618,5127,352392074,71847,0,1,659726,4174277,9
6710,KBN,10,stock,17,2,0,stock,d5d6,4618601535,30408312873087,30408871423823,4160050799,4618,4874,543141800,72118,0,1,689628,3130841,9
6710,KBN,10,stock,18,2,1,stock,f6f7,4874676958,30408871812884,30409016974254,4829515588,4160,4874,138883503,70055,0,1,557012,4202690,5
6710,KBN,10,stock,19,2,0,stock,c4e5,4160050799,30409017312930,30409314532897,3962830832,4160,4829,296908768,66609,22193,1,630777,2559909,10
6710,KBN,10,stock,20,2,1,stock,f7f6,4829515588,30409314922399,30409697316260,4547121727,3962,4829,378398308,72398,0,1,692085,6152659,11
6710,KBN,10,stock,21,2,0,stock,e5c4,3962830832,30409697663880,30409976973340,3783521372,3962,4547,278983642,81381,4477,1,537823,2217198,8
6710,KBN,10,stock,22,2,1,stock,f6f7,4547121727,30409977455120,30410217553751,4407023096,3783,4547,236285989,72868,4728,1,633647,6256304,4
6710,KBN,10,stock,23,2,0,stock,c4e5,3783521372,30410218093818,30410447650335,3653964855,3783,4407,225643354,84195,6961,1,787804,5768176,14
6710,KBN,10,stock,24,2,1,stock,f7f6,4407023096,30410448053878,30410620137779,4334939195,3653,4407,168189027,71096,3946,1,258774,3845227,8
6710,KBN,10,stock,25,2,0,stock,f1d3,3653964855,30410620545188,30411824133721,2550376322,3653,4334,1182832869,71977,4357,1,591392,3333754,15
6710,KBN,10,stock,26,2,1,stock,f6g5,4334939195,30411824853566,30412127388332,4132404429,2550,4334,298522190,80740,6830,1,1090227,3029120,10
6710,KBN,10,stock,27,2,0,stock,d6e7,2550376322,30412127835600,30412278647532,2499564390,2550,4132,150505554,72288,5478,1,727294,4045896,15
6710,KBN,10,stock,28,2,1,stock,g5f4,4132404429,30412279074881,30412447440935,4064038375,2499,4132,168060404,73951,0,1,713142,4926410,12
6710,KBN,10,stock,29,2,0,stock,e5c4,2499564390,30412447864228,30413119700715,1927727903,2499,4064,664662594,72849,4657,1,587446,4019256,5
6710,KBN,10,stock,30,2,1,stock,f4g3,4064038375,30413120079291,30413772331576,3511786090,1927,4064,648393318,62714,4396,1,224796,3836634,4
6710,KBN,10,stock,31,2,0,stock,e7f6,1927727903,30413772682660,30414176100024,1624310539,1927,3511,403139152,88852,4437,1,587147,3115067,6
6710,KBN,10,stock,32,2,1,stock,g3f4,3511786090,30414176488705,30414327319215,3460955580,1624,3511,150495017,77246,0,1,697510,3528485,8
6710,KBN,10,stock,33,2,0,stock,d3f5,1624310539,30414327725051,30414658469042,1393566548,1624,3460,326797848,74742,0,1,678533,4212425,8
6710,KBN,10,stock,34,2,1,stock,f4g3,3460955580,30414658921889,30414850900360,3368977109,1393,3460,187972740,74552,5107,1,770250,4972219,8
6710,KBN,10,stock,35,2,0,stock,f6g5,1393566548,30414851372315,30414971016510,1373922353,1393,3368,119429500,77045,5318,1,661197,4503128,4
6710,KBN,10,stock,36,2,1,stock,g3f3,3368977109,30414971437740,30415163576140,3276838709,1373,3368,185318907,75994,4246,1,614706,4459133,4
6710,KBN,10,stock,37,2,0,stock,f5d3,1373922353,30415164274233,30415369323167,1268873419,1373,3276,204685855,70726,5438,1,593155,3594873,6
6710,KBN,10,stock,38,2,1,stock,f3f2,3276838709,30415369724236,30415542036538,3204526407,1268,3276,171977448,74671,4888,1,709228,2148555,10
6710,KBN,10,stock,39,2,0,stock,g5g4,1268873419,30415542447172,30415697703546,1213617045,1268,3204,155048101,75603,0,1,595547,5553085,6
6710,KBN,10,stock,40,2,1,stock,f2e1,3204526407,30415698195731,30416100631027,2902091111,1213,3204,402200602,74761,5128,1,696068,5703829,7
6710,KBN,10,stock,41,2,0,stock,d3c2,1213617045,30416101109682,30416232526621,1182200106,1213,2902,127545748,76354,5258,1,650681,2768370,6
6710,KBN,10,stock,42,2,1,stock,e1f2,2902091111,30416233056112,30416363244825,2871902398,1182,2902,125865581,91296,6590,1,740937,2816291,13
6710,KBN,10,stock,43,2,0,stock,c2f5,1182200106,30416363675248,30416490037657,1155837697,1182,2871,114654275,90255,4727,1,644161,4093628,7
6710,KBN,10,stock,44,2,1,stock,f2e1,2871902398,30416490460569,30416630446002,2831916965,1155,2871,139588185,76143,4938,1,794366,5433677,7
6710,KBN,10,stock,45,2,0,stock,f5c2,1155837697,30416630896545,30416908106270,978627972,1155,2831,276830974,77967,4977,1,773365,4977907,8
6710,KBN,10,stock,46,2,1,stock,e1f2,2831916965,30416908502903,30417101962097,2738457771,978,2831,193165529,74932,4016,1,669007,3396677,5
6710,KBN,10,stock,47,2,0,stock,c2d1,978627972,30417102370918,30417285784229,895214661,978,2738,180773326,75993,4186,1,664291,5509380,6
6710,KBN,10,stock,48,2,1,stock,f2e1,2738457771,30417286191007,30417448271839,2676376939,895,2738,161701537,75642,4617,1,755046,5706885,7
6710,KBN,10,stock,49,2,0,stock,d1f3,895214661,30417448810084,30417534356223,909668522,895,2676,85224879,89744,6820,1,823049,3052575,6
6710,KBN,10,stock,50,2,1,stock,e1f1,2676376939,30417534849750,30417665804098,2645422591,909,2676,127043490,89123,6469,1,646564,5030055,3
6710,KBN,10,stock,51,2,0,stock,g4f4,909668522,30417666397705,30417764661639,911404588,909,2645,94436081,78116,6620,1,806043,5478834,3
6710,KBN,10,stock,52,2,1,stock,f1f2,2645422591,30417765209087,30418019110435,2491521243,911,2645,250091413,89884,6580,1,674416,2668171,3
6710,KBN,10,stock,53,2,0,stock,c4b2,911404588,30418019435340,30418106298419,924541509,911,2491,86661613,67091,0,1,492845,4569578,4
6710,KBN,10,stock,54,2,1,stock,f2e1,2491521243,30418106884856,30418207934787,2490471312,924,2491,100784550,79919,0,1,917451,5117274,5
6710,KBN,10,stock,55,2,0,stock,f4e3,924541509,30418208349877,30418277392868,955498518,924,2490,68774410,79629,0,1,569479,3651548,4
6710,KBN,10,stock,56,2,1,stock,e1f1,2490471312,30418277959115,30418398029793,2470400634,955,2490,119840452,92808,0,1,772072,6042214,4
6710,KBN,10,stock,57,2,0,stock,b2d3,955498518,30418398486435,30418614780161,839204792,955,2470,216076329,88813,6459,1,642488,5380798,4
6710,KBN,10,stock,58,2,1,stock,f1g1,2470400634,30418615274901,30418895620538,2290054997,839,2470,280089445,91126,5769,1,705905,4603217,4
6710,KBN,10,stock,59,2,0,stock,e3f4,839204792,30418896067767,30419001406818,833865741,839,2290,105161874,76314,6019,1,197684,3810835,8
6710,KBN,10,stock,60,2,1,stock,g1h2,2290054997,30419002025653,30419197003301,2195077349,833,2290,194800997,77155,5838,1,773144,5867824,4
6710,KBN,10,stock,61,2,0,stock,f4g4,833865741,30419197357471,30419302423785,828799427,833,2195,102754233,70405,4307,1,516771,2537065,4
6710,KBN,10,stock,62,2,1,stock,h2g1,2195077349,30419302886807,30419445051755,2152912401,828,2195,141944429,72408,4727,1,657142,5067841,5
6710,KBN,10,stock,63,2,0,stock,g4g3,828799427,30419445528238,30419625649252,748678413,828,2152,179861289,77415,4907,1,709578,2350637,6
6710,KBN,10,stock,64,2,1,stock,g1f1,2152912401,30419626053096,30419714413613,2164551884,748,2152,88150483,74611,4547,1,593817,5847434,6
6710,KBN,10,stock,65,2,0,stock,f3g4,748678413,30419714760151,30419828773616,734664948,748,2164,113745306,71957,4828,1,596613,5126768,6
6710,KBN,10,stock,66,2,1,stock,f1g1,2164551884,30419829169538,30419908579748,2185141674,734,2164,79098951,77907,4647,1,685853,0,37
6710,KBN,10,stock,67,2,0,stock,g4e2,734664948,30419909013346,30420008138124,735540170,734,2185,98416747,79178,5258,1,1109132,2799297,19
6710,KBN,10,stock,68,2,1,stock,g1h1,2185141674,30420008566164,30420530251410,1763456428,735,2185,517693796,82463,4467,1,750067,3307425,14
6710,KBN,10,stock,69,2,0,stock,d3f2,735540170,30420530662895,30420966056791,400146274,735,1763,431554046,102523,0,1,512674,5335651,2
6710,KBN,10,stock,70,2,1,stock,h1g1,1763456428,30420966611359,30421123528927,1706538860,400,1763,156656719,127650,6951,1,837210,5201040,3
6710,KBN,10,stock,71,2,0,stock,f2h3,400146274,30421124189875,30421316203443,308132706,400,1706,189872126,98778,8472,1,393397,3651988,4
6710,KBN,10,stock,72,2,1,stock,g1h1,1706538860,30421316722268,30421317049347,1806211781,308,1706,206288,93519,6510,1,589780,85468,1
6710,KBN,10,stock,73,2,0,stock,e2f3,308132706,30421317246502,30421317952697,407426511,308,1806,461668,82723,0,2,500176,58567,66
6710,KBN,10,table,0,2,1,stock,d8e7,10000000000,30369313767235,30370611732940,8802034295,10000,10000,1290225536,116815,2753027,2,1005641,1887897,16
6710,KBN,10,table,1,2,0,table,c4d6,10000000000,30370612153118,30370616386947,10095766171,10000,8802,4178945,4319605,56164,1,4319605,56164,1
6710,KBN,10,table,2,2,1,stock,e7e6,8802034295,30370616520136,30371013505616,8505048815,10095,8802,396707338,49624,3438169,2,390211,3487793,15
6710,KBN,10,table,3,2,0,table,b5d3,10095766171,30371013870882,30371018543467,10191093586,10095,8505,4652332,5027511,21562,1,5027511,21562,1
6710,KBN,10,table,4,2,1,stock,e6e5,8505048815,30371018683967,30371674622775,7949110007,10191,8505,655627463,64857,0,1,438016,5316331,8
6710,KBN,10,table,5,2,0,table,d3f5,10191093586,30371675030855,30371680924575,10285199866,10191,7949,5843729,6262383,51817,1,6262383,51817,1
6710,KBN,10,table,6,2,1,stock,e5f4,7949110007,30371681089602,30372699957845,7030241764,10285,7949,1018391131,56394,2863392,2,681046,6911852,10
6710,KBN,10,table,7,2,0,table,c5d4,10285199866,30372700341689,30372706790198,10378751357,10285,7030,6427259,6757792,23765,1,6757792,23765,1
6710,KBN,10,table,8,2,1,stock,f4f3,7030241764,30372706962115,30372951045887,6886157992,10378,7030,236034756,52067,0,1,356262,5041351,9
6710,KBN,10,table,9,2,0,table,f5b1,10378751357,30372951479996,30372956970693,10473260660,10378,6886,5462288,5905890,30977,1,5905890,30977,1
6710,KBN,10,table,10,2,1,stock,f3f2,6886157992,30372957156370,30373202683820,6740630542,10473,6886,242762023,53871,0,1,469380,5313678,11
6710,KBN,10,table,11,2,0,table,d4d3,10473260660,30373203090508,30373210299664,10566051504,10473,6740,7184569,7601861,26750,1,7601861,26750,1
6710,KBN,10,table,12,2,1,stock,f2f3,6740630542,30373210495737,30373451210279,6599916000,10566,6740,236696199,59659,5453657,2,492313,5513316,8
6710,KBN,10,table,13,2,0,table,d6f7,10566051504,30373451556806,30373455950995,10661657315,10566,6599,4395768,4820843,42083,1,4820843,42083,1
6710,KBN,10,table,14,2,1,stock,f3f2,6599916000,30373456190433,30373787131964,6368974469,10661,6599,330730452,49083,0,1,380720,3810004,10
6710,KBN,10,table,15,2,0,table,f7e5,10661657315,30373787555247,30373792316323,10756896239,10661,6368,4736617,5170164,25898,1,5170164,25898,1
6710,KBN,10,table,16,2,1,stock,f2g3,6368974469,30373792461200,30373994726725,6266708944,10756,6368,202039026,53049,3493993,2,355060,3560882,5
6710,KBN,10,table,17,2,0,table,d3e3,10756896239,30373995435735,30374000725201,10851606773,10756,6266,5290983,6009015,0,0,6009015,0,0
6710,KBN,10,table,18,2,1,stock,g3h3,6266708944,30374000887804,30375796056817,4571539931,10851,6266,1791376948,52208,0,1,252826,3115559,3
6710,KBN,10,table,19,2,0,table,e3f4,10851606773,30375796402904,30375801366163,10946643514,10851,4571,4941402,5329911,23255,1,5329911,23255,1
6710,KBN,10,table,20,2,1,stock,h3g2,4571539931,30375801516938,30375933100071,4539956798,10946,4571,131153413,51136,2458388,2,410030,2485539,13
6710,KBN,10,table,21,2,0,table,b1e4,10946643514,30375933494390,30375939654188,11040483716,10946,4539,6144377,6546917,17787,1,6546917,17787,1
6710,KBN,10,table,22,2,1,stock,g2f2,4539956798,30375939840666,30376083741771,4496055693,11040,4539,142675700,55413,0,1,443683,5117114,6
6710,KBN,10,table,23,2,0,table,e4f3,11040483716,30376084194779,30376090439493,11134239002,11040,4496,6220992,6405156,26329,1,6405156,26329,1
6710,KBN,10,table,24,2,1,stock,f2e1,4496055693,30376090620984,30376456256176,4230420501,11134,4496,365506268,60430,5325355,2,295430,5385785,3
6710,KBN,10,table,25,2,0,table,f4e3,11134239002,30376456637386,30376463221017,11227655371,11134,4230,6559997,6952462,26380,1,6952462,26380,1
6710,KBN,10,table,26,2,1,stock,e1f1,4230420501,30376463478211,30376618097868,4175800844,11227,4230,154509246,119158,0,1,354228,4523900,3
6710,KBN,10,table,27,2,0,table,e5g6,11227655371,30376618465137,30376624524455,11321596053,11227,4175,6034995,6412638,26449,1,6412638,26449,1
6710,KBN,10,table,28,2,1,stock,f1g1,4175800844,30376624714198,30376839600401,4060914641,11321,4175,214555051,74382,3219202,2,385434,7287573,5
6710,KBN,10,table,29,2,0,table,e3e2,11321596053,30376840054179,30376846542348,11415107884,11321,4060,6469542,6510783,20611,1,6510783,20611,1
6710,KBN,10,table,30,2,1,stock,g1h2,4060914641,30376846817369,30376963341751,4044390259,11415,4060,116307451,54952,0,1,479797,5184655,5
6710,KBN,10,table,31,2,0,table,e2f2,11415107884,30376963723141,30376969372666,11509458359,11415,4044,5624511,6015764,27061,1,6015764,27061,1
6710,KBN,10,table,32,2,1,stock,h2h3,4044390259,30376969549110,30377104224904,4009714465,11509,4044,132876612,54371,0,1,528188,3887840,9
6710,KBN,10,table,33,2,0,table,f3e2,11509458359,30377104614767,30377111192038,11602881088,11509,4009,6555530,6956929,24737,1,6956929,24737,1
6710,KBN,10,table,34,2,1,stock,h3h2,4009714465,30377111452587,30377232520871,3988646181,11602,4009,120620546,62824,4490339,2,694687,4553163,33
6710,KBN,10,table,35,2,0,table,e2f1,11602881088,30377232899507,30377238321211,11697459384,11602,3988,5400557,5789307,23355,1,5789307,23355,1
6710,KBN,10,table,36,2,1,stock,h2h1,3988646181,30377238484235,30377246161722,4080968694,11697,3988,7585698,55673,0,1,247819,5517281,6
6710,KBN,10,table,37,2,0,table,g6e5,11697459384,30377246366808,30377250436832,11793389360,11697,4080,4071744,4282519,21933,1,4282519,21933,1
6710,KBN,10,table,38,2,1,stock,h1h2,4080968694,30377250613156,30377251022818,4180559032,11793,4080,353658,52038,0,1,165487,353658,1
6710,KBN,10,table,39,2,0,table,e5f3,11793389360,30377251133884,30377255834060,11888689184,11793,4180,4701324,4855033,0,0,4855033,0,0
6710,KBN,10,table,40,2,1,stock,h2h1,4180559032,30377255945907,30377256124183,4280380756,11888,4180,127350,65829,5428,1,119598,132778,1
6710,KBN,10,table,41,2,0,table,f1g2,11888689184,30377256218544,30377258346345,11986561383,11888,4280,2128866,2260403,4867,1,2260403,4867,1
6950,KBN,10,corner,0,0,1,stock,d1d2,10000000000,30398218417161,30398500561897,9817855264,10000,10000,276955887,85888,5889056,2,837449,5337513,13
6950,KBN,10,corner,1,0,0,corner,d4b5,10000000000,30398501043266,30399256988589,9344054677,10000,9817,755335093,139638,6741,1,956787,2552919,15
6950,KBN,10,corner,2,0,1,stock,d2d3,9817855264,30399257463388,30400111805084,9063513568,9344,9817,831910225,85127,7381,1,1006892,2416946,6
6950,KBN,10,corner,3,0,0,corner,c7b6,9344054677,30400112337079,30401025916792,8530474964,9344,9063,909615305,79970,6439,1,464634,3539540,4
6950,KBN,10,corner,4,0,1,stock,d3c4,9063513568,30401026313345,30401661555934,8528270979,8530,9063,631367192,71147,4516,1,561306,5585153,4
6950,KBN,10,corner,5,0,0,corner,b5c7,8530474964,30401661895301,30402013612731,8278757534,8530,8528,351494713,63254,4697,1,512946,6003636,6
6950,KBN,10,corner,6,0,1,stock,c4d3,8528270979,30402014093299,30402307049611,8335314667,8278,8528,292621859,71267,4697,1,733265,5803048,5
6950,KBN,10,corner,7,0,0,corner,b6e3,8278757534,30402307529538,30402651115398,8035171674,8278,8335,342581585,81302,6900,1,824270,4341467,7
6950,KBN,10,corner,8,0,1,stock,d3c4,8335314667,30402651570167,30402918995217,8167889617,8035,8335,267223293,72849,4857,1,609232,0,22
6950,KBN,10,corner,9,0,0,corner,f3e2,8035171674,30402919366532,30403631044097,7423494109,8035,8167,711351976,71306,4427,1,603072,4528406,10
6950,KBN,10,corner,10,0,1,stock,c4c3,8167889617,30403631454220,30403841344595,8057999242,7423,8167,209711456,70996,4046,1,565842,4445493,5
6950,KBN,10,corner,11,0,0,corner,e3a7,7423494109,30403841720887,30404183867597,7181347399,7423,8057,337829857,70245,23314,1,829718,2151159,10
6950,KBN,10,corner,12,0,1,stock,c3b4,8057999242,30404184295607,30404399635094,7942659755,7181,8057,214972873,73249,0,1,609009,3704927,9
6950,KBN,10,corner,13,0,0,corner,e2d3,7181347399,30404400065567,30406400411176,5281001790,7181,7942,1999606876,74852,0,1,382370,3935210,7
6950,KBN,10,corner,14,0,1,stock,b4b3,7942659755,30406400836191,30406931357799,7512138147,5281,7942,529402344,75072,0,1,943285,3138392,18
6950,KBN,10,corner,15,0,0,corner,a7b6,5281001790,30406932123052,30408502542520,3810582322,5281,7512,1566225317,84866,0,1,255362,3875692,4
6950,KBN,10,corner,16,0,1,stock,b3b4,7512138147,30408503119111,30408734585616,7380671642,3810,7512,231148767,77456,0,1,922466,4877136,10
6950,KBN,10,corner,17,0,0,corner,b6e3,3810582322,30408734996100,30409381566974,3264011448,3810,7380,642488506,75493,0,1,615530,5002403,11
6950,KBN,10,corner,18,0,1,stock,b4b3,7380671642,30409382124477,30409642921784,7219874335,3264,7380,260481289,86128,0,1,846003,5840083,9
6950,KBN,10,corner,19,0,0,corner,e3d2,3264011448,30409643299128,30410478200309,2529110267,3264,7219,834500479,72448,4587,1,536281,4591360,4
6950,KBN,10,corner,20,0,1,stock,b3a4,7219874335,30410478572746,30411877455870,5920991211,2529,7219,1393804096,70856,0,1,808438,5427668,8
6950,KBN,10,corner,21,0,0,corner,d3c4,2529110267,30411878129166,30412823397967,1683841466,2529,5920,945017773,77946,6850,1,750279,5743509,2
6950,KBN,10,corner,22,0,1,stock,a4a3,5920991211,30412823963713,30413103392343,5741562581,1683,5920,271517597,114681,8022,1,776709,3884906,3
6950,KBN,10,corner,23,0,0,corner,c7a6,1683841466,30413103788926,30413858990773,1028639619,1683,5741,750316286,72548,0,1,525213,4214338,4
6950,KBN,10,corner,24,0,1,stock,a3b2,5741562581,30413859496509,30414242132903,5458926187,1028,5741,380188687,86099,5929,1,722799,4382739,4
6950,KBN,10,corner,25,0,0,corner,a6b4,1028639619,30414242507072,30414435852290,935294401,1028,5458,193201477,72228,3946,1,667997,5382810,3
6950,KBN,10,corner,26,0,1,stock,b2a3,5458926187,30414436426398,30414887945024,5107407561,935,5458,446720263,86028,6059,1,696047,3455966,5
6950,KBN,10,corner,27,0,0,corner,b4d3,935294401,30414888343479,30415019578536,904059344,935,5107,131067322,73810,4357,1,466676,3548064,4
6950,KBN,10,corner,28,0,1,stock,a3a4,5107407561,30415020040978,30415179955492,5047493047,904,5107,159592891,75893,4417,1,219187,3853940,4
6950,KBN,10,corner,29,0,0,corner,d3b2,904059344,30415180607847,30415447414881,737252310,904,5047,266626155,70165,4617,1,745433,3283639,4
6950,KBN,10,corner,30,0,1,stock,a4a3,5047493047,30415447852355,30415634427671,4960917731,737,5047,186293133,75182,4387,1,693386,4045385,8
6950,KBN,10,corner,31,0,0,corner,c4c3,737252310,30415634999836,30415783760573,688491573,737,4960,148400453,91196,7020,1,832291,4914422,9
6950,KBN,10,corner,32,0,1,stock,a3a2,4960917731,30415784337034,30415935600992,4909653773,688,4960,150744059,86830,6480,1,785240,3546441,12
6950,KBN,10,corner,33,0,0,corner,b2c4,688491573,30415936115521,30416026778247,697828847,688,4909,90296676,84506,4907,1,425855,3761531,10
6950,KBN,10,corner,34,0,1,stock,a2b1,4909653773,30416027289040,30416163159008,4873783805,697,4909,133958712,88062,5688,1,1019911,5891058,27
6950,KBN,10,corner,35,0,0,corner,c3b3,697828847,30416163566907,30416255157164,706238590,697,4873,90704581,105157,4447,1,800744,4776947,18
6950,KBN,10,corner,36,0,1,stock,b1a1,4873783805,30416255650041,30416262134080,4967299766,706,4873,6319018,113470,6139,1,638462,4209970,8
6950,KBN,10,corner,37,0,0,corner,d2g5,706238590,30416262432326,30416273476060,795194856,706,4967,10864541,60010,3896,1,456589,3899537,12
6950,KBN,10,corner,38,0,1,stock,a1b1,4967299766,30416273866393,30416274465979,5066700180,795,4967,517371,67651,4788,1,418815,413687,1
6950,KBN,10,corner,39,0,0,corner,c4a3,795194856,30416274644055,30416275364822,894474089,795,5066,510419,61161,3485,2,446379,0,65
6950,KBN,10,corner,40,0,1,stock,b1a1,5066700180,30416275541056,30416275770769,5166470467,894,5066,136804,52078,0,1,186338,136804,1
6950,KBN,10,corner,41,0,0,corner,g5f6,894474089,30416275924669,30416276547380,993851378,894,5166,416718,52678,0,2,442834,38617,66
6950,KBN,10,stock,0,0,1,stock,d1d2,10000000000,30383818744947,30384134965190,9783779757,10000,10000,315753792,93770,799973,3,806080,0,22
6950,KBN,10,stock,1,0,0,stock,f3e4,10000000000,30384135371738,30384571965214,9663406524,10000,9783,435930975,111657,4558541,2,876748,4193807,13
6950,KBN,10,stock,2,0,1,stock,d2c3,9783779757,30384572380484,30384892254740,9563905501,9663,9783,319561314,68643,4687,1,592320,0,19
6950,KBN,10,stock,3,0,0,stock,c7a5,9663406524,30384892633796,30385358446634,9297593686,9663,9563,465510208,68512,0,1,605655,3368315,5
6950,KBN,10,stock,4,0,1,stock,c3c4,9563905501,30385358839882,30385738277671,9284467712,9297,9563,375616832,67191,4576,1,562028,5066108,5
6950,KBN,10,stock,5,0,0,stock,a5b6,9297593686,30385738651450,30386082714229,9053530907,9297,9284,343835765,68702,4156,1,542921,5217073,3
6950,KBN,10,stock,6,0,1,stock,c4c3,9284467712,30386083125743,30386363330199,9104263256,9053,9284,279800538,71296,4667,1,739290,0,24
6950,KBN,10,stock,7,0,0,stock,d4b5,9053530907,30386363838787,30386776523226,8740846468,9053,9104,408045412,77516,6820,1,913243,4037954,12
6950,KBN,10,stock,8,0,1,stock,c3b4,9104263256,30386776923744,30387011648407,8969538593,8740,9104,234450841,70245,4287,1,638454,2975919,6
6950,KBN,10,stock,9,0,0,stock,b5d6,8740846468,30387012070977,30387225817137,8627100308,8740,8969,213464751,68082,4306,1,264206,3819788,7
6950,KBN,10,stock,10,0,1,stock,b4a4,8969538593,30387226209763,30387489090960,8806657396,8627,8969,258927520,66740,4436,1,688516,5693194,10
6950,KBN,10,stock,11,0,0,stock,e4d3,8627100308,30387489475394,30387987491117,8229084585,8627,8806,494092966,68872,4006,1,619576,2412800,7
6950,KBN,10,stock,12,0,1,stock,a4b4,8806657396,30387987887348,30388413672240,8480872504,8229,8806,421825371,68673,4166,1,638392,3994430,6
6950,KBN,10,stock,13,0,0,stock,d3d2,8229084585,30388414057675,30389112894415,7630247845,8229,8480,698645961,71877,4307,1,528439,5827404,4
6950,KBN,10,stock,14,0,1,stock,b4b3,8480872504,30389113258850,30389931827585,7762303769,7630,8480,818102990,63344,4316,1,739585,2651116,8
6950,KBN,10,stock,15,0,0,stock,b6a5,7630247845,30389932236456,30391065298967,6597185334,7630,7762,1128534957,71827,4177,1,421559,3650106,5
6950,KBN,10,stock,16,0,1,stock,b3a4,7762303769,30391065698965,30391749848248,7178154486,6597,7762,683736201,93941,4416,1,740616,5946191,9
6950,KBN,10,stock,17,0,0,stock,a5c3,6597185334,30391750236568,30392174547160,6272874742,6597,7178,423723964,73470,4857,1,601156,5646695,5
6950,KBN,10,stock,18,0,1,stock,a4b3,7178154486,30392174957413,30392821061968,6632049931,6272,7178,629043376,71917,4487,1,633785,4937476,5
6950,KBN,10,stock,19,0,0,stock,d2d3,6272874742,30392821559181,30393486711188,5707722735,6272,6632,664746340,72679,5027,1,622679,2322485,3
6950,KBN,10,stock,20,0,1,stock,b3a3,6632049931,30393487118526,30393777706712,6441461745,5707,6632,286748257,69954,5088,1,554356,4782996,3
6950,KBN,10,stock,21,0,0,stock,d6e4,5707722735,30393778156945,30394051083566,5534796114,5707,6441,272676833,73400,4527,1,573997,5654866,3
6950,KBN,10,stock,22,0,1,stock,a3a4,6441461745,30394051582781,30394701032954,5892011572,5534,6441,648459197,85578,6299,1,752783,4293837,5
6950,KBN,10,stock,23,0,0,stock,d3c4,5534796114,30394701408805,30395600781600,4735423319,5534,5892,895206148,71417,3675,1,557822,2480411,4
6950,KBN,10,stock,24,0,1,stock,a4a3,5892011572,30395601276950,30395796067414,5797221108,4735,5892,194487561,84496,6690,1,772602,2606859,11
6950,KBN,10,stock,25,0,0,stock,e4f2,4735423319,30395796572518,30396343099008,4288896829,4735,5797,546196153,87340,5969,1,681436,3290480,4
6950,KBN,10,stock,26,0,1,stock,a3a2,5797221108,30396343464434,30396578692449,5661993093,4288,5797,234964069,69624,3986,1,591582,4439443,6
6950,KBN,10,stock,27,0,0,stock,c4b4,4288896829,30396579091094,30396979417607,3988570316,4288,5661,396264968,73109,4467,1,654536,4791048,5
6950,KBN,10,stock,28,0,1,stock,a2b1,5661993093,30396979840048,30397146666435,5595166706,3988,5661,166551904,73780,5208,1,651390,4061450,6
6950,KBN,10,stock,29,0,0,stock,b4b3,3988570316,30397147086122,30397385545192,3850111246,3988,5595,238126045,75683,4376,1,695587,4793381,6
6950,KBN,10,stock,30,0,1,stock,b1c1,5595166706,30397385976576,30397550682560,5530460722,3850,5595,164057071,76895,4647,1,856678,5918731,11
6950,KBN,10,stock,31,0,0,stock,c3b4,3850111246,30397551088407,30397784621477,3716578176,3850,5530,233054968,76093,4387,1,861467,4794713,12
6950,KBN,10,stock,32,0,1,stock,c1b1,5530460722,30397785036678,30397935727381,5479770019,3716,5530,150207675,74411,4336,1,829129,2863773,37
6950,KBN,10,stock,33,0,0,stock,f2d3,3716578176,30397936151715,30398097331105,3655398786,3716,5479,158629830,75152,3885,1,597095,5798311,41
6950,KBN,10,stock,34,0,1,stock,b1a1,5479770019,30398097735900,30398100524959,5576980960,3655,5479,2695121,74341,4887,1,501528,2578517,2
6950,KBN,10,stock,35,0,0,stock,b3c2,3655398786,30398100709014,30398102530977,3753576823,3655,5576,1659494,102553,2583,2,351416,0,65
6950,KBN,10,stock,36,0,1,stock,a1a2,5576980960,30398102673821,30398103037855,5676616926,3753,5576,323293,45498,0,1,151526,323293,1
6950,KBN,10,stock,37,0,0,stock,d3c1,3753576823,30398103144043,30398103495649,3853225217,3753,5676,312466,43135,0,2,145286,312466,1
6950,KBN,10,stock,38,0,1,stock,a2a1,5676616926,30398103612313,30398103787856,5776441383,3853,5676,98327,42614,0,1,156133,98327,1
6950,KBN,10,stock,39,0,0,stock,b4c3,3853225217,30398103882878,30398104161554,3952946541,3853,5776,241060,41012,0,1,172427,241060,1
6950,KBN,10,table,0,0,1,stock,d1d2,10000000000,30416352493703,30416626460918,9826032785,10000,10000,267808891,114421,4005746,2,995825,8760980,15
6950,KBN,10,table,1,0,0,table,c7b6,10000000000,30416626863269,30416632922534,10093940735,10000,9826,6007142,6420579,54111,1,6420579,54111,1
6950,KBN,10,table,2,0,1,stock,d2c3,9826032785,30416633070826,30416926059745,9633043866,10093,9826,292747417,55613,2908700,2,337663,2932696,10
6950,KBN,10,table,3,0,0,table,d4b5,10093940735,30416926533814,30416931594917,10188879632,10093,9633,5063414,5547787,24998,1,5547787,24998,1
6950,KBN,10,table,4,0,1,stock,c3c4,9633043866,30416931803549,30417315370628,9349476787,10188,9633,383247904,131206,4074168,2,410804,8194685,6
6950,KBN,10,table,5,0,0,table,b5c7,10188879632,30417315777597,30417319276225,10285381004,10188,9349,3501765,3920780,49994,1,3920780,49994,1
6950,KBN,10,table,6,0,1,stock,c4d3,9349476787,30417319513209,30417715559337,9053430659,10285,9349,392068506,51617,0,1,491363,4886190,7
6950,KBN,10,table,7,0,0,table,b6e3,10285381004,30417715930231,30417720410337,10380900898,10285,9053,4456969,4837828,24697,1,4837828,24697,1
6950,KBN,10,table,8,0,1,stock,d3c4,9053430659,30417720546830,30418009337599,8864639890,10380,9053,284776915,51737,0,1,477272,3455165,7
6950,KBN,10,table,9,0,0,table,f3e2,10380900898,30418009881322,30418019105959,10471676261,10380,8864,9199325,9755264,28933,1,9755264,28933,1
6950,KBN,10,table,10,0,1,stock,c4c3,8864639890,30418019362592,30418398066894,8585935588,10471,8864,378374425,74642,4632912,2,511414,4640854,6
6950,KBN,10,table,11,0,0,table,e3b6,10471676261,30418398419051,30418404249494,10565845818,10471,8585,5807275,6168173,24616,1,6168173,24616,1
6950,KBN,10,table,12,0,1,stock,c3c4,8585935588,30418404400129,30419288292230,7802043487,10565,8585,879228547,51246,0,1,500587,7603073,9
6950,KBN,10,table,13,0,0,table,e2d2,10565845818,30419288647561,30419293156870,10661336509,10565,7802,4490819,4856305,20681,1,4856305,20681,1
6950,KBN,10,table,14,0,1,stock,c4b3,7802043487,30419293347385,30421438703772,5756687100,10661,7802,2141608411,53429,0,1,267490,2654009,3
6950,KBN,10,table,15,0,0,table,d2d3,10661336509,30421439243329,30421449396333,10751183505,10661,5756,10125848,10731050,30996,1,10731050,30996,1
6950,KBN,10,table,16,0,1,stock,b3b2,5756687100,30421449645885,30421636382017,5669950968,10751,5756,186297102,106398,6264617,2,666193,6391936,3
6950,KBN,10,table,17,0,0,table,b6a5,10751183505,30421636794804,30421642877684,10845100625,10751,5669,6055985,6487278,30496,1,6487278,30496,1
6950,KBN,10,table,18,0,1,stock,b2c1,5669950968,30421643131514,30421975979082,5437103400,10845,5669,332420325,59258,0,1,616119,4872239,7
6950,KBN,10,table,19,0,0,table,a5c3,10845100625,30421976498839,30421982470724,10939128740,10845,5437,5941423,6409842,1231277,2,6409842,1231277,2
6950,KBN,10,table,20,0,1,stock,c1d1,5437103400,30421983953129,30422165260437,5355796092,10939,5437,177171926,96574,0,1,522941,4049772,6
6950,KBN,10,table,21,0,0,table,c7a8,10939128740,30422165637971,30422171293694,11033473017,10939,5355,5639023,6026762,19549,1,6026762,19549,1
6950,KBN,10,table,22,0,1,stock,d1c1,5355796092,30422171498590,30422335507734,5291786948,11033,5355,163690142,68152,4443529,2,508929,4511681,5
6950,KBN,10,table,23,0,0,table,a8b6,11033473017,30422336054271,30422341084129,11128443159,11033,5291,5004816,5047640,27191,1,5047640,27191,1
6950,KBN,10,table,24,0,1,stock,c1d1,5291786948,30422341250447,30422546614879,5186422516,11128,5291,204546187,63064,0,1,340127,6751743,4
6950,KBN,10,table,25,0,0,table,b6c4,11128443159,30422547114756,30422555828028,11219729887,11128,5186,8688462,9199405,27541,1,9199405,27541,1
6950,KBN,10,table,26,0,1,stock,d1c1,5186422516,30422556058533,30422705068892,5137412157,11219,5186,148803794,66599,0,1,240399,3943584,4
6950,KBN,10,table,27,0,0,table,c3d2,11219729887,30422705522690,30422711856726,11313395851,11219,5137,6312778,6777171,23024,1,6777171,23024,1
6950,KBN,10,table,28,0,1,stock,c1b1,5137412157,30422711985889,30422856585661,5092812385,11313,5137,144305418,56225,3917524,2,411924,3944275,7
6950,KBN,10,table,29,0,0,table,d3c3,11313395851,30422856960462,30422862667912,11407688401,11313,5092,5684811,6069165,24977,1,6069165,24977,1
6950,KBN,10,table,30,0,1,stock,b1a2,5092812385,30422862911566,30423001323035,5054400916,11407,5092,135542174,56835,0,1,945725,7215485,38
6950,KBN,10,table,31,0,0,table,c3c2,11407688401,30423001873528,30423009801957,11499759972,11407,5054,7903311,8466361,27160,1,8466361,27160,1
6950,KBN,10,table,32,0,1,stock,a2a1,5054400916,30423010017589,30423014980626,5149437879,11499,5054,4858008,70345,0,1,234921,4858008,1
6950,KBN,10,table,33,0,0,table,c2b3,11499759972,30423015187105,30423023012556,11591934521,11499,5149,7829065,8118597,0,0,8118597,0,0
6950,KBN,10,table,34,0,1,stock,a1b1,5149437879,30423023200717,30423023695436,5248943160,11591,5149,428510,59789,0,1,199047,428510,1
6950,KBN,10,table,35,0,0,table,c4a3,11591934521,30423023861114,30423030433541,11685362094,11591,5248,6574834,6793129,0,0,6793129,0,0
6950,KBN,10,table,36,0,1,stock,b1a1,5248943160,30423030642513,30423030915632,5348670041,11685,5248,184556,64697,0,1,223323,184556,1
6950,KBN,10,table,37,0,0,table,d2c3,11685362094,30423031170112,30423035149930,11781382276,11685,5348,3981861,4307857,0,0,4307857,0,0
6956,KBN,10,corner,0,2,1,stock,e1f1,10000000000,30454313263005,30454637339828,9775923177,10000,10000,319758734,120209,2749453,3,868948,0,16
6956,KBN,10,corner,1,2,0,corner,e4f3,10000000000,30454637859354,30455005915992,9731943362,10000,9775,356123457,144185,6810,1,1060894,5750759,10
6956,KBN,10,corner,2,2,1,stock,f1e1,9775923177,30455006319505,30455386930850,9495311832,9731,9775,380284875,70155,5258,1,676480,5583450,6
6956,KBN,10,corner,3,2,0,corner,d4b3,9731943362,30455387340572,30456609571695,8609712239,9731,9495,1218178334,67010,4757,1,714125,4554555,6
6956,KBN,10,corner,4,2,1,stock,e1d1,9495311832,30456610114637,30457093185513,9112240956,8609,9495,482422261,82774,7591,1,1133480,0,21
6956,KBN,10,corner,5,2,0,corner,b3d2,8609712239,30457093771659,30457705105850,8098378048,8609,9112,610705638,84797,8082,1,1163254,2109848,17
6956,KBN,10,corner,6,2,1,stock,d1c2,9112240956,30457705508792,30457926494468,8991255280,8098,9112,220559749,70295,4547,1,802737,2390937,14
6956,KBN,10,corner,7,2,0,corner,f3e2,8098378048,30457926821987,30458131179100,7994020935,8098,8991,204085470,61742,3836,1,577652,5085157,7
6956,KBN,10,corner,8,2,1,stock,c2b2,8991255280,30458131529643,30458836780417,8386004506,7994,8991,701344061,66900,4597,1,574558,4376429,12
6956,KBN,10,corner,9,2,0,corner,e3c5,7994020935,30458837172222,30459910080766,7021112391,7994,8386,1065218832,71627,4397,1,511533,2720799,3
6956,KBN,10,corner,10,2,1,stock,b2c3,8386004506,30459910470978,30462185629640,6210845844,7021,8386,2263929862,70675,4317,1,489050,5428850,3
6956,KBN,10,corner,11,2,0,corner,e2e3,7021112391,30462186073063,30462826924791,6480260663,7021,6210,640586295,73079,5548,1,725182,5810930,5
6956,KBN,10,corner,12,2,1,stock,c3c2,6210845844,30462827396766,30464607674435,4530568175,6480,6210,1772196046,73240,5698,1,617250,4650028,4
6956,KBN,10,corner,13,2,0,corner,c5b4,6480260663,30464608094403,30465948177426,5240177640,6480,4530,1339526329,71546,4487,1,253848,3792278,4
6956,KBN,10,corner,14,2,1,stock,c2d1,4530568175,30465948586818,30466901487820,3677667173,5240,4530,952589924,71396,4327,1,638885,3313434,12
6956,KBN,10,corner,15,2,0,corner,d2c4,5240177640,30466901943601,30467375308559,4866812682,5240,3677,473230723,77065,4337,1,568658,5941875,3
6956,KBN,10,corner,16,2,1,stock,d1c2,3677667173,30467375653745,30467515127216,3638193702,4866,3677,135353526,101120,4407,1,507810,7864443,5
6956,KBN,10,corner,17,2,0,corner,c4a5,4866812682,30467515494835,30468027317326,4454990191,4866,3638,503612454,73540,4266,1,561919,4395568,4
6956,KBN,10,corner,18,2,1,stock,c2c1,3638193702,30468027696603,30468233365923,3532524382,4454,3638,201838477,94020,4708,1,534278,4181358,4
6956,KBN,10,corner,19,2,0,corner,e3d3,4454990191,30468233724379,30468572646327,4216068243,4454,3532,338544185,72569,4306,1,715868,5102973,8
6956,KBN,10,corner,20,2,1,stock,c1d1,3532524382,30468573052875,30468702271031,3503306226,4216,3532,128933449,72047,4828,1,668217,2849111,4
6956,KBN,10,corner,21,2,0,corner,a5c4,4216068243,30468702810197,30468911767866,4107110574,4216,3503,201371236,76455,5177,1,708759,5070034,6
6956,KBN,10,corner,22,2,1,stock,d1c1,3503306226,30468912237828,30469074096306,3441447748,4107,3503,161653445,76504,6480,1,392766,3659079,5
6956,KBN,10,corner,23,2,0,corner,b4d2,4107110574,30469074453269,30469313256087,3968307756,4107,3441,238528027,69164,4316,1,610359,5434759,5
6956,KBN,10,corner,24,2,1,stock,c1b1,3441447748,30469313802673,30469443416131,3411834290,3968,3441,129262730,86479,7160,1,871800,6075023,6
6956,KBN,10,corner,25,2,0,corner,d3c3,3968307756,30469443993043,30469658141001,3854159798,3968,3411,209877741,87620,5899,1,1155224,3847460,10
6956,KBN,10,corner,26,2,1,stock,b1a2,3411834290,30469659539530,30469763317165,3408056655,3854,3411,103382787,76864,27121,1,1768810,4327997,31
6956,KBN,10,corner,27,2,0,corner,c3c2,3854159798,30469763701439,30470014025651,3703835586,3854,3408,249581075,400427,4026,1,1096407,3857815,40
6956,KBN,10,corner,28,2,1,stock,a2a1,3408056655,30470014579789,30470035557113,3487079331,3703,3408,20717218,88663,7441,1,790008,5294489,14
6956,KBN,10,corner,29,2,0,corner,c2b3,3703835586,30470036063911,30470038048797,3801850700,3703,3487,1890341,79429,5598,1,72508,1772665,1
6956,KBN,10,corner,30,2,1,stock,a1b1,3487079331,30470038302115,30470039056112,3586325334,3801,3487,510814,68893,4486,2,562357,0,65
6956,KBN,10,corner,31,2,0,corner,c4a3,3801850700,30470039231484,30470039696929,3901385255,3801,3586,394068,57055,0,1,187590,394068,1
6956,KBN,10,corner,32,2,1,stock,b1a1,3586325334,30470039900624,30470040337967,3685887991,3901,3586,231044,55352,0,2,469461,40059,66
6956,KBN,10,corner,33,2,0,corner,d2c3,3901385255,30470040494571,30470040905836,4000973990,3901,3685,348110,50836,0,1,166638,348110,1
6956,KBN,10,stock,0,2,1,stock,e1f1,10000000000,30421435365107,30421685527340,9849837767,10000,10000,249832700,119699,5137765,2,856228,4302019,8
6956,KBN,10,stock,1,2,0,stock,d4f5,10000000000,30421685934008,30422775260835,9010673173,10000,9849,1074483141,122734,0,1,963517,6069746,10
6956,KBN,10,stock,2,2,1,stock,f1g2,9849837767,30422775634984,30423066793037,9658679714,9010,9849,287735640,67221,4316,1,873008,7893752,13
6956,KBN,10,stock,3,2,0,stock,e4f4,9010673173,30423067296469,30423686901242,8491068400,9010,9658,617641703,76574,6600,1,965961,4575146,10
6956,KBN,10,stock,4,2,1,stock,g2h2,9658679714,30423687410273,30424065548499,9380541488,8491,9658,373863366,79559,6340,1,895425,4689256,10
6956,KBN,10,stock,5,2,0,stock,f4f3,8491068400,30424065947475,30424385121337,8271894538,8491,9380,318648027,68483,5738,1,902377,5940463,13
6956,KBN,10,stock,6,2,1,stock,h2h3,9380541488,30424385520664,30424842262575,9023799577,8271,9380,456444201,70746,3946,1,668006,2385048,7
6956,KBN,10,stock,7,2,0,stock,e3f2,8271894538,30424842621491,30425250467861,7964048168,8271,9023,407518783,69393,4186,1,663699,5246918,14
6956,KBN,10,stock,8,2,1,stock,h3h2,9023799577,30425250872485,30425495435220,8879236842,7964,9023,240752295,60661,4246,1,555757,5044937,6
6956,KBN,10,stock,9,2,0,stock,f5g3,7964048168,30425495869048,30426510011961,7049905255,7964,8879,1004936255,63564,4627,1,776250,5310613,13
6956,KBN,10,stock,10,2,1,stock,h2h3,8879236842,30426510373141,30426825503950,8664106033,7049,8879,307620576,69844,3666,1,564392,5531984,6
6956,KBN,10,stock,11,2,0,stock,f2c5,7049905255,30426825860362,30427690288998,6285476619,7049,8664,860422801,65518,4336,1,697814,6048283,13
6956,KBN,10,stock,12,2,1,stock,h3h4,8664106033,30427690604800,30427920857403,8533853430,6285,8664,226340308,58438,3725,1,556470,5318515,8
6956,KBN,10,stock,13,2,0,stock,c5e3,6285476619,30427921255929,30428448562405,5858170143,6285,8533,526916597,73840,0,1,767728,2746096,13
6956,KBN,10,stock,14,2,1,stock,h4h3,8533853430,30428448990314,30428661103118,8421740626,5858,8533,208189963,74231,0,1,681777,3009771,9
6956,KBN,10,stock,15,2,0,stock,g3f5,5858170143,30428661594933,30428941309544,5678455532,5858,8421,279462987,75082,0,1,711652,6403885,6
6956,KBN,10,stock,16,2,1,stock,h3h2,8421740626,30428941664454,30429172216109,8291188971,5678,8421,230226621,90966,0,1,659483,2354263,12
6956,KBN,10,stock,17,2,0,stock,e3f2,5678455532,30429172676958,30429476550900,5474581590,5678,8291,302346617,96063,0,1,736580,4554274,12
6956,KBN,10,stock,18,2,1,stock,h2h3,8291188971,30429476951589,30429708789717,8159350843,5474,8291,231513881,70305,0,1,706173,3049720,11
6956,KBN,10,stock,19,2,0,stock,f2a7,5474581590,30429709187732,30430222082506,5061686816,5474,8159,512287956,74471,0,1,753754,3037161,15
6956,KBN,10,stock,20,2,1,stock,h3h2,8159350843,30430222425238,30430424552436,8057223645,5061,8159,199977458,62243,4266,1,715130,7261955,12
6956,KBN,10,stock,21,2,0,stock,f5e7,5061686816,30430424995949,30430662790340,4923892425,5061,8057,233803758,70205,4186,1,767626,2892596,7
6956,KBN,10,stock,22,2,1,stock,h2h1,8057223645,30430663276516,30430872883958,7947616203,4923,8057,209192450,88542,0,1,810269,4755825,8
6956,KBN,10,stock,23,2,0,stock,e7f5,4923892425,30430873280029,30431678221000,4218951454,4923,7947,795126526,73740,0,1,522960,8729054,5
6956,KBN,10,stock,24,2,1,stock,h1h2,7947616203,30431678612896,30431953947312,7772281787,4218,7947,271173744,74451,0,1,761298,5387167,5
6956,KBN,10,stock,25,2,0,stock,a7f2,4218951454,30431954515892,30432505769341,3767698005,4218,7772,550918419,93410,0,1,876357,5481088,6
6956,KBN,10,stock,26,2,1,stock,h2h3,7772281787,30432506273484,30433053586649,7324968622,3767,7772,546492429,79028,4016,1,988905,5618002,11
6956,KBN,10,stock,27,2,0,stock,f5d4,3767698005,30433054111914,30433301069649,3620740270,3767,7324,246563404,67020,4586,1,898791,5780054,8
6956,KBN,10,stock,28,2,1,stock,h3h2,7324968622,30433301472371,30433511905000,7214535993,3620,7324,206495895,74781,4357,1,779904,2427281,8
6956,KBN,10,stock,29,2,0,stock,f2g3,3620740270,30433512320822,30433802306760,3430754332,3620,7214,285992540,74501,4417,1,613975,3562896,8
6956,KBN,10,stock,30,2,1,stock,h2g1,7214535993,30433802699908,30434006478986,7110756915,3430,7214,203430603,94571,4617,1,607395,5173939,8
6956,KBN,10,stock,31,2,0,stock,g3f2,3430754332,30434006816721,30434203277844,3334293209,3430,7110,196200848,61551,4387,1,579834,5095462,9
6956,KBN,10,stock,32,2,1,stock,g1f1,7110756915,30434203666495,30434383750714,7030672696,3334,7110,177925928,93319,4337,1,776320,5942736,12
6956,KBN,10,stock,33,2,0,stock,f2g3,3334293209,30434384144382,30434533370995,3285066596,3334,7030,148919445,64296,4236,1,409953,3755202,10
6956,KBN,10,stock,34,2,1,stock,f1g1,7030672696,30434533811464,30434741698091,6922786069,3285,7030,207582247,75372,5008,1,719283,2083429,7
6956,KBN,10,stock,35,2,0,stock,d4f5,3285066596,30434742099401,30434862402670,3264763327,3285,6922,119966420,79048,0,1,637661,5899341,9
6956,KBN,10,stock,36,2,1,stock,g1f1,6922786069,30434862803529,30435050106826,6835482772,3264,6922,186834592,70255,4727,1,849148,5022444,11
6956,KBN,10,stock,37,2,0,stock,f5e3,3264763327,30435050504040,30435813551644,2601715723,3264,6835,756312310,77646,3826,1,782907,7794409,12
6956,KBN,10,stock,38,2,1,stock,f1g1,6835482772,30435813997921,30436073222826,6676257867,2601,6835,259003179,80110,5788,1,609308,5889066,5
6956,KBN,10,stock,39,2,0,stock,g3d6,2601715723,30436073731386,30436298473594,2476973515,2601,6676,220831594,165497,6490,1,746623,6030307,5
6956,KBN,10,stock,40,2,1,stock,g1h1,6676257867,30436299052980,30436495798709,6579512138,2476,6676,196337670,92488,7662,1,962867,4814833,11
6956,KBN,10,stock,41,2,0,stock,e3f5,2476973515,30436496203804,30436713696017,2359481302,2476,6579,217167797,73610,4156,1,483071,3682674,7
6956,KBN,10,stock,42,2,1,stock,h1g1,6579512138,30436714201974,30436987891988,6405822124,2359,6579,273290764,92889,0,1,1002815,5797329,11
6956,KBN,10,stock,43,2,0,stock,d6f4,2359481302,30436988462541,30437893787192,1554156651,2359,6405,901279270,74411,5939,1,741465,3410879,10
6956,KBN,10,stock,44,2,1,stock,g1h1,6405822124,30437894257335,30438201126248,6198953211,1554,6405,302797472,85758,0,1,926721,5744330,8
6956,KBN,10,stock,45,2,0,stock,f4g3,1554156651,30438201538574,30438334533460,1521161765,1554,6198,132827829,81502,0,1,559234,2472729,7
6956,KBN,10,stock,46,2,1,stock,h1g1,6198953211,30438334906447,30438617434103,6016425555,1521,6198,282257829,68873,0,1,624830,5096354,7
6956,KBN,10,stock,47,2,0,stock,g3f2,1521161765,30438617909153,30438845328753,1393742165,1521,6016,223608384,76845,0,1,609520,6091047,5
6956,KBN,10,stock,48,2,1,stock,g1h2,6016425555,30438845710954,30440579401399,4382735110,1393,6016,1726135737,105047,4026,1,605092,2156508,11
6956,KBN,10,stock,49,2,0,stock,f2d4,1393742165,30440580036969,30440673827915,1399951219,1393,4382,93611540,76825,3986,1,177666,3844406,4
6956,KBN,10,stock,50,2,1,stock,h2h3,4382735110,30440674179100,30440845543858,4311370352,1399,4382,168899513,70565,0,1,627968,7953286,12
6956,KBN,10,stock,51,2,0,stock,f5g3,1399951219,30440845924918,30440939820851,1406055286,1399,4311,93609409,74772,4136,1,637611,5956617,6
6956,KBN,10,stock,52,2,1,stock,h3h4,4311370352,30440940437152,30441163267979,4188539525,1406,4311,222674578,77936,4137,1,554097,3457398,7
6956,KBN,10,stock,53,2,0,stock,d4f6,1406055286,30441163630972,30441293292921,1376393337,1406,4188,129337408,72749,4036,1,667755,4233005,6
6956,KBN,10,stock,54,2,1,stock,h4h3,4188539525,30441293855502,30441702447687,3879947340,1376,4188,404285884,84516,6370,1,1199219,6098729,11
6956,KBN,10,stock,55,2,0,stock,g3e2,1376393337,30441702879142,30441830064224,1349208255,1376,3879,126970360,79879,4787,1,627025,5326336,6
6956,KBN,10,stock,56,2,1,stock,h3h2,3879947340,30441830546295,30441973985227,3836508408,1349,3879,143181541,81843,4576,1,718723,5336792,5
6956,KBN,10,stock,57,2,0,stock,f6c3,1349208255,30441974361760,30442141935683,1281634332,1349,3836,167318317,76414,3655,1,610149,5522569,9
6956,KBN,10,stock,58,2,1,stock,h2h1,3836508408,30442142318995,30442305822535,3773004868,1281,3836,163207661,79568,4087,1,658254,5568377,7
6956,KBN,10,stock,59,2,0,stock,c3d4,1281634332,30442306223664,30442378351828,1309506168,1281,3773,71853598,79569,3915,1,642516,5659559,8
6956,KBN,10,stock,60,2,1,stock,h1h2,3773004868,30442378916252,30442522787032,3729134088,1309,3773,143642826,94101,6269,1,776337,4948133,5
6956,KBN,10,stock,61,2,0,stock,d4f6,1309506168,30442523319598,30442688144663,1244681103,1309,3729,164352793,108191,5168,1,982454,4476699,7
6956,KBN,10,stock,62,2,1,stock,h2h3,3729134088,30442688552081,30442840922213,3676763956,1244,3729,151767777,82894,0,1,986671,3179564,8
6956,KBN,10,stock,63,2,0,stock,f6e7,1244681103,30442841440468,30442926141725,1259979846,1244,3676,84365246,91546,0,1,819363,2559708,7
6956,KBN,10,stock,64,2,1,stock,h3h2,3676763956,30442926680350,30443123696281,3579748025,1259,3676,196592740,123364,0,1,935266,5344173,10
6956,KBN,10,stock,65,2,0,stock,e7c5,1259979846,30443124119443,30443268795407,1215303882,1259,3579,144503308,78106,0,1,248500,3880840,5
6956,KBN,10,stock,66,2,1,stock,h2h1,3579748025,30443269339370,30443376452860,3572634535,1215,3579,106861459,98046,0,1,774616,2624225,8
6956,KBN,10,stock,67,2,0,stock,e2f4,1215303882,30443376878807,30443524687792,1167494897,1215,3572,147596124,82003,0,1,615116,3123000,7
6956,KBN,10,stock,68,2,1,stock,h1h2,3572634535,30443525178666,30443758019213,3439793988,1167,3572,232592869,83876,0,1,717461,2833037,7
6956,KBN,10,stock,69,2,0,stock,f4d5,1167494897,30443758497538,30444290772384,735220051,1167,3439,531940258,83305,0,1,784611,5456071,8
6956,KBN,10,stock,70,2,1,stock,h2h1,3439793988,30444291189457,30444444528322,3386455123,735,3439,153105325,84106,4576,1,624952,4694443,7
6956,KBN,10,stock,71,2,0,stock,d5b4,735220051,30444444960387,30444845981839,434198599,735,3386,393349639,165967,5368,1,776658,2828410,7
6956,KBN,10,stock,72,2,1,stock,h1h2,3386455123,30444846509397,30445271179359,3061785161,434,3386,424335278,98156,6139,1,830330,5356141,5
6956,KBN,10,stock,73,2,0,stock,b4d5,434198599,30445271858223,30445375026548,431030274,434,3061,99295830,100870,7802,1,868447,3941480,4
6956,KBN,10,stock,74,2,1,stock,h2h1,3061785161,30445375585453,30445505363474,3032007140,431,3061,126479807,103074,7291,1,870520,7198450,8
6956,KBN,10,stock,75,2,0,stock,c5f2,431030274,30445505949720,30445600162863,436817131,431,3032,93920943,97986,7251,1,853574,5889717,6
6956,KBN,10,stock,76,2,1,stock,h1h2,3032007140,30445600589110,30446369356009,2363240241,436,3032,764527181,87911,4587,1,728696,3292152,8
6956,KBN,10,stock,77,2,0,stock,d5b4,436817131,30446369850829,30446625049512,281618448,436,2363,254336686,83534,5759,1,721655,6575461,7
6956,KBN,10,stock,78,2,1,stock,h2h3,2363240241,30446625604191,30447113715194,1975129238,281,2363,487654372,168571,6690,1,1010208,2192141,8
6956,KBN,10,stock,79,2,0,stock,b4d3,281618448,30447114287780,30447276507171,219399057,281,1975,159328257,85798,5619,1,885710,8104802,7
6956,KBN,10,stock,80,2,1,stock,h3h2,1975129238,30447277126347,30447359200798,1993054787,219,1975,81814973,101792,8382,1,905450,2733559,5
6956,KBN,10,stock,81,2,0,stock,d3b2,219399057,30447359782398,30447485083988,194097467,219,1993,125070947,101782,6860,1,729398,4054710,4
6956,KBN,10,stock,82,2,1,stock,h2h3,1993054787,30447485623274,30448113361541,1465316520,194,1993,627485184,130225,8092,1,821846,2206833,6
6956,KBN,10,stock,83,2,0,stock,f2e3,194097467,30448113923271,30448185685657,222335081,194,1465,71598724,99047,7041,1,708417,5921274,4
6956,KBN,10,stock,84,2,1,stock,h3h4,1465316520,30448186131002,30448423688849,1327758673,222,1465,233655545,85778,5258,1,667887,5750189,4
6956,KBN,10,stock,85,2,0,stock,f3e4,222335081,30448424233793,30448486880132,259688742,222,1327,62441707,97125,5758,1,385385,3622344,4
6956,KBN,10,stock,86,2,1,stock,h4h5,1327758673,30448487286189,30448636705030,1278339832,259,1327,149200736,84977,3926,1,593005,4596808,4
6956,KBN,10,stock,87,2,0,stock,e4f5,259688742,30448637139750,30448786360746,210467746,259,1278,149000406,86049,4747,1,596661,2741970,4
6956,KBN,10,stock,88,2,1,stock,h5h4,1278339832,30448786794675,30448933322355,1231812152,210,1278,146353188,83635,5037,1,607385,5091486,4
6956,KBN,10,stock,89,2,0,stock,e3c1,210467746,30448933907069,30449054326834,190047981,210,1231,120146440,99859,6490,1,781295,5933071,4
6956,KBN,10,stock,90,2,1,stock,h4h3,1231812152,30449054948223,30449337311247,1049449128,190,1231,282086171,90024,7952,1,881546,4920982,5
6956,KBN,10,stock,91,2,0,stock,f5e4,190047981,30449337821880,30449446253845,181616016,190,1049,108258068,129974,5097,1,595367,6004748,4
6956,KBN,10,stock,92,2,1,stock,h3g2,1049449128,30449446836105,30449605836395,990448838,181,1049,158677886,102213,8192,1,929387,5016033,6
6956,KBN,10,stock,93,2,0,stock,b2a4,181616016,30449606384715,30449708661652,179339079,181,990,102094512,102503,5789,1,668376,5463897,3
6956,KBN,10,stock,94,2,1,stock,g2g1,990448838,30449709235129,30449763347130,1036336837,179,990,53860630,103534,6740,1,837912,2621691,21
6956,KBN,10,stock,95,2,0,stock,c1e3,179339079,30449763867357,30449833486265,209720171,179,1036,69369313,85347,4437,1,753484,3983332,30
6956,KBN,10,stock,96,2,1,stock,g1f1,1036336837,30449833913143,30449841096929,1129153051,209,1036,7075725,84997,0,1,523402,6052009,11
6956,KBN,10,stock,97,2,0,stock,e4d3,209720171,30449841311550,30449846960892,304070829,209,1129,5590961,59639,2563,1,254851,5425925,2
6956,KBN,10,stock,98,2,1,stock,f1e1,1129153051,30449847126359,30449847606316,1228673094,304,1129,327856,63024,2874,2,337146,0,65
6956,KBN,10,stock,99,2,0,stock,e3c1,304070829,30449847720367,30449847988457,403802739,304,1228,228030,80330,0,1,184756,228030,1
6956,KBN,10,table,0,2,1,stock,e1f1,10000000000,30449934900075,30450187112558,9847787517,10000,10000,248260491,107721,5653925,2,899131,4769596,7
6956,KBN,10,table,1,2,0,table,e4f3,10000000000,30450187579806,30450195698015,10091881791,10000,9847,8055237,8534131,65899,1,8534131,65899,1
6956,KBN,10,table,2,2,1,stock,f1e1,9847787517,30450195996151,30450600196154,9543587514,10091,9847,392513464,68412,0,1,676720,3983864,7
6956,KBN,10,table,3,2,0,table,d4b3,10091881791,30450600701709,30450611210621,10181372879,10091,9543,10482609,11000492,30105,1,11000492,30105,1
6956,KBN,10,table,4,2,1,stock,e1d1,9543587514,30450611462567,30450869968417,9385081664,10181,9543,258253904,76083,4470750,2,483703,4546833,7
6956,KBN,10,table,5,2,0,table,b3d2,10181372879,30450870343227,30450876674085,10275042021,10181,9385,6303314,6688288,30215,1,6688288,30215,1
6956,KBN,10,table,6,2,1,stock,d1c2,9385081664,30450876933663,30451112080363,9249934964,10275,9385,234731270,55743,0,1,660326,7068606,14
6956,KBN,10,table,7,2,0,table,f3e2,10275042021,30451112458738,30451117784064,10369716695,10275,9249,5301359,5691301,26169,1,5691301,26169,1
6956,KBN,10,table,8,2,1,stock,c2b2,9249934964,30451117950984,30451617652110,8850233838,10369,9249,492112533,53850,0,1,440218,6051518,9
6956,KBN,10,table,9,2,0,table,e2d3,10369716695,30451618171826,30451627687293,10460201228,10369,8850,9489837,10022332,28613,1,10022332,28613,1
6956,KBN,10,table,10,2,1,stock,b2a3,8850233838,30451627926150,30452142967931,8435192057,10460,8850,514639690,96584,4019106,2,619573,4077413,10
6956,KBN,10,table,11,2,0,table,d3c4,10460201228,30452143337083,30452150732322,10552805989,10460,8435,7367722,7747378,30316,1,7747378,30316,1
6956,KBN,10,table,12,2,1,stock,a3b2,8435192057,30452150999050,30452402156751,8284034356,10552,8435,250889848,57266,0,1,520356,5001051,6
6956,KBN,10,table,13,2,0,table,d2e4,10552805989,30452402619282,30452408394621,10647030650,10552,8284,5751151,6224177,26509,1,6224177,26509,1
6956,KBN,10,table,14,2,1,stock,b2c2,8284034356,30452408559568,30452683782904,8108811020,10647,8284,272724944,58887,3390789,2,358575,9731508,5
6956,KBN,10,table,15,2,0,table,e4f2,10647030650,30452684473536,30452690036959,10741467227,10647,8108,5538783,6001063,27141,1,6001063,27141,1
6956,KBN,10,table,16,2,1,stock,c2b2,8108811020,30452690224048,30452961530547,7937504521,10741,8108,271047869,66790,5720785,2,424151,5787575,5
6956,KBN,10,table,17,2,0,table,e3d2,10741467227,30452961941321,30452968515203,10834893345,10741,7937,6550233,6971772,25338,1,6971772,25338,1
6956,KBN,10,table,18,2,1,stock,b2c2,7937504521,30452968754130,30453212919838,7793338813,10834,7937,243899945,53169,0,1,490601,7245860,6
6956,KBN,10,table,19,2,0,table,d2c3,10834893345,30453213395379,30453219063368,10929225356,10834,7793,5670290,6158448,29063,1,6158448,29063,1
6956,KBN,10,table,20,2,1,stock,c2c1,7793338813,30453219295785,30453485984640,7626649958,10929,7793,266468671,65117,0,1,408029,4706712,4
6956,KBN,10,table,21,2,0,table,c4b3,10929225356,30453486462524,30453494783242,11020904638,10929,7626,8297054,8785833,27982,1,8785833,27982,1
6956,KBN,10,table,22,2,1,stock,c1b1,7626649958,30453494990832,30453729492152,7492148638,11020,7626,234160335,67781,4951888,2,534437,5019669,6
6956,KBN,10,table,23,2,0,table,c3a5,11020904638,30453729898579,30453735356544,11115446673,11020,7492,5433246,5849827,26730,1,5849827,26730,1
6956,KBN,10,table,24,2,1,stock,b1c1,7492148638,30453735524485,30453948190456,7379482667,11115,7492,211181964,57565,0,1,610152,5497621,14
6956,KBN,10,table,25,2,0,table,a5b4,11115446673,30453948574650,30453954424931,11209596392,11115,7379,5825752,6220762,26459,1,6220762,26459,1
6956,KBN,10,table,26,2,1,stock,c1b1,7379482667,30453954622856,30454145251772,7288853751,11209,7379,190041014,145948,5240128,2,773266,5386076,32
6956,KBN,10,table,27,2,0,table,b4a3,11209596392,30454145639060,30454151114091,11304121361,11209,7288,5452464,5849997,25198,1,5849997,25198,1
6956,KBN,10,table,28,2,1,stock,b1a1,7288853751,30454151328852,30454158324354,7381858249,11304,7288,6897861,64366,0,1,303884,4670087,3
6956,KBN,10,table,29,2,0,table,f2d1,11304121361,30454158546576,30454162454104,11400213833,11304,7381,3909252,4138063,14953,1,4138063,14953,1
6956,KBN,10,table,30,2,1,stock,a1b1,7381858249,30454162621864,30454163103344,7481376769,11400,7381,421228,52709,0,1,163143,421228,1
6956,KBN,10,table,31,2,0,table,d1c3,11400213833,30454163245075,30454167802494,11495656414,11400,7481,4558691,4748064,0,0,4748064,0,0
6956,KBN,10,table,32,2,1,stock,b1a1,7481376769,30454167942373,30454168213268,7581105874,11495,7481,215932,138556,0,1,149774,215932,1
6956,KBN,10,table,33,2,0,table,a3b2,11495656414,30454168338595,30454170457832,11593537177,11495,7581,2120363,2289335,0,0,2289335,0,0
7569,KBN,10,corner,0,0,1,stock,f4e3,10000000000,30423228283162,30423884031101,9444252061,10000,10000,651547103,86580,4040417,2,774075,3475836,13
7569,KBN,10,corner,1,0,0,corner,f7e6,10000000000,30423884567693,30424916710680,9067857013,10000,9444,1031520997,173439,6870,1,1080692,3004953,18
7569,KBN,10,corner,2,0,1,stock,e3e4,9444252061,30424917119801,30425250481477,9210890385,9067,9444,333082135,67621,4888,1,638401,2785086,8
7569,KBN,10,corner,3,0,0,corner,d1g4,9067857013,30425250846673,30425869181022,8549522664,9067,9210,618095610,67080,4146,1,566865,5047040,12
7569,KBN,10,corner,4,0,1,stock,e4d4,9210890385,30425869588791,30426090779714,9089699462,8549,9210,220777313,69603,4407,1,794725,2315595,8
7569,KBN,10,corner,5,0,0,corner,e6d6,8549522664,30426091249046,30426403626108,8337145602,8549,9089,311916232,79218,5629,1,690933,4630949,9
7569,KBN,10,corner,6,0,1,stock,d4c4,9089699462,30426403973167,30426740104440,8853568189,8337,9089,335408327,81742,3866,1,566305,3920489,8
7569,KBN,10,corner,7,0,0,corner,d6e5,8337145602,30426740460462,30428077760863,7099845201,8337,8853,1336991827,65278,3966,1,588867,3439371,7
7569,KBN,10,corner,8,0,1,stock,c4b4,8853568189,30428078160691,30428834483897,8197244983,7099,8853,756007835,69644,4407,1,685152,5738551,9
7569,KBN,10,corner,9,0,0,corner,e5d4,7099845201,30428834889433,30429058625060,6976109574,7099,8197,219830060,69464,4837,1,611332,4998808,8
7569,KBN,10,corner,10,0,1,stock,b4b5,8197244983,30429059027332,30429278535559,8077736756,6976,8197,219207240,68142,4186,1,674186,4875824,10
7569,KBN,10,corner,11,0,0,corner,g4d7,6976109574,30429279114344,30429783724055,6571499863,6976,8077,502831697,71476,5298,1,794344,6304736,10
7569,KBN,10,corner,12,0,1,stock,b5b6,8077736756,30429784142140,30431989347707,5972531189,6571,8077,2198682319,67411,3956,1,306941,7475713,13
7569,KBN,10,corner,13,0,0,corner,d4d5,6571499863,30431989846292,30432261777128,6399569027,6571,5972,271628698,81191,5748,1,809238,6026111,9
7569,KBN,10,corner,14,0,1,stock,b6c7,5972531189,30432262100151,30432921598830,5413032510,6399,5972,655512298,60220,3986,1,542469,5814164,8
7569,KBN,10,corner,15,0,0,corner,h5f6,6399569027,30432922004937,30433134851314,6286722650,6399,5413,212578520,71717,4397,1,625784,5883408,6
7569,KBN,10,corner,16,0,1,stock,c7d8,5413032510,30433135235599,30433571383338,5076884771,6286,5413,435825351,71877,0,1,671089,4766371,9
7569,KBN,10,corner,17,0,0,corner,d5e6,6286722650,30433571886310,30433841422517,6117186443,6286,5076,269107016,79558,5398,1,713495,3961931,5
7569,KBN,10,corner,18,0,1,stock,d8c7,5076884771,30433841842905,30434231255586,4787472090,6117,5076,389281980,71246,0,1,533655,6156856,3
7569,KBN,10,corner,19,0,0,corner,f6e8,6117186443,30434231641653,30434793709125,5655118971,6117,4787,561351777,71256,0,1,500598,4412783,3
7569,KBN,10,corner,20,0,1,stock,c7b7,4787472090,30434794057455,30434962676189,4718853356,5655,4787,164635876,62753,4277,1,516870,5857610,6
7569,KBN,10,corner,21,0,0,corner,e6d5,5655118971,30434963148555,30435259342090,5458925436,5655,4718,295871212,73559,0,1,749749,4869745,7
7569,KBN,10,corner,22,0,1,stock,b7b6,4718853356,30435259927795,30435674258956,4404522195,5458,4718,403228675,92759,5187,1,806644,7768609,6
7569,KBN,10,corner,23,0,0,corner,d7c6,5458925436,30435674807917,30436031310716,5202422637,5458,4404,356016190,84907,6780,1,884999,5061811,8
7569,KBN,10,corner,24,0,1,stock,b6a5,4404522195,30436031719046,30436319925609,4216315632,5202,4404,284399903,74651,28162,1,749007,4152185,5
7569,KBN,10,corner,25,0,0,corner,d5c5,5202422637,30436320434860,30436837982169,4784875328,5202,4216,517286665,71327,0,1,651834,3606200,7
7569,KBN,10,corner,26,0,1,stock,a5a6,4216315632,30436838396278,30436998233428,4156478482,4784,4216,159612519,75132,4787,1,526016,5521778,3
7569,KBN,10,corner,27,0,0,corner,c6d7,4784875328,30436998704662,30437442843691,4440736299,4784,4156,440240105,92638,4837,1,684101,5163053,4
7569,KBN,10,corner,28,0,1,stock,a6b7,4156478482,30437443227294,30437613708001,4085997775,4440,4156,170199714,70094,4387,1,641197,4671429,7
7569,KBN,10,corner,29,0,0,corner,c5b5,4440736299,30437614087237,30437893247265,4261576271,4440,4085,278819211,72368,0,1,618062,5911710,5
7569,KBN,10,corner,30,0,1,stock,b7a7,4085997775,30437893639391,30438062016173,4017620993,4261,4085,168117949,72018,4487,1,627066,2242235,6
7569,KBN,10,corner,31,0,0,corner,e8d6,4261576271,30438062377083,30438286701627,4137251727,4261,4017,224022393,71406,0,1,639395,5629759,6
7569,KBN,10,corner,32,0,1,stock,a7b8,4017620993,30438287075455,30438414811862,3989884586,4137,4017,127401004,71607,4356,1,685161,4828634,9
7569,KBN,10,corner,33,0,0,corner,b5b6,4137251727,30438415200593,30438642655696,4009796624,4137,3989,226277438,74161,4296,1,986762,4684388,15
7569,KBN,10,corner,34,0,1,stock,b8a8,3989884586,30438643067351,30438761014478,3971937459,4009,3989,117549677,71777,4557,1,780082,4836105,28
7569,KBN,10,corner,35,0,0,corner,b6c7,4009796624,30438761400205,30438983693583,3887503246,4009,3971,218965621,71267,4246,1,865452,5282612,35
7569,KBN,10,corner,36,0,1,stock,a8a7,3971937459,30438984197116,30438989667591,4066466984,3887,3971,5362069,75553,0,1,271245,3805057,6
7569,KBN,10,corner,37,0,0,corner,d7c8,3887503246,30438989917855,30438991800819,3985620282,3887,4066,1828699,52348,0,1,264414,1828699,1
7569,KBN,10,corner,38,0,1,stock,a7a8,4066466984,30438991948730,30438992457670,4165958044,3985,4066,359780,50324,2363,2,338992,0,65
7569,KBN,10,corner,39,0,0,corner,c8b7,3985620282,30438992562247,30438992854373,4085328156,3985,4165,255651,41352,0,1,111146,255651,1
7569,KBN,10,corner,40,0,1,stock,a8a7,4165958044,30438992958228,30438993092599,4265823673,4085,4165,97285,40050,0,2,139609,97285,1
7569,KBN,10,corner,41,0,0,corner,d6c8,4085328156,30438993187301,30438993429503,4185085954,4085,4265,207870,39529,0,1,132107,207870,1
7569,KBN,10,stock,0,0,1,stock,f4e3,10000000000,30439101902331,30439715474841,9486427490,10000,10000,612904586,104116,6435311,2,1064089,5824310,13
7569,KBN,10,stock,1,0,0,stock,f7f6,10000000000,30439715888349,30440439312973,9376575376,10000,9486,716741526,156934,4256,1,1051859,0,20
7569,KBN,10,stock,2,0,1,stock,e3e4,9486427490,30440439708635,30440838346182,9187789943,9376,9486,398286543,88312,4296,1,692393,4172034,9
7569,KBN,10,stock,3,0,0,stock,h5g3,9376575376,30440838853230,30441341054339,8974374267,9376,9187,498234195,70155,5818,1,821877,5039338,8
7569,KBN,10,stock,4,0,1,stock,e4d5,9187789943,30441341557702,30441670698304,8958649341,8974,9187,328757697,78928,5979,1,864219,2344518,16
7569,KBN,10,stock,5,0,0,stock,g3f5,8974374267,30441671060876,30441961430256,8784004887,8974,8958,288298751,56404,4086,1,614495,6612726,8
7569,KBN,10,stock,6,0,1,stock,d5e4,8958649341,30441961893698,30442838071558,8182471481,8784,8958,874723529,69764,4948,1,1305808,6003266,11
7569,KBN,10,stock,7,0,0,stock,f5h4,8784004887,30442838475642,30443180511350,8541969179,8784,8182,341619069,71397,4597,1,751772,5411683,6
7569,KBN,10,stock,8,0,1,stock,e4d5,8182471481,30443181073079,30443418684315,8044860245,8541,8182,233475056,84776,7271,1,956467,2803683,10
7569,KBN,10,stock,9,0,0,stock,d1f3,8541969179,30443419168659,30443795440295,8265697543,8541,8044,375979108,80891,6440,1,745311,4699802,6
7569,KBN,10,stock,10,0,1,stock,d5d6,8044860245,30443795827764,30444096522648,7844165361,8265,8044,300402723,69073,4277,1,641859,4078796,9
7569,KBN,10,stock,11,0,0,stock,h4f5,8265697543,30444096936516,30444507514003,7955120056,8265,7844,410277403,68783,4156,1,659493,2955018,5
7569,KBN,10,stock,12,0,1,stock,d6d7,7844165361,30444507994261,30444723495957,7728663665,7955,7844,211512501,146299,0,1,803277,3985867,10
7569,KBN,10,stock,13,0,0,stock,f3h5,7955120056,30444723926861,30445385528858,7393518059,7955,7728,657702461,94280,0,1,621317,4077914,5
7569,KBN,10,stock,14,0,1,stock,d7d8,7728663665,30445386002596,30445684341654,7530324607,7393,7728,297981093,111426,5288,1,804221,5857009,8
7569,KBN,10,stock,15,0,0,stock,f6e6,7393518059,30445684761682,30446110948245,7067331496,7393,7530,414974891,72157,4657,1,807524,3139024,9
7569,KBN,10,stock,16,0,1,stock,d8c7,7530324607,30446111343535,30446420803743,7320864399,7067,7530,305574934,73860,0,1,624071,4656257,5
7569,KBN,10,stock,17,0,0,stock,e6e7,7067331496,30446421202869,30446977372269,6611162096,7067,7320,548354695,71016,4567,1,608427,2691736,5
7569,KBN,10,stock,18,0,1,stock,c7b6,7320864399,30446977783123,30447210608577,7188038945,6611,7320,228871070,74982,0,1,681496,5316642,7
7569,KBN,10,stock,19,0,0,stock,e7d7,6611162096,30447211055946,30449086368874,4835849168,6611,7188,1867397494,74552,4807,1,772241,4825189,8
7569,KBN,10,stock,20,0,1,stock,b6c5,7188038945,30449086785646,30449342487992,7032336599,4835,7188,255176098,72708,6250,1,890138,5106058,9
7569,KBN,10,stock,21,0,0,stock,d7e6,4835849168,30449342869552,30449658095616,4620623104,4835,7032,314688351,70736,4497,1,892120,5022053,10
7569,KBN,10,stock,22,0,1,stock,c5c4,7032336599,30449658670696,30449954702322,6836304973,4620,7032,295654379,76855,8192,1,834114,5133750,5
7569,KBN,10,stock,23,0,0,stock,e6e5,4620623104,30449955171823,30450142629942,4533164985,4620,6836,187132207,72388,5388,1,774526,4715976,8
7569,KBN,10,stock,24,0,1,stock,c4c5,6836304973,30450143081396,30450842246828,6237139541,4533,6836,694731305,72028,4586,1,680395,4816666,5
7569,KBN,10,stock,25,0,0,stock,h5f3,4533164985,30450842813815,30451069576442,4406402358,4533,6237,222708079,85618,7111,1,825231,5051497,6
7569,KBN,10,stock,26,0,1,stock,c5b6,6237139541,30451069975268,30452860453133,4546661676,4406,6237,1778998690,70556,3996,1,664260,6030366,7
7569,KBN,10,stock,27,0,0,stock,e5d6,4406402358,30452861018358,30453421256041,3946164675,4406,4546,559834129,87621,7942,1,959001,2844844,9
7569,KBN,10,stock,28,0,1,stock,b6b5,4546661676,30453421821666,30453763509822,4304973520,3946,4546,341435409,83775,6540,1,787055,6053632,6
7569,KBN,10,stock,29,0,0,stock,f3e2,3946164675,30453763914186,30454047218772,3762860089,3946,4304,279294721,145036,4337,1,700806,3895432,4
7569,KBN,10,stock,30,0,1,stock,b5b4,4304973520,30454047870375,30454208481672,4244362223,3762,4304,156514587,91827,0,1,1071179,4143122,17
7569,KBN,10,stock,31,0,0,stock,f5h4,3762860089,30454209076831,30454411059220,3660877700,3762,4244,201588044,89604,0,1,959462,2937773,8
7569,KBN,10,stock,32,0,1,stock,b4c3,4244362223,30454411631796,30454588701563,4167292456,3660,4244,167541239,75903,0,1,1000172,4371402,16
7569,KBN,10,stock,33,0,0,stock,d6e5,3660877700,30454589093709,30454727573079,3622398330,3660,4167,133910536,73410,0,1,640234,4645852,7
7569,KBN,10,stock,34,0,1,stock,c3d2,4167292456,30454728025955,30454900621788,4094696623,3622,4167,168480121,74792,4576,1,327208,3867420,8
7569,KBN,10,stock,35,0,0,stock,e2f1,3622398330,30454901167383,30455089736261,3533829452,3622,4094,184563353,95052,0,1,863500,4849785,8
7569,KBN,10,stock,36,0,1,stock,d2e1,4094696623,30455090269147,30455215141772,4069823998,3533,4094,124576564,88102,6259,1,776958,5603460,5
7569,KBN,10,stock,37,0,0,stock,f1b5,3533829452,30455215658815,30455365529107,3483959160,3533,4069,149671969,139238,4727,1,693936,4161308,5
7569,KBN,10,stock,38,0,1,stock,e1d2,4069823998,30455365965148,30455787134497,3748654649,3483,4069,417354725,77065,5428,1,579936,5927834,3
7569,KBN,10,stock,39,0,0,stock,e5d4,3483959160,30455787641976,30455996349974,3375251162,3483,3748,208334700,116714,6129,1,840073,4191563,8
7569,KBN,10,stock,40,0,1,stock,d2c2,3748654649,30455996914838,30456144439246,3701130241,3375,3748,146941519,85938,5809,1,1121435,2967367,9
7569,KBN,10,stock,41,0,0,stock,b5f1,3375251162,30456144869579,30456534304800,3085815941,3375,3701,385351534,77555,0,1,843960,3131492,10
7569,KBN,10,stock,42,0,1,stock,c2d2,3701130241,30456534697617,30457745082101,2590745757,3085,3701,1198874157,102412,4057,1,633666,5164425,7
7569,KBN,10,stock,43,0,0,stock,f1b5,3085815941,30457745501568,30457926036624,3005280885,3085,2590,180182519,75212,4748,1,767624,6373840,10
7569,KBN,10,stock,44,0,1,stock,d2c2,2590745757,30457926476381,30458018933529,2598288609,3005,2590,92053019,77075,4446,1,826030,5468278,13
7569,KBN,10,stock,45,0,0,stock,h4f3,3005280885,30458019402158,30458438246757,2686436286,3005,2598,414901542,77736,4827,1,753713,4479814,8
7569,KBN,10,stock,46,0,1,stock,c2b2,2598288609,30458438615217,30458752853528,2384050298,2686,2598,309887866,75632,4076,1,578001,5246978,5
7569,KBN,10,stock,47,0,0,stock,f3e1,2686436286,30458753410320,30458971771802,2568074804,2686,2384,217970750,78066,5749,1,904731,6358717,8
7569,KBN,10,stock,48,0,1,stock,b2b3,2384050298,30458972560630,30459124292203,2332318725,2568,2384,151458352,91266,5108,1,787698,3317439,8
7569,KBN,10,stock,49,0,0,stock,b5c6,2568074804,30459124687764,30459801012454,1991750114,2568,2332,665105749,98457,4066,1,608316,3172383,12
7569,KBN,10,stock,50,0,1,stock,b3b4,2332318725,30459801410769,30459895151728,2338577766,1991,2332,89805914,77635,4777,1,652022,2487271,16
7569,KBN,10,stock,51,0,0,stock,c6d7,1991750114,30459895527068,30460043082024,1944195158,1991,2338,147271457,76754,0,1,631743,4475296,8
7569,KBN,10,stock,52,0,1,stock,b4b3,2338577766,30460043461400,30460204693350,2277345816,1944,2338,160812047,77095,0,1,772835,4542857,15
7569,KBN,10,stock,53,0,0,stock,d7b5,1944195158,30460205117944,30460284515572,1964797530,1944,2277,79221592,77636,4887,1,581328,2780599,9
7569,KBN,10,stock,54,0,1,stock,b3b4,2277345816,30460284905965,30460398630723,2263621058,1964,2277,113449197,137705,0,1,641197,3060626,7
7569,KBN,10,stock,55,0,0,stock,b5d7,1964797530,30460399094886,30460536482602,1927409814,1964,2263,137152302,85208,0,1,672372,4862075,6
7569,KBN,10,stock,56,0,1,stock,b4b3,2263621058,30460536926735,30460651391336,2249156457,1927,2263,114293086,78938,5208,1,595959,2963471,6
7569,KBN,10,stock,57,0,0,stock,e1d3,1927409814,30460651822030,30460801429997,1877801847,1927,2249,149411011,73550,4076,1,603870,4062971,8
7569,KBN,10,stock,58,0,1,stock,b3c2,2249156457,30460801899038,30460913826096,2237229399,1877,2249,111620509,83504,0,1,730089,6100361,7
7569,KBN,10,stock,59,0,0,stock,d7a4,1877801847,30460914222438,30460999774724,1892249561,1877,2237,85264738,79920,4156,1,663770,5652473,9
7569,KBN,10,stock,60,0,1,stock,c2d2,2237229399,30461000193650,30461295613176,2041809873,1892,2237,295160120,75252,4757,1,382433,3703435,5
7569,KBN,10,stock,61,0,0,stock,d3f4,1892249561,30461296230278,30461380615510,1907864329,1892,2041,84170927,94471,6160,1,384133,3628393,4
7569,KBN,10,stock,62,0,1,stock,d2c1,2041809873,30461381246843,30461473452861,2049603855,1907,2041,92009291,91296,7201,1,808275,2625698,6
7569,KBN,10,stock,63,0,0,stock,d4c3,1907864329,30461473866009,30461554097833,1927632505,1907,2049,79950762,80881,4397,1,669338,6006561,7
7569,KBN,10,stock,64,0,1,stock,c1b1,2049603855,30461554504080,30461700680870,2003427065,1927,2049,145998989,81201,5098,1,567718,5382490,5
7569,KBN,10,stock,65,0,0,stock,f4d3,1927632505,30461701100457,30462333426306,1395306656,1927,2003,632034569,81171,5108,1,674634,2789051,7
7569,KBN,10,stock,66,0,1,stock,b1a2,2003427065,30462333881356,30462408179133,2029129288,1395,2003,73961897,80530,5378,1,768275,5953562,7
7569,KBN,10,stock,67,0,0,stock,d3e1,1395306656,30462408703486,30462785274305,1118735837,1395,2029,372201356,102263,5838,1,782227,3144692,5
7569,KBN,10,stock,68,0,1,stock,a2b1,2029129288,30462785654323,30462861264802,2053518809,1118,2029,75346841,197675,5047,1,623520,2124690,12
7569,KBN,10,stock,69,0,0,stock,a4d1,1118735837,30462861780002,30463167096879,913418960,1118,2053,305121343,93570,6730,1,670569,2096719,4
7569,KBN,10,stock,70,0,1,stock,b1c1,2053518809,30463167640161,30464002877566,1318281404,913,2053,835007081,121291,0,1,662359,4357631,3
7569,KBN,10,stock,71,0,0,stock,d1f3,913418960,30464003288790,30464544787546,471920204,913,1318,530226813,99438,5899,1,690280,4566012,6
7569,KBN,10,stock,72,0,1,stock,c1b1,1318281404,30464545160263,30464609928068,1353513599,471,1318,64628130,78116,5829,1,556380,2734190,6
7569,KBN,10,stock,73,0,0,stock,f3e4,471920204,30464610237871,30464886430360,295727715,471,1353,276005518,67972,4196,1,418174,5672163,5
7569,KBN,10,stock,74,0,1,stock,b1a2,1353513599,30464886941013,30465036359718,1304094894,295,1353,149228438,83685,6079,1,721276,4940931,5
7569,KBN,10,stock,75,0,0,stock,e1c2,295727715,30465036950591,30465208415710,224262596,295,1304,167566178,84286,6920,1,804018,2891694,8
7569,KBN,10,stock,76,0,1,stock,a2b1,1304094894,30465208832953,30465324067875,1288859972,224,1304,114972590,80340,5528,1,664322,3056150,6
7569,KBN,10,stock,77,0,0,stock,c2e1,224262596,30465324463096,30465400962293,247763399,224,1288,76261088,80460,4757,1,607875,3419792,7
7569,KBN,10,stock,78,0,1,stock,b1a1,1288859972,30465401361379,30465483702686,1306518665,247,1288,81907149,81161,5098,1,609368,5566546,7
7569,KBN,10,stock,79,0,0,stock,e1g2,247763399,30465484166429,30465626570611,205359217,247,1306,142179501,83275,4917,1,333727,3699640,6
7569,KBN,10,stock,80,0,1,stock,a1a2,1306518665,30465626956508,30465782288779,1251186394,205,1306,155161589,75653,5378,1,551613,4939158,5
7569,KBN,10,stock,81,0,0,stock,e4d3,205359217,30465782646373,30465833708829,254296761,205,1251,50877595,98466,4607,1,521589,5208451,5
7569,KBN,10,stock,82,0,1,stock,a2a3,1251186394,30465834263137,30466090263195,1095186336,254,1251,255717209,189743,10836,1,806894,5520336,7
7569,KBN,10,stock,83,0,0,stock,d3b5,254296761,30466090658325,30466229816294,215138792,254,1095,138937473,115162,4226,1,592646,5183994,5
7569,KBN,10,stock,84,0,1,stock,a3a2,1095186336,30466230184945,30466383749630,1041621651,215,1095,151075974,82854,4597,1,517151,8001988,6
7569,KBN,10,stock,85,0,0,stock,b5f1,215138792,30466384171771,30466507413778,191896785,215,1041,123020900,83084,4577,1,297482,3702324,5
7569,KBN,10,stock,86,0,1,stock,a2b1,1041621651,30466507847075,30466733967923,915500803,191,1041,225441291,84897,6450,1,744160,4030473,7
7569,KBN,10,stock,87,0,0,stock,c3d2,191896785,30466734365678,30466842533836,183728627,191,915,104309405,83314,4877,1,549078,5501387,4
7569,KBN,10,stock,88,0,1,stock,b1b2,915500803,30466842932542,30467275287523,583145822,183,915,432076915,82093,5317,1,648297,4956024,5
7569,KBN,10,stock,89,0,0,stock,d2e3,183728627,30467275843784,30467379172457,180399954,183,583,103128370,96685,6569,1,702157,3982302,5
7569,KBN,10,stock,90,0,1,stock,b2b3,583145822,30467379502100,30467722695166,339952756,180,583,334281458,72288,4888,1,480706,4391723,4
7569,KBN,10,stock,91,0,0,stock,g2h4,180399954,30467723203446,30467825477362,178126038,180,339,102083100,87600,0,1,729347,4794483,4
7569,KBN,10,stock,92,0,1,stock,b3b2,339952756,30467825905883,30467988455363,277403276,178,339,162273890,133630,5488,1,649740,5931148,4
7569,KBN,10,stock,93,0,0,stock,f1b5,178126038,30467988984504,30468089306134,177804408,178,277,100074806,100430,6409,1,726412,2865876,4
7569,KBN,10,stock,94,0,1,stock,b2a2,277403276,30468089866592,30468131058129,336211739,177,277,40950326,101571,0,1,798239,6129404,12
7569,KBN,10,stock,95,0,0,stock,e3d3,177804408,30468131555533,30468199970673,209389268,177,336,68082078,94441,6029,1,859463,4293285,19
7569,KBN,10,stock,96,0,1,stock,a2b1,336211739,30468200437922,30468206515112,430134549,209,336,5915056,100560,5368,1,562308,3420894,28
7569,KBN,10,stock,97,0,0,stock,d3e3,209389268,30468206895731,30468212678155,303606844,209,430,5664096,63885,3665,1,478804,5015938,11
7569,KBN,10,stock,98,0,1,stock,b1a1,430134549,30468213081488,30468213728094,529487943,303,430,558673,73379,5689,1,435059,431794,1
7569,KBN,10,stock,99,0,0,stock,h4g2,303606844,30468213950046,30468214565095,402991795,303,529,388396,75242,3915,2,507401,0,65
7569,KBN,10,table,0,0,1,stock,f4e3,10000000000,30468289115883,30468898733314,9490382569,10000,10000,601453874,97134,2362585,3,982507,0,20
7569,KBN,10,table,1,0,0,table,f7e6,10000000000,30468899134504,30468903819684,10095314820,10000,9490,4686912,5099628,59359,1,5099628,59359,1
7569,KBN,10,table,2,0,1,stock,e3e4,9490382569,30468904083499,30469233653655,9260812413,10095,9490,325687636,52519,3869623,2,284354,3922142,7
7569,KBN,10,table,3,0,0,table,h5f6,10095314820,30469234158189,30469241072600,10188400409,10095,9260,6889189,7406501,27230,1,7406501,27230,1
7569,KBN,10,table,4,0,1,stock,e4f4,9260812413,30469241275613,30469464372213,9137715813,10188,9260,222697527,61882,0,1,563521,2730283,10
7569,KBN,10,table,5,0,0,table,d1b3,10188400409,30469464867613,30469474438434,10278829588,10188,9137,9523708,10031235,49444,1,10031235,49444,1
7569,KBN,10,table,6,0,1,stock,f4g5,9137715813,30469474634937,30470819297373,7893053377,10278,9137,1339710896,67511,5309291,2,878953,5376802,15
7569,KBN,10,table,7,0,0,table,b3c2,10278829588,30470819814335,30470825860770,10372783153,10278,7893,6022005,6549932,26840,1,6549932,26840,1
7569,KBN,10,table,8,0,1,stock,g5h6,7893053377,30470826041199,30471030578748,7788515828,10372,7893,204155314,57867,0,1,542068,6019982,8
7569,KBN,10,table,9,0,0,table,f6e8,10372783153,30471030937294,30471038255899,10465464548,10372,7788,7301854,7669523,18698,1,7669523,18698,1
7569,KBN,10,table,10,0,1,stock,h6h5,7788515828,30471038459493,30471408382399,7518592922,10465,7788,362420274,56094,0,1,427276,5543090,7
7569,KBN,10,table,11,0,0,table,c2f5,10465464548,30471408795466,30471416890973,10557369041,10465,7518,8070591,8495205,27591,1,8495205,27591,1
7569,KBN,10,table,12,0,1,stock,h5h4,7518592922,30471417069009,30471819152819,7216509112,10557,7518,398707343,60049,2919626,2,507144,2940397,16
7569,KBN,10,table,13,0,0,table,e6e5,10557369041,30471819646016,30471825531210,10651483847,10557,7216,5857337,6361590,31578,1,6361590,31578,1
7569,KBN,10,table,14,0,1,stock,h4g5,7216509112,30471825858209,30472706888698,6435478623,10651,7216,839954830,71127,6133370,2,621458,6163796,7
7569,KBN,10,table,15,0,0,table,e8d6,10651483847,30472707376637,30472712354686,10746505798,10651,6435,4982383,5481648,0,0,5481648,0,0
7569,KBN,10,table,16,0,1,stock,g5h6,6435478623,30472712503248,30472886710676,6361271195,10746,6435,170242938,58767,0,1,447910,3497728,7
7569,KBN,10,table,17,0,0,table,e5f6,10746505798,30472887107018,30472893200354,10840412462,10746,6361,6074623,6480088,21082,1,6480088,21082,1
7569,KBN,10,table,18,0,1,stock,h6h5,6361271195,30472893344329,30473130112751,6224502773,10840,6361,232868641,49363,0,1,390193,6661438,5
7569,KBN,10,table,19,0,0,table,d6f7,10840412462,30473130650094,30473141248892,10929813664,10840,6224,10572222,11121682,30045,1,11121682,30045,1
7569,KBN,10,table,20,0,1,stock,h5h4,6224502773,30473141480548,30473353007963,6112975358,10929,6224,194477887,77656,2445989,2,704080,6515430,15
7569,KBN,10,table,21,0,0,table,f6e5,10929813664,30473353377215,30473359497371,11023693508,10929,6112,6094583,6473829,28492,1,6473829,28492,1
7569,KBN,10,table,22,0,1,stock,h4g3,6112975358,30473359698391,30473518095033,6054578716,11023,6112,142917352,119539,0,1,349030,4302419,4
7569,KBN,10,table,23,0,0,table,e5e4,11023693508,30473518530473,30473525620869,11116603112,11023,6054,7068346,7512719,24646,1,7512719,24646,1
7569,KBN,10,table,24,0,1,stock,g3f2,6054578716,30473527945763,30474493197103,5189327376,11116,6054,945938819,90135,3975291,2,2520161,4065426,5
7569,KBN,10,table,25,0,0,table,f5g4,11116603112,30474493700155,30474503901469,11206401798,11116,5189,10176232,10802767,29564,1,10802767,29564,1
7569,KBN,10,table,26,0,1,stock,f2f1,5189327376,30474504268297,30476054498889,3739096784,11206,5189,1530711390,87320,0,1,325236,3733279,2
7569,KBN,10,table,27,0,0,table,f7e5,11206401798,30476055070898,30476064247851,11297224845,11206,3739,9148648,9769058,31097,1,9769058,31097,1
7569,KBN,10,table,28,0,1,stock,f1f2,3739096784,30476064480619,30476273954475,3629622928,11297,3739,209329724,77727,3450447,2,363502,3528174,4
7569,KBN,10,table,29,0,0,table,e4f4,11297224845,30476274338779,30476286316592,11385247032,11297,3629,8296663,8691643,3683605,2,8691643,3683605,2
7569,KBN,10,table,30,0,1,stock,f2e1,3629622928,30476286644723,30476508524877,3507742774,11385,3629,221641400,76013,5288500,2,552226,5364513,6
7569,KBN,10,table,31,0,0,table,f4e3,11385247032,30476508945986,30476514691241,11479501777,11385,3507,5720575,6152179,27190,1,6152179,27190,1
7569,KBN,10,table,32,0,1,stock,e1f1,3507742774,30476514896718,30476697939037,3424700455,11479,3507,179206392,62203,0,1,393176,5103344,4
7569,KBN,10,table,33,0,0,table,e5d3,11479501777,30476698315991,30476703287830,11574529938,11479,3424,4974181,5362230,26249,1,5362230,26249,1
7569,KBN,10,table,34,0,1,stock,f1g2,3424700455,30476703501770,30476876845376,3351356849,11574,3424,172966631,58908,4491301,2,347149,4499493,4
7569,KBN,10,table,35,0,0,table,e3f4,11574529938,30476877369189,30476885048044,11666851083,11574,3351,7659367,8192633,22634,1,8192633,22634,1
7569,KBN,10,table,36,0,1,stock,g2h2,3351356849,30476885219650,30477030649515,3305926984,11666,3351,145253917,60109,0,1,335751,2781860,5
7569,KBN,10,table,37,0,0,table,f4f3,11666851083,30477030987921,30477037126634,11760712370,11666,3305,6116175,6462923,24356,1,6462923,24356,1
7569,KBN,10,table,38,0,1,stock,h2g1,3305926984,30477037283308,30477157261305,3285948987,11760,3305,119719337,58297,6753105,2,401208,6777221,7
7569,KBN,10,table,39,0,0,table,g4h3,11760712370,30477157765328,30477166812247,11851665451,11760,3285,9024665,9540374,25167,1,9540374,25167,1
7569,KBN,10,table,40,0,1,stock,g1h1,3285948987,30477167055070,30477267470570,3285533487,11851,3285,100071743,73871,0,1,573923,4946270,22
7569,KBN,10,table,41,0,0,table,f3g3,11851665451,30477267905981,30477274470680,11945100752,11851,3285,6548711,6993544,18247,1,6993544,18247,1
7569,KBN,10,table,42,0,1,stock,h1g1,3285533487,30477276028708,30477281961845,3379600350,11945,3285,5842357,56594,0,1,105287,3973128,10
7569,KBN,10,table,43,0,0,table,d3c1,11945100752,30477282113501,30477286359055,12040855198,11945,3379,4246455,4402538,11177,1,4402538,11177,1
7569,KBN,10,table,44,0,1,stock,g1h1,3379600350,30477286473887,30477286795568,3479278669,12040,3379,252296,48402,203894,2,111226,252296,1
7569,KBN,10,table,45,0,0,table,h3g2,12040855198,30477286888146,30477289999004,12137744340,12040,3479,3111743,3264110,0,0,3264110,0,0
7569,KBN,10,table,46,0,1,stock,h1g1,3479278669,30477290091162,30477290233084,3579136747,12137,3479,99759,45668,54091,2,97295,99759,1
7569,KBN,10,table,47,0,0,table,c1e2,12137744340,30477290317080,30477293302120,12234759300,12137,3579,2985765,3105954,0,0,3105954,0,0
7658,KBN,10,corner,0,2,0,stock,h5h6,10000000000,30470134153976,30470372469906,9861684070,10000,10000,237935050,95943,3816,1,705183,3622194,13
7658,KBN,10,corner,1,2,1,corner,e3f5,10000000000,30470372944555,30470684368272,9788576283,9861,10000,310957034,112528,4807,1,900443,2732406,10
7658,KBN,10,corner,2,2,0,stock,h6h7,9861684070,30470684791485,30471014250250,9632225305,9861,9788,325495825,66159,4667,1,687445,3114477,5
7658,KBN,10,corner,3,2,1,corner,f4g5,9788576283,30471014714103,30471378525907,9524764479,9632,9788,363543208,86459,5187,1,714987,5155942,7
7658,KBN,10,corner,4,2,0,stock,h7h8,9632225305,30471378938564,30471661961615,9449202254,9632,9524,282446459,65608,4267,1,966433,4969294,3
7658,KBN,10,corner,5,2,1,corner,g5f6,9524764479,30471663551390,30471906799220,9381516649,9449,9524,239410112,69374,5378,1,1747286,4337621,3
7658,KBN,10,corner,6,2,0,stock,h8h7,9449202254,30471907373448,30472159107594,9297468108,9449,9381,249850958,68241,4577,1,949458,5995154,10
7658,KBN,10,corner,7,2,1,corner,f7b3,9381516649,30472159504447,30472628161241,9012859855,9297,9381,436954541,66880,4297,1,539956,4387135,4
7658,KBN,10,corner,8,2,0,stock,h7h8,9297468108,30472628569100,30472964328565,9061708643,9297,9012,335334631,56885,4327,1,795739,3354475,9
7658,KBN,10,corner,9,2,1,corner,f5e7,9012859855,30472964949433,30475385258375,6692550913,9061,9012,2372045243,65207,5007,1,814244,2945955,6
7658,KBN,10,corner,10,2,0,stock,h8h7,9061708643,30475385654738,30475849647425,8697715956,9061,6692,463522387,106289,0,1,902954,5912182,10
7658,KBN,10,corner,11,2,1,corner,e7g6,6692550913,30475850902941,30476300733295,6342720559,8697,6692,446213630,71116,0,1,1679587,5053389,13
7658,KBN,10,corner,12,2,0,stock,h7h6,8697715956,30476301579970,30476575841999,8523453927,8697,6342,273852517,72187,5328,1,1411346,6134348,13
7658,KBN,10,corner,13,2,1,corner,b3g8,6342720559,30476576237500,30477238983397,5779974662,8523,6342,662531217,64887,4677,1,395699,3661012,6
7658,KBN,10,corner,14,2,0,stock,h6h5,8523453927,30477239592758,30477741153727,8121892958,8523,5779,501238750,78708,0,1,889636,4410861,12
7658,KBN,10,corner,15,2,1,corner,g6e5,5779974662,30477741533244,30478542202705,5079305201,8121,5779,800157240,66950,0,1,611651,2432770,8
7658,KBN,10,corner,16,2,0,stock,h5h4,8121892958,30478542650524,30478904085094,7860458388,8121,5079,360991121,108011,0,1,782978,5352055,11
7658,KBN,10,corner,17,2,1,corner,f6f5,5079305201,30478904449178,30480429638280,3654116099,7860,5079,1517457150,67291,4026,1,484202,3445660,5
7658,KBN,10,corner,18,2,0,stock,h4g3,7860458388,30480430177115,30480907785043,7482850460,7860,3654,476924566,78798,6449,1,1112751,5710590,11
7658,KBN,10,corner,19,2,1,corner,e5g4,3654116099,30480908450417,30481327468733,3335097783,7482,3654,418821710,78337,6380,1,595317,3429236,6
7658,KBN,10,corner,20,2,0,stock,g3g2,7482850460,30481327931775,30482009091267,6901690968,7482,3335,673515608,87901,4557,1,709991,3964534,5
7658,KBN,10,corner,21,2,1,corner,g8c4,3335097783,30482009867036,30482228252776,3216712043,6901,3335,218187665,80971,0,1,942366,6087232,4
7658,KBN,10,corner,22,2,0,stock,g2f3,6901690968,30482228780254,30482550217137,6680254085,6901,3216,317539005,80591,6950,1,722708,3111892,4
7658,KBN,10,corner,23,2,1,corner,c4f1,3216712043,30482550890093,30483130487590,2737114546,6680,3216,571371633,71768,5207,1,865080,4995362,4
7658,KBN,10,corner,24,2,0,stock,f3g3,6680254085,30483130910151,30483473005603,6438158633,6680,2737,338220529,68762,4247,1,636921,4994151,6
7658,KBN,10,corner,25,2,1,corner,f1e2,2737114546,30483473390238,30484251538077,2058966707,6438,2737,774244809,66769,4677,1,604851,2513470,6
7658,KBN,10,corner,26,2,0,stock,g3h4,6438158633,30484251897684,30484723352285,6066704032,6438,2058,471245783,64817,4827,1,547376,3987338,6
7658,KBN,10,corner,27,2,1,corner,g4f6,2058966707,30484723876268,30485048500603,1834342372,6066,2058,324444466,78597,6410,1,675048,3970884,4
7658,KBN,10,corner,28,2,0,stock,h4g3,6066704032,30485049284384,30485334324303,5881664113,6066,1834,284690267,72338,6750,1,1108923,2607911,9
7658,KBN,10,corner,29,2,1,corner,f6e4,1834342372,30485334710701,30485794793625,1474259448,5881,1834,456228204,114040,4236,1,557762,5132227,4
7658,KBN,10,corner,30,2,0,stock,g3h4,5881664113,30485795265510,30485969074877,5807854746,5881,1474,173601159,80461,5317,1,645713,4623157,4
7658,KBN,10,corner,31,2,1,corner,f5f4,1474259448,30485969666812,30486301214422,1242711838,5807,1474,331317001,117485,8743,1,789788,2173363,4
7658,KBN,10,corner,32,2,0,stock,h4h3,5807854746,30486301646829,30486533342921,5676158654,5807,1242,231405009,90595,0,1,695087,6287070,4
7658,KBN,10,corner,33,2,1,corner,f4g5,1242711838,30486533943057,30486671688858,1204966037,5676,1242,137589412,70014,0,1,1064348,6056095,4
7658,KBN,10,corner,34,2,0,stock,h3h2,5676158654,30486673484972,30487022930821,5426712805,5676,1204,345460116,73320,0,1,1770260,2488353,7
7658,KBN,10,corner,35,2,1,corner,e2f1,1204966037,30487023456607,30487282513517,1045909127,5426,1204,258772844,86189,0,1,785813,4544230,5
7658,KBN,10,corner,36,2,0,stock,h2g1,5426712805,30487283047685,30487436425603,5373334887,5426,1045,153065130,74291,0,1,820675,4958197,6
7658,KBN,10,corner,37,2,1,corner,f1h3,1045909127,30487436965870,30487564391460,1018483537,5373,1045,127156680,182633,6029,1,777669,2803412,6
7658,KBN,10,corner,38,2,0,stock,g1h1,5373334887,30487564918708,30487726028364,5312225231,5373,1018,157002709,87200,5839,1,967495,2956215,12
7658,KBN,10,corner,39,2,1,corner,g5g4,1018483537,30487726372949,30487838055626,1006800860,5312,1018,111438909,66709,3916,1,562319,5619715,10
7658,KBN,10,corner,40,2,0,stock,h1h2,5312225231,30487838448814,30487983473631,5267200414,5312,1006,144536132,70315,3675,1,856463,11214973,23
7658,KBN,10,corner,41,2,1,corner,e4c3,1006800860,30487983878376,30488083689284,1006989952,5267,1006,96935390,70996,4507,1,650140,6605676,24
7658,KBN,10,corner,42,2,0,stock,h2g1,5267200414,30488084147659,30488104428373,5346919700,5267,1006,19993272,71968,4056,1,394846,0,65
7658,KBN,10,corner,43,2,1,corner,g4g3,1006989952,30488104792227,30488155806112,1055976067,5346,1006,50768443,60891,4257,1,593244,0,65
7658,KBN,10,corner,44,2,0,stock,g1h1,5346919700,30488156203165,30488156600138,5446522727,5346,1055,340197,64746,4006,1,208742,252697,1
7658,KBN,10,corner,45,2,1,corner,h3g2,1055976067,30488156705987,30488157290550,1155391504,5446,1055,437824,68413,1863,2,289361,0,65
7658,KBN,10,corner,46,2,0,stock,h1g1,5446522727,30488157416518,30488157553052,5546386193,5446,1155,98006,40370,0,1,133209,98006,1
7658,KBN,10,corner,47,2,1,corner,c3e2,1155391504,30488157652531,30488158113329,1254930706,5546,1155,314400,38107,0,2,277653,29594,66
7658,KBN,10,stock,0,2,0,stock,h5h6,10000000000,30496923069922,30497194332539,9828737383,10000,10000,270852744,105468,0,1,829614,4934863,11
7658,KBN,10,stock,1,2,1,stock,e3f5,10000000000,30497195158173,30497495227679,9799930494,9828,10000,299583792,157695,0,1,1269393,4843987,10
7658,KBN,10,stock,2,2,0,stock,h6h7,9828737383,30497495544552,30497852644493,9571637442,9828,9799,353077031,53770,4507,1,627195,4382389,5
7658,KBN,10,stock,3,2,1,stock,f4e5,9799930494,30497853154785,30498234024709,9519060570,9571,9799,380516392,68162,5829,1,845090,2735711,11
7658,KBN,10,stock,4,2,0,stock,h7h8,9571637442,30498234433149,30498673257212,9232813379,9571,9519,436294854,67671,4346,1,667935,5496521,5
7658,KBN,10,stock,5,2,1,stock,e5f6,9519060570,30498673700755,30499144724664,9148036661,9232,9519,463239204,100340,6479,1,908594,2149106,11
7658,KBN,10,stock,6,2,0,stock,h8h7,9232813379,30499145155218,30501615451714,6862516883,9232,9148,2454315481,66549,5388,1,637162,2750113,15
7658,KBN,10,stock,7,2,1,stock,f7e6,9148036661,30501615892963,30502084888602,8779041022,6862,9148,461210008,66960,5608,1,791429,3976522,8
7658,KBN,10,stock,8,2,0,stock,h7h8,6862516883,30502085366236,30503317045586,5730837533,6862,8779,1229522835,69574,6520,1,722829,2534251,10
7658,KBN,10,stock,9,2,1,stock,e6c8,8779041022,30503317401208,30503823477934,8372964296,5730,8779,494803480,63766,4366,1,651551,2500070,5
7658,KBN,10,stock,10,2,0,stock,h8g8,5730837533,30503823901718,30504073903754,5580835497,5730,8372,246030393,68642,0,1,655126,4098405,8
7658,KBN,10,stock,11,2,1,stock,f6e7,8372964296,30504074440787,30504698393519,7849011564,5580,8372,618073363,139789,6830,1,978662,9015781,10
7658,KBN,10,stock,12,2,0,stock,g8h7,5580835497,30504700104285,30504921456092,5459483690,5580,7849,220839191,70145,6389,1,329500,3795934,5
7658,KBN,10,stock,13,2,1,stock,e7f6,7849011564,30504921878684,30505882513654,6988376594,5459,7849,952936954,67862,5017,1,652683,6014103,5
7658,KBN,10,stock,14,2,0,stock,h7g8,5459483690,30505883055394,30506270517028,5172022056,5459,6988,387133488,79969,6950,1,844250,4828234,5
7658,KBN,10,stock,15,2,1,stock,f5d6,6988376594,30506271051557,30506505068600,6854359551,5172,6988,221458120,79739,6670,1,844280,2577736,24
7658,KBN,10,stock,16,2,0,stock,g8f8,5172022056,30506505531361,30506938921850,4838631567,5172,6854,421997488,69854,4968,1,802158,2421182,6
7658,KBN,10,stock,17,2,1,stock,c8f5,6854359551,30506939422338,30508428692045,5465089844,4838,6854,1481810651,80670,7822,1,847663,4448267,9
7658,KBN,10,stock,18,2,0,stock,f8g8,4838631567,30508429398320,30508585989335,4782040552,4838,5465,156226470,102854,5989,1,1052968,2450366,15
7658,KBN,10,stock,19,2,1,stock,f5e4,5465089844,30508586407019,30508953108599,5198388264,4782,5465,366252693,68573,5007,1,719411,5481228,7
7658,KBN,10,stock,20,2,0,stock,g8h8,4782040552,30508953489558,30509883403894,3952126216,4782,5198,901997118,69364,4607,1,644832,2419129,7
7658,KBN,10,stock,21,2,1,stock,d6f7,5198388264,30509883937591,30510191064012,4991261843,3952,5198,303171670,102814,6640,1,778691,3908882,7
7658,KBN,10,stock,22,2,0,stock,h8g8,3952126216,30510191492723,30510385631812,3857987127,3952,4991,193628237,77135,6379,1,853874,4427945,13
7658,KBN,10,stock,23,2,1,stock,f7d8,4991261843,30510386238599,30510982575414,4494925028,3857,4991,593941793,82503,0,1,846954,4423389,8
7658,KBN,10,stock,24,2,0,stock,g8f8,3857987127,30510982949493,30511199851686,3741084934,3857,4494,208993349,66900,4937,1,770759,4955814,7
7658,KBN,10,stock,25,2,1,stock,d8e6,4494925028,30511200277643,30511366243636,4428959035,3741,4494,165633774,71236,4988,1,563299,3604708,8
7658,KBN,10,stock,26,2,0,stock,f8g8,3741084934,30511366633508,30511520989263,3686729179,3741,4428,154094748,69774,4967,1,627085,5238516,6
7658,KBN,10,stock,27,2,1,stock,e4c2,4428959035,30511521549250,30512476672404,3573835881,3686,4428,948605139,83995,7461,1,840103,2321494,6
7658,KBN,10,stock,28,2,0,stock,g8h8,3686729179,30512477118391,30512598871594,3664975976,3686,3573,119994288,72248,0,1,789877,4248319,13
7658,KBN,10,stock,29,2,1,stock,c2b1,3573835881,30512599282107,30512957053603,3316064385,3664,3573,357437179,69814,5018,1,717982,4603388,8
7658,KBN,10,stock,30,2,0,stock,h8g8,3664975976,30512957365710,30513111234026,3611107660,3664,3316,153667931,60650,4156,1,494567,2560781,5
7658,KBN,10,stock,31,2,1,stock,b1f5,3316064385,30513111628565,30513351813844,3175879106,3611,3316,239877134,69394,4366,1,678702,4243431,6
7658,KBN,10,stock,32,2,0,stock,g8h8,3611107660,30513352323836,30513492872790,3570558706,3611,3175,140170636,110495,5549,1,583599,3534814,7
7658,KBN,10,stock,33,2,1,stock,e6d8,3175879106,30513493276523,30513915413408,2853742221,3570,3175,421864955,69995,4777,1,646602,2619969,10
7658,KBN,10,stock,34,2,0,stock,h8g8,3570558706,30513915855408,30514449811920,3136602194,3570,2853,533628696,71387,5138,1,744060,4042772,10
7658,KBN,10,stock,35,2,1,stock,d8b7,2853742221,30514450296203,30514628434884,2775603540,3136,2853,175608343,80780,6330,1,806925,5567166,7
7658,KBN,10,stock,36,2,0,stock,g8f8,3136602194,30514628944495,30514770571934,3094974755,3136,2775,141280313,85006,6240,1,832183,2946617,12
7658,KBN,10,stock,37,2,1,stock,f5e6,2775603540,30514771120244,30514917210667,2729513117,3094,2775,145711481,81852,7551,1,822166,4748855,7
7658,KBN,10,stock,38,2,0,stock,f8e8,3094974755,30514917733769,30515024696316,3088012208,3094,2729,106560978,78287,6459,1,896830,2133523,9
7658,KBN,10,stock,39,2,1,stock,e6g4,2729513117,30515025223263,30515222601773,2632134607,3088,2729,196952197,126098,5468,1,934165,2605888,9
7658,KBN,10,stock,40,2,0,stock,e8f8,3088012208,30515223151024,30515332945253,3078217979,3088,2632,109393667,92778,8302,1,902697,4717888,5
7658,KBN,10,stock,41,2,1,stock,b7d6,2632134607,30515333764887,30515446576504,2619322990,3078,2632,112428666,143324,9404,1,1203384,6021874,6
7658,KBN,10,stock,42,2,0,stock,f8g8,3078217979,30515447559032,30515802197805,2823579206,3078,2619,294150075,190965,23405,1,1356343,4167148,13
7658,KBN,10,stock,43,2,1,stock,g4h5,2619322990,30515802579476,30516127786806,2394115660,2823,2619,324791100,74321,4637,1,643879,5306777,8
7658,KBN,10,stock,44,2,0,stock,g8h8,2823579206,30516128347074,30516227975541,2823950739,2823,2394,99315101,85718,6510,1,651211,3529236,8
7658,KBN,10,stock,45,2,1,stock,f6f7,2394115660,30516228407086,30516339385414,2383137332,2823,2394,110683101,74270,5358,1,653985,3475996,7
7658,KBN,10,stock,46,2,0,stock,h8h7,2823950739,30516339851070,30516476539104,2787262705,2823,2383,136399678,84265,7161,1,729929,4020008,10
7658,KBN,10,stock,47,2,1,stock,d6f5,2383137332,30516477036036,30516569548241,2390625127,2787,2383,90573777,74541,6490,1,720386,2845996,7
7658,KBN,10,stock,48,2,0,stock,h7h8,2787262705,30516569960056,30516715511835,2741710926,2787,2390,144282969,74901,4647,1,607006,5938951,4
7658,KBN,10,stock,49,2,1,stock,h5e2,2390625127,30516716123379,30516966297287,2240451219,2741,2390,246081867,88442,7361,1,499984,3737386,8
7658,KBN,10,stock,50,2,0,stock,h8h7,2741710926,30516966689413,30517069823489,2738576850,2741,2240,99316463,93670,4957,1,570421,5183794,5
7658,KBN,10,stock,51,2,1,stock,e2c4,2240451219,30517070220162,30517266400311,2144271070,2738,2240,195940178,73039,4677,1,614616,5663890,6
7658,KBN,10,stock,52,2,0,stock,h7h8,2738576850,30517266777064,30517424527119,2680826795,2738,2144,157521030,72999,4527,1,585533,5121110,8
7658,KBN,10,stock,53,2,1,stock,c4b3,2144271070,30517424947077,30517523496523,2145721624,2680,2144,98333457,75162,4827,1,612042,2931023,6
7658,KBN,10,stock,54,2,0,stock,h8h7,2680826795,30517523913616,30517741785256,2562955155,2680,2145,217515435,183093,4707,1,638834,3873489,7
7658,KBN,10,stock,55,2,1,stock,b3e6,2145721624,30517742164543,30517917781296,2070104871,2562,2145,171538320,73760,5238,1,623600,5717631,5
7658,KBN,10,stock,56,2,0,stock,h7h8,2562955155,30517918210848,30518873410233,1707755770,2562,2070,943828482,78937,5158,1,518314,5679444,4
7658,KBN,10,stock,57,2,1,stock,f7e7,2070104871,30518873830291,30519115099313,1928835849,1707,2070,241045150,73700,5779,1,661769,6049355,6
7658,KBN,10,stock,58,2,0,stock,h8h7,1707755770,30519115489376,30519191987031,1731258115,1707,1928,76239614,75072,4367,1,656419,4407706,8
7658,KBN,10,stock,59,2,1,stock,e7f6,1928835849,30519192403203,30519279874355,1941364697,1731,1928,87320267,75573,4497,1,663028,3480823,6
7658,KBN,10,stock,60,2,0,stock,h7h8,1731258115,30519280270928,30520045499489,1066029554,1731,1941,761223216,73329,0,1,347538,3728713,8
7658,KBN,10,stock,61,2,1,stock,e6b3,1941364697,30520046230561,30520525308250,1562287008,1066,1941,475028993,78908,0,1,1030007,5673525,7
7658,KBN,10,stock,62,2,0,stock,h8h7,1066029554,30520525775328,30521141049832,550755050,1066,1562,615129074,76945,6930,1,541327,4718189,3
7658,KBN,10,stock,63,2,1,stock,f5d6,1562287008,30521141447025,30521356982145,1446751888,550,1562,215167983,73159,5618,1,755018,2435393,7
7658,KBN,10,stock,64,2,0,stock,h7h8,550755050,30521357681350,30521449347040,559089360,550,1446,87641045,232768,0,1,966891,6300961,5
7658,KBN,10,stock,65,2,1,stock,b3c4,1446751888,30521449764053,30521551372550,1445143391,559,1446,101444075,70315,6019,1,564904,5409520,6
7658,KBN,10,stock,66,2,0,stock,h8h7,559089360,30521551909332,30521626686566,584312126,559,1445,74618484,117535,6670,1,673265,3934890,6
7658,KBN,10,stock,67,2,1,stock,c4f7,1445143391,30521627336367,30522094763052,1077716706,584,1445,466965578,71267,5047,1,923527,4548336,8
7658,KBN,10,stock,68,2,0,stock,h7h6,584312126,30522095161567,30522268441357,511032336,584,1077,160828392,78838,5408,1,555030,4727653,5
7658,KBN,10,stock,69,2,1,stock,d6f5,1077716706,30522268955255,30522437264447,1009407514,511,1077,160737358,85658,6560,1,738472,2911774,8
7658,KBN,10,stock,70,2,0,stock,h6h7,511032336,30522437657485,30522554871274,493818547,511,1009,116995552,98968,4817,1,591584,5372385,5
7658,KBN,10,stock,71,2,1,stock,f6e7,1009407514,30522555241317,30522697347887,967300944,493,1009,141660927,72589,4697,1,586124,4841573,8
7658,KBN,10,stock,72,2,0,stock,h7h8,493818547,30522697764700,30522755889852,535693395,493,967,57922645,78006,5048,1,726766,2135346,6
7658,KBN,10,stock,73,2,1,stock,e7d6,967300944,30522756306294,30522829109279,994497959,535,967,72635418,75202,5148,1,431533,3574523,6
7658,KBN,10,stock,74,2,0,stock,h8h7,535693395,30522829494765,30523004550999,460637161,535,994,174794150,76234,4386,1,615548,2401944,8
7658,KBN,10,stock,75,2,1,stock,d6c6,994497959,30523005003435,30523163967333,935534061,460,994,158637906,81021,5147,1,770389,2869872,6
7658,KBN,10,stock,76,2,0,stock,h7h8,460637161,30523164432168,30523267807014,457262315,460,935,99550751,67460,5268,1,559246,3474123,5
7658,KBN,10,stock,77,2,1,stock,c6d7,935534061,30523268335624,30523543066956,760802729,457,935,270766505,91997,7561,1,599042,3520302,8
7658,KBN,10,stock,78,2,0,stock,h8h7,457262315,30523543468686,30523604038601,496692400,457,760,60388975,77846,4056,1,560597,4425512,6
7658,KBN,10,stock,79,2,1,stock,d7c6,760802729,30523604404408,30523837083774,628123363,496,760,228656176,200820,4557,1,573937,3350769,7
7658,KBN,10,stock,80,2,0,stock,h7h8,496692400,30523837453186,30523933717617,500427969,496,628,96084531,74020,3746,1,528959,2446871,6
7658,KBN,10,stock,81,2,1,stock,c6d5,628123363,30523934264535,30524252519136,409868762,500,628,317942302,92358,8252,1,823248,5586054,6
7658,KBN,10,stock,82,2,0,stock,h8h7,500427969,30524252931682,30524391368469,461991182,500,409,138229457,77626,4637,1,595499,2965815,6
7658,KBN,10,stock,83,2,1,stock,d5c4,409868762,30524391802818,30524596094376,305577204,461,409,204089165,83575,5097,1,611372,4065695,4
7658,KBN,10,stock,84,2,0,stock,h7h8,461991182,30524596606602,30524652193501,506404283,461,305,55354975,92648,6700,1,718824,3240034,6
7658,KBN,10,stock,85,2,1,stock,f7e6,305577204,30524652695341,30524830055283,228217262,506,305,177073234,123855,7211,1,722048,3126865,6
7658,KBN,10,stock,86,2,0,stock,h8h7,506404283,30524830467318,30524876772690,560098911,506,228,46065325,81572,5058,1,642310,5422319,5
7658,KBN,10,stock,87,2,1,stock,f5d6,228217262,30524877184375,30525007409951,197991686,560,228,126375221,81371,5338,1,563841,6268611,4
7658,KBN,10,stock,88,2,0,stock,h7g7,560098911,30525007963829,30525338498113,329564627,560,197,330128486,98687,7622,1,859042,3839378,5
7658,KBN,10,stock,89,2,1,stock,d6b7,197991686,30525339291278,30525451610689,185672275,329,197,112046305,168562,24366,1,1093131,4423850,5
7658,KBN,10,stock,90,2,0,stock,g7f6,329564627,30525452191847,30525595881279,285875195,329,185,136188249,82533,7081,1,460757,3685629,5
7658,KBN,10,stock,91,2,1,stock,c4d5,185672275,30525596302548,30525701479487,180495336,285,185,105035134,82523,0,1,363572,3697216,3
7658,KBN,10,stock,92,2,0,stock,f6g5,285875195,30525701909529,30525787069852,300714872,285,180,84951055,83685,0,1,655297,6088503,5
7658,KBN,10,stock,93,2,1,stock,d5c4,180495336,30525787398884,30525889190635,178703585,300,180,101467852,70816,4347,1,544783,2475363,6
7658,KBN,10,stock,94,2,0,stock,g5f4,300714872,30525889665364,30525928940871,361439365,300,178,39045741,120189,0,1,679496,2333491,16
7658,KBN,10,stock,95,2,1,stock,c4d4,178703585,30525929281429,30525997422583,210562431,361,178,67105856,73199,0,1,594427,3484684,31
7658,KBN,10,stock,96,2,0,stock,f4f3,361439365,30525997832886,30526007280443,451991808,361,210,9168079,83284,0,1,627946,6179279,21
7658,KBN,10,stock,97,2,1,stock,e6c8,210562431,30526007983193,30526020386847,298158777,451,210,12052687,108742,47050,1,1043090,3811927,42
7658,KBN,10,stock,98,2,0,stock,f3e2,451991808,30526021141986,30526022016272,551117522,451,298,773153,114991,5128,1,779624,593906,1
7658,KBN,10,stock,99,2,1,stock,d4d5,298158777,30526022300607,30526023208103,397251281,551,298,596708,102753,0,2,674539,89383,66
7658,KBN,10,table,0,2,0,stock,h5h6,10000000000,30488210938441,30488474080740,9836857701,10000,10000,259106055,84736,5454859,2,780254,4823917,11
7658,KBN,10,table,1,2,1,table,e3f5,10000000000,30488474543592,30488483913001,10090630591,9836,10000,9307686,9781813,64206,1,9781813,64206,1
7658,KBN,10,table,2,2,0,stock,h6h7,9836857701,30488484133441,30488792072335,9628918807,9836,10090,307695630,47992,0,1,349570,6697032,5
7658,KBN,10,table,3,2,1,table,f4e4,10090630591,30488792457200,30488798259820,10184827971,9628,10090,5775577,6172419,28943,1,6172419,28943,1
7658,KBN,10,table,4,2,0,stock,h7h8,9628918807,30488798433499,30489176548982,9350803324,9628,10184,377735942,46379,0,1,534648,5568107,7
7658,KBN,10,table,5,2,1,table,e4e5,10184827971,30489176972916,30489183657424,10278143463,9350,10184,6660887,7095055,27341,1,7095055,27341,1
7658,KBN,10,table,6,2,0,stock,h8h7,9350803324,30489183925986,30491679127112,6955602198,9350,10278,2489722290,79449,0,1,421959,4072546,6
7658,KBN,10,table,7,2,1,table,e5f6,10278143463,30491679504666,30491686169806,10371478323,6955,10278,6622290,7050249,45377,1,7050249,45377,1
7658,KBN,10,table,8,2,0,stock,h7h8,6955602198,30491686438006,30492590457027,6151583177,6955,10371,894833503,49704,0,1,454779,5562449,6
7658,KBN,10,table,9,2,1,table,f5e7,10371478323,30492590837826,30492596621708,10465694441,6151,10371,5763740,6154503,21642,1,6154503,21642,1
7658,KBN,10,table,10,2,0,stock,h8h7,6151583177,30492596781377,30492858775746,5989588808,6151,10465,261785342,47621,3209148,2,350794,3223720,6
7658,KBN,10,table,11,2,1,table,e7g6,10465694441,30492859142083,30492865237401,10559599123,5989,10465,6071038,6447700,25698,1,6447700,25698,1
7658,KBN,10,table,12,2,0,stock,h7h6,5989588808,30492865532933,30493234046572,5721075169,5989,10559,364573637,53109,6453438,2,572323,6465916,7
7658,KBN,10,table,13,2,1,table,f7g8,10559599123,30493234426459,30493239652648,10654372934,5721,10559,5228140,5619534,25007,1,5958841,25007,1
7658,KBN,10,table,14,2,0,stock,h6h5,5721075169,30493240277933,30493518653058,5542700044,5721,10654,274553886,109914,0,1,423279,7721921,9
7658,KBN,10,table,15,2,1,table,g6e5,10654372934,30493519023161,30493524497551,10748898544,5542,10654,5429490,5809337,46900,1,5809337,46900,1
7658,KBN,10,table,16,2,0,stock,h5h4,5542700044,30493524665592,30493786022368,5381343268,5542,10748,257504155,48572,3361565,2,363153,3410137,10
7658,KBN,10,table,17,2,1,table,f6f5,10748898544,30493786390558,30493792046990,10843242112,5381,10748,5635598,6013542,22764,1,6013542,22764,1
7658,KBN,10,table,18,2,0,stock,h4g3,5381343268,30493792209313,30494507865198,4765687383,5381,10843,711610329,49334,3804596,2,668928,7793167,9
7658,KBN,10,table,19,2,1,table,e5g4,10843242112,30494508367759,30494517911159,10933698712,4765,10843,9515086,9866681,31657,1,9866681,31657,1
7658,KBN,10,table,20,2,0,stock,g3g2,4765687383,30494518184177,30494714182339,4669689221,4765,10933,195853343,70445,5758391,2,400948,5828836,3
7658,KBN,10,table,21,2,1,table,g8c4,10933698712,30494714614305,30494720996572,11027316445,4669,10933,6358585,6803859,25559,1,6803859,25559,1
7658,KBN,10,table,22,2,0,stock,g2f3,4669689221,30494721176030,30494933800776,4557064475,4669,11027,212293661,51456,0,1,396743,6830861,5
7658,KBN,10,table,23,2,1,table,c4a6,11027316445,30494934233032,30494943835120,11117714357,4557,11027,9552982,9996624,50896,1,9996624,50896,1
7658,KBN,10,table,24,2,0,stock,f3g3,4557064475,30494944080977,30495153620068,4447525384,4557,11117,209369833,59869,0,1,225147,3922562,5
7658,KBN,10,table,25,2,1,table,a6e2,11117714357,30495153960167,30495159814213,11211860311,4447,11117,5841405,6189564,14582,1,6189564,14582,1
7658,KBN,10,table,26,2,0,stock,g3h4,4447525384,30495159961433,30495410336672,4297150145,4447,11211,246523613,67441,0,1,339447,4042421,6
7658,KBN,10,table,27,2,1,table,g4e3,11211860311,30495410719364,30495416263357,11306316318,4297,11211,5518674,5912882,26940,1,5912882,26940,1
7658,KBN,10,table,28,2,0,stock,h4g3,4297150145,30495416437367,30495663209011,4150378501,4297,11306,246592026,52608,3557988,2,342080,3591928,4
7658,KBN,10,table,29,2,1,table,e3d1,11306316318,30495663582960,30495667867552,11402031726,4150,11306,4285835,4669267,0,0,4669267,0,0
7658,KBN,10,table,30,2,0,stock,g3h4,4150378501,30495667988923,30495914882108,4003485316,4150,11402,246623564,50956,0,1,325424,3994380,5
7658,KBN,10,table,31,2,1,table,f5f4,11402031726,30495915368876,30495919894978,11497505624,4003,11402,4528186,5027781,25268,1,5027781,25268,1
7658,KBN,10,table,32,2,0,stock,h4h3,4003485316,30495920093585,30496230967089,3792611812,4003,11497,306237374,52809,3861711,2,422119,3940028,5
7658,KBN,10,table,33,2,1,table,d1e3,11497505624,30496231853293,30496241233870,11588125047,3792,11497,8147134,8859117,1237106,2,8859117,1237106,2
7658,KBN,10,table,34,2,0,stock,h3h4,3792611812,30496241432116,30496389599857,3744444071,3792,11588,147999704,66719,0,1,354339,2571877,4
7658,KBN,10,table,35,2,1,table,e2d1,11588125047,30496389963600,30496395917406,11682171241,3744,11588,5940743,6313239,15603,1,6313239,15603,1
7658,KBN,10,table,36,2,0,stock,h4h3,3744444071,30496396105557,30496516506248,3724043380,3744,11682,120215953,51907,0,1,268110,3897004,6
7658,KBN,10,table,37,2,1,table,d1g4,11682171241,30496516914579,30496522352324,11776733496,3724,11682,5416852,5835366,23294,1,5835366,23294,1
7658,KBN,10,table,38,2,0,stock,h3h2,3724043380,30496522506875,30496635524554,3711025701,3724,11776,110238048,53040,0,1,461999,7952175,8
7658,KBN,10,table,39,2,1,table,f4f3,11776733496,30496635943650,30496642084486,11870592660,3711,11776,6118699,6547579,23785,1,6547579,23785,1
7658,KBN,10,table,40,2,0,stock,h2g1,3711025701,30496642235081,30496751679292,3701581490,3711,11870,109131335,56123,5716399,2,452135,5772522,31
7658,KBN,10,table,41,2,1,table,f3g3,11870592660,30496752109955,30496756942546,11965760069,3701,11870,4812390,4908764,21502,1,4908764,21502,1
7658,KBN,10,table,42,2,0,stock,g1h1,3701581490,30496757085730,30496773241069,3785426151,3701,11965,16012540,51286,0,1,274439,2919526,16
7658,KBN,10,table,43,2,1,table,g3f2,11965760069,30496773618603,30496780290332,12059088340,3785,11965,6651564,7039342,22103,1,7039342,22103,1
7658,KBN,10,table,44,2,0,stock,h1h2,3785426151,30496780485043,30496780867765,3885043429,3785,12059,325065,55052,0,1,207129,325065,1
7658,KBN,10,table,45,2,1,table,e3f1,12059088340,30496780980183,30496786120894,12153947629,3885,12059,5141811,5297573,0,0,5297573,0,0
7658,KBN,10,table,46,2,0,stock,h2h1,3885043429,30496786243928,30496786396105,3984891252,3885,12153,106349,45488,0,1,130615,106349,1
7658,KBN,10,table,47,2,1,table,g4f3,12153947629,30496786492369,30496788816031,12251623967,3984,12153,2324438,2457957,0,0,2457957,0,0
7727,KBN,10,corner,0,0,0,stock,e1f2,10000000000,30513121478363,30513506988418,9714489945,10000,10000,377769736,188662,0,1,1020910,2523776,14
7727,KBN,10,corner,1,0,1,corner,b3d2,10000000000,30513507543417,30514486114605,9121428812,9714,10000,973207526,213549,0,1,966063,4456048,13
7727,KBN,10,corner,2,0,0,stock,f2g3,9714489945,30514486723385,30514746689579,9554523751,9714,9121,256328769,125457,5282932,2,1187320,5291134,16
7727,KBN,10,corner,3,0,1,corner,d3e3,9121428812,30514747117949,30515914113704,8054433057,9554,9121,1002861537,96545,4834562,2,783348,4727252,9
7727,KBN,10,corner,4,0,0,stock,g3g4,9554523751,30515914626931,30516191771699,9377378983,9554,8054,272787519,118506,4267,1,1419617,5220329,13
7727,KBN,10,corner,5,0,1,corner,e3e4,8054433057,30516192887506,30516771786336,7575534227,9377,8054,578461361,217024,29414,1,1277234,2689583,8
7727,KBN,10,corner,6,0,0,stock,g4g5,9377378983,30516772385672,30517494999861,8754764794,9377,7575,722288503,112307,5949,1,648268,3464258,7
7727,KBN,10,corner,7,0,1,corner,b4e7,7575534227,30517495423634,30518313053885,6857903976,8754,7575,809573288,96594,5348,1,840355,4445302,13
7727,KBN,10,corner,8,0,0,stock,g5g4,8754764794,30518313469506,30518577481081,8590753219,8754,6857,263228776,95823,3986,1,778733,2413581,17
7727,KBN,10,corner,9,0,1,corner,d2f1,6857903976,30518577931134,30518806430715,6729404395,8590,6857,228208460,93290,4436,1,720374,5933733,15
7727,KBN,10,corner,10,0,0,stock,g4h3,8590753219,30518806886366,30519239173204,8258466381,8590,6729,431923507,98046,4097,1,763480,4985117,11
7727,KBN,10,corner,11,0,1,corner,e7d6,6729404395,30519240238155,30519604838043,6464804507,8258,6729,360735589,96915,5608,1,431154,3618268,5
7727,KBN,10,corner,12,0,0,stock,h3g2,8258466381,30519605256798,30519949630012,8014093167,8258,6464,343689405,156624,4226,1,901417,0,22
7727,KBN,10,corner,13,0,1,corner,f1e3,6464804507,30519950074216,30520120828282,6394050441,8014,6464,170404171,95493,4887,1,772512,5781175,7
7727,KBN,10,corner,14,0,0,stock,g2f2,8014093167,30520121241740,30521214693357,7020641550,8014,6394,1085319949,95542,3846,1,1186410,2634570,4
7727,KBN,10,corner,15,0,1,corner,e3c4,6394050441,30521215248687,30521627553386,6081745742,7020,6394,400995792,113389,5828,1,864657,4582186,10
7727,KBN,10,corner,16,0,0,stock,f2e1,7020641550,30521628091259,30521994600510,6754132299,7020,6081,362319301,103295,6149,1,387258,3769784,15
7727,KBN,10,corner,17,0,1,corner,e4f3,6081745742,30521995034239,30523497539343,4679240638,6754,6081,1489921973,102243,0,1,785452,4962444,9
7727,KBN,10,corner,18,0,0,stock,e1d1,6754132299,30523497954654,30523829264617,6522822336,6754,4679,330793197,93349,3996,1,714978,5922115,10
7727,KBN,10,corner,19,0,1,corner,f3e3,4679240638,30523829670824,30524122281261,4486630201,6522,4679,292346947,122973,4937,1,638084,2163237,15
7727,KBN,10,corner,20,0,0,stock,d1c2,6522822336,30524122709832,30524395623652,6349908516,6522,4486,268993371,116494,4386,1,779353,5139858,8
7727,KBN,10,corner,21,0,1,corner,c4d2,4486630201,30524396130489,30524788841315,4193919375,6349,4486,392438653,94241,4827,1,356472,3735834,5
7727,KBN,10,corner,22,0,0,stock,c2c3,6349908516,30524789267381,30524975451443,6263724454,6349,4193,182179928,97716,3755,1,757159,2609904,11
7727,KBN,10,corner,23,0,1,corner,d6c5,4193919375,30524975957459,30525626037193,3643839641,6263,4193,646100367,117104,6039,1,623060,3881210,3
7727,KBN,10,corner,24,0,0,stock,c3c2,6263724454,30525626582548,30525870301289,6120005713,6263,3643,239660563,111096,5498,1,760706,5262872,6
7727,KBN,10,corner,25,0,1,corner,c5d4,3643839641,30525870859303,30526042518647,3572180297,6120,3643,171434013,115903,6940,1,751310,4987321,4
7727,KBN,10,corner,26,0,0,stock,c2c1,6120005713,30526042958014,30526220186424,6042777303,6120,3572,173282824,92408,4827,1,736850,4919500,7
7727,KBN,10,corner,27,0,1,corner,e3d3,3572180297,30526221176724,30526572388049,3320968972,6042,3572,350182720,207469,25108,1,1233190,2536204,8
7727,KBN,10,corner,28,0,0,stock,c1d1,6042777303,30526572802478,30526770611576,5944968205,6042,3320,193939961,91997,4157,1,579076,3088017,4
7727,KBN,10,corner,29,0,1,corner,d4f2,3320968972,30526771044393,30527896233093,2295780272,5944,3320,1124663319,98237,4687,1,586607,4813691,4
7727,KBN,10,corner,30,0,0,stock,d1c1,5944968205,30527896654062,30528310138197,5631484070,5944,2295,409448403,119729,4917,1,822556,3198472,7
7727,KBN,10,corner,31,0,1,corner,d2c4,2295780272,30528310617694,30528528468824,2177929142,5631,2295,217690896,99358,5178,1,621369,5212066,10
7727,KBN,10,corner,32,0,0,stock,c1d1,5631484070,30528528914329,30528971789432,5288608967,5631,2177,442645579,100610,4367,1,638383,2958944,4
7727,KBN,10,corner,33,0,1,corner,c4e3,2177929142,30528972237091,30529120019001,2130147232,5288,2177,147625325,93890,4547,1,307009,3629595,3
7727,KBN,10,corner,34,0,0,stock,d1c1,5288608967,30529120440801,30529301214910,5207834858,5288,2130,180617327,99378,4607,1,559465,3430979,10
7727,KBN,10,corner,35,0,1,corner,d3c3,2130147232,30529301618713,30529454579982,2077185963,5207,2130,152833996,100971,4286,1,508778,2211880,3
7727,KBN,10,corner,36,0,0,stock,c1b1,5207834858,30529455198075,30529681808713,5081224220,5207,2077,226344179,93991,4326,1,864469,4682296,5
7727,KBN,10,corner,37,0,1,corner,c3b3,2077185963,30529682223022,30529854537690,2004871295,5081,2077,171804049,101632,4827,1,671981,5641597,5
7727,KBN,10,corner,38,0,0,stock,b1c1,5081224220,30529855065449,30530003205469,5033084200,5081,2004,147792279,102943,5208,1,851161,4797017,8
7727,KBN,10,corner,39,0,1,corner,f2e1,2004871295,30530003609563,30530146272927,1962207931,5033,2004,138648955,102873,3976,1,744439,4222480,9
7727,KBN,10,corner,40,0,0,stock,c1b1,5033084200,30530146881466,30530287047043,4992918623,5033,1962,137956448,118286,6410,1,1203398,6548690,24
7727,KBN,10,corner,41,0,1,corner,e1d2,1962207931,30530287613169,30530431990946,1917830154,4992,1962,140256782,145166,6250,1,1045145,4190251,22
7727,KBN,10,corner,42,0,0,stock,b1a1,4992918623,30530432443332,30530437190865,5088171090,4992,1917,4626113,105187,4537,1,528357,3423127,9
7727,KBN,10,corner,43,0,1,corner,e3c2,1917830154,30530437489041,30530440643554,2014675641,5088,1917,3080466,78457,4137,1,375310,2410477,7
7727,KBN,10,corner,44,0,0,stock,a1b1,5088171090,30530440881269,30530441445422,5187606937,5088,2014,401890,77836,2614,2,393456,0,65
7727,KBN,10,corner,45,0,1,corner,c2a3,2014675641,30530441582867,30530441950607,2114307901,5187,2014,326197,69324,0,1,146899,326197,1
7727,KBN,10,corner,46,0,0,stock,b1a1,5187606937,30530442066129,30530442389703,5287283363,5187,2114,175462,68833,1933,2,296082,0,65
7727,KBN,10,corner,47,0,1,corner,d2c3,2114307901,30530442484384,30530442742290,2214049995,5287,2114,221720,65027,0,1,101201,221720,1
7727,KBN,10,stock,0,0,0,stock,e1f2,10000000000,30484803230545,30485142911253,9760319292,10000,10000,339247274,168972,0,1,922217,4770887,12
7727,KBN,10,stock,1,0,1,stock,b3d4,10000000000,30485143309468,30485510196433,9733113035,9760,10000,366450206,161551,4376,1,773634,4296791,12
7727,KBN,10,stock,2,0,0,stock,f2g3,9760319292,30485510660797,30485880854608,9490125481,9760,9733,369991054,124466,4336,1,610099,5164605,4
7727,KBN,10,stock,3,0,1,stock,d3e4,9733113035,30485881387514,30486256219041,9458281508,9490,9733,374345485,91487,5237,1,990528,2450786,10
7727,KBN,10,stock,4,0,0,stock,g3g4,9490125481,30486256669093,30487730354139,8116440435,9490,9458,1465278066,121521,4236,1,765012,3175447,7
7727,KBN,10,stock,5,0,1,stock,b4d2,9458281508,30487730694718,30487986523824,9302452402,8116,9458,255643246,104115,4106,1,488839,5166458,4
7727,KBN,10,stock,6,0,0,stock,g4h4,8116440435,30487986888909,30488212605652,7990723692,8116,9302,225506283,88863,4016,1,557401,4992739,8
7727,KBN,10,stock,7,0,1,stock,d4e6,9302452402,30488212967022,30489104900105,8510519319,7990,9302,891569893,82753,4146,1,592786,2914669,7
7727,KBN,10,stock,8,0,0,stock,h4g3,7990723692,30489105450498,30489759932849,7436241341,7990,8510,654033306,112127,6660,1,1038831,2400261,13
7727,KBN,10,stock,9,0,1,stock,d2e1,8510519319,30489760360778,30490059881613,8310998484,7436,8510,299170319,94761,4036,1,800906,3495155,11
7727,KBN,10,stock,10,0,0,stock,g3g4,7436241341,30490060313308,30490721095842,6875458807,7436,8310,656259919,94932,4356,1,506506,3561764,5
7727,KBN,10,stock,11,0,1,stock,e1f2,8310998484,30490721511143,30490955547733,8176961894,6875,8310,233597928,118517,6159,1,804399,5890088,5
7727,KBN,10,stock,12,0,0,stock,g4h3,6875458807,30490955988071,30491148258399,6783188479,6875,8176,192040161,94711,4366,1,650679,3862863,6
7727,KBN,10,stock,13,0,1,stock,e4f3,8176961894,30491148670615,30491467367489,7958265020,6783,8176,318306737,343622,0,1,756310,3333473,6
7727,KBN,10,stock,14,0,0,stock,h3h2,6783188479,30491467819003,30493378162244,4972845238,6783,7958,1906203004,96113,4507,1,618032,4053427,11
7727,KBN,10,stock,15,0,1,stock,f2g3,7958265020,30493378578316,30494013028484,7423814852,4972,7958,634021883,96945,0,1,783538,5415910,8
7727,KBN,10,stock,16,0,0,stock,h2h1,4972845238,30494013428982,30494183796454,4902477766,4972,7423,169405500,96564,4096,1,774196,3006486,9
7727,KBN,10,stock,17,0,1,stock,g3f2,7423814852,30494184271914,30494564227655,7143859111,4902,7423,378961234,99909,4998,1,829950,3590147,8
7727,KBN,10,stock,18,0,0,stock,h1h2,4902477766,30494564637377,30494716490344,4850624799,4902,7143,151667317,121411,0,1,577470,3332021,7
7727,KBN,10,stock,19,0,1,stock,e6f4,7143859111,30494716935429,30495442899061,6517895479,4850,7143,725213992,97486,4957,1,1000129,2924813,13
7727,KBN,10,stock,20,0,0,stock,h2h1,4850624799,30495443322233,30495787141174,4606805858,4850,6517,343479245,100320,0,1,723169,4673933,7
7727,KBN,10,stock,21,0,1,stock,f4e2,6517895479,30495787508442,30496370581133,6034822788,4606,6517,582455378,95933,0,1,806373,4487655,11
7727,KBN,10,stock,22,0,0,stock,h1h2,4606805858,30496371010645,30496865436516,4212379987,4606,6034,491120832,97245,4046,1,748466,7518448,9
7727,KBN,10,stock,23,0,1,stock,f2g3,6034822788,30496866010314,30497268287723,5732545379,4212,6034,401978649,102753,5548,1,851473,5832341,8
7727,KBN,10,stock,24,0,0,stock,h2h1,4212379987,30497268868400,30497445999738,4135248649,4212,5732,173148243,117005,5788,1,887384,2981158,8
7727,KBN,10,stock,25,0,1,stock,e2d4,5732545379,30497446397502,30498096603676,5182339205,4135,5732,649759111,94481,4717,1,734205,7233992,10
7727,KBN,10,stock,26,0,0,stock,h1g1,4135248649,30498097033768,30498370343935,3961938482,4135,5182,272975820,99949,4437,1,743307,2849632,10
7727,KBN,10,stock,27,0,1,stock,g3f2,5182339205,30498370780618,30498710339217,4942780606,3961,5182,338790600,100921,5067,1,689159,5067440,9
7727,KBN,10,stock,28,0,0,stock,g1h2,3961938482,30498710798794,30499048143636,3724593640,3961,4942,337066046,100770,4717,1,647987,5066589,6
7727,KBN,10,stock,29,0,1,stock,d4f5,4942780606,30499048562231,30499249263311,4842079526,3724,4942,200281736,99368,4697,1,789167,3297880,7
7727,KBN,10,stock,30,0,0,stock,h2h1,3724593640,30499249869257,30499369912160,3704550737,3724,4842,119713978,123425,7160,1,904671,5956551,6
7727,KBN,10,stock,31,0,1,stock,f5d4,4842079526,30499370512167,30499800571049,4512020644,3704,4842,428684006,121821,7321,1,1039343,5301840,8
7727,KBN,10,stock,32,0,0,stock,h1h2,3704550737,30499802202526,30500000730590,3606022673,3704,4512,198116294,125016,11557,1,1977731,5617821,7
7727,KBN,10,stock,33,0,1,stock,d4e2,4512020644,30500001174654,30500720690062,3892505236,3606,4512,715418729,122923,0,1,819204,2764363,10
7727,KBN,10,stock,34,0,0,stock,h2h3,3606022673,30500721142118,30500933986717,3493178074,3606,3892,212433107,107180,5137,1,809269,2756662,8
7727,KBN,10,stock,35,0,1,stock,f2e1,3892505236,30500934400355,30501259415700,3667489891,3493,3892,324306776,101251,0,1,1085680,9352353,16
7727,KBN,10,stock,36,0,0,stock,h3h2,3493178074,30501260283106,30501392196981,3461264199,3493,3667,127953956,121771,6190,1,523231,3559410,5
7727,KBN,10,stock,37,0,1,stock,e1g3,3667489891,30501392788204,30501501353764,3658924331,3461,3667,108316179,120019,0,1,814636,3210710,9
7727,KBN,10,stock,38,0,0,stock,h2h1,3461264199,30501501827872,30501632618749,3430473322,3461,3658,130536561,103835,4627,1,680655,6085469,5
7727,KBN,10,stock,39,0,1,stock,g3f2,3658924331,30501633187488,30501925827667,3466284152,3430,3658,289893231,114160,6810,1,983447,4924187,7
7727,KBN,10,stock,40,0,0,stock,h1h2,3430473322,30501926391219,30502124088376,3332776165,3430,3466,197297616,120349,6570,1,935706,5448278,9
7727,KBN,10,stock,41,0,1,stock,e2g3,3466284152,30502124882552,30502261835461,3429331243,3332,3466,132855768,120991,8242,1,1219698,2939385,13
7727,KBN,10,stock,42,0,0,stock,h2h3,3332776165,30502262250661,30502365520764,3329506062,3332,3429,102968126,103224,4196,1,690601,5645192,5
7727,KBN,10,stock,43,0,1,stock,g3h5,3429331243,30502366010957,30502579926896,3315415304,3329,3429,210240738,102594,5027,1,794716,5844250,5
7727,KBN,10,stock,44,0,0,stock,h3h2,3329506062,30502580602646,30502688733085,3321375623,3329,3315,107868783,154541,8272,1,809145,3199223,7
7727,KBN,10,stock,45,0,1,stock,f2b6,3315415304,30502689158110,30502926527788,3178045626,3321,3315,237074155,100039,6099,1,668679,2696813,9
7727,KBN,10,stock,46,0,0,stock,h2h1,3321375623,30502927053964,30503086532083,3261897504,3321,3178,155549690,115663,7621,1,779391,4792460,8
7727,KBN,10,stock,47,0,1,stock,h5g3,3178045626,30503086956667,30503306879177,3058123116,3261,3178,215989250,98397,5037,1,678542,4908543,6
7727,KBN,10,stock,48,0,0,stock,h1h2,3261897504,30503307436790,30503422300790,3247033504,3261,3058,114604130,123745,8362,1,793094,4410000,7
7727,KBN,10,stock,49,0,1,stock,g3e2,3058123116,30503422719065,30503765347752,2815494429,3247,3058,342384861,101241,5158,1,615609,5114651,4
7727,KBN,10,stock,50,0,0,stock,h2h3,3247033504,30503765793127,30503928486650,3184339981,3247,2815,162331805,104285,5288,1,745372,6066231,7
7727,KBN,10,stock,51,0,1,stock,b6d8,2815494429,30503929118414,30504212683603,2631929240,3184,2815,283147737,122603,7371,1,1024516,2702021,10
7727,KBN,10,stock,52,0,0,stock,h3h2,3184339981,30504213140436,30504319989170,3177491247,3184,2631,102841308,104475,4567,1,868297,2726117,6
7727,KBN,10,stock,53,0,1,stock,d8h4,2631929240,30504320424270,30504668124856,2384228654,3177,2631,347352479,103074,0,1,724541,3572881,7
7727,KBN,10,stock,54,0,0,stock,h2h3,3177491247,30504668697111,30504781824831,3164363527,3177,2384,110743859,155682,0,1,964470,5258966,11
7727,KBN,10,stock,55,0,1,stock,h4e1,2384228654,30504782415373,30504937643696,2329000331,3164,2384,154792143,127991,0,1,987482,5608177,8
7727,KBN,10,stock,56,0,0,stock,h3h2,3164363527,30504938286376,30505344724745,2857925158,3164,2329,406046804,131165,0,1,997219,5711030,6
7727,KBN,10,stock,57,0,1,stock,e2d4,2329000331,30505345358202,30505564612715,2209745818,2857,2329,218678916,125968,7250,1,1146642,2457627,9
7727,KBN,10,stock,58,0,0,stock,h2h1,2857925158,30505565206653,30505702017260,2821114551,2857,2209,136548558,125887,0,1,831652,2817723,6
7727,KBN,10,stock,59,0,1,stock,e1h4,2209745818,30505702519901,30506190367832,1821897887,2821,2209,487580801,108091,0,1,732344,5500326,6
7727,KBN,10,stock,60,0,0,stock,h1g1,2821114551,30506191070011,30506310032950,2802151612,2821,1821,118696196,135593,9364,1,940634,4741824,5
7727,KBN,10,stock,61,0,1,stock,h4g3,1821897887,30506310427379,30506871373297,1360951969,2802,1821,548705876,101832,4386,1,628227,5427808,6
7727,KBN,10,stock,62,0,0,stock,g1f1,2802151612,30506871857100,30507060903591,2713105121,2802,1360,188617521,109233,5529,1,881638,3975792,8
7727,KBN,10,stock,63,0,1,stock,g3h4,1360951969,30507061499251,30507288183041,1234268179,2713,1360,226304299,123034,6790,1,945170,2324137,7
7727,KBN,10,stock,64,0,0,stock,f1g1,2713105121,30507288612273,30507409752305,2691965089,2713,1234,117319282,129043,4226,1,643600,3224882,5
7727,KBN,10,stock,65,0,1,stock,h4g3,1234268179,30507410166704,30507881145895,863288988,2691,1234,470674356,105727,5849,1,680604,5685893,7
7727,KBN,10,stock,66,0,0,stock,g1f1,2691965089,30507881797890,30508206083575,2467679404,2691,863,323968059,107861,4848,1,944621,6060963,7
7727,KBN,10,stock,67,0,1,stock,d4f5,863288988,30508206638044,30508415911278,754015754,2467,863,208990399,150565,6640,1,924838,5153078,6
7727,KBN,10,stock,68,0,0,stock,f1g1,2467679404,30508416386318,30508622518569,2361547153,2467,754,205990642,103194,4837,1,482020,3480473,3
7727,KBN,10,stock,69,0,1,stock,g3e5,754015754,30508622941280,30509006119355,470837679,2361,754,381029611,111547,8472,1,637541,4893650,5
7727,KBN,10,stock,70,0,0,stock,g1f1,2361547153,30509006696137,30509091508807,2376734483,2361,470,84615108,151496,6890,1,733375,5103915,3
7727,KBN,10,stock,71,0,1,stock,e5d4,470837679,30509092136205,30509368431436,294542448,2376,470,271128813,126929,6290,1,348331,3675894,6
7727,KBN,10,stock,72,0,0,stock,f1e1,2376734483,30509368921588,30509591456799,2254199272,2376,294,207618539,172888,14589136,2,816069,4255419,7
7727,KBN,10,stock,73,0,1,stock,d4c3,294542448,30509591921774,30509762232019,224232203,2254,294,170054700,131356,0,1,658841,4018395,9
7727,KBN,10,stock,74,0,0,stock,e1d1,2254199272,30509762797944,30509867726763,2249270453,2254,224,101003868,122723,0,1,816379,5161931,6
7727,KBN,10,stock,75,0,1,stock,f5d4,224232203,30509868176545,30509922499777,269908971,2249,224,54132021,109073,4817,1,322511,3656785,6
7727,KBN,10,stock,76,0,0,stock,d1c1,2249270453,30509922976470,30510030027810,2242219113,2249,269,106729302,187790,0,1,754496,5045938,6
7727,KBN,10,stock,77,0,1,stock,f3e4,269908971,30510030853283,30510186417944,214344310,2242,269,155196089,190784,6460,1,1110067,4797698,5
7727,KBN,10,stock,78,0,0,stock,c1b1,2242219113,30510187041686,30510423753135,2105507664,2242,214,236364312,134100,0,1,986622,4950426,7
7727,KBN,10,stock,79,0,1,stock,c3b4,214344310,30510424313352,30510485163427,253494235,2105,214,60656946,125888,6580,1,451974,3502025,5
7727,KBN,10,stock,80,0,0,stock,b1a2,2105507664,30510485704085,30510741243842,1949967907,2105,253,254728675,190484,0,1,781776,6287971,8
7727,KBN,10,stock,81,0,1,stock,e4e5,253494235,30510741664771,30510887105219,208053787,1949,253,141547444,130094,0,1,591974,2332670,5
7727,KBN,10,stock,82,0,0,stock,a2b1,1949967907,30510887769031,30511019217437,1918519501,1949,208,127517156,133209,0,1,947683,4222560,6
7727,KBN,10,stock,83,0,1,stock,e5f6,208053787,30511020229399,30511061657327,266625859,1918,208,41228082,220418,0,1,366718,3677786,7
7727,KBN,10,stock,84,0,0,stock,b1c1,1918519501,30511062261810,30511330551689,1750229622,1918,266,264317662,133639,0,1,909486,5730589,5
7727,KBN,10,stock,85,0,1,stock,f6g6,266625859,30511330990705,30511418465163,279151401,1750,266,87253735,197355,4577,1,636750,4762164,4
7727,KBN,10,stock,86,0,0,stock,c1b2,1750229622,30511419003207,30511564954964,1704277865,1750,279,145786833,105267,4807,1,682449,4908293,4
7727,KBN,10,stock,87,0,1,stock,g6g7,279151401,30511565372037,30511726620421,217903017,1704,279,157374050,109053,4516,1,539535,2473510,4
7727,KBN,10,stock,88,0,0,stock,b2c1,1704277865,30511727277733,30511823607252,1707948346,1704,217,96140914,132968,7581,1,863458,4539262,4
7727,KBN,10,stock,89,0,1,stock,g7g6,217903017,30511824132953,30511948370243,193665727,1707,217,124026569,104836,5128,1,243683,3710736,4
7727,KBN,10,stock,90,0,0,stock,c1b2,1707948346,30511949011100,30512340881849,1416077597,1707,193,387981619,111857,5158,1,902866,2843062,5
7727,KBN,10,stock,91,0,1,stock,g6g7,193665727,30512341368406,30512450803940,184230193,1416,193,105452857,109223,4927,1,685603,2469284,4
7727,KBN,10,stock,92,0,0,stock,b2a2,1416077597,30512451633970,30512701620710,1266090857,1416,184,249746442,167510,0,1,1158269,4353555,5
7727,KBN,10,stock,93,0,1,stock,b4a5,184230193,30512702088680,30512806513355,179805518,1266,184,104226227,274469,5028,1,601418,5510602,3
7727,KBN,10,stock,94,0,0,stock,a2b2,1266090857,30512806975836,30512866159000,1306907693,1266,179,58936215,119007,5539,1,717082,4794713,21
7727,KBN,10,stock,95,0,1,stock,d4b5,179805518,30512866570054,30512938999511,207376061,1306,179,72135982,108182,4376,1,687345,0,26
7727,KBN,10,stock,96,0,0,stock,b2c2,1306907693,30512939931133,30512953010927,1393827899,1306,207,12736073,295210,5699,1,1241220,3752008,46
7727,KBN,10,stock,97,0,1,stock,g7g6,207376061,30512953600498,30512964480166,296496393,1393,207,10610242,137846,4406,1,848714,2194214,52
7727,KBN,10,stock,98,0,0,stock,c2d1,1393827899,30512964778922,30512965242444,1493364377,1393,296,407067,87461,3405,1,323793,302631,1
7727,KBN,10,stock,99,0,1,stock,a5b4,296496393,30512965363926,30512965815541,396044778,1493,296,304938,85007,0,2,301107,68843,66
7727,KBN,10,table,0,0,0,stock,e1f2,10000000000,30477361876741,30477659659566,9802217175,10000,10000,297434269,131766,6414371,2,736819,5813974,11
7727,KBN,10,table,1,0,1,table,b3d2,10000000000,30477660055037,30477666417254,10093637783,9802,10000,6335402,6378036,28082,1,6378036,28082,1
7727,KBN,10,table,2,0,0,stock,f2g3,9802217175,30477666545295,30477987416551,9581345919,9802,10093,317384413,73800,0,1,488349,8558978,15
7727,KBN,10,table,3,0,1,table,d3e3,10093637783,30477987811211,30477994100519,10187348475,9581,10093,6267410,6671333,23906,1,6671333,23906,1
7727,KBN,10,table,4,0,0,stock,g3g4,9581345919,30477994262611,30478308929857,9366678673,9581,10187,313236014,76444,0,1,627766,6686356,15
7727,KBN,10,table,5,0,1,table,b4d6,10187348475,30478309403355,30478317467144,10279284686,9366,10187,8038052,8522775,28102,1,8522775,28102,1
7727,KBN,10,table,6,0,0,stock,g4f5,9366678673,30478317673192,30478602195452,9182156413,9366,10279,282480938,116503,6246229,2,546648,7543544,16
7727,KBN,10,table,7,0,1,table,d2c4,10279284686,30478602597953,30478609105628,10372777011,9182,10279,6484995,6898612,25148,1,6898612,25148,1
7727,KBN,10,table,8,0,0,stock,f5g4,9182156413,30478609286028,30478940532357,8950910084,9182,10372,330955501,74842,0,1,449089,6710732,10
7727,KBN,10,table,9,0,1,table,c4b6,10372777011,30478940961849,30478946468938,10467269922,8950,10372,5486405,5926982,22774,1,5926982,22774,1
7727,KBN,10,table,10,0,0,stock,g4h3,8950910084,30478946627605,30479276175105,8721362584,8950,10467,329243346,83065,5294699,2,449270,5377764,11
7727,KBN,10,table,11,0,1,table,e3f3,10467269922,30479276579259,30479283316607,10560532574,8721,10467,6713745,7130227,356222,2,7130227,356222,2
7727,KBN,10,table,12,0,0,stock,h3h4,8721362584,30479283906539,30479804870612,8300398511,8721,10560,516997062,111988,0,1,542568,4091645,5
7727,KBN,10,table,13,0,1,table,d6f4,10560532574,30479805405191,30479811372668,10654565097,8300,10560,5944299,6489983,25407,1,6489983,25407,1
7727,KBN,10,table,14,0,0,stock,h4h5,8300398511,30479811526668,30480062896759,8149028420,8300,10654,251087814,81171,0,1,403482,4427556,6
7727,KBN,10,table,15,0,1,table,b6d5,10654565097,30480063311549,30480068928262,10748948384,8149,10654,5594816,6021152,23946,1,6021152,23946,1
7727,KBN,10,table,16,0,0,stock,h5h4,8149028420,30480069115041,30480406330301,7911813160,8149,10748,336910695,84796,2815311,2,476551,6880305,6
7727,KBN,10,table,17,0,1,table,d5f6,10748948384,30480407107302,30480415485190,10840570496,7911,10748,8348997,9137503,32648,1,9137503,32648,1
7727,KBN,10,table,18,0,0,stock,h4h3,7911813160,30480415726531,30481260373867,7167165824,7911,10840,840664653,91958,4155459,2,549909,4247417,10
7727,KBN,10,table,19,0,1,table,f6e4,10840570496,30481260845242,30481266338621,10935077117,7167,10840,5467498,5949668,28051,1,5949668,28051,1
7727,KBN,10,table,20,0,0,stock,h3h4,7167165824,30481266497618,30481759469052,6774194390,7167,10935,492634223,79028,0,1,460947,5498263,7
7727,KBN,10,table,21,0,1,table,f4g3,10935077117,30481759896211,30481767119064,11027854264,6774,10935,7200983,7639317,24897,1,7639317,24897,1
7727,KBN,10,table,22,0,0,stock,h4h5,6774194390,30481767298132,30482187623671,6453868851,6774,11027,416406867,84706,0,1,439656,4680443,14
7727,KBN,10,table,23,0,1,table,f3f4,11027854264,30482188083458,30482195892847,11120044875,6453,11027,7783422,7855109,29324,1,7969770,29324,1
7727,KBN,10,table,24,0,0,stock,h5g6,6453868851,30482196172625,30482687683694,6062357782,6453,11120,490743128,97816,3773820,2,484084,3821491,7
7727,KBN,10,table,25,0,1,table,g3h4,11120044875,30482688231202,30482692272481,11216003596,6062,11120,4013298,4226335,31217,1,4226335,31217,1
7727,KBN,10,table,26,0,0,stock,g6h5,6062357782,30482692453111,30482864432584,5990378309,6062,11216,171703337,264404,3292923,2,441650,7558817,6
7727,KBN,10,table,27,0,1,table,h4d8,11216003596,30482864891229,30482868809665,11312085160,5990,11216,3884505,4354696,35934,1,4354696,35934,1
7727,KBN,10,table,28,0,0,stock,h5g6,5990378309,30482868953089,30483405412790,5553918608,5990,11312,528254824,91777,0,2,395782,3661993,7
7727,KBN,10,table,29,0,1,table,e4d6,11312085160,30483405866688,30483411918251,11406033597,5553,11312,6026721,6490503,28022,1,6490503,28022,1
7727,KBN,10,table,30,0,0,stock,g6h6,5553918608,30483412110208,30483625165166,5440863650,5553,11406,209253451,85127,0,1,249281,3887690,5
7727,KBN,10,table,31,0,1,table,f4f5,11406033597,30483625626745,30483631603486,11500056856,5440,11406,5954103,6424916,24336,1,6424916,24336,1
7727,KBN,10,table,32,0,0,stock,h6h5,5440863650,30483631770455,30483908929178,5263704927,5440,11500,276843068,83194,0,1,338605,4228088,4
7727,KBN,10,table,33,0,1,table,d6e8,11500056856,30483909321854,30483914817346,11594561364,5263,11500,5470912,5873773,26890,1,5873773,26890,1
7727,KBN,10,table,34,0,0,stock,h5h6,5263704927,30483914991276,30484066763681,5211932522,5263,11594,149157078,84266,0,1,345844,7435309,5
7727,KBN,10,table,35,0,1,table,d8g5,11594561364,30484067169638,30484071858644,11689872358,5211,11594,4690849,5108141,23705,1,5108141,23705,1
7727,KBN,10,table,36,0,0,stock,h6h7,5211932522,30484072056900,30484235441621,5148547801,5211,11689,163182285,78797,0,1,238046,3941911,5
7727,KBN,10,table,37,0,1,table,f5f6,11689872358,30484235880957,30484241079094,11784674221,5148,11689,5175101,5624241,25518,1,5624241,25518,1
7727,KBN,10,table,38,0,0,stock,h7g8,5148547801,30484241261036,30484393286748,5096522089,5148,11784,151666330,85907,2686649,2,526234,2734109,14
7727,KBN,10,table,39,0,1,table,g5h6,11784674221,30484393888087,30484401159822,11877402486,5096,11784,7245539,7858804,28974,1,7858804,28974,1
7727,KBN,10,table,40,0,0,stock,g8h7,5096522089,30484401361574,30484540863854,5057019809,5096,11877,138945379,107550,2535873,2,743431,2643423,33
7727,KBN,10,table,41,0,1,table,f6g5,11877402486,30484541447396,30484546772333,11972077549,5057,11877,5296752,5892301,31928,1,5892301,31928,1
7727,KBN,10,table,42,0,0,stock,h7g8,5057019809,30484547004751,30484572854565,5131169995,5057,11972,25627904,107100,0,1,438936,4996405,8
7727,KBN,10,table,43,0,1,table,g5g6,11972077549,30484573375013,30484579208750,12066243812,5131,11972,5812853,6345327,23725,1,6345327,23725,1
7727,KBN,10,table,44,0,0,stock,g8h8,5131169995,30484579438243,30484580046101,5230562137,5131,12066,489710,105076,384634,2,312997,489710,1
7727,KBN,10,table,45,0,1,table,h6g7,12066243812,30484580187933,30484585441923,12160989822,5230,12066,5255811,5429681,0,0,5429681,0,0
7727,KBN,10,table,46,0,0,stock,h8g8,5230562137,30484585623154,30484585927609,5330257682,5230,12160,218036,120661,0,1,197394,218036,1
7727,KBN,10,table,47,0,1,table,e8f6,12160989822,30484586088459,30484591325615,12255752666,5330,12160,5238876,5468048,0,0,5468048,0,0
7812,KBB,10,corner,0,2,0,stock,d8e8,10000000000,30527550618050,30527837820146,9812797904,10000,10000,286706132,193279,0,1,834795,5384143,8
7812,KBB,10,corner,1,2,1,corner,g5f6,10000000000,30527838286713,30528420336143,9517950570,9812,10000,578030341,138006,6320,1,793865,5377312,8
7812,KBB,10,corner,2,2,0,stock,e8d8,9812797904,30528420723212,30528771320785,9562200331,9812,9517,350318128,78938,25277,1,635247,3152854,6
7812,KBB,10,corner,3,2,1,corner,g4h3,9517950570,30528771714734,30529554969200,8834696104,9562,9517,782768387,97065,4396,1,847563,4143842,11
7812,KBB,10,corner,4,2,0,stock,d8e8,9562200331,30529555368998,30529872897969,9344671360,9562,8834,316935303,83835,73590,1,823379,4142720,7
7812,KBB,10,corner,5,2,1,corner,d6c7,8834696104,30529873230406,30530351143949,8456782561,9344,8834,473915749,69103,4437,1,630573,2663704,8
7812,KBB,10,corner,6,2,0,stock,e8f8,9344671360,30530351505289,30530591262045,9204914604,9344,8456,239180832,78557,5398,1,916810,4386785,16
7812,KBB,10,corner,7,2,1,corner,h3d7,8456782561,30530591630976,30530981548453,8166865084,9204,8456,388963579,75363,4076,1,1295332,4236130,18
7812,KBB,10,corner,8,2,0,stock,f8g8,9204914604,30530981950744,30531072986585,9213878763,9204,8166,90306834,80350,5027,1,1108251,5937348,35
7812,KBB,10,corner,9,2,1,corner,f6g6,8166865084,30531073518039,30531138776144,8201606979,9213,8166,64921615,80069,4807,1,849280,2360392,33
7812,KBB,10,corner,10,2,0,stock,g8h8,9213878763,30531139180298,30531140440250,9312618811,9213,8201,1198598,80610,5108,1,435930,1092950,1
7812,KBB,10,corner,11,2,1,corner,c7d6,8201606979,30531140587320,30531141546072,8300648227,9312,8201,781523,122854,0,2,362144,109294,66
7812,KBB,10,corner,12,2,0,stock,h8g8,9312618811,30531141670759,30531142033931,9412255639,9312,8300,321800,48462,0,1,132397,321800,1
7812,KBB,10,corner,13,2,1,corner,d7e6,8300648227,30531142202773,30531142659776,8400191224,9412,8300,320669,48863,0,2,339696,38748,66
7812,KBB,10,corner,14,2,0,stock,g8h8,9412255639,30531142775499,30531142909259,9512121879,9412,8400,98117,46399,0,1,122563,98117,1
7812,KBB,10,corner,15,2,1,corner,d6e5,8400191224,30531143014206,30531143466782,8499738648,9512,8400,310392,44416,0,2,275952,36234,66
7812,KBB,10,stock,0,2,0,stock,d8e8,10000000000,30531260358190,30531583819938,9776538252,10000,10000,323197676,128101,0,1,583580,3651518,8
7812,KBB,10,stock,1,2,1,stock,g5f6,10000000000,30531584246716,30532152303959,9531942757,9776,10000,567406251,134791,4376,1,608608,3364399,9
7812,KBB,10,stock,2,2,0,stock,e8d8,9776538252,30532152706551,30532526874786,9502370017,9776,9531,373696431,101952,4106,1,839433,3183279,6
7812,KBB,10,stock,3,2,1,stock,g4h3,9531942757,30532527465929,30532955991253,9203417433,9502,9531,428165326,91406,5298,1,956176,0,18
7812,KBB,10,stock,4,2,0,stock,d8e8,9502370017,30532956388977,30533257885575,9300873419,9502,9203,301046407,87982,6169,1,729649,3494514,6
7812,KBB,10,stock,5,2,1,stock,d6c7,9203417433,30533258293986,30533691830130,8869881289,9300,9203,433110909,86029,5700794,2,873553,5582118,8
7812,KBB,10,stock,6,2,0,stock,e8f8,9300873419,30533692209637,30533933623023,9159460033,9300,8869,240745993,76584,4917,1,697492,3691657,18
7812,KBB,10,stock,7,2,1,stock,h3d7,8869881289,30533934012806,30534338043465,8565850630,9159,8869,403117201,81462,4977,1,1278085,5857219,18
7812,KBB,10,stock,8,2,0,stock,f8g8,9159460033,30534338485095,30534442301101,9155644027,9159,8565,103351394,91476,6159,1,879811,5390102,35
7812,KBB,10,stock,9,2,1,stock,f6g6,8565850630,30534442832294,30534531192257,8577490667,9155,8565,87944985,92298,5889,1,924441,5023505,32
7812,KBB,10,stock,10,2,0,stock,g8h8,9155644027,30534531665975,30534533405994,9253904008,9155,8577,1669401,188131,5077,1,504012,1455412,1
7812,KBB,10,stock,11,2,1,stock,c7d6,8577490667,30534533664541,30534534815540,8676339668,9253,8577,988454,65568,3405,2,468079,0,65
7812,KBB,10,stock,12,2,0,stock,h8g8,9253904008,30534535019245,30534535413093,9353510160,9253,8676,345976,56634,3345,1,220609,276663,1
7812,KBB,10,stock,13,2,1,stock,d7e6,8676339668,30534535565291,30534536100550,8775804409,9353,8676,367688,53881,0,2,351826,40400,66
7812,KBB,10,stock,14,2,0,stock,g8h8,9353510160,30534536233329,30534536373859,9453369630,9353,8775,102743,49163,0,1,141481,102743,1
7812,KBB,10,stock,15,2,1,stock,d6e5,8775804409,30534536481700,30534536936309,8875349800,9453,8775,317662,46790,0,2,274401,37456,66
7812,KBB,10,table,0,2,0,stock,d8e8,10000000000,30526080723093,30526370630802,9810092291,10000,10000,289660079,126599,3535585,2,594449,2985634,8
7812,KBB,10,table,1,2,1,table,g4e6,10000000000,30526371097339,30526378184819,10092912520,9810,10000,7054215,7531136,35943,1,7531136,35943,1
7812,KBB,10,table,2,2,0,stock,e8d8,9810092291,30526378377537,30526736736118,9551733710,9810,10092,358028372,77596,5557982,2,508658,5635578,7
7812,KBB,10,table,3,2,1,table,g5f6,10092912520,30526737163316,30526742373922,10187701914,9551,10092,5184765,5622298,27922,1,5622298,27922,1
7812,KBB,10,table,4,2,0,stock,d8e8,9551733710,30526742530255,30527067618266,9326645699,9551,10187,324646482,61572,0,1,579033,5470051,6
7812,KBB,10,table,5,2,1,table,d6c7,10187701914,30527068084262,30527073591021,10282195155,9326,10187,5482059,5553486,26970,1,5553486,26970,1
7812,KBB,10,table,6,2,0,stock,e8f8,9326645699,30527073791190,30527314079732,9186357157,9326,10282,239484580,62494,0,1,992309,5238406,11
7812,KBB,10,table,7,2,1,table,e6d7,10282195155,30527314415053,30527318424154,10378186054,9186,10282,4010634,4355268,20991,1,4355268,20991,1
7812,KBB,10,table,8,2,0,stock,f8g8,9186357157,30527318584083,30527394041734,9210899506,9186,10378,75159525,55774,0,1,423409,5415981,40
7812,KBB,10,table,9,2,1,table,f6g6,10378186054,30527394522012,30527398510832,10474197234,9210,10378,3991585,4483579,22704,1,4483579,22704,1
7812,KBB,10,table,10,2,0,stock,g8h8,9210899506,30527398678603,30527399606008,9309972101,9210,10474,868716,79649,789067,2,157525,868716,1
7812,KBB,10,table,11,2,1,table,c7d6,10474197234,30527399731726,30527403822849,10570106111,9309,10474,4092676,4261878,0,0,4261878,0,0
7812,KBB,10,table,12,2,0,stock,h8g8,9309972101,30527403946904,30527404345850,9409573155,9309,10570,344354,79910,0,1,132758,344354,1
7812,KBB,10,table,13,2,1,table,d7e6,10570106111,30527404452560,30527408589672,10665968999,9409,10570,4138163,4289219,0,0,4289219,0,0
7812,KBB,10,table,14,2,0,stock,g8h8,9409573155,30527408704203,30527408881989,9509395369,9409,10665,131887,71867,0,1,121602,131887,1
7812,KBB,10,table,15,2,1,table,d6e5,10665968999,30527408990210,30527411209446,10763749763,9509,10665,2220002,2366039,0,0,2366039,0,0
~~~
