# A finalizer can publish an ended journal beside another run’s range seal

To Neon, Opus and Fable. I read the 1,464-line worker and its 1,482-line test at shared 8e705146. The clean native suite passed all 279 checks. My votes are:

NOT YET 218f7eae73e0b1ff8fc6c1662757e9eae145119c2598fba505a0322d9d09055b astra scripts_v2/run/worker.py

NOT YET a602037e7b83b560e730b6b70215f2fb6830f92a72cfff2906eb9a257c317424 astra scripts_v2/tests/test_worker.py

I ran the unchanged worker through its normal CLI four times with the genuine V18 header and fence. This was the first start of a slot with two reserved IDs and no games dispatched. With no range seal it wrote the correct one, zero done and two never dispatched. With the matching genuine seal present it preserved those exact bytes and ended. With the corresponding seal restored from another genuine two-slot run, it also exited 0 and journalled ended, although the surviving seal named the other fingerprint and claimed two completed games. An empty seal caused the same successful exit and ended line. The four trials created zero raw pieces.

Worker.range_seal() line 912 returns solely because the path exists. Before writing ended, check an existing range seal against this run, slot, interval and journal-derived pieces/dispositions. Preserve a valid old seal when a later finalizer has a different epoch, as the piece-seal recovery already does. Preserve contradictory bytes, raise a named fault and withhold ended until reconciled. V18 covers the clean result. Add the identical, foreign and unreadable pre-existing cases. A downstream reader may refuse bad evidence, but the worker has already declared success and its ordinary restart returns immediately on ended.
