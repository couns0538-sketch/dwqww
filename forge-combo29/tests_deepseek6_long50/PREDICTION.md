long 50 prediction (the tuner's steps: the smallest change that moves the O tree by 2 percent)
-- own commit before the counted runs

1. The five integer-or-switch settings need NO new runs: their tuner step is already the smallest
   possible change, and long 27 measured it at or over 2 percent -- NullMoveBase 1 (+4.35 %),
   LmpBase 1 (+3.45 % via the +c end), SingularDepth 1 (+2.45 %/−3.54 %), IirDepth 1
   (+7.26 %/+10.00 %), NonPawnCorrection false (+2.51 %). Their answer = the tuner step itself.
   Kill: any of them whose tuner step measured UNDER 2 percent in long 27 (then a smaller change
   is impossible and the setting's answer is still the step, reported as under-2-percent).
2. For the eight scaled settings, the found 2-percent step c2 lies within [c/4, 2c] of the tuner's
   step c. Kill: any c2 outside that interval.
3. Every run value stays inside its option's range (clamps named otherwise). Kill: an unclamped
   value out of range.
4. The per-setting two ends at the SAME tested level differ by less than a factor of 3 in their
   |ratio - 1| (the response is smooth across the two directions). Kill: any level where one end
   crosses 2 percent and the other end is under 0.7 percent at the same distance from the default.
