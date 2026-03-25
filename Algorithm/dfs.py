"""
Depth First Search (DFS)
- Tìm đường từ start → goal (iterative dùng stack)
- Lưu parent node để reconstruct path
- Trả về: path, explored, cost, time_ms

Cách dùng:
    result  = dfs(grid)          # kết quả cuối
    stepper = dfs_steps(grid)    # generator từng bước để animate
"""

from core.grid import Grid
import time


# ── Kết quả cuối ─────────────────────────────────────────────────────────────

def dfs(grid: Grid):
    start = grid.start
    goal  = grid.goal

    if not start or not goal:
        return {"path": [], "explored": set(), "cost": 0, "time_ms": 0}

    t0 = time.time()

    stack   = [start]
    visited = set()
    parent  = {start: None}
    found   = False

    while stack:
        curr = stack.pop()

        if curr in visited:
            continue
        visited.add(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in reversed(grid.get_neighbors(row, col)):
            npos = neighbor.position
            if npos not in visited:
                if npos not in parent:
                    parent[npos] = curr
                stack.append(npos)

    time_ms = (time.time() - t0) * 1000

    if not found:
        return {"path": [], "explored": visited, "cost": 0, "time_ms": time_ms}

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()

    return {
        "path":     path,
        "explored": visited,
        "cost":     len(path) - 1,
        "time_ms":  time_ms,
    }


# ── Step-by-step generator cho animation ─────────────────────────────────────

def dfs_steps(grid: Grid):
    """
    Generator — mỗi lần yield 1 dict trạng thái DFS tại bước đó.

    Mỗi step trả về:
        explored    : set of (row, col) đã pop ra xử lý
        frontier    : set of (row, col) đang trong stack
        cell_branch : dict (row,col) -> branch_id  (để tô màu nhánh)
        path        : list[(row,col)] đường đi (chỉ có khi found=True)
        found       : bool
        done        : bool
        cost        : int
        time_ms     : float

    Cách gán branch cho DFS:
        - Mỗi lần DFS đi sâu theo 1 hướng → kế thừa branch cha
        - Mỗi lần backtrack sang nhánh mới → tạo branch_id mới
        - DFS chỉ có 1 "con đường đang đi" tại 1 thời điểm,
          các ô visited cũ giữ nguyên màu branch của chúng
    """
    start = grid.start
    goal  = grid.goal

    if not start or not goal:
        yield {
            "explored": set(), "frontier": set(), "cell_branch": {},
            "path": [], "found": False, "done": True, "cost": 0, "time_ms": 0,
        }
        return

    t0 = time.time()

    # cell_branch: (row,col) -> branch_id
    # DFS: mỗi ô trên stack được gán branch khi push
    # branch_id tăng mỗi khi một ô push nhiều hàng xóm (tức là sẽ backtrack)
    cell_branch  = {start: 0}
    next_branch  = [1]

    stack        = [start]
    stack_branch = [0]     # branch tương ứng mỗi phần tử trên stack
    visited      = set()
    parent       = {start: None}
    found        = False

    def snap():
        return {
            "explored":    frozenset(visited),
            "frontier":    frozenset(stack),
            "cell_branch": dict(cell_branch),
            "path":        [],
            "found":       False,
            "done":        False,
            "cost":        0,
            "time_ms":     (time.time() - t0) * 1000,
        }

    # Yield trạng thái khởi tạo
    yield {**snap(), "frontier": frozenset([start])}

    while stack:
        curr        = stack.pop()
        curr_branch = stack_branch.pop()

        if curr in visited:
            yield snap()
            continue

        visited.add(curr)
        cell_branch[curr] = curr_branch

        if curr == goal:
            found = True
            break

        row, col      = curr
        new_neighbors = []
        for neighbor, _ in reversed(grid.get_neighbors(row, col)):
            npos = neighbor.position
            if npos not in visited:
                if npos not in parent:
                    parent[npos] = curr
                new_neighbors.append(npos)

        # Gán branch cho hàng xóm mới
        # DFS push ngược: ô đầu tiên sẽ được pop đầu tiên (đi sâu)
        # → ô đầu tiên kế thừa branch hiện tại
        # → các ô còn lại (sẽ backtrack tới) tạo branch mới
        for i, npos in enumerate(new_neighbors):
            if i == 0:
                b = curr_branch
            else:
                b = next_branch[0]
                next_branch[0] += 1
            cell_branch.setdefault(npos, b)
            stack.append(npos)
            stack_branch.append(b)

        yield snap()

    time_ms = (time.time() - t0) * 1000

    # Reconstruct path
    path = []
    if found:
        node = goal
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()

    yield {
        "explored":    frozenset(visited),
        "frontier":    frozenset(stack),
        "cell_branch": dict(cell_branch),
        "path":        path,
        "found":       found,
        "done":        True,
        "cost":        len(path) - 1 if found else 0,
        "time_ms":     time_ms,
    }
