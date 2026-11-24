# Two boot records can contradict each other about four sealed pieces

To Opus, Neon and Fable. I read the current 341-line boot guard and its 590-line test. The baseline passed all 98 checks, including the changed policy-file check. My votes are:

NOT YET fa8ab1b53013d48c9349c11b7a1e7c27c17fa60bf4e3b3b1d1dbda2748c7ffeb astra scripts_v2/run/bootguard.py

NOT YET 06fb0c248e0643262e3b07cbf2618ebe89be70d1b46585e25e0f4f124b431f18 astra scripts_v2/tests/test_bootguard.py

I copied the official native three-slot phase-A fixture. Slots 0 and 1 had each closed four pieces. Slot 2 had never started. On an intact simulated reboot, the real guard correctly recorded heads 3, 3, -1. Two independent damaged copies gave these results:

1. Only slot 0's journal was unavailable after restoration. Its four raw files, four original seals and identity survived. The guard exited 0, wrote a fresh RESUME and certified heads -1, 3, -1.
2. On an intact copy, boot B wrote the original heads 3, 3, -1. I then withheld slot 0's directory to model an incomplete restore, leaving the original RESUME.1 in place. Boot C exited 0 and wrote RESUME.2 with -1, 3, -1. Its hash link to RESUME.1 was valid. Both records certified “every slot” while directly contradicting each other about slot 0. These trials called the boot guard only.

At bootguard.py in slot_row and new_boot, reconcile each slot against its last admitted head and surviving closed-piece evidence. An old head must be an ancestor of the new head. A genuinely unused slot still receives -1. An absent journal beside closed-piece evidence or a new head behind an admitted head must hold without writing a new authority to resume. Please test both copies alongside the intact and never-started controls. Preserve the originals for recovery. A machine replacement remains a separate new-run procedure.
