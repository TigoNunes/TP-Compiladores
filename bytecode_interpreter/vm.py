"""Stack virtual machine for the bytecode tiny language."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .errors import RuntimeInterpreterError
from .instruction import ARITHMETIC_BINARY, COMPARISON, Instruction, OpCode

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
UINT32_MOD = 2**32


@dataclass
class ExecutionResult:
    success: bool
    output: list[str] = field(default_factory=list)
    executed_instructions: int = 0
    final_stack: list[int] = field(default_factory=list)
    final_memory: dict[str, int] = field(default_factory=dict)
    error: str | None = None


class VirtualMachine:
    """Executes bytecode instructions on a stack machine."""

    def __init__(
        self,
        input_values: Iterable[int] | None = None,
        max_stack_size: int = 10_000,
        max_steps: int = 10_000_000,
    ) -> None:
        self.max_stack_size = max_stack_size
        self.max_steps = max_steps
        self._initial_input = list(input_values or [])
        self.reset()

    def set_input(self, input_values: Iterable[int]) -> None:
        self._initial_input = list(input_values)
        self.input_buffer = list(self._initial_input)

    def reset(self) -> None:
        self.stack: list[int] = []
        self.memory: dict[str, int] = {}
        self.call_stack: list[int] = []
        self.labels: dict[str, int] = {}
        self.output: list[str] = []
        self.input_buffer = list(self._initial_input)
        self.instructions: list[Instruction] = []
        self.ip = 0
        self.halted = False
        self.executed_instructions = 0

    def execute(self, program: list[Instruction]) -> ExecutionResult:
        self.reset()
        self.instructions = program

        try:
            self._build_label_map()

            while not self.halted and self.ip < len(self.instructions):
                if self.executed_instructions >= self.max_steps:
                    raise RuntimeInterpreterError(
                        f"maximum instruction count exceeded ({self.max_steps})",
                        self._current_line(),
                    )

                instruction = self.instructions[self.ip]
                self._execute_instruction(instruction)
                self.executed_instructions += 1
                self.ip += 1

            return ExecutionResult(
                success=True,
                output=list(self.output),
                executed_instructions=self.executed_instructions,
                final_stack=list(self.stack),
                final_memory=dict(self.memory),
            )
        except RuntimeInterpreterError as exc:
            return ExecutionResult(
                success=False,
                output=list(self.output),
                executed_instructions=self.executed_instructions,
                final_stack=list(self.stack),
                final_memory=dict(self.memory),
                error=str(exc),
            )

    def _build_label_map(self) -> None:
        for index, instruction in enumerate(self.instructions):
            if instruction.opcode != OpCode.LABEL:
                continue
            assert instruction.argument is not None
            if instruction.argument in self.labels:
                raise RuntimeInterpreterError(
                    f"duplicate label: {instruction.argument}",
                    instruction.line_number,
                )
            self.labels[instruction.argument] = index

    def _execute_instruction(self, instruction: Instruction) -> None:
        opcode = instruction.opcode

        if opcode == OpCode.EMPTY or opcode == OpCode.LABEL:
            return
        if opcode == OpCode.PUSH:
            self._push(self._parse_int(instruction.argument, instruction))
            return
        if opcode == OpCode.POP:
            self._pop(instruction)
            return
        if opcode in ARITHMETIC_BINARY:
            self._execute_arithmetic(opcode, instruction)
            return
        if opcode == OpCode.NEG:
            self._push(-self._pop(instruction), instruction)
            return
        if opcode == OpCode.STORE:
            assert instruction.argument is not None
            self.memory[instruction.argument] = self._pop(instruction)
            return
        if opcode == OpCode.LOAD:
            assert instruction.argument is not None
            if instruction.argument not in self.memory:
                raise RuntimeInterpreterError(
                    f"undefined variable: {instruction.argument}",
                    instruction.line_number,
                )
            self._push(self.memory[instruction.argument], instruction)
            return
        if opcode == OpCode.JMP:
            assert instruction.argument is not None
            self._jump(instruction.argument, instruction)
            return
        if opcode == OpCode.JZ:
            assert instruction.argument is not None
            if self._pop(instruction) == 0:
                self._jump(instruction.argument, instruction)
            return
        if opcode == OpCode.JNZ:
            assert instruction.argument is not None
            if self._pop(instruction) != 0:
                self._jump(instruction.argument, instruction)
            return
        if opcode == OpCode.HALT:
            self.halted = True
            return
        if opcode in COMPARISON:
            self._execute_comparison(opcode, instruction)
            return
        if opcode == OpCode.CALL:
            assert instruction.argument is not None
            self._call(instruction.argument, instruction)
            return
        if opcode == OpCode.RET:
            self._return(instruction)
            return
        if opcode == OpCode.PRINT:
            value = self._pop(instruction)
            self.output.append(str(value))
            self._push(value, instruction)
            return
        if opcode == OpCode.READ:
            if not self.input_buffer:
                raise RuntimeInterpreterError("READ input buffer is empty", instruction.line_number)
            self._push(self.input_buffer.pop(0), instruction)
            return

        raise RuntimeInterpreterError(f"unsupported opcode: {opcode}", instruction.line_number)

    def _execute_arithmetic(self, opcode: OpCode, instruction: Instruction) -> None:
        b = self._pop(instruction)
        a = self._pop(instruction)

        if opcode == OpCode.ADD:
            result = a + b
        elif opcode == OpCode.SUB:
            result = a - b
        elif opcode == OpCode.MUL:
            result = a * b
        elif opcode == OpCode.DIV:
            if b == 0:
                raise RuntimeInterpreterError("division by zero", instruction.line_number)
            result = truncating_division(a, b)
        elif opcode == OpCode.MOD:
            if b == 0:
                raise RuntimeInterpreterError("modulo by zero", instruction.line_number)
            result = csharp_modulo(a, b)
        else:
            raise RuntimeInterpreterError(f"invalid arithmetic opcode: {opcode}", instruction.line_number)

        self._push(result, instruction)

    def _execute_comparison(self, opcode: OpCode, instruction: Instruction) -> None:
        b = self._pop(instruction)
        a = self._pop(instruction)

        if opcode == OpCode.EQ:
            result = a == b
        elif opcode == OpCode.NEQ:
            result = a != b
        elif opcode == OpCode.LT:
            result = a < b
        elif opcode == OpCode.GT:
            result = a > b
        elif opcode == OpCode.LE:
            result = a <= b
        elif opcode == OpCode.GE:
            result = a >= b
        else:
            raise RuntimeInterpreterError(f"invalid comparison opcode: {opcode}", instruction.line_number)

        self._push(1 if result else 0, instruction)

    def _jump(self, target: str, instruction: Instruction) -> None:
        self.ip = self._resolve_target(target, instruction) - 1

    def _call(self, target: str, instruction: Instruction) -> None:
        return_address = self.ip + 1
        target_index = self._resolve_target(target, instruction)
        self.call_stack.append(return_address)
        self._push(return_address, instruction)
        self.ip = target_index - 1

    def _return(self, instruction: Instruction) -> None:
        if not self.call_stack:
            raise RuntimeInterpreterError("RET without a matching CALL", instruction.line_number)

        return_address = self.call_stack.pop()
        self._remove_return_address_from_data_stack(return_address)
        self.ip = return_address - 1

    def _remove_return_address_from_data_stack(self, return_address: int) -> None:
        if not self.stack:
            return

        if self.stack[-1] == return_address:
            self.stack.pop()
            return

        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index] == return_address:
                del self.stack[index]
                return

    def _resolve_target(self, target: str, instruction: Instruction) -> int:
        if is_int_literal(target):
            address = int(target)
            if address % 4 != 0:
                raise RuntimeInterpreterError(
                    f"invalid address {address}: numeric addresses must be multiples of 4",
                    instruction.line_number,
                )
            index = address // 4
        else:
            if target not in self.labels:
                raise RuntimeInterpreterError(f"label not found: {target}", instruction.line_number)
            index = self.labels[target]

        if index < 0 or index >= len(self.instructions):
            raise RuntimeInterpreterError(f"jump target out of bounds: {target}", instruction.line_number)
        return index

    def _parse_int(self, argument: str | None, instruction: Instruction) -> int:
        if argument is None or not is_int_literal(argument):
            raise RuntimeInterpreterError(f"invalid integer argument: {argument}", instruction.line_number)
        return int(argument)

    def _pop(self, instruction: Instruction) -> int:
        if not self.stack:
            raise RuntimeInterpreterError("stack underflow", instruction.line_number)
        return self.stack.pop()

    def _push(self, value: int, instruction: Instruction | None = None) -> None:
        if len(self.stack) >= self.max_stack_size:
            line_number = instruction.line_number if instruction is not None else self._current_line()
            raise RuntimeInterpreterError("stack overflow", line_number)
        self.stack.append(to_int32(value))

    def _current_line(self) -> int | None:
        if 0 <= self.ip < len(self.instructions):
            return self.instructions[self.ip].line_number
        return None


def is_int_literal(value: str) -> bool:
    try:
        int(value)
    except ValueError:
        return False
    return True


def to_int32(value: int) -> int:
    value %= UINT32_MOD
    if value > INT32_MAX:
        value -= UINT32_MOD
    return value


def truncating_division(a: int, b: int) -> int:
    quotient = abs(a) // abs(b)
    if (a < 0) ^ (b < 0):
        return -quotient
    return quotient


def csharp_modulo(a: int, b: int) -> int:
    return a - truncating_division(a, b) * b
