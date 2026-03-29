"""
renderer.py
Vẽ Grid lên màn hình Pygame bằng ảnh PNG thay thế màu cũ.

Quy tắc tile:
  E  → normal_path.png  (cứ 3 ô thì 1 ô dùng normal_path2.png)
       normal_path2 xoay 90° khi thuật toán đang dò theo trục Y
  W  → wall.png / wall1.png … wall5.png  (random mỗi ô, cố định sau khi tạo)
  O  → cost_path.png
  T  → good.png
  G  → goal.png
  P  → normal_path.png  (Start cũng dùng đường bình thường)

Trong quá trình search:
  explored   → explored.png  (đè lên ô đã dò)
  frontier   → current_search.png  (ô đang xét)
  Shipper    → CHƯA hiện

Sau khi search xong (done):
  - Reset map về trạng thái ban đầu
  - Shipper xuất hiện, đi từng ô theo path
  - Ô shipper đã đi qua → final_path.png
"""

import os
import random
import pygame
from typing import Dict, List, Optional, Set, Tuple
from core.grid import Grid

CELL_SIZE = 36
MARGIN    = 1


def _load(path: str, size: tuple) -> pygame.Surface:
    """Load và scale ảnh về đúng CELL_SIZE × CELL_SIZE. Fallback nếu thiếu file."""
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((200, 200, 200, 255))
    return surf


class Renderer:
    def __init__(self, grid: Grid, offset_x: int = 0, offset_y: int = 0,
                 base_dir: str = ''):
        self.grid      = grid
        self.offset_x  = offset_x
        self.offset_y  = offset_y
        self.base_dir  = base_dir
        self._cell     = (CELL_SIZE, CELL_SIZE)

        # ── Tải sprites ──────────────────────────────────────────────────
        pic = lambda name: os.path.join(base_dir, 'picture', name)

        self.spr_normal      = _load(pic('normal_path.png'),   self._cell)
        self.spr_normal2     = _load(pic('normal_path2.png'),  self._cell)
        self.spr_normal2_rot = pygame.transform.rotate(self.spr_normal2, 90)
        # Wall variants: wall.png, wall1.png … wall5.png  (6 biến thể)
        self.spr_walls       = [
            _load(pic('wall.png'),  self._cell),
            _load(pic('wall1.png'), self._cell),
            _load(pic('wall2.png'), self._cell),
            _load(pic('wall3.png'), self._cell),
            _load(pic('wall4.png'), self._cell),
            _load(pic('wall5.png'), self._cell),
        ]
        self.spr_cost        = _load(pic('cost_path.png'),     self._cell)
        self.spr_good        = _load(pic('good.png'),          self._cell)
        self.spr_goal        = _load(pic('goal.png'),          self._cell)
        self.spr_explored    = _load(pic('explored.png'),      self._cell)
        self.spr_current     = _load(pic('current_search.png'),self._cell)
        self.spr_final       = _load(pic('explored.png'),    self._cell)

        # Shipper (dùng ảnh gốc, không scale về CELL_SIZE vì có thể to hơn)
        shipper_raw = pic('shipper.png')
        if os.path.exists(shipper_raw):
            self.spr_shipper = pygame.image.load(shipper_raw).convert_alpha()
            self.spr_shipper = pygame.transform.smoothscale(
                self.spr_shipper, self._cell)
        else:
            self.spr_shipper = pygame.Surface(self._cell, pygame.SRCALPHA)
            self.spr_shipper.fill((255, 165, 0, 255))

        # ── Bảng tile cố định mỗi map (để dùng lại khi reset) ────────────
        # Precompute ô nào dùng normal_path2 (cứ mỗi 3 ô E thì 1 ô dùng np2)
        self._e_counter: Dict[Tuple[int,int], int] = {}
        cnt = 0
        for r in range(grid.rows):
            for c in range(grid.cols):
                if grid.get_node(r, c).cell_type in ('E', 'P'):
                    self._e_counter[(r, c)] = cnt
                    cnt += 1

        # Precompute variant wall ngẫu nhiên cho từng ô tường (cố định suốt vòng đời map)
        self._wall_variant: Dict[Tuple[int,int], int] = {}
        for r in range(grid.rows):
            for c in range(grid.cols):
                if grid.get_node(r, c).cell_type == 'W':
                    self._wall_variant[(r, c)] = random.randrange(len(self.spr_walls))


        self._phase         = 'idle'    # 'idle' | 'searching' | 'walking'
        self._explored: Set = set()
        self._frontier: Set = set()
        self._final_path: List = []
        self._visited_path: Set = set()   # ô shipper đã đi qua
        self._shipper_pos: Optional[Tuple[int,int]] = None
        self._direction   = 'x'          # hướng dò hiện tại: 'x' hoặc 'y'

    # ── Public API ────────────────────────────────────────────────────────

    def set_phase_searching(self, explored: Set, frontier: Set,
                            direction: str = 'x'):
        """Gọi mỗi step khi đang search."""
        self._phase    = 'searching'
        self._explored = explored
        self._frontier = frontier
        self._direction = direction

    def set_phase_walking(self, path: List[Tuple[int,int]]):
        """Gọi sau khi search xong, bắt đầu cho shipper đi."""
        self._phase        = 'walking'
        self._final_path   = list(path)
        self._visited_path = set()
        self._shipper_pos  = path[0] if path else None
        self._explored     = set()
        self._frontier     = set()

    def advance_shipper(self) -> bool:
        """
        Di chuyển shipper thêm 1 bước trên path.
        Trả về True nếu còn bước, False nếu đã tới đích.
        """
        if not self._final_path:
            return False
        if self._shipper_pos in self._final_path:
            idx = self._final_path.index(self._shipper_pos)
        else:
            return False

        self._visited_path.add(self._shipper_pos)

        if idx + 1 < len(self._final_path):
            self._shipper_pos = self._final_path[idx + 1]
            return True
        return False

    def reset_state(self):
        self._phase        = 'idle'
        self._explored     = set()
        self._frontier     = set()
        self._final_path   = []
        self._visited_path = set()
        self._shipper_pos  = None

    # ── Draw ──────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        """Vẽ toàn bộ grid theo phase hiện tại."""
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self._draw_cell(surface, r, c)

        # Vẽ shipper lên trên cùng
        if self._phase == 'walking' and self._shipper_pos is not None:
            sr, sc = self._shipper_pos
            x = self.offset_x + sc * (CELL_SIZE + MARGIN)
            y = self.offset_y + sr * (CELL_SIZE + MARGIN)
            surface.blit(self.spr_shipper, (x, y))

    def _draw_cell(self, surface: pygame.Surface, row: int, col: int):
        node = self.grid.get_node(row, col)
        ct   = node.cell_type
        pos  = (row, col)

        x = self.offset_x + col * (CELL_SIZE + MARGIN)
        y = self.offset_y + row * (CELL_SIZE + MARGIN)

        # 1. Vẽ tile nền (luôn vẽ trước)
        base = self._base_sprite(row, col, ct)
        surface.blit(base, (x, y))

        # 2. Đè overlay theo phase
        if self._phase == 'searching':
            if pos in self._frontier and ct not in ('W', 'G'):
                surface.blit(self.spr_current, (x, y))
            elif pos in self._explored and ct not in ('W', 'G', 'P'):
                surface.blit(self.spr_explored, (x, y))

        elif self._phase == 'walking':
            if ct not in ('W', 'G') and pos in self._visited_path:
                surface.blit(self.spr_final, (x, y))

    def _base_sprite(self, row: int, col: int, ct: str) -> pygame.Surface:
        """Trả về sprite nền cho ô (row, col) theo loại ô."""
        if ct == 'W':
            variant = self._wall_variant.get((row, col), 0)
            return self.spr_walls[variant]
        if ct == 'O':
            return self.spr_cost
        if ct == 'T':
            return self.spr_good
        if ct == 'G':
            return self.spr_goal
        # E và P đều dùng normal_path / normal_path2
        idx = self._e_counter.get((row, col), 0)
        if idx % 4 == 3:          # cứ 3 normal_path thì 1 normal_path2
            if self._direction == 'y':
                return self.spr_normal2_rot
            return self.spr_normal2
        return self.spr_normal

    # ── Pixel helpers ─────────────────────────────────────────────────────

    def pixel_to_cell(self, px: int, py: int) -> Optional[Tuple[int,int]]:
        col = (px - self.offset_x) // (CELL_SIZE + MARGIN)
        row = (py - self.offset_y) // (CELL_SIZE + MARGIN)
        if self.grid.in_bounds(row, col):
            return (row, col)
        return None

    @property
    def grid_pixel_width(self) -> int:
        return self.grid.cols * (CELL_SIZE + MARGIN)

    @property
    def grid_pixel_height(self) -> int:
        return self.grid.rows * (CELL_SIZE + MARGIN)