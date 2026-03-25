# Algorithm/ucs.py

"""
Uniform Cost Search (UCS)
- Giống BFS nhưng ưu tiên node có tổng chi phí g nhỏ nhất.
- Phù hợp khi map có ô cost khác nhau (ví dụ O = 3, E = 1).
"""

import heapq
import time
from core.grid import Grid


def _reconstruct_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def ucs(grid: Grid):
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        return {"path": [], "explored": set(), "cost": 0, "time_ms": 0}

    t0 = time.time()

    pq = [(0, start)]              # (g_cost, position)
    parent = {start: None}
    g_score = {start: 0}
    explored = set()
    found = False

    while pq:
        curr_cost, curr = heapq.heappop(pq)

        if curr in explored:
            continue
        explored.add(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            new_cost = curr_cost + neighbor.cost

            if npos not in g_score or new_cost < g_score[npos]:
                g_score[npos] = new_cost
                parent[npos] = curr
                heapq.heappush(pq, (new_cost, npos))

    time_ms = (time.time() - t0) * 1000

    if not found:
        return {"path": [], "explored": explored, "cost": 0, "time_ms": time_ms}

    path = _reconstruct_path(parent, goal)

    return {
        "path": path,
        "explored": explored,
        "cost": g_score[goal],   # UCS phải trả cost thật
        "time_ms": time_ms,
    }


def ucs_steps(grid: Grid):
    """
    Generator step-by-step cho animation.
    Trả format giống bfs_steps / dfs_steps.
    """
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        yield {
            "explored": set(), "frontier": set(), "cell_branch": {},
            "path": [], "found": False, "done": True, "cost": 0, "time_ms": 0,
        }
        return

    t0 = time.time()

    pq = [(0, start)]
    parent = {start: None}
    g_score = {start: 0}
    explored = set()
    found = False

    def frontier_set():
        return frozenset(pos for _, pos in pq if pos not in explored)

    def snap(done=False, path=None, found=False):
        return {
            "explored": frozenset(explored),
            "frontier": frontier_set(),
            "cell_branch": {},
            "path": path if path is not None else [],
            "found": found,
            "done": done,
            "cost": g_score[goal] if found and goal in g_score else 0,
            "time_ms": (time.time() - t0) * 1000,
        }

    yield {
        "explored": frozenset(),
        "frontier": frozenset({start}),
        "cell_branch": {},
        "path": [],
        "found": False,
        "done": False,
        "cost": 0,
        "time_ms": (time.time() - t0) * 1000,
    }

    while pq:
        curr_cost, curr = heapq.heappop(pq)

        if curr in explored:
            continue

        explored.add(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            new_cost = curr_cost + neighbor.cost

            if npos not in g_score or new_cost < g_score[npos]:
                g_score[npos] = new_cost
                parent[npos] = curr
                heapq.heappush(pq, (new_cost, npos))

        yield snap()

    time_ms = (time.time() - t0) * 1000

    path = []
    if found:
        path = _reconstruct_path(parent, goal)

    yield {
        "explored": frozenset(explored),
        "frontier": frontier_set(),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        "cost": g_score[goal] if found else 0,
        "time_ms": time_ms,
    }