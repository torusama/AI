"""
renderer.py
Vẽ Grid và trạng thái thuật toán lên màn hình Pygame.
"""

import pygame
from typing import List, Tuple, Set, Optional
from core.grid import Grid
from gui.colors import (
    CELL_COLORS, EXPLORED_COLOR, FRONTIER_COLOR, PATH_COLOR,
    GRID_LINE, TEXT_DARK
)

# Kích thước mỗi ô (pixel)
CELL_SIZE = 36
MARGIN    = 1    # Khoảng cách giữa các ô


class Renderer:
    """
    Vẽ toàn bộ Grid và overlay trạng thái thuật toán lên surface Pygame.

    Attributes:
        grid (Grid): Bản đồ cần vẽ.
        offset_x (int): Tọa độ x bắt đầu vẽ grid (để chừa chỗ cho panel).
        offset_y (int): Tọa độ y bắt đầu vẽ grid.
    """

    def __init__(self, grid: Grid, offset_x: int = 0, offset_y: int = 0):
        self.grid     = grid
        self.offset_x = offset_x
        self.offset_y = offset_y

        # Tải font
        pygame.font.init()
        self.font_cell  = pygame.font.SysFont('Arial', 11, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 13, bold=True)

    # ── Vẽ toàn bộ grid ───────────────────────────────────────────────────

    def draw(
        self,
        surface: pygame.Surface,
        explored:  Optional[Set[Tuple[int, int]]] = None,
        frontier:  Optional[Set[Tuple[int, int]]] = None,
        path:      Optional[List[Tuple[int, int]]] = None,
    ):
        """
        Vẽ grid lên surface.

        Args:
            surface:  Pygame surface để vẽ lên.
            explored: Tập hợp (row, col) đã khám phá.
            frontier: Tập hợp (row, col) đang trong frontier.
            path:     Danh sách (row, col) tạo thành đường đi cuối cùng.
        """
        explored = explored or set()
        frontier = frontier or set()
        path     = set(path) if path else set()

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self._draw_cell(surface, r, c, explored, frontier, path)

    def _draw_cell(
        self,
        surface: pygame.Surface,
        row: int, col: int,
        explored: Set[Tuple[int, int]],
        frontier: Set[Tuple[int, int]],
        path:     Set[Tuple[int, int]],
    ):
        """Vẽ một ô đơn lẻ với màu tương ứng."""
        node = self.grid.get_node(row, col)
        pos  = (row, col)

        # Xác định màu nền ô
        if pos in path and node.cell_type not in ('P', 'G'):
            color = PATH_COLOR
        elif pos in frontier:
            color = FRONTIER_COLOR
        elif pos in explored and node.cell_type not in ('P', 'G', 'W'):
            color = EXPLORED_COLOR
        else:
            color = CELL_COLORS.get(node.cell_type, (240, 240, 240))

        # Tính tọa độ pixel
        x = self.offset_x + col * (CELL_SIZE + MARGIN)
        y = self.offset_y + row * (CELL_SIZE + MARGIN)
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

        # Vẽ ô
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, GRID_LINE, rect, 1)

        # Vẽ nhãn ký tự trong ô
        label = node.cell_type
        if label in ('P', 'G', 'T', 'O'):
            text_surf = self.font_cell.render(label, True, TEXT_DARK)
            text_rect = text_surf.get_rect(center=rect.center)
            surface.blit(text_surf, text_rect)

    # ── Tiện ích ──────────────────────────────────────────────────────────

    def pixel_to_cell(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """
        Chuyển tọa độ pixel (click chuột) sang (row, col) trên grid.
        Trả về None nếu click ngoài grid.
        """
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