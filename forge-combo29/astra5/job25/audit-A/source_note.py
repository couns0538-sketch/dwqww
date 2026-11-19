"""Record the verified spots controlling hard-node publication and UCI reporting."""
from pathlib import Path
from hashlib import sha256
root=Path(__file__).resolve().parent.parent
for tree in ['r15d','kF']:
    src=(root/'builds'/tree/'src/search.cpp')
    lines=src.read_text().splitlines()
    print(tree,'src/search.cpp','sha256',sha256(src.read_bytes()).hexdigest())
    needles=['std::uint64_t Worker::total_nodes() const','bool Worker::should_stop_with(', 'node_limit_specified_ && total_nodes()', 'bool Worker::should_stop()','nodes_.store(local_nodes_',  'const std::uint64_t nodes = use_node_override', 'result.nodes = total_nodes() + extra_nodes_', 'if (emit_info && soft_node_limit_ != 0)']
    for needle in needles:
        hits=[(i,s.strip()) for i,s in enumerate(lines,1) if needle in s]
        assert hits, (tree,needle)
        for idx,line in hits:print(f'{idx}: {line}')

    if tree=='r15d':
        for i,line in enumerate(lines,1):
            if '&& should_stop()) aborted_' in line: print(i,line.strip())
    else:
        for i,line in enumerate(lines,1):
            if 'fast_single_node_stop_ = parent_worker_' in line:
                print('worker-count eligibility',i,' '.join(l.strip() for l in lines[i-1:i+2]))
        header=root/'builds'/tree/'include/forge/search.hpp'
        for i,line in enumerate(header.read_text().splitlines(),1):
            if 'return ((local_nodes_ & 1023U)' in line: print('search.hpp',i,line.strip())
