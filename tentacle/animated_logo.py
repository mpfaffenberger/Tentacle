from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class AnimatedLogo(Widget):
    """Big, braille-style Tentacle logo without external dependencies."""

    DEFAULT_CSS = """
    AnimatedLogo {
        height: 7;
        width: 1fr;
        content-align: center middle;
        background: transparent;
        align: center middle;
    }

    AnimatedLogo .logo-text {
        text-style: bold;
        color: #bb9af7;
        text-align: center;
        margin: 0;
    }
    """

    LOGO_TEXT: ClassVar[str] = "TENTACLE"
    LETTER_HEIGHT: ClassVar[int] = 12
    LETTER_WIDTH: ClassVar[int] = 8
    LETTER_SPACING: ClassVar[int] = 2
    FILL_CHAR: ClassVar[str] = "█"
    LETTER_PATTERNS: ClassVar[dict[str, tuple[str, ...]]] = {
        "T": (
            "████████",
            "████████",
            "████████",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
            "   ██   ",
        ),
        "E": (
            "████████",
            "████████",
            "████████",
            "██      ",
            "██      ",
            "████████",
            "████████",
            "████████",
            "██      ",
            "██      ",
            "████████",
            "████████",
        ),
        "N": (
            "██    ██",
            "███   ██",
            "███   ██",
            "██ █  ██",
            "██ █  ██",
            "██  █ ██",
            "██  █ ██",
            "██   ███",
            "██   ███",
            "██    ██",
            "██    ██",
            "██    ██",
        ),
        "A": (
            "   ██   ",
            "  ████  ",
            "  ████  ",
            " ██  ██ ",
            " ██  ██ ",
            "████████",
            "████████",
            "██    ██",
            "██    ██",
            "██    ██",
            "██    ██",
            "██    ██",
        ),
        "C": (
            " ██████ ",
            "████████",
            "████████",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "████████",
            "████████",
            " ██████ ",
        ),
        "L": (
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "██      ",
            "████████",
            "████████",
        ),
    }

    def compose(self) -> ComposeResult:
        """Create a braille-based big logo."""
        ascii_rows = self._build_ascii_logo()
        braille_rows = self._ascii_to_braille(ascii_rows, self.FILL_CHAR)

        yield Static("", classes="logo-text")
        for row in braille_rows:
            yield Static(row, classes="logo-text")
        yield Static("", classes="logo-text")

    def on_resize(self) -> None:
        """Handle resize events to maintain proper sizing."""
        self.refresh()

    @classmethod
    def _build_ascii_logo(cls) -> list[str]:
        rows = ["" for _ in range(cls.LETTER_HEIGHT)]
        spacing = " " * cls.LETTER_SPACING

        for index, letter in enumerate(cls.LOGO_TEXT):
            pattern = cls._pattern_for_letter(letter)
            for row_index, value in enumerate(pattern):
                rows[row_index] += value
                if index != len(cls.LOGO_TEXT) - 1:
                    rows[row_index] += spacing

        rows = [row.rstrip() for row in rows]
        width = max((len(row) for row in rows), default=0)
        if width % 2 != 0:
            width += 1
        rows = [row.ljust(width) for row in rows]

        remainder = len(rows) % 4
        if remainder:
            rows.extend([" " * width] * (4 - remainder))

        return rows

    @classmethod
    def _pattern_for_letter(cls, letter: str) -> list[str]:
        pattern = cls.LETTER_PATTERNS.get(letter)
        if pattern is None:
            return [" " * cls.LETTER_WIDTH for _ in range(cls.LETTER_HEIGHT)]
        return list(pattern)

    @staticmethod
    def _ascii_to_braille(rows: list[str] | str, fill_char: str) -> list[str]:
        if isinstance(rows, str):
            rows = rows.splitlines()

        if not rows:
            return []

        rows = [row.rstrip("\n") for row in rows]
        width = max(len(row) for row in rows)
        if width % 2 != 0:
            width += 1
        padded_rows = [row.ljust(width) for row in rows]

        remainder = len(padded_rows) % 4
        if remainder:
            padded_rows.extend([" " * width] * (4 - remainder))

        dot_map = {
            (0, 0): 0,
            (1, 0): 1,
            (2, 0): 2,
            (3, 0): 6,
            (0, 1): 3,
            (1, 1): 4,
            (2, 1): 5,
            (3, 1): 7,
        }

        braille_rows: list[str] = []
        for base_row in range(0, len(padded_rows), 4):
            line_chars: list[str] = []
            for base_col in range(0, width, 2):
                bits = 0
                for row_offset in range(4):
                    for col_offset in range(2):
                        if padded_rows[base_row + row_offset][base_col + col_offset] == fill_char:
                            bits |= 1 << dot_map[(row_offset, col_offset)]
                line_chars.append(chr(0x2800 + bits))
            braille_rows.append("".join(line_chars).rstrip())

        return braille_rows
