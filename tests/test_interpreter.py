from __future__ import annotations

import unittest

from bytecode_interpreter.optimizer import BytecodeOptimizer
from bytecode_interpreter.parser import BytecodeParser
from bytecode_interpreter.vm import VirtualMachine, csharp_modulo, to_int32, truncating_division


def run_program(source: str, input_values: list[int] | None = None):
    instructions = BytecodeParser().parse(source)
    return VirtualMachine(input_values=input_values).execute(instructions)


class BytecodeInterpreterTests(unittest.TestCase):
    def test_basic_arithmetic_and_variables(self) -> None:
        result = run_program(
            """
            PUSH 10
            STORE a
            LOAD a
            PUSH 2
            MUL
            STORE b
            LOAD b
            PRINT
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["20"])

    def test_if_else(self) -> None:
        result = run_program(
            """
            PUSH 4
            STORE x
            LOAD x
            PUSH 2
            GT
            JZ ELSE_BLOCK
            PUSH 1
            PRINT
            JMP END_IF

            ELSE_BLOCK:
            PUSH 0
            PRINT

            END_IF:
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["1"])

    def test_function_call_with_numeric_addresses(self) -> None:
        result = run_program(
            """
            CALL 12
            HALT

            MAIN_START:
            PUSH 3
            PUSH 4
            STORE b
            STORE a
            CALL 52
            PUSH 0
            STORE r
            RET

            ADD_INICIO:
            LOAD a
            LOAD b
            ADD
            PRINT
            POP
            RET
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["7"])

    def test_while_loop(self) -> None:
        result = run_program(
            """
            PUSH 5
            STORE x
            LOOP_START:
            LOAD x
            PUSH 0
            GT
            JZ LOOP_END
            LOAD x
            PRINT
            LOAD x
            PUSH 1
            SUB
            STORE x
            JMP LOOP_START

            LOOP_END:
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["5", "4", "3", "2", "1"])

    def test_function_result_via_memory(self) -> None:
        result = run_program(
            """
            PUSH 3
            PUSH 7
            STORE b
            STORE a
            CALL FUNC_START
            LOAD r
            PRINT
            JMP END

            FUNC_START:
            LOAD a
            LOAD b
            ADD
            STORE r
            RET

            END:
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["10"])

    def test_read_consumes_configured_input(self) -> None:
        result = run_program(
            """
            READ
            STORE x
            LOAD x
            PRINT
            """,
            input_values=[42],
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["42"])

    def test_label_opcode_form_is_supported(self) -> None:
        result = run_program(
            """
            PUSH 0
            JNZ skip
            PUSH 50
            PRINT
            HALT
            LABEL skip
            PUSH 100
            PRINT
            HALT
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["50"])

    def test_arithmetic_uses_signed_32_bit_wraparound(self) -> None:
        result = run_program(
            """
            PUSH 2147483647
            PUSH 1
            ADD
            PRINT
            HALT
            """
        )

        self.assertTrue(result.success, result.error)
        self.assertEqual(result.output, ["-2147483648"])

    def test_errors_are_reported(self) -> None:
        division = run_program("PUSH 1\nPUSH 0\nDIV\n")
        missing_variable = run_program("LOAD x\n")
        bad_return = run_program("RET\n")

        self.assertFalse(division.success)
        self.assertIn("division by zero", division.error or "")
        self.assertFalse(missing_variable.success)
        self.assertIn("undefined variable", missing_variable.error or "")
        self.assertFalse(bad_return.success)
        self.assertIn("RET without", bad_return.error or "")

    def test_csharp_integer_math_semantics(self) -> None:
        self.assertEqual(truncating_division(-5, 2), -2)
        self.assertEqual(csharp_modulo(-5, 2), -1)
        self.assertEqual(to_int32(2147483648), -2147483648)

    def test_optimizer_reduces_constant_code(self) -> None:
        parser = BytecodeParser()
        instructions = parser.parse(
            """
            PUSH 10
            STORE x
            LOAD x
            PUSH 2
            MUL
            PRINT
            """
        )

        optimizer = BytecodeOptimizer()
        optimized = optimizer.optimize(instructions).instructions
        optimized_source = "\n".join(item.to_source() for item in optimized)

        self.assertLess(len(optimized), len(instructions))
        self.assertEqual(optimized_source, "PUSH 20\nPRINT")
        self.assertEqual(
            VirtualMachine().execute(optimized).output,
            VirtualMachine().execute(instructions).output,
        )


if __name__ == "__main__":
    unittest.main()
