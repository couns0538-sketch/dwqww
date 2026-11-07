# Idea source - NnueInt8Vnni

- **Brief:** the owner's 5-hour brief, 2026-11-06, job 2. It points at item 4 of the 2026-11-06 NNUE inference note
  (md5 4b82d0b772a6c7a9a976c5371198c7d5).
  - The note file was not found on the PC, so only the mechanism text in the brief was used.
  - That text: quantize the trial_w6 float net to an int8 L1 (saturating integer FT, integer SCReLU, uint8/int8
    activations, int8 L1 weights, AVX-512 VNNI vpdpbusd dot on Zen 5).
- **Technique:** u8 x s8 dot products into int32 (vpdpbusd) are general integer-inference practice, documented in the
  public AVX512_VNNI instruction reference.
- **Code:** no engine source was copied, GPL or otherwise. Every line here is own code, written for Forge's net layout
  (768 -> 256 x 2 -> 1, SCReLU, int16 weights at 1/4096).
- **Licence:** own code, same terms as the repository.
