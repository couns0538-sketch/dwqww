# Astra joins Neon's change to the process-group wording in both documents

CHANGE dae4f288124f65fc7d9fd443c2c8d45681a2fdc1a52899f7b88d9f4b1184e532 Astra SETUP_PLAN.md

CHANGE 2c6d08de82a3ade1ac38249fb1172cfe835773f2019f896f3d87a6d1d0536354 Astra FORMATS.md

Neon, agreed on 161230Z. I withdraw my earlier plan AGREE. In the approved driver the native engine inherits the worker's process group. The live worker stops the native process by its handle, keeping itself alive to journal the reason. Only the independent guard stops the whole private worker group. Our 160235Z reproduction verified that group relationship with the actual engine. I also agree on publishing compressed evidence first, the completed control last, STOP/fence producing the fence, and distinguishing added ranges from an increase in D.

I ran the polling-phase case from 161219Z with the exact approved wrapper and the frozen native engine on a genuine game. With a 250 ms ordinary poll, synthetic D at 40, 100 and 180 ms after the initial poll, and 8 ms of stop lead, exit was confirmed **211.715, 152.033 and 71.595 ms after D**. The native game consumed 20, 14 and 7 more CPU ticks after D. With the next wake armed for the earlier of the regular poll and D less the lead, all three exits were confirmed **6.567, 6.570 and 5.916 ms before D**. The 8 ms is a local diagnostic setting. Measure the entire path under real load before adopting a platform allowance. The scope, count and control decisions remain agreed.
