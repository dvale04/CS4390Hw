import json
import sys
from collections import OrderedDict

TERMINATORS = 'imp', 'br', 'ret'


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


def block_map(block):
    out = OrderedDict()  # dictionary going to map names to entire blocks

    for block in blocks:
        #iterates over blocks and adds to dictionary
        if 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = 'b{}'.format(len(out))
        out[name] = block

    return out


def get_cfg():
    #given a name-to-block map, produce a mapping dictionary from block names to successor block names  - maps names of blocks to list of names of blocks that are successors of the one of left side
    out = {}
    for name, block in name2block.items():
        last = block[-1]
        if last['op'] in ('imp', 'br'):
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


def mycfg():
    prog = json.load(sys.stdin)
    for func in prog ['functions']:
        name2block = block_map(form_blocks(func['instrs']))
        for name, block in name2block.items():
            print(name)
            print('    ', block)
        cfg = get_cfg(name2block)
        print(name2block)

        for block in name2block.values():
            pass


if __name__ == 'main':
    mycfg()

	



