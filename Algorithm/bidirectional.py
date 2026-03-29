"""
Bidirectional Search (BDS)
- Chạy BFS từ cả Start và Goal cùng lúc.
- Phù hợp cho không gian trạng thái đối xứng, giảm độ sâu tìm kiếm.
"""

from collections import deque
import time
from core.grid import Grid


def _compute_path_cost(grid: Grid, path):
    if not path:
        return 0
    # Tổng cost các ô đi vào, không tính ô start.
    return sum(grid.get_cost(r, c) for r, c in path[1:])


def _find_compatible_state(state, opposite_states_by_pos, all_goods):
    pos, collected_goods = state
    for opposite_state in opposite_states_by_pos.get(pos, []):
        if collected_goods | opposite_state[1] == all_goods:
            return opposite_state
    return None


def _reconstruct_path(meet_fwd, meet_bwd, parent_fwd, parent_bwd):
    path_fwd_states = []
    node = meet_fwd
    while node is not None:
        path_fwd_states.append(node)
        node = parent_fwd[node]
    path_fwd_states.reverse()

    path_bwd_states = []
    node = meet_bwd
    while node is not None:
        path_bwd_states.append(node)
        node = parent_bwd.get(node)

    path_fwd = [state[0] for state in path_fwd_states]
    path_bwd = [state[0] for state in path_bwd_states]

    # Bỏ vị trí meet bị trùng giữa 2 nửa đường đi.
    return path_fwd + path_bwd[1:]


def _expand_one(
    queue,
    visited_self,
    states_by_pos_self,
    states_by_pos_other,
    parent_self,
    grid,
    explored,
    all_goods,
):
    if not queue:
        return False, None, None

    curr = queue.popleft()
    curr_pos, curr_goods = curr
    explored.add(curr_pos)

    meet_other = _find_compatible_state(curr, states_by_pos_other, all_goods)
    if meet_other is not None:
        return True, curr, meet_other

    row, col = curr_pos
    for neighbor, _ in grid.get_neighbors(row, col):
        npos = neighbor.position

        next_goods = curr_goods
        if npos in all_goods:
            next_goods = curr_goods | frozenset({npos})

        nstate = (npos, next_goods)
        if nstate in visited_self:
            continue

        visited_self.add(nstate)
        parent_self[nstate] = curr
        queue.append(nstate)
        states_by_pos_self.setdefault(npos, []).append(nstate)

        meet_other = _find_compatible_state(nstate, states_by_pos_other, all_goods)
        if meet_other is not None:
            return True, nstate, meet_other

    return False, None, None


def bidirectional_search(grid: Grid):
    start = grid.start
    goal = grid.goal
    all_goods = frozenset(grid.goods)

    if not start or not goal:
        return {"path": [], "explored": set(), "cost": 0, "time_ms": 0}

    start_goods = frozenset({start}) if start in all_goods else frozenset()
    goal_goods = frozenset({goal}) if goal in all_goods else frozenset()

    if start == goal and start_goods == all_goods:
        return {"path": [start], "explored": {start}, "cost": 0, "time_ms": 0}

    t0 = time.time()

    start_state = (start, start_goods)
    goal_state = (goal, goal_goods)

    queue_fwd = deque([start_state])
    queue_bwd = deque([goal_state])

    visited_fwd = {start_state}
    visited_bwd = {goal_state}

    states_fwd_by_pos = {start: [start_state]}
    states_bwd_by_pos = {goal: [goal_state]}

    parent_fwd = {start_state: None}
    parent_bwd = {goal_state: None}

    explored = set()
    meet_fwd = None
    meet_bwd = None

    while queue_fwd and queue_bwd:
        if len(queue_fwd) <= len(queue_bwd):
            found, curr_self, curr_other = _expand_one(
                queue_fwd,
                visited_fwd,
                states_fwd_by_pos,
                states_bwd_by_pos,
                parent_fwd,
                grid,
                explored,
                all_goods,
            )
            if found:
                meet_fwd, meet_bwd = curr_self, curr_other
        else:
            found, curr_self, curr_other = _expand_one(
                queue_bwd,
                visited_bwd,
                states_bwd_by_pos,
                states_fwd_by_pos,
                parent_bwd,
                grid,
                explored,
                all_goods,
            )
            if found:
                meet_bwd, meet_fwd = curr_self, curr_other

        if found:
            break

    time_ms = (time.time() - t0) * 1000

    if meet_fwd is None or meet_bwd is None:
        return {"path": [], "explored": explored, "cost": 0, "time_ms": time_ms}

    path = _reconstruct_path(meet_fwd, meet_bwd, parent_fwd, parent_bwd)
    return {
        "path": path,
        "explored": explored,
        "cost": _compute_path_cost(grid, path),
        "time_ms": time_ms,
    }


def bidirectional_steps(grid: Grid):
    """Generator step-by-step cho animation."""
    start = grid.start
    goal = grid.goal
    all_goods = frozenset(grid.goods)

    if not start or not goal:
        yield {
            "explored": set(), "frontier": set(), "cell_branch": {},
            "path": [], "found": False, "done": True, "cost": 0, "time_ms": 0,
        }
        return

    start_goods = frozenset({start}) if start in all_goods else frozenset()
    goal_goods = frozenset({goal}) if goal in all_goods else frozenset()

    if start == goal and start_goods == all_goods:
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

    start_state = (start, start_goods)
    goal_state = (goal, goal_goods)

    queue_fwd = deque([start_state])
    queue_bwd = deque([goal_state])

    visited_fwd = {start_state}
    visited_bwd = {goal_state}

    states_fwd_by_pos = {start: [start_state]}
    states_bwd_by_pos = {goal: [goal_state]}

    parent_fwd = {start_state: None}
    parent_bwd = {goal_state: None}

    explored = set()
    meet_fwd = None
    meet_bwd = None

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
            found, curr_self, curr_other = _expand_one(
                queue_fwd,
                visited_fwd,
                states_fwd_by_pos,
                states_bwd_by_pos,
                parent_fwd,
                grid,
                explored,
                all_goods,
            )
            if found:
                meet_fwd, meet_bwd = curr_self, curr_other
        else:
            found, curr_self, curr_other = _expand_one(
                queue_bwd,
                visited_bwd,
                states_bwd_by_pos,
                states_fwd_by_pos,
                parent_bwd,
                grid,
                explored,
                all_goods,
            )
            if found:
                meet_bwd, meet_fwd = curr_self, curr_other

        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(
                [state[0] for state in queue_fwd] + [state[0] for state in queue_bwd]
            ),
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

    if meet_fwd is None or meet_bwd is None:
        yield {
            "explored": frozenset(explored),
            "frontier": frozenset(
                [state[0] for state in queue_fwd] + [state[0] for state in queue_bwd]
            ),
            "cell_branch": {},
            "path": [],
            "found": False,
            "done": True,
            "cost": 0,
            "time_ms": time_ms,
        }
        return

    path = _reconstruct_path(meet_fwd, meet_bwd, parent_fwd, parent_bwd)
    yield {
        "explored": frozenset(explored),
        "frontier": frozenset(
            [state[0] for state in queue_fwd] + [state[0] for state in queue_bwd]
        ),
        "cell_branch": {},
        "path": path,
        "found": True,
        "done": True,
        "cost": _compute_path_cost(grid, path),
        "time_ms": time_ms,
    }
