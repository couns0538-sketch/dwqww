"""S10 d11 activation gate; partial first implementation retained as RED proof."""
import re
def validate_activity(uci,off,on,option):
 def nodes(text):
  matches=re.findall(r'^info string bench depth 11 nodes ([0-9]+) time [0-9]+ nps [0-9]+$',text,re.M)
  if len(matches)!=1:raise ValueError('one depth11 benchmark record required')
  return int(matches[0])
 return {'off_nodes':nodes(off),'on_nodes':nodes(on)}
