FORGE NNUE DATA AND TRAINING TOOLS
Python 3.10, Windows x64; DirectML target: AMD Radeon RX 7900 XT.

These are complete scripts, not code fragments. Extract the bundle and run
commands in that folder. Keep forge_selfplay.py beside convert_training.py.
No OpenAI API or API key is used.

INSTALL (PowerShell or Command Prompt)

    py -3.10 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\python.exe -m pip install -r requirements-directml.txt

Data generation/conversion alone does not require PyTorch:

    .\.venv\Scripts\python.exe -m pip install -r requirements-selfplay.txt

The DirectML version is pinned to 0.2.5.dev240914, whose wheel requires
PyTorch 2.4.1. numpy 1.26.4 avoids the older PyTorch/NumPy 2 ABI mismatch.
Use a current AMD graphics driver. Native Windows DirectML is the default.

RUN SELF-PLAY

    .\.venv\Scripts\python.exe .\forge_selfplay.py --engine "C:\Users\Administrator\grok-pc\forge.exe" --workers 4 --cpus 12-15 --nodes 5000 --out .\out

This runs continuously. All four workers and their engines use the affinity
MASK [12,13,14,15] and Windows IDLE_PRIORITY_CLASS. IDs are zero-based logical
CPUs. Each worker shares this mask; they are not assigned to separate CPUs.
The parent writer stays at normal priority. Affinity/priority failures stop
the run; the script does not silently use other CPUs.

Depth instead of nodes (the budget options are mutually exclusive):

    .\.venv\Scripts\python.exe .\forge_selfplay.py --engine "C:\Users\Administrator\grok-pc\forge.exe" --workers 4 --cpus 12-15 --depth 8 --out .\out

Finite initial smoke test, producing a finished data file:

    .\.venv\Scripts\python.exe .\forge_selfplay.py --engine "C:\Users\Administrator\grok-pc\forge.exe" --workers 4 --cpus 12-15 --nodes 5000 --games-per-worker 2 --out .\out-smoke

Use --help for all settings. Important defaults:
  --opening-plies 8       Uniform random legal moves from the normal start.
  --max-ply 300           Total game plies, INCLUDING the eight opening plies.
  --adjudicate-cp 2000    Inclusive threshold, for the SAME winning side.
  --adjudicate-plies 4    Consecutive evaluated plies; a weaker/changed/bounded
                         score resets the streak. Mate scores can adjudicate
                         but are never exported.
  --max-score 3000        Only non-mate cp labels with |cp| <= 3000 are exported.
  --lines-per-file 10000000
  --progress-seconds 60
  --engine-timeout 60     Increase if IDLE scheduling delays engine replies.

One engine is kept alive per worker, configured Threads=1 and Hash=16.
python-chess sends ucinewgame at game boundaries and a growing
"position startpos moves ..." before each search. UCI requires the entire
move list in that command; it has no standard append-only position command.
The board's complete history is retained for engine and Python repetition
checks. The first labelled position is the board reached after the eight
random opening moves, before the ninth move is played.

Games end at checkmate, stalemate, insufficient material, an ACTUAL third
occurrence of the current position, or the 50-move threshold already reached
on the board (100 reversible halfmoves). A draw that could be claimed only
after a future move is not taken early. Checkmate takes precedence over the
draw rules and the maximum-ply limit. Terminal random openings are skipped.

Positions in check, captures (including en passant), promotions, mate scores,
|cp| > 3000, and final bound-only scores are not recorded. Their moves are
still played. Exact scores following earlier aspiration bounds are accepted.
Adjudication uses White POV internally so alternating STM signs do not
mistakenly change the winner.

OUTPUT, DEDUPLICATION AND RESUME

Every output line has exactly three fields:

    FEN | score | result

score: signed integer CENTIPAWNS FROM THE SIDE TO MOVE.
result: 1.0/0.5/0.0 FROM WHITE'S POINT OF VIEW.
The best move is used for filtering; it is not an extra output column.
Only completed games receive result labels. An unfinished interrupted game
is discarded rather than being labelled as a fabricated draw.

Finished files: out\forge_selfplay_001.txt, ...002.txt, ...
Checksum files: out\forge_selfplay_001.txt.md5, ...
Active file:    out\forge_selfplay_NNN.txt.part
Persistent set: out\forge_seen_hashes.sqlite3

The SQLite table is an on-disk set of BLAKE2b 128-bit position hashes across
ALL numbered files, not a RAM-only per-file set. The hashed key is the first
four FEN fields; the halfmove and fullmove counters are ignored. FENs use
standard, explicit en-passant fields. Hash collisions are theoretically
possible; 128-bit hashes make accidental collisions negligible.

The writer fsyncs data BEFORE committing its hashes and offset. A process
crash can leave a .part file; on restart its uncommitted tail is rolled back
to the durable offset and its committed contents are sealed with MD5. An
uncommitted orphan is preserved under an .uncommitted-* suffix. Finished
.txt and .md5 files are never overwritten. Numbering always continues, even
when only a reserved/orphan number exists. Pre-existing finished numbered
files absent from the DB are indexed once by streaming through them.

Press Ctrl+C once. A worker watcher asks an ongoing search to stop, so even
depth searches can quit promptly. Stopped searches never label a game.
The parent drains completed games, the workers quit their
engines, and the current partial-size file is finished and checksummed.
Restart the SAME command with the SAME out folder to resume. Keep the entire
output folder, including the SQLite DB and any -wal/-shm companions, together.
Do not edit indexed data or delete its DB. An OS lock allows only one writer
(self-play or converter) per output folder; crashes release the lock.

Progress is per session: completed games, unique saved positions and their
hourly rates per worker and in total. "eligible" is before deduplication.
Search percentage measures wall time between UCI go and bestmove, including
OS scheduling and pipe latency. It excludes position setup and writing.
The total percentage is the average across worker lifetimes, not a sum
that can exceed 100%. It is not CPU utilization. Startup/idle time counts
against it; short smoke-test rates are not a sustained performance estimate.

CONVERT STOCKFISH BINPACK OR LEELA DATA

Binary formats require their native decoder executable. pip does NOT install
these executables, and the bundle does not include them. This avoids guessing
binary layouts or silently losing castling, orientation, EP or result data.
The second script streams the decoded plain records and uses the same
rotating, persistent-dedup writer as self-play.

For standard BINP-format Stockfish binpacks, get nnue_data_compression.exe
from the format author's project:
  https://github.com/Sopel97/nnue_data_compress/releases
  https://github.com/Sopel97/nnue_data_compress
Its verified CLI is: nnue_data_compression input.binpack output.plain

    .\.venv\Scripts\python.exe .\convert_training.py binpack "C:\data\dataset.binpack" --decoder "C:\tools\nnue_data_compression.exe" --out .\out-converted --quiet-only

The decoder's score is multiplied by --score-scale (default 1.0). The binpack
container does not specify a universal cp calibration. Check the producer:
for historic Stockfish data whose pawn unit is 208, use
--score-scale 0.4807692307692308. For actual cp data, keep 1.0. Mate encodings
in binary datasets are producer-specific; --quiet-only also excludes
|converted cp| > 3000. Exotic/newer binpack variants or Chess960 require an
appropriate native decoder and engine feature contract; they are not claimed
to be supported by this standard BINP adapter.

For LC0 v6/v7 gzipped training chunks, unpack any outer TAR archive into a
dedicated chunk directory. Supply the matching native lc0_rescorer.exe from
the LC0 project and at least 3-man Syzygy tablebases. This is the RESCORER
executable, not an ordinary UCI-only lc0.exe.
  https://github.com/LeelaChessZero/lc0
  https://github.com/LeelaChessZero/lc0/blob/master/src/trainingdata/rescorer.cc

    .\.venv\Scripts\python.exe .\convert_training.py leela "C:\data\leela-chunks" --decoder "C:\tools\lc0_rescorer.exe" --syzygy "C:\tablebases\3-4-5" --out .\out-converted --quiet-only

The adapter explicitly passes --delete-files=false because the rescorer's
default deletes inputs. It explicitly clears the output chunk directory, even
if a local LC0 config file set one. It asks for
the best move/score. The native tool reconstructs FENs and handles format
orientation/canonicalization. It may repair game outcomes from tablebases.
LC0 q values are not measured centipawns: the native q-to-score formula is
660.6*q / (1 - 0.9751875*q^10), in its legacy SF units. The adapter defaults
to 100/208 scaling for Leela; these are CP ESTIMATES, not Forge-calibrated
evaluations. --score-scale overrides this assumption.

To obtain Forge's own cp labels, rescore decoded positions with Forge:

    .\.venv\Scripts\python.exe .\convert_training.py leela "C:\data\leela-chunks" --decoder "C:\tools\lc0_rescorer.exe" --syzygy "C:\tablebases\3-4-5" --rescore-engine "C:\Users\Administrator\grok-pc\forge.exe" --nodes 5000 --quiet-only --out .\out-converted

Rescoring keeps the source game result (after any native TB repair), replaces
the score and best move, and skips terminal, mate or bound-only evaluations.
The separate rescore helper is single-process; the generator's worker CPU
affinity settings apply to the generator itself.

Already have native Stockfish .plain text? No decoder is needed:

    .\.venv\Scripts\python.exe .\convert_training.py plain "C:\data\dataset.plain" --quiet-only --out .\out-converted

SF .plain records have fen/move/score/ply/result fields and end with "e".
Both score and result {-1,0,+1} are STM-relative in that format. The adapter
converts the game result to White POV. Plain decoders can normalize unused
EP fields/counters; these do not change the NNUE piece-square features.

Native decoding uses a temporary expanded .plain FILE, not all RAM. Ensure
there is disk space; --temp-dir "D:\temp" selects another drive. --quiet-only
needs a legal move field or --rescore-engine. Malformed/truncated records
produce an error, not invented zero labels. A valid converted prefix may
already have been saved when an error is reported.

Use --out .\out while self-play is stopped to merge imports into the SAME
persistent dedup set. Using a separate folder gives it a separate set.

TRAIN ON THE RADEON 7900 XT (WINDOWS DIRECTML)

Use finished, checksummed files. Ctrl+C once to finish the generator's active
file if the first 10-million-line rotation has not yet occurred. Generation
can then be restarted alongside training; the trainer takes an immutable
file-size snapshot at startup and ignores active .part files.

    .\.venv\Scripts\python.exe .\train_nnue.py --data ".\out\forge_selfplay_*.txt" --device directml --device-name "7900 XT" --shape 256 --run-dir .\forge-training

Include separate converted files if applicable:

    .\.venv\Scripts\python.exe .\train_nnue.py --data ".\out\forge_selfplay_*.txt" ".\out-converted\forge_selfplay_*.txt" --device directml --shape 256 --run-dir .\forge-training-all

--device-name defaults to "7900 XT" and selects that discrete GPU by name.
It will not silently choose the integrated GPU. --device-index N overrides
name selection. No GPU match produces an error listing the available names.

The trainer uses IterableDataset, byte-range sharding across ALL files,
bounded raw-line shuffle buffers, and batched dense matrix multiplication.
CPU loader processes return plain NumPy arrays; only the main process uses
the GPU. Loaders use spawn on every platform, including the ROCm fallback.
No custom CUDA kernels, sparse GPU kernels, torch.compile, or AMP
are required. Adam uses foreach=False for DirectML compatibility.

Defaults: batch 1024, 2 loader workers, 8192 raw records buffered per worker,
10 total epochs, all training records per epoch. Change --batch-size,
--loader-workers, --shuffle-buffer or --steps-per-epoch as needed. RAM is
bounded by buffers, batches and workers; it does not grow with dataset size.
The MD5 sidecar is used as a completion marker, not rehashed at each epoch.
--allow-unsealed permits external complete .txt files without sidecars.

The target is:
  blend * sigmoid(score_stm_cp * K/400) + (1-blend) * result_stm
where blend defaults to .75 and K=2.25. White results are flipped for Black
to move. Loss is MSE in probability space. Five percent of positions are
held out by a stable counter-independent FEN hash. Counter variants always
stay in one split. Validation is position-level, not independent-game Elo
evidence. The validation scan is capped at 100 batches by default.

Int16 fake quantization is enabled by default; --no-qat disables it. Weights
are constrained to the representable range. Export uses the same rounding,
feature-major order and scales as the supplied Forge C++ implementation.

The default shape is (768 -> 256) shared by the two perspectives, with
clamp(x,0,1)^2 activation and a concatenated 512 -> 1 output. --shape 128
changes the accumulator width. --shape 256,32,32 can train an additional
dense stack, but requires --export checkpoint: it does NOT match Forge's
one-output-layer exporter and needs an engine-specific serializer.

The input mapping remains Forge's 768 relative piece-square features;
changing widths is not sufficient to match HalfKP, king-bucket, or other
feature schemes. An engine with another feature scheme needs corresponding
encoder and serializer changes. See engine_contract.json for exact mapping.

Every completed epoch saves uniquely named .pt and .json files. Forge export
also writes .inc quantized include and .bin float32 trainer weights. Ctrl+C
finishes the current step and saves a checkpoint if progress has not already
been saved. Resume includes optimizer state. A partial epoch is replayed;
this is not an exact data-cursor/RNG continuation. To resume in PowerShell:

    $ckpt = (Get-ChildItem .\forge-training\*.pt | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
    .\.venv\Scripts\python.exe .\train_nnue.py --data ".\out\forge_selfplay_*.txt" --device directml --resume "$ckpt" --epochs 20 --run-dir .\forge-training

--epochs is the TOTAL epoch target, not an additional count. New runs require
a new --run-dir, so an earlier run is not overwritten. A CPU smoke test can
use --device cpu --epochs 1 --batch-size 32 --loader-workers 0.

The bundle includes examples\forge_sample.txt (916 positions) and its checksum
for a quick GPU smoke test before generating your own large dataset:

    .\.venv\Scripts\python.exe .\train_nnue.py --data ".\examples\forge_sample.txt" --device directml --shape 256 --epochs 1 --batch-size 64 --loader-workers 0 --run-dir .\gpu-smoke

This small sample is not enough to train a competitive engine.

ROCM THROUGH WSL2 FALLBACK

Use a separate Linux environment, not the Windows DirectML venv. Install the
AMD-supported WSL2 driver/ROCm/PyTorch combination for RX 7900 XT from:
  https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/wsl/wsl_compatibility.html
The inspected ROCm 7.2.1 matrix lists RX 7900 XT and PyTorch 2.9.1. Match the
complete supported driver/OS/framework combination in those instructions;
an arbitrary ROCm wheel is not interchangeable. Then install python-chess,
numpy and psutil into that environment and run, for example:

    python3 train_nnue.py --data "/mnt/c/Users/Administrator/grok-pc/nnue-tools/out/forge_selfplay_*.txt" --device rocm --device-name "7900 XT" --shape 256 --run-dir forge-training-rocm

ROCm intentionally uses torch.cuda APIs in PyTorch. The script checks that
the installation is HIP-backed and the requested GPU exists. This fallback
does not change features, targets or exported weights.

LOADING WEIGHTS INTO THE ENGINE

The supplied Forge 6.2 source was inspected directly. Its default architecture
is 768 -> 256 per perspective, then 512 -> 1. It uses embedded weights and
does NOT implement an EvalFile runtime loader. The exported .bin is a raw
float32 file for the supplied C++ trainer's --load option, NOT a universal
Stockfish .nnue file.

For that Forge source, copy a trained .inc to src\nnue_weights.inc and rebuild:

    Copy-Item "<your-export>.inc" "C:\path\to\forge-source\src\nnue_weights.inc"
    cmake -S "C:\path\to\forge-source" -B "C:\path\to\forge-source\build" -A x64
    cmake --build "C:\path\to\forge-source\build" --config Release

Those example build commands require Visual Studio C++ tools and CMake.
If --shape differs from 256, build with the matching FORGE_NNUE_HIDDEN macro;
the exported include has compile-time shape and scaling checks. Other Forge
versions may default to different widths (e.g. the supplied later donor uses
128). The include marks a full evaluation network, not a residual correction.

No separately identified GrokChess loader or callable "Engine NNUE" service
was supplied. engine_contract.json is the exact verified Forge handoff,
including source hashes. A GrokChess binary loader must confirm the SAME
feature mapping, perspective order, activation, scales, serialization and
full-eval/residual convention before a drop-in file can be promised.
Matching only layer sizes cannot establish binary compatibility.

VALIDATION AND SOURCES

See VALIDATION.txt. Local checks covered real UCI self-play, global dedup,
numbering/rotation/MD5, crash recovery, Ctrl+C, native binpack conversion,
streaming training/resume, and original Forge C++ inference parity.
Windows API calls were mocked for the affinity/priority unit check. No actual
Windows/DirectML/7900 XT or WSL2 ROCm hardware run is claimed.

Primary references used:
  https://python-chess.readthedocs.io/en/stable/engine.html
  https://psutil.readthedocs.io/stable/
  https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-windows
  https://pypi.org/project/torch-directml/0.2.5.dev240914/
  https://docs.pytorch.org/docs/stable/data.html
  https://github.com/Sopel97/nnue_data_compress
  https://github.com/LeelaChessZero/lc0/blob/master/src/trainingdata/rescorer.cc
  https://github.com/LeelaChessZero/lc0/blob/master/src/trainingdata/trainingdata_v6.h
