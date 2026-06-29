"""Conservative bytecode optimizer used for the optional extra credit."""

from __future__ import annotations

from dataclasses import dataclass, field

from .instruction import ARITHMETIC_BINARY, COMPARISON, CONTROL_FLOW, Instruction, OpCode
from .vm import csharp_modulo, is_int_literal, truncating_division


@dataclass
class OptimizationResult:
    instructions: list[Instruction]
    before_size: int
    after_size: int
    optimizations_applied: int = 0
    warnings: list[str] = field(default_factory=list)


class BytecodeOptimizer:
    """Applies local optimizations that preserve behavior for label-based code."""

    def __init__(self, max_passes: int = 10) -> None:
        self.max_passes = max_passes
        self.before_size = 0
        self.after_size = 0

    def optimize(self, instructions: list[Instruction]) -> OptimizationResult:
        self.before_size = len(instructions)

        if has_numeric_control_target(instructions):
            self.after_size = len(instructions)
            return OptimizationResult(
                instructions=list(instructions),
                before_size=self.before_size,
                after_size=self.after_size,
                warnings=[
                    "optimization skipped because numeric jump/call targets depend on instruction indexes"
                ],
            )

        optimized = [item for item in instructions if item.opcode != OpCode.EMPTY]
        optimizations = self.before_size - len(optimized)

        for _ in range(self.max_passes):
            changed = False
            before_pass = len(optimized)

            optimized, count = self._constant_propagation(optimized)
            optimizations += count
            changed = changed or count > 0

            optimized, count = self._constant_folding(optimized)
            optimizations += count
            changed = changed or count > 0

            optimized, count = self._remove_push_pop(optimized)
            optimizations += count
            changed = changed or count > 0

            optimized, count = self._dead_store_elimination(optimized)
            optimizations += count
            changed = changed or count > 0

            if not changed and len(optimized) == before_pass:
                break

        self.after_size = len(optimized)
        return OptimizationResult(optimized, self.before_size, self.after_size, optimizations)

    def _constant_propagation(
        self,
        instructions: list[Instruction],
    ) -> tuple[list[Instruction], int]:
        result: list[Instruction] = []
        constants: dict[str, int] = {}
        count = 0

        for index, current in enumerate(instructions):
            if current.opcode == OpCode.STORE and current.argument is not None:
                previous = instructions[index - 1] if index > 0 else None
                if (
                    previous is not None
                    and previous.opcode == OpCode.PUSH
                    and previous.argument is not None
                    and is_int_literal(previous.argument)
                ):
                    constants[current.argument] = int(previous.argument)
                else:
                    constants.pop(current.argument, None)

            if current.opcode in CONTROL_FLOW or current.opcode == OpCode.LABEL:
                constants.clear()

            if (
                current.opcode == OpCode.LOAD
                and current.argument is not None
                and current.argument in constants
            ):
                result.append(
                    Instruction(
                        OpCode.PUSH,
                        str(constants[current.argument]),
                        current.line_number,
                        current.raw_text,
                    )
                )
                count += 1
                continue

            result.append(current)

        return result, count

    def _constant_folding(
        self,
        instructions: list[Instruction],
    ) -> tuple[list[Instruction], int]:
        result: list[Instruction] = []
        index = 0
        count = 0

        while index < len(instructions):
            current = instructions[index]

            if (
                current.opcode == OpCode.PUSH
                and current.argument is not None
                and is_int_literal(current.argument)
                and index + 1 < len(instructions)
                and instructions[index + 1].opcode == OpCode.NEG
            ):
                result.append(
                    Instruction(
                        OpCode.PUSH,
                        str(-int(current.argument)),
                        current.line_number,
                        current.raw_text,
                    )
                )
                index += 2
                count += 1
                continue

            if (
                current.opcode == OpCode.PUSH
                and current.argument is not None
                and is_int_literal(current.argument)
                and index + 2 < len(instructions)
                and instructions[index + 1].opcode == OpCode.PUSH
                and instructions[index + 1].argument is not None
                and is_int_literal(instructions[index + 1].argument)
                and (
                    instructions[index + 2].opcode in ARITHMETIC_BINARY
                    or instructions[index + 2].opcode in COMPARISON
                )
            ):
                folded = evaluate_constant_operation(
                    int(current.argument),
                    int(instructions[index + 1].argument),
                    instructions[index + 2].opcode,
                )
                if folded is not None:
                    result.append(
                        Instruction(
                            OpCode.PUSH,
                            str(folded),
                            current.line_number,
                            current.raw_text,
                        )
                    )
                    index += 3
                    count += 1
                    continue

            result.append(current)
            index += 1

        return result, count

    def _remove_push_pop(
        self,
        instructions: list[Instruction],
    ) -> tuple[list[Instruction], int]:
        result: list[Instruction] = []
        index = 0
        count = 0

        while index < len(instructions):
            current = instructions[index]
            if (
                current.opcode == OpCode.PUSH
                and index + 1 < len(instructions)
                and instructions[index + 1].opcode == OpCode.POP
            ):
                index += 2
                count += 1
                continue

            result.append(current)
            index += 1

        return result, count

    def _dead_store_elimination(
        self,
        instructions: list[Instruction],
    ) -> tuple[list[Instruction], int]:
        live_stores: set[int] = set()

        for index, instruction in enumerate(instructions):
            if instruction.opcode != OpCode.STORE or instruction.argument is None:
                continue

            var_name = instruction.argument
            for later in instructions[index + 1 :]:
                if later.opcode == OpCode.LOAD and later.argument == var_name:
                    live_stores.add(index)
                    break
                if later.opcode == OpCode.STORE and later.argument == var_name:
                    break
                if later.opcode in CONTROL_FLOW or later.opcode == OpCode.LABEL:
                    live_stores.add(index)
                    break

        result: list[Instruction] = []
        index = 0
        count = 0

        while index < len(instructions):
            current = instructions[index]
            if (
                current.opcode == OpCode.PUSH
                and index + 1 < len(instructions)
                and instructions[index + 1].opcode == OpCode.STORE
                and index + 1 not in live_stores
            ):
                index += 2
                count += 1
                continue

            result.append(current)
            index += 1

        return result, count


def has_numeric_control_target(instructions: list[Instruction]) -> bool:
    return any(
        instruction.opcode in {OpCode.JMP, OpCode.JZ, OpCode.JNZ, OpCode.CALL}
        and instruction.argument is not None
        and is_int_literal(instruction.argument)
        for instruction in instructions
    )


def evaluate_constant_operation(a: int, b: int, opcode: OpCode) -> int | None:
    if opcode == OpCode.ADD:
        return a + b
    if opcode == OpCode.SUB:
        return a - b
    if opcode == OpCode.MUL:
        return a * b
    if opcode == OpCode.DIV:
        return None if b == 0 else truncating_division(a, b)
    if opcode == OpCode.MOD:
        return None if b == 0 else csharp_modulo(a, b)
    if opcode == OpCode.EQ:
        return 1 if a == b else 0
    if opcode == OpCode.NEQ:
        return 1 if a != b else 0
    if opcode == OpCode.LT:
        return 1 if a < b else 0
    if opcode == OpCode.GT:
        return 1 if a > b else 0
    if opcode == OpCode.LE:
        return 1 if a <= b else 0
    if opcode == OpCode.GE:
        return 1 if a >= b else 0
    return None
