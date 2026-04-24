from __future__ import annotations

import argparse

FONT_5X7: dict[str, tuple[str, ...]] = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00001", "00001", "00001", "00001", "10001", "10001", "01110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "10001", "11001", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "?": ("11111", "00001", "00010", "00100", "00100", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}

BLOCK_ELEMENTS = {chr(codepoint) for codepoint in range(0x2580, 0x25A0)}


def _require_block_element(ch: str, arg_name: str) -> None:
    if ch not in BLOCK_ELEMENTS:
        raise ValueError(
            f"{arg_name} 必须是方块元素字符（U+2580..U+259F），当前为: {ch!r}"
        )


def _require_single_char(ch: str, arg_name: str) -> None:
    if len(ch) != 1:
        raise ValueError(f"{arg_name} 必须是单个字符，当前为: {ch!r}")


def render_block_text(
    text: str,
    *,
    foreground: str = "█",
    shadow: str = "░",
    letter_spacing: int = 1,
    line_spacing: int = 1,
    shadow_offset_x: int = 1,
    shadow_offset_y: int = 1,
    empty: str = " ",
) -> str:
    _require_block_element(foreground, "foreground")
    _require_block_element(shadow, "shadow")
    _require_single_char(empty, "empty")

    normalized = text.upper()
    input_lines = normalized.splitlines() or [normalized]
    letter_spacing = max(letter_spacing, 0)
    line_spacing = max(line_spacing, 0)
    shadow_offset_x = max(shadow_offset_x, 0)
    shadow_offset_y = max(shadow_offset_y, 0)

    base_rows: list[list[bool]] = []
    for line_idx, raw_line in enumerate(input_lines):
        glyph_line = raw_line or " "
        for row_index in range(7):
            row_bits: list[bool] = []
            for ch_idx, ch in enumerate(glyph_line):
                pattern = FONT_5X7.get(ch, FONT_5X7["?"])
                row_bits.extend(bit == "1" for bit in pattern[row_index])
                if ch_idx != len(glyph_line) - 1 and letter_spacing:
                    row_bits.extend(False for _ in range(letter_spacing))
            base_rows.append(row_bits)
        if line_idx != len(input_lines) - 1:
            for _ in range(line_spacing):
                base_rows.append([])

    text_width = max((len(row) for row in base_rows), default=0)
    text_height = len(base_rows)
    canvas_width = text_width + shadow_offset_x
    canvas_height = text_height + shadow_offset_y

    glyph_mask = [
        [False for _ in range(canvas_width)] for _ in range(canvas_height)
    ]
    shadow_mask = [
        [False for _ in range(canvas_width)] for _ in range(canvas_height)
    ]

    for y, row in enumerate(base_rows):
        for x, on in enumerate(row):
            if not on:
                continue
            glyph_mask[y][x] = True
            shadow_mask[y + shadow_offset_y][x + shadow_offset_x] = True

    output_rows: list[str] = []
    for y in range(canvas_height):
        chars: list[str] = []
        for x in range(canvas_width):
            if glyph_mask[y][x]:
                chars.append(foreground)
            elif shadow_mask[y][x]:
                chars.append(shadow)
            else:
                chars.append(empty)
        output_rows.append("".join(chars).rstrip() or empty)

    while output_rows and output_rows[-1] == empty:
        output_rows.pop()

    return "\n".join(output_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="终端方块元素文本渲染工具")
    parser.add_argument(
        "text",
        nargs="*",
        help="要渲染的文本；可省略（默认渲染 HSR SIM）",
    )
    parser.add_argument(
        "--foreground",
        default="█",
        help="前景字符（默认 █，需在 U+2580..U+259F）",
    )
    parser.add_argument(
        "--shadow",
        default="░",
        help="阴影字符（默认 ░，需在 U+2580..U+259F）",
    )
    parser.add_argument(
        "--background",
        dest="shadow",
        help="兼容参数：等同 --shadow",
    )
    parser.add_argument(
        "--letter-spacing",
        type=int,
        default=1,
        help="字母间距（空白列数，默认 1）",
    )
    parser.add_argument(
        "--line-spacing",
        type=int,
        default=1,
        help="行间距（空白行数，默认 1）",
    )
    parser.add_argument(
        "--shadow-offset-x",
        type=int,
        default=1,
        help="阴影水平偏移（默认 1）",
    )
    parser.add_argument(
        "--shadow-offset-y",
        type=int,
        default=1,
        help="阴影垂直偏移（默认 1）",
    )
    parser.add_argument(
        "--empty",
        default=" ",
        help="空白区域字符（默认空格）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = " ".join(args.text) if args.text else "HSR SIM"
    rendered = render_block_text(
        text,
        foreground=args.foreground,
        shadow=args.shadow,
        letter_spacing=args.letter_spacing,
        line_spacing=args.line_spacing,
        shadow_offset_x=args.shadow_offset_x,
        shadow_offset_y=args.shadow_offset_y,
        empty=args.empty,
    )
    print(rendered)


if __name__ == "__main__":
    main()
