"""Command line interface for the bytecode interpreter."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .errors import InterpreterError
from .optimizer import BytecodeOptimizer
from .parser import BytecodeParser
from .vm import VirtualMachine


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        source = read_program(args.program)
        input_values = parse_input_values(args.input)
        parser = BytecodeParser()
        instructions = parser.parse(source)

        if args.optimize or args.dump_optimized:
            optimizer = BytecodeOptimizer()
            optimization = optimizer.optimize(instructions)
            instructions = optimization.instructions

            for warning in optimization.warnings:
                print(f"Warning: {warning}", file=sys.stderr)

        if args.dump_optimized:
            sys.stdout.write(render_program(instructions))
            return 0

        vm = VirtualMachine(input_values=input_values, max_steps=args.max_steps)
        result = vm.execute(instructions)
        if not result.success:
            print(format_runtime_error(result.error or "runtime error"))
            return 0

        if result.output:
            sys.stdout.write("\n".join(result.output))
            sys.stdout.write("\n")
        return 0
    except (OSError, InterpreterError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interprets the stack bytecode language from the Compilers assignment."
    )
    parser.add_argument(
        "program",
        nargs="?",
        help="Optional bytecode file. If omitted, the program is read from stdin.",
    )
    parser.add_argument(
        "--input",
        default="",
        help="Whitespace or comma separated integer values consumed by READ.",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Optimize bytecode before executing it.",
    )
    parser.add_argument(
        "--dump-optimized",
        action="store_true",
        help="Print optimized bytecode instead of executing it.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=10_000_000,
        help="Maximum executed instructions before aborting.",
    )
    return parser


def read_program(path: str | None) -> str:
    if path is None:
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def parse_input_values(raw: str) -> list[int]:
    if not raw.strip():
        return []
    return [int(part) for part in re.split(r"[\s,]+", raw.strip()) if part]


def render_program(instructions: list) -> str:
    lines = [instruction.to_source() for instruction in instructions]
    return "\n".join(lines).rstrip() + ("\n" if lines else "")


def format_runtime_error(error: str) -> str:
    normalized = error.lower()
    if "division by zero" in normalized:
        return "# error: div by zero"
    if "modulo by zero" in normalized:
        return "# error: mod by zero"
    if "stack overflow" in normalized:
        return "# error: stack overflow"
    if "stack underflow" in normalized:
        return "# error: stack underflow"
    if "undefined variable" in normalized:
        return "# error: undefined variable"
    if "label not found" in normalized:
        return "# error: label not found"
    if "ret without" in normalized:
        return "# error: ret without call"
    if "read input buffer is empty" in normalized:
        return "# error: read input empty"
    return f"# error: {error}"


if __name__ == "__main__":
    raise SystemExit(main())
