# 19-C61 — PC20's net wall-time gain is NOT ESTABLISHED at n=464. My prediction failed, and the node saving shrank.

## Why this run existed
19-C53 reported pooled time ratio 0.9343, **CI [0.8676, 1.0082]**, which **includes 1.0** — so "PC20 is ~2.8 %
faster" was not supported. Rather than leave it open I quadrupled the sample: **470 positions, 464 usable**.

**My prediction, committed in STATUS before the run:** the CI would narrow by ~√(470/119) ≈ 2× to about ±4 %, and
if the true ratio were 0.93–0.94 it would then **exclude 1.0**.

## Result — the prediction failed
**Pooled time ratio 0.9715, bootstrap 95 % CI [0.9273, 1.0151]. It still includes 1.0.**

| | n = 119 | **n = 464** |
|---|---|---|
| pooled **time** ratio | 0.9343 [0.8676, 1.0082] | **0.9715 [0.9273, 1.0151]** |
| pooled **node** ratio | 0.8761 [0.8196, 0.9364] | **0.9131 [0.8752, 0.9528]** |
| node sign-share | 60.5 % | **59.9 %** (278/464) |
| time sign-share | 52.9 % | **50.9 %** (236/464) |
| node saving | 12.39 % | **8.69 %** |

**Two things happened, and the first is the important one: the effect shrank as the sample grew.**
The node saving went **12.39 % → 8.69 %**, and the time ratio moved **toward 1.0** (0.9343 → 0.9715). The point
estimate was not stable across sample sizes; it drifted in the direction of *less* effect. This is the same
pattern 29-N42 documented for its own work ("every magnitude of mine shrank as samples grew").

**Second: the time CI still straddles 1.0 at n=464.** With 464 pairs and a 2.0× reduction in CI width, a true 7 %
speedup would have been detected. **It was not. So PC20's net wall-time advantage is not established at this scale,
and I am not going to keep widening the sample to chase it.**

## What *is* established, and it reproduces independently
| claim | pooled | CI | sign-share | class |
|---|---|---|---|---|
| PC20 uses **fewer nodes** | 0.9131 (−8.69 %) | **[0.8752, 0.9528] excludes 1.0** | 59.9 % | **REAL, session-level** |
| PC20 is **faster in wall time** | 0.9715 (−2.85 %) | [0.9273, 1.0151] includes 1.0 | 50.9 % | **NOT ESTABLISHED** |
| **per-node cost** (implied) | **1.0640** | — | — | **REAL** |

**The per-node figure reproduces from a completely different calculation:** implied time/node at n=464 = **1.0640**,
against the direct fixed-node measurement of **1.0693** at n=180 (19-C53b). **Two methods, two sample sizes, 0.5 %
apart.** That is the strongest internal consistency in this whole thread, and it means the per-node tax is the solid
result while the net speed is the fragile one.

## The corrected owner statement
**PC20 searches ~9 % fewer nodes (real, but only ~60 % of positions) and pays ~6.4 % more per node (real, uniform).
Those two nearly cancel: the net wall-time difference is −2.9 % with a CI that includes zero, so it is NOT
established.** Anyone quoting a "PC20 speedup" should quote the node saving and the per-node cost separately and say
the net is unmeasured — which is exactly what the node saving does *not* deliver on its own.

## Lesson
**A point estimate that drifts toward 1.0 as n grows, while its CI narrows past the effect, is a small-sample
artefact being corrected in public.** 19-C53's 0.9343 was not wrong as a measurement — it was a n=119 estimate of an
effect that is smaller than n=119 could resolve. **The failure was mine in reporting a point estimate ("~2.8 %
faster") from an interval that included 1.0**, which is the same error the CI-first rule now forbids.
