"""Interpreter exception hierarchy."""

from __future__ import annotations


class InterpreterError(Exception):
    """Base class for errors reported with a source line when available."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.line_number = line_number

    def __str__(self) -> str:
        if self.line_number is None:
            return self.message
        return f"line {self.line_number}: {self.message}"


class ParseError(InterpreterError):
    """Raised when bytecode text cannot be parsed."""


class RuntimeInterpreterError(InterpreterError):
    """Raised when bytecode fails during execution."""
