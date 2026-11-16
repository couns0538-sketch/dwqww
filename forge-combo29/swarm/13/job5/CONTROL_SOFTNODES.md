| plant | what it is | flagged as different? | should be | result |
|---|---|---|---|---|
| P0 identity | two identical runs | False | False | correctly NOT flagged as a difference |
| A nodes differ by 1 | identical but one node | True | True | FLAGGED |
| B depth differs | one depth shallower | True | True | FLAGGED |
| C score differs | cp 17 -> cp 18, same nodes | True | True | FLAGGED |
| D bestmove differs | d2d4 -> e2e4 | True | True | FLAGGED |
| E finished-depth | softnodes nodes 2574 vs go depth 6 nodes 1703 | True | True | FLAGGED |
| F finished-depth identity | 2574 vs 2574 | False | False | correctly NOT flagged |

Rule 1 verdict: the softnodes comparison catches every planted difference and does not flag identical runs, so its zero is a real measurement
