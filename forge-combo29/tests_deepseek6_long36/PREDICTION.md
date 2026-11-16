long 36 prediction (SENSITIVITY D: the four biggest G-movers of long 27, all six pairs) -- own commit before the first counted run

The four settings of long 27 with the largest |ratio - 1| on G (max over their two ends), and the
end that made the G tree smaller:
  1. SingularDepth (G ratios 1.1459 / 0.9092) -- smaller-tree end: +c (SingularDepth 7)
  2. LmrQuietDivisor (1.0533 / 0.9293) -- smaller-tree end: -c (LmrQuietDivisor 193)
  3. LmrQuietBase (1.0682 / 0.9438) -- smaller-tree end: -c (LmrQuietBase 85)
  4. IirDepth (1.0042 / 1.0559) -- the smaller of its two ends is -c (IirDepth 1), which on G is
     still slightly ABOVE S14; noted as the odd one out.

1. The six combined runs (both settings at their chosen ends, under S14, rows on O and G at
   depth 12) exist and each differs from S14. Kill: any exact identity.
2. Per pair, on G: the measured ratio against the product of the two single G ratios (from long
   27) stays within 1 percent: SD7 x LQD193 = 0.9092 x 0.9293 = 0.8449; SD7 x LQB85 = 0.8582;
   SD7 x IIR1 = 0.9130; LQD193 x LQB85 = 0.8767; LQD193 x IIR1 = 0.9336; LQB85 x IIR1 = 0.9478.
   Kill: any pair off by more than 1 percent of its product.
3. The same on O: the products (from long 27's O ratios: SD+c 0.9646, LQD-m 0.9511, LQB-m
   0.9804, IIR-m 1.0726): SD7xLQD193 = 0.9176; SD7xLQB85 = 0.9457; SD7xIIR1 = 1.0347; LQD193x
   LQB85 = 0.9324; LQD193xIIR1 = 1.0202; LQB85xIIR1 = 1.0516 -- measured within 1 percent of
   each. Kill: any pair off by more than 1 percent.
