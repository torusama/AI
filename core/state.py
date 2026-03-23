from dataclasses import dataclass, field
from typing import FrozenSet, Tuple
 
 
@dataclass(frozen=True)
class State:
    """
    Trạng thái của Pacman tại một thời điểm.
 
    Attributes:
        row (int): Hàng hiện tại (0-indexed, tính từ trên xuống).
        col (int): Cột hiện tại (0-indexed, tính từ trái sang).
        goods_collected (FrozenSet): Tập hợp tọa độ hàng đã thu thập.
                                     Dùng frozenset để State có thể hash được.
    """
    row: int
    col: int
    goods_collected: FrozenSet[Tuple[int, int]] = field(default_factory=frozenset)
 
    @property
    def position(self) -> Tuple[int, int]:
        """Trả về vị trí dạng tuple (row, col)."""
        return (self.row, self.col)
 
    def collect_good(self, pos: Tuple[int, int]) -> 'State':
        """
        Tạo State mới sau khi thu thập hàng tại vị trí pos.
        (State là immutable nên phải tạo object mới.)
        """
        new_goods = self.goods_collected | frozenset([pos])
        return State(self.row, self.col, new_goods)
 
    def move_to(self, new_row: int, new_col: int) -> 'State':
        """
        Tạo State mới sau khi di chuyển đến (new_row, new_col).
        Giữ nguyên goods_collected.
        """
        return State(new_row, new_col, self.goods_collected)
 
    def has_collected(self, pos: Tuple[int, int]) -> bool:
        """Kiểm tra đã thu thập hàng tại pos chưa."""
        return pos in self.goods_collected
 
    def __repr__(self) -> str:
        return f"State(row={self.row}, col={self.col}, goods={len(self.goods_collected)} collected)"
 
 
# ── Dùng đơn giản (không track goods) ──────────────────────────────────────
 
def make_state(row: int, col: int) -> State:
    """Tạo State cơ bản không track hàng hóa."""
    return State(row, col)
 
 
def make_state_with_goods(row: int, col: int, goods: FrozenSet[Tuple[int, int]]) -> State:
    """Tạo State có track hàng hóa đã thu thập."""
    return State(row, col, goods)