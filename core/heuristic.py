"""
Heuristic system cho các thuật toán informed search.
"""

from typing import Tuple
import math


def manhattan_distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean_distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def heuristic_to_goal(position: Tuple[int, int], goal: Tuple[int, int], mode: str = 'manhattan') -> float:
    if mode == 'euclidean':
        return euclidean_distance(position, goal)
    return manhattan_distance(position, goal)