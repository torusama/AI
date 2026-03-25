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


def astar_steps(grid: Grid, heuristic_name='manhattan'):
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

    open_heap = [(heuristic_fn(start, goal), 0, start)]   # (f, g, pos)
    parent = {start: None}
    g_score = {start: 0}
    explored = set()
    found = False

    def frontier_set():
        return frozenset(pos for _, _, pos in open_heap if pos not in explored)

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
        f_cost, curr_cost, curr = heapq.heappop(open_heap)

        if curr in explored:
            continue

        explored.add(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            new_g = curr_cost + neighbor.cost

            if npos not in g_score or new_g < g_score[npos]:
                g_score[npos] = new_g
                parent[npos] = curr
                new_f = new_g + heuristic_fn(npos, goal)
                heapq.heappush(open_heap, (new_f, new_g, npos))

        yield {
            "explored": frozenset(explored),
            "frontier": frontier_set(),
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
        "frontier": frontier_set(),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        "cost": g_score[goal] if found else 0,
        "time_ms": time_ms,
    }