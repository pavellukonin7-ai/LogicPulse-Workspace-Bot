import math
import unittest

from tg_LogicPulse_bot.services.calculator import CalculatorError, calculate, format_result


class CalculatorTests(unittest.TestCase):
    def test_arithmetic_and_power(self):
        self.assertEqual(calculate("(2 + 3) * 4^2"), 80)

    def test_percent_in_russian(self):
        self.assertAlmostEqual(calculate("18% от 1250"), 225)

    def test_decimal_comma(self):
        self.assertAlmostEqual(calculate("1,5 + 2,25"), 3.75)

    def test_functions_and_constants(self):
        self.assertAlmostEqual(calculate("sin(pi / 2) + log(1000, 10)"), 4)

    def test_function_arguments_without_spaces(self):
        self.assertAlmostEqual(calculate("log(1000,10)"), 3)

    def test_complex_numbers(self):
        self.assertEqual(format_result(calculate("(3 + 4*i)^2")), "-7 + 24i")

    def test_negative_cube_root(self):
        self.assertAlmostEqual(calculate("cbrt(-8)"), -2)

    def test_disallows_python_access(self):
        with self.assertRaises(CalculatorError):
            calculate("().__class__.__mro__")

    def test_disallows_unknown_names(self):
        with self.assertRaises(CalculatorError):
            calculate("open(1)")

    def test_zero_division_is_safe_error(self):
        with self.assertRaises(CalculatorError):
            calculate("1 / 0")

    def test_rejects_excessive_power(self):
        with self.assertRaises(CalculatorError):
            calculate("2^10001")


if __name__ == "__main__":
    unittest.main()
