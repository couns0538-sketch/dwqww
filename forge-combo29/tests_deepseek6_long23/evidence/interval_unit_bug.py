import math

# deepseek6 long 23: shows the interval bug my FIRST recount run had, checkably, from M51's
# published n5 vector alone. n5's index i is the pair score in HALF points (0..4); the pair
# score in points is i/2 and the fraction of the two available points is i/4. Dividing the
# standard error by 2 (treating i as points) doubles the reported interval.

n5 = [98, 211, 397, 204, 90]
P = sum(n5)
mi = sum(i * n5[i] for i in range(5)) / P
var_i = sum(n5[i] * (i - mi) ** 2 for i in range(5)) / (P - 1)
sc = mi / 4.0
elo = -400.0 * math.log10(1.0 / sc - 1.0)
deriv = 400.0 / (math.log(10.0) * sc * (1.0 - sc))

se_bug = math.sqrt(var_i / P) / 2.0   # WRONG: i treated as points
se_ok = math.sqrt(var_i / P) / 4.0    # right: i/2 = points, /2 again = fraction of two points

for tag, se in (("buggy (divide by 2)", se_bug), ("correct (divide by 4)", se_ok)):
    h = 1.959964 * deriv * se
    print("M51 %-22s Elo=%+.2f 95%%[%+.2f,%+.2f] width=%.2f" % (tag, elo, elo - h, elo + h, 2 * h))
print()
print("ratio of widths = %.4f  (1.0000 would mean the bug was not the cause)" % (se_bug / se_ok))
