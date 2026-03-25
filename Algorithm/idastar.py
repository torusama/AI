"""
Iterative Deepening A* (IDA*)
- Dùng ngưỡng f = g + h (h là Manhattan distance).
- Kết hợp ưu điểm DFS (ít bộ nhớ) với heuristic của A*.
"""

import time
from core.grid import Grid
from core.heuristic import heuristic_to_goal


def _ida_star_run(grid: Grid, capture_steps: bool):
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        return {
            "path": [], "explored": set(), "cost": 0,
            "time_ms": 0, "found": False, "snapshots": [],
        }

    t0 = time.time()
    threshold = heuristic_to_goal(start, goal)

    explored_overall = set()
    snapshots = []

    def save_snapshot(path):
        if not capture_steps:
            return
        snapshots.append({
            "explored": frozenset(explored_overall),
            "frontier": frozenset(path),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": False,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        })

    def search(path, path_set, g_cost, bound):
        node = path[-1]
        h_cost = heuristic_to_goal(node, goal)
        f_cost = g_cost + h_cost

        if f_cost > bound:
            return f_cost, None

        explored_overall.add(node)
        save_snapshot(path)

        if node == goal:
            return "FOUND", list(path)

        min_exceeded = float("inf")

        row, col = node
        neighbors = sorted(
            grid.get_neighbors(row, col),
            key=lambda item: heuristic_to_goal(item[0].position, goal)
        )

        for neighbor, _ in neighbors:
            npos = neighbor.position
            if npos in path_set:
                continue

            path.append(npos)
            path_set.add(npos)

            result, found_path = search(path, path_set, g_cost + neighbor.cost, bound)
            if result == "FOUND":
                return "FOUND", found_path

            if result < min_exceeded:
                min_exceeded = result

            path.pop()
            path_set.remove(npos)

        return min_exceeded, None

    final_path = []
    found = False

    while True:
        path = [start]
        path_set = {start}

        result, maybe_path = search(path, path_set, 0, threshold)

        if result == "FOUND":
            final_path = maybe_path or []
            found = True
            break

        if result == float("inf"):
            break

        threshold = result

    time_ms = (time.time() - t0) * 1000

    return {
        "path": final_path,
        "explored": explored_overall,
        "cost": len(final_path) - 1 if found else 0,
        "time_ms": time_ms,
        "found": found,
        "snapshots": snapshots,
    }


def ida_star(grid: Grid):
    result = _ida_star_run(grid, capture_steps=False)
    return {
        "path": result["path"],
        "explored": result["explored"],
        "cost": result["cost"],
        "time_ms": result["time_ms"],
    }


def ida_star_steps(grid: Grid):
    """Generator step-by-step cho animation."""
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        yield {
            "explored": set(), "frontier": set(), "cell_branch": {},
            "path": [], "found": False, "done": True, "cost": 0, "time_ms": 0,
        }
        return

    t0 = time.time()

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

    result = _ida_star_run(grid, capture_steps=True)

    for snap in result["snapshots"]:
        yield snap

    yield {
        "explored": frozenset(result["explored"]),
        "frontier": frozenset(),
        "cell_branch": {},
        "path": result["path"],
        "found": result["found"],
        "done": True,
        "cost": result["cost"],
        "time_ms": result["time_ms"],
    }
