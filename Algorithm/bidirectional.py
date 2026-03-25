"""
Bidirectional Search (BDS)
- Chạy BFS từ cả Start và Goal cùng lúc.
- Phù hợp cho không gian trạng thái đối xứng, giảm độ sâu tìm kiếm.
"""

from collections import deque
import time
from core.grid import Grid


def _reconstruct_path(meet, parent_fwd, parent_bwd):
    path_fwd = []
    node = meet
    while node is not None:
        path_fwd.append(node)
        node = parent_fwd[node]
    path_fwd.reverse()

    path_bwd = []
    node = parent_bwd.get(meet)
    while node is not None:
        path_bwd.append(node)
        node = parent_bwd.get(node)

    return path_fwd + path_bwd


def _expand_one(queue, visited_self, visited_other, parent_self, grid, explored):
    if not queue:
        return False, None

    curr = queue.popleft()
    explored.add(curr)

    if curr in visited_other:
        return True, curr

    row, col = curr
    for neighbor, _ in grid.get_neighbors(row, col):
        npos = neighbor.position
        if npos in visited_self:
            continue
        visited_self.add(npos)
        parent_self[npos] = curr
        queue.append(npos)
        if npos in visited_other:
            return True, npos

    return False, None


def bidirectional_search(grid: Grid):
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        return {"path": [], "explored": set(), "cost": 0, "time_ms": 0}

    if start == goal:
        return {"path": [start], "explored": {start}, "cost": 0, "time_ms": 0}

    t0 = time.time()

    queue_fwd = deque([start])
    queue_bwd = deque([goal])

    visited_fwd = {start}
    visited_bwd = {goal}

    parent_fwd = {start: None}
    parent_bwd = {goal: None}

    explored = set()
    meet = None

    while queue_fwd and queue_bwd:
        if len(queue_fwd) <= len(queue_bwd):
            found, meet = _expand_one(
                queue_fwd, visited_fwd, visited_bwd, parent_fwd, grid, explored
            )
        else:
            found, meet = _expand_one(
                queue_bwd, visited_bwd, visited_fwd, parent_bwd, grid, explored
            )

        if found:
            break

    time_ms = (time.time() - t0) * 1000

    if meet is None:
        return {"path": [], "explored": explored, "cost": 0, "time_ms": time_ms}

    path = _reconstruct_path(meet, parent_fwd, parent_bwd)
    return {
        "path": path,
        "explored": explored,
        "cost": len(path) - 1,
        "time_ms": time_ms,
    }


def bidirectional_steps(grid: Grid):
    """Generator step-by-step cho animation."""
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        yield {
            "explored": set(), "frontier": set(), "cell_branch": {},
            "path": [], "found": False, "done": True, "cost": 0, "time_ms": 0,
        }
        return

    if start == goal:
        yield {
            "explored": frozenset({start}),
            "frontier": frozenset(),
            "cell_branch": {},
            "path": [start],
            "found": True,
            "done": True,
            "cost": 0,
            "time_ms": 0,
        }
        return

    t0 = time.time()

    queue_fwd = deque([start])
    queue_bwd = deque([goal])

    visited_fwd = {start}
    visited_bwd = {goal}

    parent_fwd = {start: None}
    parent_bwd = {goal: None}

    explored = set()
    meet = None

    yield {
        "explored": frozenset(),
        "frontier": frozenset({start, goal}),
        "cell_branch": {},
        "path": [],
        "found": False,
        "done": False,
        "cost": 0,
        "time_ms": (time.time() - t0) * 1000,
    }

    while queue_fwd and queue_bwd:
        if len(queue_fwd) <= len(queue_bwd):
            found, meet = _expand_one(
                queue_fwd, visited_fwd, visited_bwd, parent_fwd, grid, explored
            )
        else:
            found, meet = _expand_one(
                queue_bwd, visited_bwd, visited_fwd, parent_bwd, grid, explored
            )

        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(set(queue_fwd) | set(queue_bwd)),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": False,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        }

        if found:
            break

    time_ms = (time.time() - t0) * 1000

    if meet is None:
        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(set(queue_fwd) | set(queue_bwd)),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": True,
            "cost": 0,
            "time_ms": time_ms,
        }
        return

    path = _reconstruct_path(meet, parent_fwd, parent_bwd)
    yield {
        "explored": frozenset(explored),
        "frontier": frozenset(set(queue_fwd) | set(queue_bwd)),
        "cell_branch": {},
        "path": path,
        "found": True,
        "done": True,
        "cost": len(path) - 1,
        "time_ms": time_ms,
    }
