# Data Flow Analysis Assignment

## Overview
This assignment implements two data flow analyses using the worklist algorithm:
1. **Reaching Definitions Analysis** - Tracks which variable definitions reach each program point
2. **Available Expressions Analysis** - Identifies expressions computed on all paths to each program point

## Files
- `df_analysis.py` - Main implementation with both analyses
- `test/` - Test cases organized by analysis type
- `README.md` - This file

## Usage

### Running Analyses
```bash
# Reaching Definitions
bril2json < program.bril | python3 df_analysis.py reaching-defs

# Available Expressions  
bril2json < program.bril | python3 df_analysis.py available-exprs
