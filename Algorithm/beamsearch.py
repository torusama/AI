import time

from core.grid import Grid
from core.heuristic import manhattan_distance, euclidean_distance


DEFAULT_BEAM_WIDTH = 2


def _reconstruct_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def beam_search_steps(grid: Grid, heuristic_name='manhattan', beam_width=DEFAULT_BEAM_WIDTH):
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

    beam_width = max(1, int(beam_width))
    t0 = time.time()

    current_beam = [start]
    parent = {start: None}
    g_score = {start: 0}
    visited = {start}
    explored = set()
    found = False

    # FIX 1: Check if start == goal immediately
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

    while current_beam:
        next_candidates = []

        for curr in current_beam:
            # FIX 2: Check goal BEFORE expanding (early termination)
            if curr == goal:
                found = True
                break

            explored.add(curr)

            row, col = curr
            for neighbor, _ in grid.get_neighbors(row, col):
                npos = neighbor.position
                if npos in visited:
                    continue

                visited.add(npos)
                parent[npos] = curr
                g_score[npos] = g_score[curr] + neighbor.cost

                # FIX 3: Early termination when goal is generated
                if npos == goal:
                    found = True
                    break

                next_candidates.append((heuristic_fn(npos, goal), npos))

            if found:
                break

        if found:
            break

        next_candidates.sort(key=lambda item: (item[0], item[1]))
        current_beam = [pos for _, pos in next_candidates[:beam_width]]

        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(current_beam),
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
        "frontier": frozenset(current_beam if not found else []),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        # FIX 4: Safe access with .get() to avoid KeyError
        "cost": g_score.get(goal, 0) if found else 0,
        "time_ms": time_ms,
    }