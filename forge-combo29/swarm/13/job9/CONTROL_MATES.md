control position: 6k1/8/6K1/8/8/8/8/7R w - - 0 1 (python-chess: forced mate in 3 plies)
engine PV: g6f6 g8f8 h1h8 -> PV delivers mate at ply 3
engine claimed mate 2 -> needs <= 3 plies

| plant | what it is | check says delivered? | should be delivered? | result |
|---|---|---|---|---|
| P0 real claim | claim mate 2, real PV delivers at ply 3 | True | True | correct |
| A claim too short | claim mate 1 (needs <=1), PV needs 3 | False | False | correct |
| B truncated PV | claim mate 2, PV cut to 1 ply | False | False | correct |
| C illegal PV move | claim mate 2, first PV move illegal | False | False | correct |
| D empty PV | claim mate 2, no PV at all | False | False | correct |

Rule 1 verdict: every planted mate failure is rejected and the real claim is accepted, so the zero is a measurement
