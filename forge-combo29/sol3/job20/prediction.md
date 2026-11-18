# Job 20 prediction

Both arms use PC20, Threads 1, Hash 16, and the pinned standalone
net768. I predict zero fast/reference integer disagreements in each
clean arm. Share means counted v3 calls divided by the sum of consumed
nodes. For S1 the node denominator is the completed depth-9 info.
For S2 it is the engine's final softnodes marker, which includes work
after the last completed iteration.

| Workload | Build | Difference range | V3 calls per node range |
| --- | --- | ---: | ---: |
| S1 | r15d-shadow | 0 | 48.60–48.70% |
| S1 | kF-shadow | 0 | 48.60–48.70% |
| S2 | r15d-shadow | 0 | 38–52% |
| S2 | kF-shadow | 0 | 38–52% |

S1 repeats K1 exactly, whose observed share was 48.6363% for both.
The separate Job 9 game-path run had a 42.39% share using final
consumed nodes. The opening roots and game-ending rule here differ,
so I use a broad S2 range.
