"""R10: nnue-pytorch's own evaluation of a K32H3^ .nnue on a list of FENs (the reference for Forge's EvalFileHalfKA).
Run with the trainer's venv and clone (read only; CPU only, no GPU):
  NNUE_REPO=<clone> NNUE_DATA_LOADER_LIB=<dll> NNUE_FT_BACKEND=torch <venv python> -I -B parity_nnue_pytorch.py \
      <net.nnue> <fens.txt> <out.txt> [--l1 N --l2 N --l3 N] [--float32] [--batch 2000]
Path inside the trainer: model.NNUEReader (its file parser) -> data_loader.get_sparse_batch_from_fens("K32H3", ...)
(its C++ feature extractor) -> model.forward(..., fake_quantize_acts=True, fake_quantize_weights=True), in float64 by
default (exact on this integer grid; --float32 = the trainer's training precision). Writes per FEN the trainer's integer
output value round(out * 9600) (= the engine's raw value) and out * 600 (the evaluation in score units).
With `compare <ref.txt> <forge.txt>` instead: counts exact matches of the raw values (any Python)."""
import os
import sys


def compare(ref_path, forge_path):
    ref = [ln.split() for ln in open(ref_path, encoding="ascii")]
    got = [ln.split() for ln in open(forge_path, encoding="ascii")]
    if len(ref) != len(got):
        raise SystemExit(f"line counts differ: {len(ref)} vs {len(got)}")
    diffs = [abs(int(a[0]) - int(b[0])) for a, b in zip(ref, got)]
    exact = sum(d == 0 for d in diffs)
    cp_diffs = [abs(float(a[1]) - int(b[1])) for a, b in zip(ref, got)]
    print(f"{len(diffs)} positions: raw output exact {exact} ({100.0 * exact / len(diffs):.3f}%), max |raw diff| {max(diffs)}, "
          f"max |eval diff| {max(cp_diffs):.4f} (Forge truncates raw/16 to whole centipawns)")
    return 0 if exact == len(diffs) else 1


def main():
    a = sys.argv
    if a[1] == "compare":
        sys.exit(compare(a[2], a[3]))
    net, fens_path, out_path = a[1], a[2], a[3]

    def opt(name, default):
        return int(a[a.index(name) + 1]) if name in a else default

    sys.path.insert(0, os.environ["NNUE_REPO"])
    import torch
    import data_loader
    import model as M

    cfg = M.ModelConfig(L1=opt("--l1", 256), L2=opt("--l2", 32), L3=opt("--l3", 32))
    with open(net, "rb") as f:
        mdl = M.NNUEReader(f, "K32H3^", cfg).model
    dtype = torch.float32 if "--float32" in a else torch.float64
    mdl = mdl.to(dtype).eval()
    fens = []
    for line in open(fens_path, encoding="ascii"):
        fen = line.split(" | ")[0].strip()
        if fen:
            fens.append(fen)
    batch = opt("--batch", 2000)
    rows = []
    with torch.no_grad():
        for i in range(0, len(fens), batch):
            chunk = fens[i:i + batch]
            n = len(chunk)
            b = data_loader.get_sparse_batch_from_fens("K32H3", chunk, [0] * n, [1] * n, [0] * n)
            us, them, wi, bi, _outcome, _score, pc, qb = b.contents.get_tensors("cpu")
            out = mdl.forward(us.to(dtype), them.to(dtype), wi, bi, pc, qb, fake_quantize_acts=True,
                              fake_quantize_weights=True)
            data_loader.destroy_sparse_batch(b)
            for v in out.flatten().tolist():
                rows.append((int(round(v * 9600)), v * 600))
    with open(out_path, "w", encoding="ascii", newline="\n") as f:
        for raw, ev in rows:
            f.write(f"{raw} {ev:.6f}\n")
    print(f"nnue-pytorch ({dtype}): {len(rows)} positions -> {out_path}")


if __name__ == "__main__":
    main()
