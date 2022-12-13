import math
import pdb

from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from typing import Any, List, Iterable, NamedTuple

import portion as P  # type: ignore

from toolz import concat  # type: ignore


@dataclass
class Rectangle:
    left: float
    top: float
    right: float
    bottom: float

    def __post_init__(self):
        assert self.left <= self.right
        assert self.top <= self.bottom

    @classmethod
    def from_corner_and_size(cls, x, y, w, h):
        left = x
        top = y
        right = x + w
        bottom = y + h
        return cls(left, top, right, bottom)

    @property
    def center(self):
        x = (self.left + self.right) / 2
        y = (self.top + self.bottom) / 2
        return x, y

    @property
    def size(self):
        w = self.right - self.left
        h = self.bottom - self.top
        return w, h

    def to_interval_x(self) -> P.Interval:
        return P.closed(self.left, self.right)

    def to_interval_y(self) -> P.Interval:
        return P.closed(self.top, self.bottom)

    def is_finite(self):
        return not (
            self.left == -P.inf
            or self.top == -P.inf
            or self.right == P.inf
            or self.bottom == P.inf
        )


class State(NamedTuple):
    candidates: List[Rectangle]
    defects_top: List[Rectangle]
    limits_vertical: Any


class multimap(defaultdict):
    """A mapping of {key: [val1, val2, ...]}."""

    def __init__(self, pairs: Iterable[tuple]):
        """Given (key, val) pairs, return {key: [val, ...], ...}."""
        self.default_factory = list
        for (key, val) in pairs:
            self[key].append(val)


def get_maximal_rectangles(
    board: Rectangle,
    defects: List[Rectangle],
    to_visualize=False,
) -> List[Rectangle]:
    defects_borders = [
        Rectangle(-P.inf, -P.inf, board.left, P.inf),
        Rectangle(-P.inf, -P.inf, P.inf, board.top),
        Rectangle(board.right, -P.inf, P.inf, P.inf),
        Rectangle(-P.inf, board.bottom, P.inf, P.inf),
    ]
    defects_aug = defects_borders + defects

    bot_to_defects = multimap([(d.bottom, d) for d in defects_aug])
    top_to_defects = multimap([(d.top, d) for d in defects_aug])

    bot_lines = sorted(bot_to_defects.keys())
    top_lines = sorted(top_to_defects.keys())

    def iteration(state_prev: State, line: float) -> State:
        top_line = state_prev.defects_top[0].bottom
        bot_line = line

        defects_bot_curr = [d for d in top_to_defects[line]]
        defects_bot = [d for d in top_to_defects[line] if top_line < d.bottom]

        if not defects_bot:
            state_next = state_prev
            limits_vertical = state_prev.limits_vertical
            candidates = []
        else:
            defects_top_interval = P.Interval(
                *[d.to_interval_x() for d in state_prev.defects_top]
            )
            defects_bot_interval = P.Interval(*[d.to_interval_x() for d in defects_bot])

            candidates = [
                Rectangle(
                    left=limit.lower,
                    top=top_line,
                    right=limit.upper,
                    bottom=bot_line,
                )
                for limit in state_prev.limits_vertical
                if -P.inf < limit.lower
                and limit.upper < P.inf
                and limit.overlaps(defects_bot_interval)
                and top_line < bot_line
            ]

            limits_vertical = state_prev.limits_vertical - defects_bot_interval
            limits_vertical = [
                limit
                for limit in limits_vertical
                if limit.overlaps(defects_top_interval)
            ]
            limits_vertical = P.Interval(*limits_vertical)

            state_next = State(
                state_prev.candidates + candidates,
                state_prev.defects_top,
                limits_vertical,
            )

        return state_next

    def go(hline):
        state_init = State([], bot_to_defects[hline], P.closed(-P.inf, P.inf))
        state_final = reduce(iteration, top_lines, state_init)
        return state_final.candidates

    return list(concat(go(hline) for hline in bot_lines))


def get_maximal_rectangles_naive(
    board: Rectangle, defects: List[Rectangle]
) -> List[Rectangle]:
    """Naïve method of generating candidates by enumerating all posibilities."""
    contains_defect = lambda r: any(r.overlaps(defect, "open") for defect in defects)
    lefts = [defect.right for defect in defects] + [board.left]
    tops = [defect.bottom for defect in defects] + [board.top]
    rights = [defect.left for defect in defects] + [board.right]
    bottoms = [defect.top for defect in defects] + [board.bottom]
    rectangles = [
        Rectangle(l, t, r, b)
        for l, t, r, b in product(lefts, tops, rights, bottoms)
        if l <= r and t <= b and not contains_defect(Rectangle(l, t, r, b))
    ]
    is_maximal = lambda r: not any(r in q for q in rectangles if q != r)
    return [r for r in rectangles if r.area() > 0 and is_maximal(r)]
