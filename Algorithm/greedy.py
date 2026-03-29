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


def _make_state(pos, collected, all_goods):
    """Normalize state: luôn collect goods tại vị trí hiện tại."""
    if pos in all_goods:
        collected = collected | frozenset({pos})
    return (pos, collected)


def _state_heuristic(state, goal, all_goods, heuristic_fn):
    pos, collected_goods = state
    remaining_goods = all_goods - collected_goods
    if remaining_goods:
        nearest_goods = min(remaining_goods, key=lambda g: heuristic_fn(pos, g))
        return heuristic_fn(pos, nearest_goods) + heuristic_fn(nearest_goods, goal)
    return heuristic_fn(pos, goal)


def greedy_steps(grid: Grid, heuristic_name='manhattan'):
    start = grid.start
    goal = grid.goal
    all_goods = frozenset(grid.goods)

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

    # FIX: Dùng _make_state để normalize — tránh duplicate state tại goods position
    start_state = _make_state(start, frozenset(), all_goods)

    if start == goal and start_state[1] == all_goods:
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

    counter = 0
    open_heap = [(_state_heuristic(start_state, goal, all_goods, heuristic_fn), counter, start_state)]

    visited = {start_state}
    parent = {start_state: None}
    g_score = {start_state: 0}
    explored = set()
    frontier_count = {start: 1}

    found = False
    goal_state = None

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
        _, _, curr_state = heapq.heappop(open_heap)
        curr, collected_goods = curr_state

        if curr_state in explored:
            frontier_count[curr] = frontier_count.get(curr, 1) - 1
            if frontier_count[curr] <= 0:
                frontier_count.pop(curr, None)
            continue

        explored.add(curr_state)
        frontier_count[curr] = frontier_count.get(curr, 1) - 1
        if frontier_count[curr] <= 0:
            frontier_count.pop(curr, None)

        if curr == goal and collected_goods == all_goods:
            found = True
            goal_state = curr_state
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position

            # FIX: Dùng _make_state — collect goods ngay khi tạo state mới
            next_state = _make_state(npos, collected_goods, all_goods)

            if next_state in visited:
                continue

            visited.add(next_state)
            parent[next_state] = curr_state
            g_score[next_state] = g_score[curr_state] + neighbor.cost

            counter += 1
            heapq.heappush(
                open_heap,
                (_state_heuristic(next_state, goal, all_goods, heuristic_fn), counter, next_state),
            )
            frontier_count[npos] = frontier_count.get(npos, 0) + 1

        yield {
            "explored": frozenset(state[0] for state in explored),
            "frontier": frozenset(frontier_count.keys()),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": False,
            "cost": 0,
            "time_ms": (time.time() - t0) * 1000,
        }

    time_ms = (time.time() - t0) * 1000
    path_states = _reconstruct_path(parent, goal_state) if found and goal_state is not None else []
    path = [state[0] for state in path_states]

    yield {
        "explored": frozenset(state[0] for state in explored),
        "frontier": frozenset(frontier_count.keys()),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        "cost": g_score.get(goal_state, 0) if found else 0,
        "time_ms": time_ms,
    }