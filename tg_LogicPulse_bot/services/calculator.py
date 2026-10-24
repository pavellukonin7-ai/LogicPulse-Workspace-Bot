"""Безопасный локальный калькулятор математических выражений."""

from __future__ import annotations

import ast
import cmath
import math
import operator
import re
from typing import Callable


class CalculatorError(ValueError):
    """Ошибка разбора или вычисления выражения."""


def _real_if_close(value: complex | float | int):
    if isinstance(value, complex) and abs(value.imag) < 1e-12:
        return value.real
    return value


def _unary_complex(fn: Callable[[complex], complex]):
    def wrapped(value):
        return _real_if_close(fn(value))

    return wrapped


def _factorial(value):
    if isinstance(value, complex) or int(value) != value or not 0 <= value <= 500:
        raise CalculatorError("factorial принимает целое число от 0 до 500")
    return math.factorial(int(value))


def _round(value, digits=0):
    if isinstance(digits, complex) or int(digits) != digits or not -100 <= digits <= 100:
        raise CalculatorError("точность round должна быть целым числом от -100 до 100")
    return round(value, int(digits))


def _cbrt(value):
    if not isinstance(value, complex) and value < 0:
        return -((-value) ** (1 / 3))
    return _real_if_close(value ** (1 / 3))


def _log(value, base=math.e):
    if base == math.e:
        return _real_if_close(cmath.log(value))
    return _real_if_close(cmath.log(value) / cmath.log(base))


FUNCTIONS = {
    "sqrt": _unary_complex(cmath.sqrt),
    "cbrt": _cbrt,
    "sin": _unary_complex(cmath.sin),
    "cos": _unary_complex(cmath.cos),
    "tan": _unary_complex(cmath.tan),
    "asin": _unary_complex(cmath.asin),
    "acos": _unary_complex(cmath.acos),
    "atan": _unary_complex(cmath.atan),
    "sinh": _unary_complex(cmath.sinh),
    "cosh": _unary_complex(cmath.cosh),
    "tanh": _unary_complex(cmath.tanh),
    "ln": _log,
    "log": _log,
    "log10": lambda value: _log(value, 10),
    "log2": lambda value: _log(value, 2),
    "exp": _unary_complex(cmath.exp),
    "abs": abs,
    "round": _round,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": _factorial,
    "degrees": math.degrees,
    "radians": math.radians,
    "min": min,
    "max": max,
}

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "i": 1j,
    "j": 1j,
}

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _normalise(expression: str) -> str:
    result = expression.strip().lower()
    result = result.translate(str.maketrans({"×": "*", "÷": "/", "−": "-", "—": "-", "^": "**"}))
    result = re.sub(r"\bкорень\b", "sqrt", result)
    result = re.sub(r"\b(\d+(?:[.,]\d+)?)\s*%\s*(?:от|of)\s*", r"(\1/100)*", result)
    result = _replace_decimal_commas(result)
    result = re.sub(r"(\d+(?:\.\d+)?|\([^()]++\))\s*%", r"(\1/100)", result)
    return result


def _replace_decimal_commas(expression: str) -> str:
    """Заменить 1,5 на 1.5, сохранив запятые аргументов функций."""
    result = []
    function_depth = []
    for index, char in enumerate(expression):
        if char == "(":
            prefix = expression[:index].rstrip()
            function_depth.append(bool(re.search(r"[a-z_]\w*$", prefix)))
        elif char == ")" and function_depth:
            function_depth.pop()

        decimal_comma = (
            char == ","
            and index > 0
            and index + 1 < len(expression)
            and expression[index - 1].isdigit()
            and expression[index + 1].isdigit()
            and not any(function_depth)
        )
        result.append("." if decimal_comma else char)
    return "".join(result)


class _Evaluator:
    def __init__(self):
        self.nodes = 0

    def evaluate(self, node):
        self.nodes += 1
        if self.nodes > 120:
            raise CalculatorError("выражение слишком сложное")

        if isinstance(node, ast.Expression):
            return self.evaluate(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float, complex)):
                raise CalculatorError("допустимы только числа")
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in CONSTANTS:
                raise CalculatorError(f"неизвестная константа: {node.id}")
            return CONSTANTS[node.id]
        if isinstance(node, ast.UnaryOp) and type(node.op) in UNARY_OPERATORS:
            return UNARY_OPERATORS[type(node.op)](self.evaluate(node.operand))
        if isinstance(node, ast.BinOp):
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            if isinstance(node.op, ast.Pow):
                if isinstance(right, complex) or abs(right) > 10_000:
                    raise CalculatorError("слишком большая степень")
                value = left**right
            elif type(node.op) in BINARY_OPERATORS:
                value = BINARY_OPERATORS[type(node.op)](left, right)
            else:
                raise CalculatorError("эта операция не поддерживается")
            self._check_size(value)
            return value
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
                raise CalculatorError("эта функция не поддерживается")
            if node.keywords or not 1 <= len(node.args) <= 20:
                raise CalculatorError("неверные аргументы функции")
            args = [self.evaluate(arg) for arg in node.args]
            try:
                value = FUNCTIONS[node.func.id](*args)
            except CalculatorError:
                raise
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise CalculatorError("неверные аргументы функции") from exc
            self._check_size(value)
            return value
        raise CalculatorError("выражение содержит недопустимую конструкцию")

    @staticmethod
    def _check_size(value):
        if isinstance(value, (int, float, complex)):
            try:
                magnitude = abs(value)
            except OverflowError as exc:
                raise CalculatorError("результат слишком большой") from exc
            if isinstance(magnitude, float) and (math.isnan(magnitude) or math.isinf(magnitude)):
                raise CalculatorError("результат не является конечным числом")
            if magnitude > 10**1000:
                raise CalculatorError("результат слишком большой")


def calculate(expression: str):
    """Вычислить выражение без eval и доступа к объектам Python."""
    if not expression.strip():
        raise CalculatorError("введите выражение")
    if len(expression) > 500:
        raise CalculatorError("сократите выражение до 500 символов")
    normalised = _normalise(expression)
    try:
        tree = ast.parse(normalised, mode="eval")
        return _Evaluator().evaluate(tree)
    except CalculatorError:
        raise
    except (SyntaxError, ArithmeticError, ValueError, OverflowError) as exc:
        raise CalculatorError("не удалось разобрать или вычислить выражение") from exc


def format_result(value) -> str:
    """Компактно отформатировать обычный или комплексный результат."""
    value = _real_if_close(value)
    if isinstance(value, complex):
        real = f"{value.real:.15g}"
        imag = f"{abs(value.imag):.15g}"
        sign = "+" if value.imag >= 0 else "−"
        return f"{real} {sign} {imag}i"
    if isinstance(value, int):
        return str(value)
    return f"{value:.15g}"
