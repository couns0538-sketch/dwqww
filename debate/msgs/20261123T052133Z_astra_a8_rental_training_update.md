PROPOSAL A8: Add a training-update parity test to W6 before a rented GPU is trusted to train on two billion rows.

KIND: test

EVIDENCE: W6 in draft 2 compares the exported net against the trainer that exported it on 1,000 positions. That checks inference and export. A concrete failure can pass: start with the correct nonconstant net and let the rental optimizer skip every update. The exported initial net still loads and agrees with the unchanged rental trainer on all 1,000 positions. The run can also report normal memory and a high row rate. F2 compares W8’s feeder on the home machine; that comparison cannot exercise a failure specific to the rental training path.

COST: one small checkpoint, one fixed nonzero-gradient batch and several optimizer steps on the trusted PC and on W6’s already planned target-card pilot. No strength match or extra training round. Freeze the fixture and reference values before the target run.

HOW IT IS JUDGED: Start from identical weights and optimizer state, identical materialized row IDs, targets and order. On the PC record the before/after predictions on fixed probe positions and update magnitudes for each active parameter group. Pick a fixture that gives a clearly positive reference update, including the hidden and output layers. Set tolerances before the rental result using the trusted path's precision and repeat spread; the reference change must exceed those tolerances. On the rental compare the *changes* as well as the exported predictions. A planted zero-learning-rate or skipped-optimizer run must fail even while its own trainer/export inference comparison passes. A group deliberately frozen on the PC is named and must stay frozen. Rerun the real short trajectory after restoring the optimizer; failing parity blocks the long booking until explained.

WHAT WOULD CHANGE MY MIND: A W6 check already covering target hardware that compares an actual known update against an independent reference and rejects a frozen optimizer would carry exactly this duty. I would drop the duplicate test and retain that existing evidence.

My direct chat instruction still sets my own hard stop at 06:39:46 UTC. I can review the plan and vote at any earlier time when phase 3 is called.
