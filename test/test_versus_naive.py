from typing import List

from hypothesis import given
from hypothesis.strategies import (
    DrawFn,
    composite,
    integers,
    floats,
)


from mer import Rectangle, get_maximal_empty_rectangles, get_maximal_empty_rectangles_naive


small_nat = integers(min_value=0, max_value=7)


@composite
def defect(draw: DrawFn) -> Rectangle:
    l = draw(floats(0, 1))
    t = draw(floats(0, 1))
    r = draw(floats(l, 1))
    b = draw(floats(t, 1))
    return Rectangle(l, t, r, b)


@composite
def defects(draw: DrawFn) -> List[Rectangle]:
    return [draw(defect()) for _ in range(draw(small_nat))]


@given(defects())
def test_versus_naive(defects: List[Rectangle]) -> None:
    to_set = lambda cs: set([repr(c) for c in cs])
    board = Rectangle(0, 0, 1, 1)
    mers1 = get_maximal_empty_rectangles(board, defects)
    mers2 = get_maximal_empty_rectangles_naive(board, defects)
    to_set(mers1) == to_set(mers2)
