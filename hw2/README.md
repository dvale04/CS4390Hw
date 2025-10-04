# Advanced Compilers 

## CS 4390 - Fall 2025

## Data Flow Analysis Assignment 
- This assignment implements two data flow analyses using the worklist algorithm:
1. **Reaching Definitions Analysis** - Checks the assignments that define the current values of variables
2. **Available Expressions Analysis** - Checks which expressions have already been computed in the execution at a program point


## Usage
- Used turnt to construct tests. 

To run the analyses in Bril program:

bril2json < {filename} | python3 ../df.py

from test file
