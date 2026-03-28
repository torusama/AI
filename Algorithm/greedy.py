import heapq
import time

from core.grid import Grid
from core.heuristic import manhattan_distance, euclidean_distance


def _reconstruct_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def greedy_steps(grid: Grid, heuristic_name='manhattan'):
    start = grid.start
    goal = grid.goal

    if not start or not goal:
        yield {
            "explored": set(),
            "frontier": set(),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": True,
            "cost": 0,
            "time_ms": 0,
        }
        return

    if heuristic_name == 'euclidean':
        heuristic_fn = euclidean_distance
    else:
        heuristic_fn = manhattan_distance

    t0 = time.time()

    # FIX 1: Handle start == goal early
    if start == goal:
        yield {
            "explored": frozenset(),
            "frontier": frozenset({start}),
            "cell_branch": {},
            "path": [start],
            "found": True,
            "done": True,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        }
        return

    # FIX 2: Add tie-breaker counter to avoid TypeError on heap comparison
    counter = 0
    open_heap = [(heuristic_fn(start, goal), counter, start)]

    visited = {start}
    parent = {start: None}
    g_score = {start: 0}
    explored = set()

    # FIX 3: Maintain frontier set explicitly instead of scanning heap O(n)
    frontier = {start}

    found = False

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

    while open_heap:
        _, _, curr = heapq.heappop(open_heap)

        if curr in explored:
            continue

        explored.add(curr)
        frontier.discard(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            if npos in visited:
                continue

            visited.add(npos)
            parent[npos] = curr
            g_score[npos] = g_score[curr] + neighbor.cost

            counter += 1
            heapq.heappush(open_heap, (heuristic_fn(npos, goal), counter, npos))
            frontier.add(npos)

        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(frontier),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": False,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        }

    time_ms = (time.time() - t0) * 1000
    path = _reconstruct_path(parent, goal) if found else []

    yield {
        "explored": frozenset(explored),
        "frontier": frozenset(frontier),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        # FIX 4: Safe access with .get() to avoid KeyError
        "cost": g_score.get(goal, 0) if found else 0,
        "time_ms": time_ms,
    }