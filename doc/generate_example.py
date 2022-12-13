import math
import pdb

from collections import defaultdict
from dataclasses import dataclass
from functools import reduce
from typing import Any, List, Iterable, NamedTuple

import portion as P  # type: ignore
import streamlit as st  # type: ignore

from toolz import concat  # type: ignore

from chalk import blank, rectangle, hrule, Diagram, RGB
from mer import Rectangle


W = 2
H = 2


COLORS = {
    "default": RGB(33, 158, 188),
    "selected1": RGB(2, 48, 71),
    "selected2": RGB(142, 202, 230),
    "candidate": RGB(255, 183, 3),
    "gray": RGB(125, 125, 125),
    "light-gray": RGB(200, 200, 200),
}


class Visualizer:
    def __init__(self):
        self.dia_limits_vertical = Diagram.empty()
        self.dia_defects = Diagram.empty()
        self.dia_mers = Diagram.empty()
        self.dia_hrules = Diagram.empty()
        self.dia_defects_top = Diagram.empty()
        self.dia_defects_bot = Diagram.empty()
        self.CANVAS = blank(0, 0, W, H)

    @staticmethod
    def rects_to_diagram(rects: List[Rectangle]) -> Diagram:
        return Diagram.concat(
            rectangle(*r.size).translate(*r.center) for r in rects if r.is_finite()
        )

    def set_defects(self, defects):
        self.dia_defects = self.rects_to_diagram(defects).set_fill_color(
            COLORS["default"]
        )

    def set_mers(self, mers):
        mers1 = [mer for mer in mers if not (mer.left == 0 or mer.top == 0 or mer.right == W or mer.bottom == H)]
        self.dia_mers = self.rects_to_diagram(mers1).set_fill_color(COLORS["candidate"])

    def set_defects_top(self, defects):
        self.dia_defects_top = self.rects_to_diagram(defects).set_fill_color(COLORS["selected1"])
        # + hrule(W).translate(W / 2, defects[0].bottom).set_stroke_color( COLORS["selected1"])

    def set_defects_bot(self, defects):
        self.dia_defects_bot = self.rects_to_diagram(defects).set_fill_color(COLORS["selected2"])

    def set_limits_vertical(self, limits_vertical, top):
        # pdb.set_trace()
        try:
            rects = [Rectangle(lim.lower, top, lim.upper, H) for lim in limits_vertical]
            self.dia_limits_vertical = self.rects_to_diagram(rects).set_fill_color(COLORS["light-gray"]).set_stroke_color(COLORS["light-gray"])
        except:
            self.dia_limits_vertical = Diagram.empty()

    def set_hrules(self, lines):
        dia = Diagram.empty()
        for line in lines:
            if 0 < line < H:
                dia = dia + hrule(W).translate(W / 2, line).set_stroke_color(
                    COLORS["gray"]
                )
        self.dia_hrules = dia

    def draw(self, path: str = "test.png"):
        diagram = (
            self.dia_limits_vertical
            + self.dia_defects
            + self.dia_mers
            + self.dia_defects_top
            + self.dia_defects_bot
            + self.dia_hrules
            + self.CANVAS
        )
        diagram.render(path, width=256, height=256)
        st.image(path)


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
    board: Rectangle, defects: List[Rectangle]
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

    viz = Visualizer()
    viz.set_defects(defects)

    viz.set_hrules(top_lines)
    viz.draw("02-top-lines.png")

    viz.set_hrules(bot_lines)
    viz.draw("02-bot-lines.png")

    viz.set_hrules([])

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

        if state_prev.defects_top[0].is_finite():
            "top_line", top_line
            "bot_line", bot_line
            viz.set_defects_top(state_prev.defects_top)
            viz.set_defects_bot(defects_bot_curr)
            viz.set_mers(candidates)
            viz.set_limits_vertical(limits_vertical, top_line)
            viz.draw("03-step-{}-{}.png".format(top_line, bot_line))
            st.markdown("---")
        # pdb.set_trace()

        return state_next

    def go(hline):
        state_init = State([], bot_to_defects[hline], P.closed(-P.inf, P.inf))
        state_final = reduce(iteration, top_lines, state_init)
        return state_final.candidates

    return list(concat(go(hline) for hline in bot_lines))


board = Rectangle(left=0, top=0, right=W, bottom=H)
defects = [
    Rectangle.from_corner_and_size(0.45, 0.15, 0.30, 0.20),
    Rectangle.from_corner_and_size(0.75, 0.65, 0.50, 0.10),
    Rectangle.from_corner_and_size(1.45, 0.30, 0.20, 0.75),
    Rectangle.from_corner_and_size(0.25, 0.95, 0.30, 0.30),
    Rectangle.from_corner_and_size(0.95, 1.25, 0.10, 0.10),
    Rectangle.from_corner_and_size(0.75, 1.45, 0.10, 0.10),
    Rectangle.from_corner_and_size(1.00, 1.45, 0.40, 0.20),
    Rectangle.from_corner_and_size(0.80, 1.85, 0.40, 0.10),
]

viz = Visualizer()
viz.set_defects(defects)
viz.draw(path="00-input.png")

mers = get_maximal_rectangles(board, defects)
mers = [mer for mer in mers if not (mer.left == 0 or mer.top == 0 or mer.right == W or mer.bottom == H)]
for i, mer in enumerate(mers):
    viz.set_mers([mer])
    viz.draw(path="01-output-{:02d}.png".format(i))
