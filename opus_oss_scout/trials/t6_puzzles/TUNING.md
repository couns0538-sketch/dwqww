# T6 puzzle screen: ideas for the crew

1. **Use as a pre-gate screen, not as an Elo measure.**
   - A search change that loses tactics shows up as a lower solve rate at fixed nodes within minutes, on CPUs 2-3,
     independent of the load.
   - A change can still gain Elo while losing puzzles (and the reverse), so the gate decides.
2. **A fixed, versioned sample.** Commit the puzzle IDs of a sample (e.g. this seed-20261106 set of 2,000) and keep it
   frozen, so solve rates are comparable across candidates. Refresh it only with a new name.
3. **Paired comparison.** Run the lock and the candidate on the same puzzles. Report the discordant pairs (lock solves,
   candidate fails, and the reverse) with a sign test. That is far more sensitive than comparing two rates.
4. **Budgets.** 20k nodes is a quick "did anything break" check; 200k-1M nodes is closer to gate depth. Rating bands
   show where a change helps: the 2500+ band is where search changes usually show.
5. **Themes.** The Lichess themes (mate, mateIn2, fork, pin, endgame, ...) allow per-theme rates. A pruning change that
   hurts `mate` puzzles is a typical red flag.
6. **Licence / data.** The puzzles are CC0-1.0 and come from Lichess games analysed with Stockfish (dataset card).
   Using them as a test set is fine. Training on them would be a provenance question for the owner.
