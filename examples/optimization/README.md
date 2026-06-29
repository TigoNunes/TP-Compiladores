# Optimization examples

Run any example with:

```bash
python main.py --dump-optimized examples/optimization/example_01.before.bytecode
```

The optimizer is conservative: it skips programs that use numeric jump/call targets, because reducing
the instruction list would change those addresses.

## Included examples

1. `example_01`: folds `PUSH 2`, `PUSH 3`, `ADD` into `PUSH 5`.
2. `example_02`: folds a chain of constant arithmetic into one constant.
3. `example_03`: folds unary negation.
4. `example_04`: folds a constant comparison.
5. `example_05`: propagates a constant variable, folds the expression, and removes the dead store.
