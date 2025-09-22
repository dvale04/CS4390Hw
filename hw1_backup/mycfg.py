import json
import sys
from collections import OrderedDict, deque

TERMINATORS = 'jmp', 'br', 'ret'


def form_blocks(body):
    cur_block = []

    for instr in body:
        if 'op' in instr:  # an actual #instruction
            cur_block.append(instr)  # become list of instructions including the terminator

            # Check for terminator
            if instr['op'] in TERMINATORS:
                #need to terminate block and start new one
                yield cur_block  #formed a basic block
                cur_block = []

        else:  # A label
            #when hit label want to end the current basic block
            yield cur_block
            cur_block = [instr]

    #end to function no control operator no return consider
    #implicit return at the end of last basic block
    yield cur_block


def block_map(blocks):
    out = OrderedDict()  # maintains order
    # dictionary going to map names to entire blocks

    for block in blocks:
        #iterates over blocks and adds to dictionary
        if 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = 'b{}'.format(len(out))
        out[name] = block

    return out


def get_cfg(name2block):
    #given a name-to-block map, produce a mapping dictionary from block names to successor block names  - maps names of blocks to list of names of blocks that are successors of the one of left side
    out = {}
    keys = list(name2block.keys())
    for i, (name, block) in enumerate(name2block.items()):
        last = block[-1]
        if last['op'] in ('jmp', 'br'):
            succ = last['labels']
        elif last['op'] == 'ret':  #exit block
            succ = []

        else:
            if i == len(name2block) -1:
                succ = []
            else:  #block falls through to the next block
                succ = [list(name2block.keys())[i + 1]]

        out[name] = succ

    return out






def get_path_lengths(cfg, entry):
    """
    Compute the shortest path length (in edges) from the entry node to each node in the CFG.

    Parameters:
        cfg (dict): mapping {node: [successors]}
        entry (str): starting node

    Returns:
        dict: {node: distance from entry}, unreachable nodes are omitted
    """

    distance = {} 
    queue = deque([entry])
    distance[entry] = 0

    while queue:
        curr = queue.popleft()
        for successor in cfg.get(curr, []):
            if successor not in distance:
                    distance[successor] = distance[curr] + 1
                    queue.append(successor)

    return distance




def reverse_postorder(cfg, entry):
    """
    Compute reverse postorder (RPO) for a CFG.

    Parameters:
        cfg (dict): mapping {node: [successors]}
        entry (str): starting node

    Returns:
        list: nodes in reverse postorder
    """
    visited = set()
    order = []

    def dfs(curr):
        visited.add(curr)
        for successor in cfg.get(curr, []):
            if successor not in visited:
                dfs(successor)
        order.append(curr)
    
    dfs(entry)
    order.reverse()
    return order



def find_back_edges(cfg, entry):

    """
    Find back edges in a CFG using DFS.

    Parameters:
        cfg(dict): mapping {node: [successors]}
        entry(str): starting node

    Returns: list of edges (u,v) where u->v is a back edge
    """
    visited = set()
    stack = set()
    back_edges = []

    def dfs(u):
        visited.add(u)
        stack.add(u)
        for v in cfg.get(u, []):
            if v not in visited:
                dfs(v)
            elif v in stack:
                back_edges.append((u, v))
        stack.remove(u)
    
    dfs(entry)
    return back_edges



def is_reducible(cfg, entry):


    """
    Determine whether a CFG is reducible.

    Parameters:
        cfg(dict): mapping {node: [successors]}
        entry(str): starting node

    Returns: True if the CFG is reducible or False if the CFG is irreducible
    """
    back_edges = find_back_edges(cfg, entry)

    if not back_edges:
        return True
    
    nodes = list(cfg.keys())
    #use MUST analysis approach
    dom = {node: set(nodes) for node in nodes}

    dom[entry] = {entry}

    changed = True
    while changed:
        changed = False
        for node in nodes:
            if node == entry:
                continue 

            predecessors = [p for p in nodes if node in cfg.get(p, [])]
            
            if not predecessors: # for unreachable nodes
                continue

            new_dom = set.intersection(*(dom[p] for p in predecessors))
            
            new_dom.add(node)

            # dominators changed
            if new_dom!= dom[node]:
                dom[node] = new_dom
                changed = True 


    for u, v in back_edges:
        if v not in dom[u]:
            return False 
            
    return True 
    









def mycfg():
    prog = json.load(sys.stdin)
    for func in prog ['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        cfg = get_cfg(name2block)

        print('digraph {} {{'.format(func['name']))
        for name in name2block:
            print(' {};'.format(name))
        for name, succs in cfg.items():
            for succ in succs:
                print(' {} -> {};'.format(name, succ))
        print('}')


if __name__ == '__main__':
    mycfg()

	



