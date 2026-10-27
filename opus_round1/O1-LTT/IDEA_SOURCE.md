# O1-LTT IDEA_SOURCE (UCI LocklessTT, test plan G-B5)

| Element | Source (concept only; all code is our own) |
|---|---|
| Lockless shared hash table: store each entry as machine words written without a lock; mix the key with the data so that a read combining two writes fails the key check and is treated as a miss | Robert Hyatt and Timothy Mann, "A lock-less transposition table implementation for parallel search chess engines", ICGA Journal 25(2), 2002 (the "key XOR data" scheme); Chess Programming Wiki, "Shared Hash Table", section on lockless hashing (https://www.chessprogramming.org/Shared_Hash_Table) |
| Variant used here: the 16-byte Forge entry is two 64-bit words; the first holds the move and the 32-bit key tag XOR a 32-bit hash of the move and of the whole second word (the payload) | Own design. The XOR guard covers all 96 data bits of an entry: the move and the 64-bit payload |
| Relaxed atomic 64-bit loads and stores for the words, so that concurrent access is defined behaviour and ThreadSanitizer-clean, with no ordering cost on x86-64 | C++20 memory model (`std::atomic_ref`); GCC `__atomic` builtins documentation |
| Report and source context | OPUS_TOP_ENGINES_2025_2026.pdf (Opus research report, round 2: lockless TT as an SMP item) and its cited public sources; test plan row G-B5 |
| Tests: torn-write simulation (mixing words of two writes), multi-thread stress with data derived from the key, lockless == locked on identical operation sequences | Own test design |

No Elo claim. The gate is SMP-only (Threads > 1), as the job asks.
