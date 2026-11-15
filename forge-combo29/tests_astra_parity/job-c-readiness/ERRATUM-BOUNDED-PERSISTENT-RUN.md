# Readiness clarification: persistent process and command limit

Independent review verified all seven original pins and found no issue with the source hooks, build overlay, option/corpus inputs, net-switching sequence or true five-second sanitizer shutdown requirement.

One scheduling statement in READINESS.md needs a stricter interpretation. Splitting observation or polling calls into bounded intervals does not by itself bound the underlying native command's lifetime. Do not claim that a persistent20,000-position engine run complies with the owner's eight-minute command limit merely because the controller polls it in short calls.

For the exact one-process/no-ucinewgame target, either complete that native run within eight minutes, or obtain an explicit scheduling clarification from Fable/the owner before declaring a longer continuous native command. If the limit prevents completion, preserve and report the actual completed count as a shortfall; fresh-process batches do not satisfy the one-process20k requirement. This clarification changes no source, protocol, historical evidence or authorization. Job C has not started.
