"""Parser for the bytecode tiny language."""

from __future__ import annotations

from pathlib import Path

from .errors import ParseError
from .instruction import Instruction, NO_ARGUMENT, OpCode, REQUIRES_ARGUMENT


class BytecodeParser:
    """Converts UTF-8 bytecode text into validated instructions."""

    def parse_file(self, path: str | Path) -> list[Instruction]:
        return self.parse(Path(path).read_text(encoding="utf-8"))

    def parse(self, text: str) -> list[Instruction]:
        instructions: list[Instruction] = []

        for index, original_line in enumerate(text.splitlines(), start=1):
            try:
                instructions.append(self._parse_line(original_line, index))
            except ParseError:
                raise
            except Exception as exc:
                raise ParseError(str(exc), index) from exc

        return instructions

    def _parse_line(self, original_line: str, line_number: int) -> Instruction:
        line = original_line.strip()

        if not line or line.startswith("#"):
            return Instruction(OpCode.EMPTY, line_number=line_number, raw_text=original_line)

        comment_start = line.find("#")
        if comment_start >= 0:
            line = line[:comment_start].strip()

        if not line:
            return Instruction(OpCode.EMPTY, line_number=line_number, raw_text=original_line)

        if line.endswith(":"):
            label_name = line[:-1].strip()
            if not label_name:
                raise ParseError("empty label", line_number)
            if any(char.isspace() for char in label_name):
                raise ParseError(f"invalid label name: {label_name}", line_number)
            return Instruction(
                OpCode.LABEL,
                label_name,
                line_number=line_number,
                raw_text=original_line,
            )

        parts = line.split()
        op_text = parts[0].upper()
        try:
            opcode = OpCode(op_text)
        except ValueError as exc:
            raise ParseError(f"unknown opcode: {parts[0]}", line_number) from exc

        argument = parts[1] if len(parts) > 1 else None
        if len(parts) > 2:
            raise ParseError(f"instruction {opcode.value} has too many arguments", line_number)

        self._validate_instruction(opcode, argument, line_number)
        return Instruction(opcode, argument, line_number=line_number, raw_text=original_line)

    @staticmethod
    def _validate_instruction(
        opcode: OpCode,
        argument: str | None,
        line_number: int,
    ) -> None:
        if opcode in REQUIRES_ARGUMENT and not argument:
            raise ParseError(f"instruction {opcode.value} requires an argument", line_number)
        if opcode in NO_ARGUMENT and argument:
            raise ParseError(f"instruction {opcode.value} does not accept an argument", line_number)
