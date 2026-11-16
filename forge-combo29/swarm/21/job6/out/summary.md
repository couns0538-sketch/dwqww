| case | what the parser saw | parsed | expected | result |
|---|---|---|---|---|
| control_no_ucinewgame | parsed 30 from 'nodes 30' | 30 | 30 | ok |
| ucinewgame_before | parsed 30 from 'nodes 30' | 30 | 30 | ok |
| position_then_ucinewgame | parsed 20 from 'nodes 20' | 20 | 20 | ok |
| second_position_control | parsed 28 from 'nodes 28' | 28 | 28 | ok |
| PLANT-empty | correctly rejected: case 'PLANT-empty': NO `nodes N` line in the engine's answer; the check measured nothing | - | - | ok |
| PLANT-wrong | parsed 30 vs impossible expected 1030 | 30 | 1030 | ok (mismatch correctly reported) |

failures: none
=> CONFIRMS 30-F6 (with the parser proved non-vacuous)
