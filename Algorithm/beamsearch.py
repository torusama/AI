import time

from core.grid import Grid
from core.heuristic import manhattan_distance, euclidean_distance


DEFAULT_BEAM_WIDTH = 8


def _reconstruct_path(parent, goal):
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def _state_heuristic(state, goal, all_goods, heuristic_fn):
    pos, collected_goods = state
    remaining_goods = all_goods - collected_goods
    if remaining_goods:
        return min(heuristic_fn(pos, goods_pos) for goods_pos in remaining_goods)
    return heuristic_fn(pos, goal)


def beam_search_steps(grid: Grid, heuristic_name='manhattan', beam_width=DEFAULT_BEAM_WIDTH):
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

    beam_width = max(1, int(beam_width))
    t0 = time.time()

    start_goods = frozenset({start}) if start in all_goods else frozenset()
    start_state = (start, start_goods)

    current_beam = [start_state]
    parent = {start_state: None}
    g_score = {start_state: 0}
    visited = {start_state}
    explored = set()
    found = False
    goal_state = None

    if start == goal and start_goods == all_goods:
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

        for curr_state in current_beam:
            curr, collected_goods = curr_state

            if curr == goal and collected_goods == all_goods:
                found = True
                goal_state = curr_state
                break

            explored.add(curr)

            row, col = curr
            for neighbor, _ in grid.get_neighbors(row, col):
                npos = neighbor.position
                next_goods = collected_goods
                if npos in all_goods:
                    next_goods = collected_goods | frozenset({npos})

                next_state = (npos, next_goods)
                if next_state in visited:
                    continue

                visited.add(next_state)
                parent[next_state] = curr_state
                g_score[next_state] = g_score[curr_state] + neighbor.cost

                if npos == goal and next_goods == all_goods:
                    found = True
                    goal_state = next_state
                    break

                next_candidates.append((
                    g_score[next_state] + _state_heuristic(next_state, goal, all_goods, heuristic_fn),
                    -len(next_goods),
                    npos,
                    next_state,
                ))

            if found:
                break

        if found:
            break

        next_candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        current_beam = [state for _, _, _, state in next_candidates[:beam_width]]

        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(state[0] for state in current_beam),
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
        "explored": frozenset(explored),
        "frontier": frozenset(state[0] for state in current_beam) if not found else frozenset(),
        "cell_branch": {},
        "path": path,
        "found": found,
        "done": True,
        "cost": g_score.get(goal_state, 0) if found else 0,
        "time_ms": time_ms,
    }
