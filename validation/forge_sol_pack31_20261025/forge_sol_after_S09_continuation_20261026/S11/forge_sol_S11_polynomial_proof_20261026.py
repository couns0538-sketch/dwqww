"""Independent modular-algebra screen; not a native C++ result or speed test."""
import json
from pathlib import Path
import random
MASK=(1<<64)-1
BASE=1099511628211
FINAL=0x9E3779B97F4A7C15

def horner(counts):
 result=0
 for count in counts:result=(result*BASE+count+1)&MASK
 return result*FINAL&MASK

def contributions():
 return [[((count+1)*pow(BASE,9-slot,1<<64)*FINAL)&MASK for count in range(65)] for slot in range(10)]

def expanded(counts,table):return sum(table[index][count] for index,count in enumerate(counts))&MASK

def main():
 table=contributions();cases=[]
 for slot in range(10):
  for count in range(65):
   vector=[0]*10;vector[slot]=count;cases.append(vector)
 rng=random.Random(20261026)
 random_cases=[[rng.randrange(65) for _ in range(10)] for _ in range(10000)]
 boundary=[[0]*10,[64]*10,[64,0]*5,[0,64]*5]
 mismatch=sum(horner(c)!=expanded(c,table) for c in cases+random_cases+boundary)
 assert mismatch==0
 mutant=[list(row) for row in table];mutant[9][1]^=1
 caught=sum(horner(c)!=expanded(c,mutant) for c in cases)
 assert caught>0
 result={'status':'PASS_ALGEBRA_SCREEN_ONLY','modulus':'2^64','basis_cases':len(cases),'fixed_seed_random_cases':len(random_cases),'seed':20261026,'boundary_cases':len(boundary),'mismatches':mismatch,'perturbed_table_basis_mismatches':caught,'native_Cpp_verified':False,'overflow':'Unsigned64 polynomial operations intentionally wrap modulo2^64; no signed arithmetic depends on wrapping','proof':'Horner is affine in10 counts. Equality at zero and each single-coordinate value establishes the same affine map on every count vector0..64; sum tables is affine with those same coordinate contributions.'}
 (Path(__file__).parent/'forge_sol_S11_polynomial_proof_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
if __name__=='__main__':main()
