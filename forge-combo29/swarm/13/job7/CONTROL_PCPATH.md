| plant | what it is | flagged? | should be | result |
|---|---|---|---|---|
| P0 identity | identical runs | False | False | correct |
| A nodes +1 | one node differs | True | True | correct |
| B depth differs | one depth | True | True | correct |
| C score differs | one centipawn | True | True | correct |
| D bestmove differs | other move | True | True | correct |
| E mate vs cp | mate 3 instead of cp | True | True | correct |
| F legal move | g5h5 in this position | False | False | correct |
| G ILLEGAL move planted | a1a8 is not legal here | True | True | correct |

Rule 1 verdict: every plant caught, identities not flagged - the zeros are measurements
