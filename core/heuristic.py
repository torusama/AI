"""
Heuristic system cho các thuật toán informed search.
"""

from typing import Tuple


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    """Tính khoảng cách Manhattan giữa hai tọa độ (row, col)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def heuristic_to_goal(position: Tuple[int, int], goal: Tuple[int, int]) -> int:
    """Heuristic mặc định hiện tại: Manhattan distance tới goal."""
    return manhattan_distance(position, goal)
