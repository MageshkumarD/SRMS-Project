"""
Table and Text Formatting Utility.
Provides zero-dependency, clean ASCII/Unicode table rendering for the CLI.
Enhances with tabulate/colorama if installed.
"""

from typing import Any, List, Optional, Sequence


def format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[Any]],
    title: Optional[str] = None,
    max_col_width: int = 35,
) -> str:
    """
    Renders rows into a clean, aligned, boxed table.
    Works natively without requiring third-party libraries.
    """
    if not headers and not rows:
        return "(No records to display)"

    # Convert all cell items to strings and handle None
    clean_rows = []
    for row in rows:
        clean_row = []
        for cell in row:
            if cell is None:
                val = "-"
            elif isinstance(cell, float):
                val = f"{cell:.2f}"
            else:
                val = str(cell)
            if len(val) > max_col_width:
                val = val[: max_col_width - 3] + "..."
            clean_row.append(val)
        clean_rows.append(clean_row)

    clean_headers = [str(h) for h in headers]

    # Calculate column widths
    col_count = max(len(clean_headers), max((len(r) for r in clean_rows), default=0))
    # Pad headers or rows if counts differ
    while len(clean_headers) < col_count:
        clean_headers.append("")

    col_widths = [len(h) for h in clean_headers]
    for row in clean_rows:
        for i in range(col_count):
            val = row[i] if i < len(row) else ""
            if len(val) > col_widths[i]:
                col_widths[i] = len(val)

    # Box-drawing characters
    # Top border: ┌───┬───┐
    # Header sep: ├───┼───┤
    # Bottom:     └───┴───┘
    # Vertical:   │
    top_border = "┌" + "┬".join("─" * (w + 2) for w in col_widths) + "┐"
    header_sep = "├" + "┼".join("─" * (w + 2) for w in col_widths) + "┤"
    bottom_border = "└" + "┴".join("─" * (w + 2) for w in col_widths) + "┘"

    lines = []
    total_width = sum(col_widths) + (3 * len(col_widths)) + 1

    if title:
        lines.append("=" * total_width)
        lines.append(f"  {title}".center(total_width))
        lines.append("=" * total_width)

    lines.append(top_border)

    # Header line
    header_cells = [f" {h.center(col_widths[i])} " for i, h in enumerate(clean_headers)]
    lines.append("│" + "│".join(header_cells) + "│")
    lines.append(header_sep)

    # Row lines
    if not clean_rows:
        empty_msg = "No records found".center(total_width - 2)
        lines.append(f"│{empty_msg}│")
    else:
        for row in clean_rows:
            cells = []
            for i in range(col_count):
                val = row[i] if i < len(row) else ""
                # Right-align numeric values, left-align text
                if val.replace(".", "", 1).isdigit() or (val.startswith("-") and val[1:].replace(".", "", 1).isdigit()):
                    cell_str = f" {val.rjust(col_widths[i])} "
                else:
                    cell_str = f" {val.ljust(col_widths[i])} "
                cells.append(cell_str)
            lines.append("│" + "│".join(cells) + "│")

    lines.append(bottom_border)
    return "\n".join(lines)


def format_card(fields: List[tuple]) -> str:
    """
    Renders key-value record details as a clean summary card.
    fields is a list of (label, value).
    """
    if not fields:
        return ""
    max_label_len = max(len(str(label)) for label, _ in fields)
    lines = ["┌" + "─" * 60 + "┐"]
    for label, val in fields:
        val_str = "-" if val is None else str(val)
        display_str = f"  {str(label).rjust(max_label_len)} : {val_str}"
        lines.append(f"│ {display_str.ljust(58)} │")
    lines.append("└" + "─" * 60 + "┘")
    return "\n".join(lines)
