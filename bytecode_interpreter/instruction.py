"""Instruction model and opcode definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OpCode(StrEnum):
    PUSH = "PUSH"
    POP = "POP"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    MOD = "MOD"
    NEG = "NEG"
    STORE = "STORE"
    LOAD = "LOAD"
    JMP = "JMP"
    JZ = "JZ"
    JNZ = "JNZ"
    HALT = "HALT"
    EQ = "EQ"
    NEQ = "NEQ"
    LT = "LT"
    GT = "GT"
    LE = "LE"
    GE = "GE"
    CALL = "CALL"
    RET = "RET"
    PRINT = "PRINT"
    READ = "READ"
    LABEL = "LABEL"
    EMPTY = "EMPTY"


REQUIRES_ARGUMENT = {
    OpCode.PUSH,
    OpCode.STORE,
    OpCode.LOAD,
    OpCode.JMP,
    OpCode.JZ,
    OpCode.JNZ,
    OpCode.CALL,
}

NO_ARGUMENT = {
    OpCode.POP,
    OpCode.ADD,
    OpCode.SUB,
    OpCode.MUL,
    OpCode.DIV,
    OpCode.MOD,
    OpCode.NEG,
    OpCode.EQ,
    OpCode.NEQ,
    OpCode.LT,
    OpCode.GT,
    OpCode.LE,
    OpCode.GE,
    OpCode.RET,
    OpCode.PRINT,
    OpCode.READ,
    OpCode.HALT,
}

CONTROL_FLOW = {
    OpCode.JMP,
    OpCode.JZ,
    OpCode.JNZ,
    OpCode.CALL,
    OpCode.RET,
    OpCode.HALT,
}

ARITHMETIC_BINARY = {
    OpCode.ADD,
    OpCode.SUB,
    OpCode.MUL,
    OpCode.DIV,
    OpCode.MOD,
}

COMPARISON = {
    OpCode.EQ,
    OpCode.NEQ,
    OpCode.LT,
    OpCode.GT,
    OpCode.LE,
    OpCode.GE,
}


@dataclass(frozen=True)
class Instruction:
    opcode: OpCode
    argument: str | None = None
    line_number: int = 0
    raw_text: str = ""

    def to_source(self) -> str:
        if self.opcode == OpCode.EMPTY:
            return ""
        if self.opcode == OpCode.LABEL:
            return f"{self.argument}:"
        if self.argument is None:
            return self.opcode.value
        return f"{self.opcode.value} {self.argument}"

    def __str__(self) -> str:
        return self.to_source()
