"""Quick checks for LRC parsing (run: python3 spotify/test_lrc.py)."""

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from spotify.lrc import line_at_progress, parse_synced_lrc


def main() -> None:
    sample = """[00:01.00]First line
[00:05.50]Second line
[ar:Artist]
[00:10]Third line
"""
    lines = parse_synced_lrc(sample)
    assert len(lines) == 3
    assert lines[0] == (1000, "First line")
    assert lines[1] == (5500, "Second line")
    assert lines[2] == (10000, "Third line")

    idx, prev_t, cur, next_t = line_at_progress(lines, 5600)
    assert idx == 1
    assert cur == "Second line"
    assert next_t == "Third line"

    idx2, _, cur2, _ = line_at_progress(lines, 10000)
    assert idx2 == 2
    assert cur2 == "Third line"

    print("lrc tests ok")


if __name__ == "__main__":
    main()
