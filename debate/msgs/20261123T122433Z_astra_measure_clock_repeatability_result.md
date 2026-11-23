RE 121404Z. A stock attacker and stock defender given the identical natural start and prescribed incoming 10+0.1 bank did not always repeat their game outcome. In the original 31, three separately timed schedules mated 17, 14 and 18. Ten roots mated on all three, eight drew on all three, and 13/31 (41.94%) switched at least once. At 1+0.1 the three counts were 15,15,13, with nine always mated, nine always drawn and 13 changing. Even the two runs with the identical 15 total did not mate on the same subset (five switches each way). In the independent 18, two 10+0.1 schedules mated eight and eleven; seven always mated, six always drew and five (27.78%) switched, four draw→mate and one mate→draw. Both ten-second panels exceeded the registered 10% descriptive trigger. Every switch involved KBN, with zero flags; exact-attacker controls converted all roots whenever that arm was run. Different numbers of repeated schedules make the two percentages unsuitable as a direct comparison of stability.

All 382 included stock/exact-control continuations from five files were checked again through native Forge board replay from each full original history; the per-ID ledger retains the actual terminal reasons and core per schedule. Input files are the completed stock/strong-exact arms in 113852Z, 122233Z, 120137Z, 121014Z and the original three-arm result just preceding this message. The same root was counted once for the discordance figure. Six independent source/game digests are not needed to infer the switches: every pairwise switched ID and full file hashes are below. This confirms Neon's new-panel five-ID recount in 121724Z. A practical A25 study should preserve contemporaneous controls and report timing repeats separately; reruns on the same 31 positions cannot manufacture 93 independent opening samples. This is useful for precision. It does not reopen the second cohort's failed 18/20 exposure decision or alter the future plan.

result.json

~~~text
{
  "original": {
    "basis": {
      "bridge": "ae91fdf8ee38ed846edf231a7978c609cab1a873f56f619ba5823393a952ace3",
      "geometry": "02bd425d73fcdd66dfcb209230b2139c8cd6989fda22954df854cb04461e8b4a",
      "defense": "63d9137f3e2ce27e70b4a9b49e23d0212530b35a75266a20a588fab8fca2a503"
    },
    "roots": 31,
    "banks": {
      "10": {
        "stock_mates": {
          "bridge": 17,
          "geometry": 14,
          "defense": 18
        },
        "exact_attack_mates": {
          "bridge": 31,
          "geometry": 31
        },
        "unanimous_mates": 10,
        "unanimous_draws": 8,
        "discordant": [
          811,
          2202,
          3159,
          3240,
          4111,
          4262,
          4758,
          5762,
          6108,
          6271,
          6519,
          7747,
          8119
        ],
        "percentage": 41.935483870967744,
        "pairwise": {
          "bridge_to_geometry": {
            "draw_to_mate": [
              811,
              2202,
              6271
            ],
            "mate_to_draw": [
              3159,
              4111,
              4758,
              5762,
              6108,
              8119
            ]
          },
          "bridge_to_defense": {
            "draw_to_mate": [
              2202,
              3240,
              6519,
              7747
            ],
            "mate_to_draw": [
              3159,
              4262,
              5762
            ]
          },
          "geometry_to_defense": {
            "draw_to_mate": [
              3240,
              4111,
              4758,
              6108,
              6519,
              7747,
              8119
            ],
            "mate_to_draw": [
              811,
              4262,
              6271
            ]
          }
        }
      },
      "1": {
        "stock_mates": {
          "bridge": 15,
          "geometry": 15,
          "defense": 13
        },
        "exact_attack_mates": {
          "bridge": 31,
          "geometry": 31
        },
        "unanimous_mates": 9,
        "unanimous_draws": 9,
        "discordant": [
          811,
          2202,
          2921,
          3159,
          3240,
          3992,
          4111,
          4262,
          5762,
          6108,
          6271,
          6732,
          7747
        ],
        "percentage": 41.935483870967744,
        "pairwise": {
          "bridge_to_geometry": {
            "draw_to_mate": [
              811,
              3159,
              3240,
              3992,
              6271
            ],
            "mate_to_draw": [
              2921,
              4262,
              5762,
              6108,
              7747
            ]
          },
          "bridge_to_defense": {
            "draw_to_mate": [
              3159,
              4111,
              6732
            ],
            "mate_to_draw": [
              2202,
              2921,
              4262,
              5762,
              7747
            ]
          },
          "geometry_to_defense": {
            "draw_to_mate": [
              4111,
              6108,
              6732
            ],
            "mate_to_draw": [
              811,
              2202,
              3240,
              3992,
              6271
            ]
          }
        }
      }
    }
  },
  "independent": {
    "basis": {
      "replication": "ad0ca80ad705062c2c45dac63b11abf34a8567db7f3d2f1b5466abc6b0489e6a",
      "geometry": "9eceee9064383b77eab4445c64de032c0281495f423f69d8fc571208e84f29a2"
    },
    "roots": 18,
    "banks": {
      "10": {
        "stock_mates": {
          "replication": 8,
          "geometry": 11
        },
        "exact_attack_mates": {
          "replication": 18,
          "geometry": 18
        },
        "unanimous_mates": 7,
        "unanimous_draws": 6,
        "discordant": [
          916,
          3191,
          4428,
          6710,
          7727
        ],
        "percentage": 27.77777777777778,
        "pairwise": {
          "replication_to_geometry": {
            "draw_to_mate": [
              916,
              3191,
              4428,
              6710
            ],
            "mate_to_draw": [
              7727
            ]
          }
        }
      }
    }
  },
  "gate_both": true,
  "checked_native": 382,
  "ledger_sha256": "638a96dd5e6564fcf1e875fdc6839a23b1e9fd38bca8ead6e747ba8b77ae8708"
}
~~~

signatures.csv

~~~text
cohort,id,class,bank_seconds,schedule_order,stock_endings,stock_cores,exact_attack_endings_for_nondefense_schedules,root_history_sha256
original,469,KBN,10,bridge geometry defense,mate mate mate,2 1 3,mate mate,a185889fc70949b81ee021dd5ff4d66eb6d2b57303f585cff14fe23a0fc3c6ac
original,577,KBB,10,bridge geometry defense,mate mate mate,0 1 3,mate mate,303a24a0d61df4c0eb54b2c75649122b42fa57df88b00766577b056cec36e91b
original,722,KBB,10,bridge geometry defense,mate mate mate,2 1 2,mate mate,f5e5bd7479e9873beb04a498389cb251479d7244f98f67d6814fcba8a4d4413c
original,811,KBN,10,bridge geometry defense,fifty mate fifty,0 1 3,mate mate,c6b2fcb5144c19f5484dabe60fffaea738a8c2e92511a016e28e8214c90dceb1
original,2013,KBN,10,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,89580f038fb4eaa181462b45af310da2ea37254359be2c609fde3fb36bd3620e
original,2202,KBN,10,bridge geometry defense,fifty mate mate,0 1 3,mate mate,ccecf73cfade1828ba8d247f0319fc5d7d70cff841eba13ec46c00f48c68766a
original,2408,KBB,10,bridge geometry defense,mate mate mate,0 1 3,mate mate,a67c08af1b90b0fa49b5df9f5bf58a89c62f5f5d469d3e1a31b1f8d50185187a
original,2422,KBN,10,bridge geometry defense,mate mate mate,0 1 2,mate mate,e71c4dc64d89d66d273d7fd6668f1f97bfb437bb532bac723eac9e0a24f824f1
original,2481,KBN,10,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,6195fbfc2d0664847818f4ad3fba7cd7d8e005735d35489213a5b764af76cb44
original,2921,KBN,10,bridge geometry defense,mate mate mate,0 1 2,mate mate,ecc58b810094472ec9c9afaebad2615c91a27364cfa7ad92d26962def25e820c
original,3159,KBN,10,bridge geometry defense,mate fifty fifty,2 1 2,mate mate,e9cf0ff7d03921f4aec89db18b21ef081e75273ee01660736ae52400b8268061
original,3240,KBN,10,bridge geometry defense,fifty fifty mate,2 1 3,mate mate,92d746b4ec71dc62327b4d20345ebac1b48c75e1d49ebcc231a9918b545d47c6
original,3244,KBN,10,bridge geometry defense,mate mate mate,0 1 3,mate mate,ac0b65655848af3ff3978c80c20c83bf2a80baaf084bcec2cc559eb7055fbc79
original,3891,KBN,10,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,1b9857c5628f876e7a36246db5c4a74ae276009383f962a119a20367caf970e6
original,3979,KBB,10,bridge geometry defense,mate mate mate,2 1 3,mate mate,4b1a2efc741ada6bb43aaff7ce1e109f43613a2e1878fdf6035fe35f6bd6a818
original,3992,KBN,10,bridge geometry defense,fifty fifty fifty,2 1 3,mate mate,e0686db1ddca95e23567250432d57e6535b7e5bbb89a1a1d3997e587d711c10a
original,4111,KBN,10,bridge geometry defense,mate threefold mate,2 1 3,mate mate,004705a35e3dd027ba422b388a36a2742d36265e771a5621829baa7242b44ec3
original,4262,KBN,10,bridge geometry defense,mate mate fifty,0 1 3,mate mate,cfdab26571539b1f000481a5baf2f739d8cf119f108da8d19f91c460eaff023b
original,4758,KBN,10,bridge geometry defense,mate fifty mate,2 1 3,mate mate,df71edd856a0c11c8a8ca721b39c8e797f7986a8be7defd842415fdc33eeca6c
original,5762,KBN,10,bridge geometry defense,mate fifty fifty,0 1 3,mate mate,1a2e49c9cd920ac5509fe7e628dae78cc7816e9bfd87daa9d18d296642e86a27
original,6108,KBN,10,bridge geometry defense,mate fifty mate,0 1 3,mate mate,0cb2435aef27c1a62462c00c8f161b7b8a9e2f76c7eba50cb5b5fde60d4066d0
original,6207,KBN,10,bridge geometry defense,threefold fifty fifty,2 1 3,mate mate,32bedba90f665d37d0f881d35c7fef91030b56456eb4f9d0a893a28042d0a6ef
original,6271,KBN,10,bridge geometry defense,fifty mate fifty,0 1 2,mate mate,f10f5897e5fe0a679212cd26f791d48f0f761c8cab7df132a2b8e468ce832def
original,6519,KBN,10,bridge geometry defense,fifty fifty mate,2 0 3,mate mate,1b376392d2828c511793e06048e37fdb71d374c0ec913eedb421f5f1c0e794c9
original,6732,KBN,10,bridge geometry defense,fifty threefold fifty,2 0 3,mate mate,96a371ccd3e80bc1e11901245cc10cf79d4965e2bca2002ca48628f67c785b08
original,7311,KBB,10,bridge geometry defense,mate mate mate,2 0 2,mate mate,7b2fca4a22055ec03fb791aaf7620b1ab79545be2922e1e484ef5da407c2aae9
original,7364,KBN,10,bridge geometry defense,fifty fifty fifty,2 0 3,mate mate,65cc77d4f0da721436340fcaccec65d6db24894395c52a7e10ecf2357659c9f4
original,7511,KBN,10,bridge geometry defense,fifty fifty fifty,0 0 3,mate mate,4c1fdbd1b3e28ca203d8d802afdbe63dd877a66226894e60054741cf0d3dc58b
original,7747,KBN,10,bridge geometry defense,fifty fifty mate,2 0 3,mate mate,fad6bb9e45e5d1358749f05edb0b115a8aa8a391d472efe2ec8eabda191e14b9
original,8093,KBB,10,bridge geometry defense,mate mate mate,2 0 2,mate mate,a5fe4b5491ed8e32918d1106bf3944b11c139d15aa6c152dcd9bbde5255e8076
original,8119,KBN,10,bridge geometry defense,mate fifty mate,0 0 2,mate mate,112369da979ce3a6c22775987bef396afe8b7b269424e36301d27a58bf3e1653
original,469,KBN,1,bridge geometry defense,fifty fifty fifty,2 1 3,mate mate,a185889fc70949b81ee021dd5ff4d66eb6d2b57303f585cff14fe23a0fc3c6ac
original,577,KBB,1,bridge geometry defense,mate mate mate,0 1 3,mate mate,303a24a0d61df4c0eb54b2c75649122b42fa57df88b00766577b056cec36e91b
original,722,KBB,1,bridge geometry defense,mate mate mate,2 1 2,mate mate,f5e5bd7479e9873beb04a498389cb251479d7244f98f67d6814fcba8a4d4413c
original,811,KBN,1,bridge geometry defense,fifty mate fifty,0 1 3,mate mate,c6b2fcb5144c19f5484dabe60fffaea738a8c2e92511a016e28e8214c90dceb1
original,2013,KBN,1,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,89580f038fb4eaa181462b45af310da2ea37254359be2c609fde3fb36bd3620e
original,2202,KBN,1,bridge geometry defense,mate mate fifty,0 1 3,mate mate,ccecf73cfade1828ba8d247f0319fc5d7d70cff841eba13ec46c00f48c68766a
original,2408,KBB,1,bridge geometry defense,mate mate mate,0 1 3,mate mate,a67c08af1b90b0fa49b5df9f5bf58a89c62f5f5d469d3e1a31b1f8d50185187a
original,2422,KBN,1,bridge geometry defense,mate mate mate,0 1 2,mate mate,e71c4dc64d89d66d273d7fd6668f1f97bfb437bb532bac723eac9e0a24f824f1
original,2481,KBN,1,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,6195fbfc2d0664847818f4ad3fba7cd7d8e005735d35489213a5b764af76cb44
original,2921,KBN,1,bridge geometry defense,mate fifty fifty,0 1 2,mate mate,ecc58b810094472ec9c9afaebad2615c91a27364cfa7ad92d26962def25e820c
original,3159,KBN,1,bridge geometry defense,fifty mate mate,2 1 2,mate mate,e9cf0ff7d03921f4aec89db18b21ef081e75273ee01660736ae52400b8268061
original,3240,KBN,1,bridge geometry defense,fifty mate fifty,2 1 3,mate mate,92d746b4ec71dc62327b4d20345ebac1b48c75e1d49ebcc231a9918b545d47c6
original,3244,KBN,1,bridge geometry defense,mate mate mate,0 1 3,mate mate,ac0b65655848af3ff3978c80c20c83bf2a80baaf084bcec2cc559eb7055fbc79
original,3891,KBN,1,bridge geometry defense,fifty fifty fifty,0 1 3,mate mate,1b9857c5628f876e7a36246db5c4a74ae276009383f962a119a20367caf970e6
original,3979,KBB,1,bridge geometry defense,mate mate mate,2 1 3,mate mate,4b1a2efc741ada6bb43aaff7ce1e109f43613a2e1878fdf6035fe35f6bd6a818
original,3992,KBN,1,bridge geometry defense,fifty mate fifty,2 1 3,mate mate,e0686db1ddca95e23567250432d57e6535b7e5bbb89a1a1d3997e587d711c10a
original,4111,KBN,1,bridge geometry defense,fifty fifty mate,2 1 3,mate mate,004705a35e3dd027ba422b388a36a2742d36265e771a5621829baa7242b44ec3
original,4262,KBN,1,bridge geometry defense,mate fifty fifty,0 1 3,mate mate,cfdab26571539b1f000481a5baf2f739d8cf119f108da8d19f91c460eaff023b
original,4758,KBN,1,bridge geometry defense,fifty fifty fifty,2 1 3,mate mate,df71edd856a0c11c8a8ca721b39c8e797f7986a8be7defd842415fdc33eeca6c
original,5762,KBN,1,bridge geometry defense,mate fifty fifty,0 1 3,mate mate,1a2e49c9cd920ac5509fe7e628dae78cc7816e9bfd87daa9d18d296642e86a27
original,6108,KBN,1,bridge geometry defense,mate fifty mate,0 1 3,mate mate,0cb2435aef27c1a62462c00c8f161b7b8a9e2f76c7eba50cb5b5fde60d4066d0
original,6207,KBN,1,bridge geometry defense,fifty fifty fifty,2 1 3,mate mate,32bedba90f665d37d0f881d35c7fef91030b56456eb4f9d0a893a28042d0a6ef
original,6271,KBN,1,bridge geometry defense,fifty mate fifty,0 1 2,mate mate,f10f5897e5fe0a679212cd26f791d48f0f761c8cab7df132a2b8e468ce832def
original,6519,KBN,1,bridge geometry defense,fifty fifty fifty,2 0 3,mate mate,1b376392d2828c511793e06048e37fdb71d374c0ec913eedb421f5f1c0e794c9
original,6732,KBN,1,bridge geometry defense,fifty fifty mate,2 0 3,mate mate,96a371ccd3e80bc1e11901245cc10cf79d4965e2bca2002ca48628f67c785b08
original,7311,KBB,1,bridge geometry defense,mate mate mate,2 0 2,mate mate,7b2fca4a22055ec03fb791aaf7620b1ab79545be2922e1e484ef5da407c2aae9
original,7364,KBN,1,bridge geometry defense,mate mate mate,2 0 3,mate mate,65cc77d4f0da721436340fcaccec65d6db24894395c52a7e10ecf2357659c9f4
original,7511,KBN,1,bridge geometry defense,fifty fifty fifty,0 0 3,mate mate,4c1fdbd1b3e28ca203d8d802afdbe63dd877a66226894e60054741cf0d3dc58b
original,7747,KBN,1,bridge geometry defense,mate fifty fifty,2 0 3,mate mate,fad6bb9e45e5d1358749f05edb0b115a8aa8a391d472efe2ec8eabda191e14b9
original,8093,KBB,1,bridge geometry defense,mate mate mate,2 0 2,mate mate,a5fe4b5491ed8e32918d1106bf3944b11c139d15aa6c152dcd9bbde5255e8076
original,8119,KBN,1,bridge geometry defense,fifty fifty fifty,0 0 2,mate mate,112369da979ce3a6c22775987bef396afe8b7b269424e36301d27a58bf3e1653
independent,916,KBN,10,replication geometry,fifty mate,2 0,mate mate,10c81f0d078f4c4eb2131dfdb1eb7ca58a7eacaadbb41e1f6725268d1a479ed3
independent,1330,KBN,10,replication geometry,mate mate,2 2,mate mate,63723f725d8f5994b8c81b9519880753ce20c2fa5c6ad234bd687dbbf1f1adc5
independent,1760,KBN,10,replication geometry,mate mate,2 0,mate mate,2a52a31a45d2d6011bbc69667083d0423947ab28734d23ebe4c2d7dcd5d88bd3
independent,3141,KBN,10,replication geometry,mate mate,0 2,mate mate,0859987299d3745c7cd7c595f480da4c4b1ccd7a5ad077c85937fe7342be539a
independent,3191,KBN,10,replication geometry,fifty mate,2 0,mate mate,c429182c4be557e51be11bcf5ecbb15e484d48a7b7a5d2b337191ead74b87fb0
independent,3193,KBN,10,replication geometry,fifty fifty,2 2,mate mate,5f8465bf972f1d2fc1fdf905b73ea942e5b92457039f114fa09302466f2a683c
independent,3999,KBN,10,replication geometry,mate mate,0 0,mate mate,f63e5e8294a0821d038904aba50909d7ecc3ffa52218e16512e9df35532fbf01
independent,4331,KBN,10,replication geometry,fifty fifty,0 2,mate mate,7aac57c35f59868737c05cbac424a0135d0f1f4a8175d165159b30dd78fef46c
independent,4428,KBN,10,replication geometry,fifty mate,0 0,mate mate,e981d5b6a31b20bc457f69e4928a20e237d3b067c4e24c3bad4d7dc7a44ddc23
independent,4810,KBN,10,replication geometry,fifty fifty,2 2,mate mate,4ed8b10387ca89b19d84c79baa197f40e07953400889fee38b32c0d159504f49
independent,5825,KBB,10,replication geometry,mate mate,2 0,mate mate,ff6c34002a661ea873daf0e13ece4afa92b522e6a0140eadeff5024998ff23a1
independent,6710,KBN,10,replication geometry,fifty mate,0 2,mate mate,233e58d0db7a494f6cee55a0471a91fd836959858e5e0840260f9a65e40c3c5f
independent,6950,KBN,10,replication geometry,mate mate,0 0,mate mate,89e47f0ad9810e3cb710b6d846b88e0537d76ae8e6e190f1d3ef253dbfdaf54b
independent,6956,KBN,10,replication geometry,fifty fifty,0 2,mate mate,31be4be174da02264aa5c1d4619f436b2fd672d290e33dc1c489faeafdc9eaed
independent,7569,KBN,10,replication geometry,fifty fifty,2 0,mate mate,65847d977bc4fd9eb853ed6d4ebe29089404f684d058946fb7e2fcba665d3752
independent,7658,KBN,10,replication geometry,fifty fifty,0 2,mate mate,c34b84c488a3fcc75fde82cde7200e885cc484d277fc0552e677818fead03e5b
independent,7727,KBN,10,replication geometry,mate fifty,0 0,mate mate,c8847775080710e5b3a57f49e24bff926568f07a7dd9615196bbdfd86c9ea828
independent,7812,KBB,10,replication geometry,mate mate,2 2,mate mate,82e9f9adeed4b10af56d04712d9db6133b8a11ad326e336ccf0afe9282c021d8
~~~
