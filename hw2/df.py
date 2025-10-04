import sys
import json
from collections import namedtuple

from form_blocks import form_blocks
import cfg

# A single dataflow analysis consists of these part:
# - forward: True for forward, False for backward.
# - init: An initial value (bottom or top of the latice).
# - merge: Take a list of values and produce a single value.
# - transfer: The transfer function.
Analysis = namedtuple("Analysis", ["forward", "init", "merge", "transfer"])


def union(sets):
    out = set()
    for s in sets:
        out.update(s)
    return out

def intersection(sets):
    if not sets: 
        return set()
    out = sets[0].copy()
    for s in sets[1:]:
        out.intersection_update(s)
    return out


def df_worklist(blocks, analysis):
    """The worklist algorithm for iterating a data flow analysis to a
    fixed point.
    """
    preds, succs = cfg.edges(blocks)

    # Switch between directions.
    if analysis.forward:
        first_block = list(blocks.keys())[0]  # Entry.
        in_edges = preds
        out_edges = succs
    else:
        first_block = list(blocks.keys())[-1]  # Exit.
        in_edges = succs
        out_edges = preds

    # Initialize.
    in_ = {first_block: analysis.init}
    out = {node: analysis.init for node in blocks}

    # Iterate.
    worklist = list(blocks.keys())
    while worklist:
        node = worklist.pop(0)

        inval = analysis.merge(out[n] for n in in_edges[node])
        in_[node] = inval

        outval = analysis.transfer(blocks[node], inval)

        if outval != out[node]:
            out[node] = outval
            worklist += out_edges[node]

    if analysis.forward:
        return in_, out
    else:
        return out, in_


def fmt(val):
    """Guess a good way to format a data flow value. (Works for sets and
    dicts, at least.)
    """
    if isinstance(val, set):
        if val:
            return ", ".join(v for v in sorted(val))
        else:
            return "∅"
    elif isinstance(val, dict):
        if val:
            return ", ".join("{}: {}".format(k, v) for k, v in sorted(val.items()))
        else:
            return "∅"
    else:
        return str(val)


def run_df(bril, analysis):
    for func in bril["functions"]:
        # Form the CFG.
        blocks = cfg.block_map(form_blocks(func["instrs"]))
        cfg.add_terminators(blocks)

        in_, out = df_worklist(blocks, analysis)
        for block in blocks:
            print("{}:".format(block))
            print("  in: ", fmt(in_[block]))
            print("  out:", fmt(out[block]))


def gen(block):
    """Variables that are written in the block."""
    return {i["dest"] for i in block if "dest" in i}


def use(block):
    """Variables that are read before they are written in the block."""
    defined = set()  # Locally defined.
    used = set()
    for i in block:
        used.update(v for v in i.get("args", []) if v not in defined)
        if "dest" in i:
            defined.add(i["dest"])
    return used


def cprop_transfer(block, in_vals):
    out_vals = dict(in_vals)
    for instr in block:
        if "dest" in instr:
            if instr["op"] == "const":
                out_vals[instr["dest"]] = instr["value"]
            else:
                out_vals[instr["dest"]] = "?"
    return out_vals


def cprop_merge(vals_list):
    out_vals = {}
    for vals in vals_list:
        for name, val in vals.items():
            if val == "?":
                out_vals[name] = "?"
            else:
                if name in out_vals:
                    if out_vals[name] != val:
                        out_vals[name] = "?"
                else:
                    out_vals[name] = val
    return out_vals 



def reaching_defs(block, in_vals):
    gen_set = set()
    kill_set = set()

    defined_vars = set()

    for instr in block:
        if 'dest' in instr:
            var = instr['dest']
            def_id = f"{var}@{id(instr)}"
            gen_set.add(def_id)
            defined_vars.add(var)

    for def_id in in_vals:
        var = def_id.split('@')[0]
        if var in defined_vars:
            kill_set.add(def_id)  

    return gen_set.union(in_vals - kill_set)

def available_exprs(block, in_vals):
    gen_set = set()
    kill_set = set()

    defined_vars = set()

    expressions = []
    for instr in block:
        if 'args' in instr and len(instr['args']) > 0:
            # Create expression identifier
            args_str = ','.join(sorted(instr['args']))
            expr_id = f"{instr['op']}({args_str})"
            expressions.append((expr_id, instr['args']))
        
        if 'dest' in instr:
            defined_vars.add(instr['dest'])

    for expr_id, args in expressions:   

        uses_defined_var = any(arg in defined_vars for arg in args)
        if not uses_defined_var:
                gen_set.add(expr_id) 
#kill the expressions
    for expr_id, args in expressions:
        for var in args:
            if var in defined_vars:
                kill_set.add(expr_id) 
#use transfer function: out = gen ∪ (in - kill)
    return gen_set.union(in_vals - kill_set)               

ANALYSES = {
    # A really really basic analysis that just accumulates all the
    # currently-defined variables.
    "defined": Analysis(
        True,
        init=set(),
        merge=union,
        transfer=lambda block, in_: in_.union(gen(block)),
    ),
    # Live variable analysis: the variables that are both defined at a
    # given point and might be read along some path in the future.
    "live": Analysis(
        False,
        init=set(),
        merge=union,
        transfer=lambda block, out: use(block).union(out - gen(block)),
    ),
    # A simple constant propagation pass.
    "cprop": Analysis(
        True,
        init={},
        merge=cprop_merge,
        transfer=cprop_transfer,
    ),
    "reaching-defs": Analysis(
        True,           # Forward analysis
        init=set(),     # Start with empty set for entry block
        merge=union,    # Union for may-analysis
        transfer=reaching_defs,
    ),
    "available-exprs": Analysis(
        True,               # Forward analysis
        init=set(),         # Start with empty set for entry block  
        merge=intersection, # Intersection for must-analysis
        transfer=available_exprs,
    ),
}

if __name__ == "__main__":
    bril = json.load(sys.stdin)
    run_df(bril, ANALYSES[sys.argv[1]])
