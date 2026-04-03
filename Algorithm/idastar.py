"""
Iterative Deepening A* (IDA*)
- Dung nguong f = g + h.
- Ho tro 2 heuristic: Manhattan va Euclidean.
- Ket hop uu diem DFS (it bo nho) voi heuristic cua A*.
"""

import time
from core.grid import Grid
from core.heuristic import heuristic_to_goal


def _compute_path_cost(grid: Grid, path):
    if not path:
        return 0
    # Path cost is the sum of costs of entered cells (excluding start).
    return sum(grid.get_cost(r, c) for r, c in path[1:])


def _ida_star_run(grid: Grid, capture_steps: bool, heuristic_name: str = 'manhattan'):
    start = grid.start
    goal = grid.goal
    all_goods = frozenset(grid.goods)

    if not start or not goal:
        return {
            "path": [],
            "explored": set(),
            "cost": 0,
            "time_ms": 0,
            "found": False,
            "snapshots": [],
        }

    t0 = time.time()
    start_goods = frozenset({start}) if start in all_goods else frozenset()
    start_state = (start, start_goods)

    threshold = heuristic_to_goal(start, goal, heuristic_name)

    explored_overall = set()
    snapshots = []
    transposition_table = {}

    def save_snapshot(path):
        if not capture_steps:
            return
        snapshots.append({
            "explored": frozenset(explored_overall),
            "frontier": frozenset(state[0] for state in path),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": False,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        })

    def search(path, path_set, g_cost, bound):
        state = path[-1]
        node, collected_goods = state
        h_cost = heuristic_to_goal(node, goal, heuristic_name)
        f_cost = g_cost + h_cost

        if f_cost > bound:
            return f_cost, None

        if state in transposition_table and transposition_table[state] <= g_cost:
            return float("inf"), None
        transposition_table[state] = g_cost

        explored_overall.add(node)
        save_snapshot(path)

        if node == goal and collected_goods == all_goods:
            return "FOUND", list(path)

        min_exceeded = float("inf")
        row, col = node

        neighbors = []
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            n_collected_goods = collected_goods
            if npos in all_goods:
                n_collected_goods = collected_goods | frozenset({npos})
            n_state = (npos, n_collected_goods)
            n_g = g_cost + neighbor.cost
            n_h = heuristic_to_goal(npos, goal, heuristic_name)
            neighbors.append((n_state, n_g, n_g + n_h))

        neighbors.sort(key=lambda x: x[2])

        for n_state, n_g, _ in neighbors:
            if n_state in path_set:
                continue

            path.append(n_state)
            path_set.add(n_state)

            result, found_path = search(path, path_set, n_g, bound)

            if result == "FOUND":
                return "FOUND", found_path

            if result < min_exceeded:
                min_exceeded = result

            path.pop()
            path_set.remove(n_state)

        return min_exceeded, None

    final_path = []
    found = False

    while True:
        transposition_table = {}
        path = [start_state]
        path_set = {start_state}

        result, maybe_path = search(path, path_set, 0, threshold)

        if result == "FOUND":
            final_path = [state[0] for state in (maybe_path or [])]
            found = True
            break

        if result == float("inf"):
            break

        threshold = result

    time_ms = (time.time() - t0) * 1000
    final_cost = _compute_path_cost(grid, final_path) if found else 0

    return {
        "path": final_path,
        "explored": explored_overall,
        "cost": final_cost,
        "time_ms": time_ms,
        "found": found,
        "snapshots": snapshots,
    }


def ida_star(grid: Grid, heuristic_name: str = 'manhattan'):
    result = _ida_star_run(grid, capture_steps=False, heuristic_name=heuristic_name)
    return {
        "path": result["path"],
        "explored": result["explored"],
        "cost": result["cost"],
        "time_ms": result["time_ms"],
    }


def ida_star_steps(grid: Grid, heuristic_name: str = 'manhattan'):
    """Generator step-by-step cho animation."""
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

    import threading, queue

    _DONE = object()

    def worker(q):
        all_goods = frozenset(grid.goods)
        start_goods = frozenset({start}) if start in all_goods else frozenset()
        start_state = (start, start_goods)

        threshold = heuristic_to_goal(start, goal, heuristic_name)
        explored_overall = set()
        transposition_table = {}
        final_path = []
        found = False
        last_emitted_explored_count = -1

        def emit_progress(path, force=False):
            nonlocal last_emitted_explored_count
            explored_count = len(explored_overall)
            if not force and explored_count == last_emitted_explored_count:
                return
            last_emitted_explored_count = explored_count
            q.put({
                "explored": frozenset(explored_overall),
                "frontier": frozenset(s[0] for s in path),
                "cell_branch": {},
                "path": [],
                "found": False,
                "done": False,
                "cost": 0,
                "time_ms": (time.time() - t0) * 1000,
            })

        def search(path, path_set, g_cost, bound):
            state = path[-1]
            node, collected_goods = state
            h_cost = heuristic_to_goal(node, goal, heuristic_name)
            f_cost = g_cost + h_cost

            if f_cost > bound:
                return f_cost, None

            if state in transposition_table and transposition_table[state] <= g_cost:
                return float("inf"), None
            transposition_table[state] = g_cost

            explored_overall.add(node)
            emit_progress(path)

            if node == goal and collected_goods == all_goods:
                return "FOUND", list(path)

            min_exceeded = float("inf")
            row, col = node

            neighbors = []
            for neighbor, _ in grid.get_neighbors(row, col):
                npos = neighbor.position
                n_collected_goods = collected_goods
                if npos in all_goods:
                    n_collected_goods = collected_goods | frozenset({npos})
                n_state = (npos, n_collected_goods)
                n_g = g_cost + neighbor.cost
                n_h = heuristic_to_goal(npos, goal, heuristic_name)
                neighbors.append((n_state, n_g, n_g + n_h))

            neighbors.sort(key=lambda x: x[2])

            for n_state, n_g, _ in neighbors:
                if n_state in path_set:
                    continue

                path.append(n_state)
                path_set.add(n_state)

                result, found_path = search(path, path_set, n_g, bound)

                if result == "FOUND":
                    return "FOUND", found_path

                if result < min_exceeded:
                    min_exceeded = result

                path.pop()
                path_set.remove(n_state)

            return min_exceeded, None

        while True:
            transposition_table = {}
            path = [start_state]
            path_set = {start_state}

            result, maybe_path = search(path, path_set, 0, threshold)

            if result == "FOUND":
                final_path = [state[0] for state in (maybe_path or [])]
                found = True
                break

            if result == float("inf"):
                break

            threshold = result

        time_ms = (time.time() - t0) * 1000
        final_cost = _compute_path_cost(grid, final_path) if found else 0

        q.put(_DONE)
        q.put({
            "explored": frozenset(explored_overall),
            "frontier": frozenset(),
            "cell_branch": {},
            "path": final_path,
            "found": found,
            "done": True,
            "cost": final_cost,
            "time_ms": time_ms,
        })

    q = queue.Queue()
    t = threading.Thread(target=worker, args=(q,), daemon=True)
    t.start()

    while True:
        item = q.get()
        if item is _DONE:
            yield q.get()
            break
        yield item
