"""
test_map.py
Script nhanh để kiểm tra map load đúng không.
Chạy: python test_map.py (từ thư mục gốc project)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.grid import Grid

def test_map(filepath: str):
    print(f"=== Load map: {filepath} ===\n")

    grid = Grid.from_file(filepath)

    print(f"Kích thước  : {grid.rows} x {grid.cols}")
    print(f"Start (P)   : {grid.start}")
    print(f"Goal  (G)   : {grid.goal}")
    print(f"Goods (T)   : {grid.goods}")
    print()

    # Kiểm tra start và goal tồn tại
    assert grid.start is not None, "❌ Không tìm thấy P (Pacman start)!"
    assert grid.goal  is not None, "❌ Không tìm thấy G (Goal)!"
    print("✅ Start và Goal hợp lệ")

    # Kiểm tra hàng xóm từ start
    r, c = grid.start
    neighbors = grid.get_neighbors(r, c)
    print(f"✅ Hàng xóm của Start {grid.start}: {[(n.position, d) for n, d in neighbors]}")

    # In bản đồ ra terminal
    print("\n=== Bản đồ ===")
    print(grid.display())
    print("\n✅ Load map thành công!")

if __name__ == "__main__":
    test_map("maps/easy.txt")