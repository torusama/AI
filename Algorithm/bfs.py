"""
Breadth First Search (BFS)
- Tìm đường từ start → goal
- Trả về từng STEP để animate (mỗi bước = pop 1 node khỏi queue)
- Mỗi ô được gán branch_id để tô màu theo nhánh đường đi

Cách dùng:
    result  = bfs(grid)          # kết quả cuối (path, explored, cost, time_ms)
    stepper = bfs_steps(grid)    # generator từng bước để animate
"""

from collections import deque
from core.grid import Grid
import time


# ── Kết quả cuối (dùng cho panel stats) ──────────────────────────────────────

def bfs(grid: Grid):
    start = grid.start
    goal  = grid.goal

    if not start or not goal:
        return {"path": [], "explored": set(), "cost": 0, "time_ms": 0}

    t0 = time.time()

    queue    = deque([start])
    visited  = {start}
    parent   = {start: None}
    explored = set()
    found    = False

    while queue:
        curr = queue.popleft()
        explored.add(curr)

        if curr == goal:
            found = True
            break

        row, col = curr
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            if npos not in visited:
                visited.add(npos)
                parent[npos] = curr
                queue.append(npos)

    time_ms = (time.time() - t0) * 1000

    if not found:
        return {"path": [], "explored": explored, "cost": 0, "time_ms": time_ms}

    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()

    return {
        "path":     path,
        "explored": explored,
        "cost":     len(path) - 1,
        "time_ms":  time_ms,
    }


# ── Step-by-step generator cho animation ─────────────────────────────────────

def bfs_steps(grid: Grid):
    """
    Generator — mỗi lần yield 1 dict trạng thái BFS tại bước đó.

    Mỗi step trả về:
        explored    : set of (row, col) đã pop ra xử lý
        frontier    : set of (row, col) đang trong queue
        cell_branch : dict (row,col) -> branch_id  (để tô màu nhánh)
        path        : list[(row,col)] đường đi (chỉ có khi found=True)
        found       : bool
        done        : bool  (True ở step cuối cùng)
        cost        : int
        time_ms     : float
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

    # branch_id: mỗi ô thuộc về 1 "nhánh đường đi"
    # Khi 1 node expand có nhiều hàng xóm mới:
    #   - hàng xóm đầu tiên kế thừa branch của cha
    #   - các hàng xóm còn lại tạo branch mới
    cell_branch  = {start: 0}
    next_branch  = [1]

    queue        = deque([start])
    queue_branch = deque([0])   # branch tương ứng mỗi phần tử trong queue
    visited      = {start}
    parent       = {start: None}
    explored     = set()
    found        = False

    def snap():
        return {
            "explored":    frozenset(explored),
            "frontier":    frozenset(queue),
            "cell_branch": dict(cell_branch),
            "path":        [],
            "found":       False,
            "done":        False,
            "cost":        0,
            "time_ms":     (time.time() - t0) * 1000,
        }

    # Yield trạng thái khởi tạo
    yield {**snap(), "frontier": frozenset([start])}

    while queue:
        curr        = queue.popleft()
        curr_branch = queue_branch.popleft()
        explored.add(curr)

        if curr == goal:
            found = True
            break

        row, col      = curr
        new_neighbors = []
        for neighbor, _ in grid.get_neighbors(row, col):
            npos = neighbor.position
            if npos not in visited:
                visited.add(npos)
                parent[npos] = curr
                new_neighbors.append(npos)

        # Gán branch cho hàng xóm mới
        for i, npos in enumerate(new_neighbors):
            if i == 0:
                b = curr_branch      # kế thừa branch cha
            else:
                b = next_branch[0]   # tạo branch mới
                next_branch[0] += 1
            cell_branch[npos] = b
            queue.append(npos)
            queue_branch.append(b)

        yield snap()

    time_ms = (time.time() - t0) * 1000

    # Reconstruct path nếu tìm thấy
    path = []
    if found:
        node = goal
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()

    # Step cuối — kết quả đầy đủ
    yield {
        "explored":    frozenset(explored),
        "frontier":    frozenset(queue),
        "cell_branch": dict(cell_branch),
        "path":        path,
        "found":       found,
        "done":        True,
        "cost":        len(path) - 1 if found else 0,
        "time_ms":     time_ms,
    }
