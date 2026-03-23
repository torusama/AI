"""
Chức năng:
- Load map từ file .txt
- Truy vấn thông tin ô (loại ô, chi phí, hàng xóm)
- Tìm vị trí Pacman, Goal, Goods
"""

from typing import List, Tuple, Optional, Dict
from core.cost import (
    CELL_WALL, CELL_PACMAN, CELL_GOAL, CELL_GOODS,
    DIRECTIONS, get_cost, is_passable
)


class Node:
    """
    Đại diện cho một ô trong Grid.

    Attributes:
        row (int): Hàng của ô.
        col (int): Cột của ô.
        cell_type (str): Loại ô ('E', 'W', 'O', 'T', 'P', 'G').
        cost (float): Chi phí di chuyển vào ô này.
    """

    def __init__(self, row: int, col: int, cell_type: str):
        self.row = row
        self.col = col
        self.cell_type = cell_type
        self.cost = get_cost(cell_type)

    @property
    def position(self) -> Tuple[int, int]:
        return (self.row, self.col)

    @property
    def passable(self) -> bool:
        return is_passable(self.cell_type)

    def __repr__(self) -> str:
        return f"Node({self.row},{self.col} type='{self.cell_type}' cost={self.cost})"


class Grid:
    """
    Bản đồ Grid 2D.

    Cung cấp:
    - Truy cập ô qua grid[row][col] hoặc grid.get_node(row, col)
    - Danh sách hàng xóm hợp lệ của một ô
    - Vị trí bắt đầu (Pacman), đích (Goal), hàng hóa (Goods)
    """

    def __init__(self, cells: List[List[str]]):
        """
        Khởi tạo Grid từ ma trận ký tự 2D.

        Args:
            cells: List[List[str]] — ma trận ký tự từ file map.
        """
        self.rows = len(cells)
        self.cols = len(cells[0]) if cells else 0
        self._nodes: List[List[Node]] = [
            [Node(r, c, cells[r][c]) for c in range(self.cols)]
            for r in range(self.rows)
        ]
        self._start: Optional[Tuple[int, int]] = None
        self._goal: Optional[Tuple[int, int]] = None
        self._goods: List[Tuple[int, int]] = []
        self._scan_special_cells()

    # ── Khởi tạo ──────────────────────────────────────────────────────────

    def _scan_special_cells(self):
        """Tìm vị trí Pacman, Goal, và tất cả Goods trên map."""
        for r in range(self.rows):
            for c in range(self.cols):
                ct = self._nodes[r][c].cell_type
                if ct == CELL_PACMAN:
                    self._start = (r, c)
                elif ct == CELL_GOAL:
                    self._goal = (r, c)
                elif ct == CELL_GOODS:
                    self._goods.append((r, c))

    # ── Truy cập node ─────────────────────────────────────────────────────

    def get_node(self, row: int, col: int) -> Optional[Node]:
        """Trả về Node tại (row, col), hoặc None nếu ngoài bản đồ."""
        if self.in_bounds(row, col):
            return self._nodes[row][col]
        return None

    def in_bounds(self, row: int, col: int) -> bool:
        """Kiểm tra tọa độ có nằm trong bản đồ không."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_cell_type(self, row: int, col: int) -> Optional[str]:
        node = self.get_node(row, col)
        return node.cell_type if node else None

    def get_cost(self, row: int, col: int) -> float:
        node = self.get_node(row, col)
        return node.cost if node else float('inf')

    # ── Hàng xóm ──────────────────────────────────────────────────────────

    def get_neighbors(self, row: int, col: int) -> List[Tuple[Node, str]]:
        """
        Trả về danh sách (Node, direction) hợp lệ từ ô (row, col).
        Loại bỏ: ngoài bản đồ, tường (Wall).

        Returns:
            List of (neighbor_node, direction_name)
        """
        neighbors = []
        for dr, dc, direction in DIRECTIONS:
            nr, nc = row + dr, col + dc
            node = self.get_node(nr, nc)
            if node and node.passable:
                neighbors.append((node, direction))
        return neighbors

    # ── Vị trí đặc biệt ───────────────────────────────────────────────────

    @property
    def start(self) -> Optional[Tuple[int, int]]:
        """Vị trí bắt đầu (Pacman)."""
        return self._start

    @property
    def goal(self) -> Optional[Tuple[int, int]]:
        """Vị trí đích (Goal)."""
        return self._goal

    @property
    def goods(self) -> List[Tuple[int, int]]:
        """Danh sách tọa độ tất cả Goods trên map."""
        return list(self._goods)

    # ── Load từ file ───────────────────────────────────────────────────────

    @classmethod
    def from_file(cls, filepath: str) -> 'Grid':
        """
        Load bản đồ từ file .txt.

        Định dạng file: mỗi hàng là 1 dòng, các ô cách nhau bởi khoảng trắng.
        Ví dụ:
            P E W E T
            E W O E E
            E E E W G

        Args:
            filepath: Đường dẫn tới file map.

        Returns:
            Grid object.

        Raises:
            FileNotFoundError: Nếu file không tồn tại.
            ValueError: Nếu file rỗng hoặc sai định dạng.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            raise ValueError(f"File map rỗng: {filepath}")

        cells = [line.split() for line in lines]

        # Validate: tất cả hàng phải cùng độ rộng
        col_count = len(cells[0])
        for i, row in enumerate(cells):
            if len(row) != col_count:
                raise ValueError(
                    f"Hàng {i} có {len(row)} ô, kỳ vọng {col_count}. "
                    f"File: {filepath}"
                )

        return cls(cells)

    @classmethod
    def from_string(cls, map_str: str) -> 'Grid':
        """
        Load bản đồ từ chuỗi string (dùng cho testing).

        Args:
            map_str: Chuỗi map nhiều dòng.
        """
        lines = [line.strip() for line in map_str.strip().splitlines() if line.strip()]
        cells = [line.split() for line in lines]
        return cls(cells)

    # ── Hiển thị ──────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"Grid({self.rows}x{self.cols}, start={self._start}, goal={self._goal}, goods={len(self._goods)})"

    def display(self) -> str:
        """In bản đồ ra dạng text (dùng để debug)."""
        rows = []
        for r in range(self.rows):
            row_str = ' '.join(self._nodes[r][c].cell_type for c in range(self.cols))
            rows.append(row_str)
        return '\n'.join(rows)