import subprocess,sys,re,json
exe=sys.argv[1]
commands='uci\nsetoption name NnueExactInt32 value true\nbench 1\nbench 1\nsetoption name NnueExactInt32 value false\nquit\n'
p=subprocess.run([exe],input=commands,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
print(p.stdout,end='');print(p.stderr,file=sys.stderr,end='')
checks={'clean_exit':p.returncode==0,'new_option_off_default':'option name NnueExactInt32 type check default false' in p.stdout,'active_once':p.stdout.count('info string NnueExactInt32 active')==1,'backend_counter_nonzero':bool(re.search(r'int32_updates [1-9][0-9]*',p.stdout)),'late_mutation_rejected':'NnueExactInt32 must be set before the first go or bench' in p.stdout}
for label,extra in [('perft','go perft 1\n'),('nnue_disabled','setoption name UseNNUE value false\nbench 1\n')]:
 p2=subprocess.run([exe],input='uci\nsetoption name NnueExactInt32 value true\n'+extra+'quit\n',text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=45)
 print(label+':\n'+p2.stdout,end='');checks[label+'_no_false_active']=p2.returncode==0 and 'info string NnueExactInt32 active' not in p2.stdout
print(json.dumps(checks,sort_keys=True));sys.exit(0 if all(checks.values()) else 1)
