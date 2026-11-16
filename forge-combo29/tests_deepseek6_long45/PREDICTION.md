long 45 prediction (the eight biggest G-movers of longs 27/28 at depth 14 on G) -- own commit before the counted runs

The eight settings, one end each (the end with the LARGER |G ratio - 1| in longs 27/28):
SingularMargin 1 (G d12 ratio 1.1612), SingularDepth 5 (1.1459), LmrQuietDivisor 193 (0.9293),
LmrQuietBase 85 (1.0682), IirDepth 3 (1.0559), RfpMargin 78 (1.0564), LmpBase 7 (0.9722),
RfpImproving 34 (1.0204).

1. S14 run twice on G at depth 14: the two sums are EQUAL to each other (deterministic); that
   value is the base. Kill: the two differ.
2. The base sum sits in [40,000,000, 46,000,000] (about 2.3x the G depth-12 sum). Kill: outside.
3. The two Singular settings AMPLIFY at depth 14: |ratio14 - 1| > |ratio12 - 1| for both.
   Kill: either does not.
4. At least five of the other six also amplify. Kill: fewer than four.
5. The ORDERING of the eight by |ratio - 1| is preserved from depth 12 to depth 14 at the top
   (SingularMargin and SingularDepth stay the top two). Kill: either loses its top-two place.
