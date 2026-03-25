"""
renderer.py
Vẽ Grid và trạng thái thuật toán lên màn hình Pygame.

Hỗ trợ 2 chế độ:
  1. Kết quả cuối (explored + path)  — như cũ
  2. Animate step-by-step từ bfs_steps() / dfs_steps():
       - Đang chạy : frontier = VÀNG, explored = XANH NHẠT (1 màu duy nhất)
       - Kết thúc  : đường đúng = ĐỎ ĐẬM, nhánh sai = ĐỎ NHẠT
"""

import pygame
from typing import Dict, List, Optional, Set, Tuple
from core.grid import Grid
from gui.colors import (
    CELL_COLORS, EXPLORED_COLOR, FRONTIER_COLOR,
    PATH_COLOR, PATH_WRONG_COLOR,
    GRID_LINE, TEXT_DARK,
)

CELL_SIZE = 36
MARGIN    = 1


class Renderer:
    def __init__(self, grid: Grid, offset_x: int = 0, offset_y: int = 0):
        self.grid     = grid
        self.offset_x = offset_x
        self.offset_y = offset_y

        pygame.font.init()
        self.font_cell  = pygame.font.SysFont('Arial', 11, bold=True)
        self.font_label = pygame.font.SysFont('Arial', 13, bold=True)

    # ── Vẽ kết quả cuối (chế độ cũ) ──────────────────────────────────────

    def draw(
        self,
        surface:  pygame.Surface,
        explored: Optional[Set[Tuple[int, int]]] = None,
        frontier: Optional[Set[Tuple[int, int]]] = None,
        path:     Optional[List[Tuple[int, int]]] = None,
    ):
        explored = explored or set()
        frontier = frontier or set()
        path_set = set(path) if path else set()

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self._draw_cell_classic(surface, r, c, explored, frontier, path_set)

    def _draw_cell_classic(self, surface, row, col, explored, frontier, path_set):
        node = self.grid.get_node(row, col)
        pos  = (row, col)

        if pos in path_set and node.cell_type not in ('P', 'G'):
            color = PATH_COLOR
        elif pos in frontier:
            color = FRONTIER_COLOR
        elif pos in explored and node.cell_type not in ('P', 'G', 'W'):
            color = EXPLORED_COLOR
        else:
            color = CELL_COLORS.get(node.cell_type, (240, 240, 240))

        self._blit_cell(surface, row, col, color, node.cell_type)

    # ── Vẽ animate step-by-step ───────────────────────────────────────────

    def draw_step(
        self,
        surface:     pygame.Surface,
        step:        dict,
    ):
        """
        Vẽ 1 frame từ bfs_steps() generator.

        step dict keys: explored, frontier, cell_branch, path, found, done
        """
        cell_branch: Dict[Tuple[int,int], int] = step.get("cell_branch", {})
        explored:    Set  = step.get("explored",    set())
        frontier:    Set  = step.get("frontier",    set())
        path:        List = step.get("path",         [])
        found:       bool = step.get("found",       False)
        done:        bool = step.get("done",        False)

        path_set = set(path) if path else set()

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self._draw_cell_step(
                    surface, r, c,
                    cell_branch, explored, frontier,
                    path_set, found, done,
                )

        # Vẽ đường line lên trên khi done + found
        if done and found and len(path) > 1:
            self._draw_path_line(surface, path)

    def _draw_cell_step(
        self, surface, row, col,
        cell_branch, explored, frontier,
        path_set, found, done,
    ):
        node = self.grid.get_node(row, col)
        pos  = (row, col)
        ct   = node.cell_type

        # Ô đặc biệt: Start, Goal, Wall — không đổi màu
        if ct in ('P', 'G', 'W'):
            color = CELL_COLORS[ct]
            self._blit_cell(surface, row, col, color, ct)
            return

        if done and found:
            # ── Kết quả cuối ──
            # Đường đúng: ĐỎ ĐẬM | Nhánh sai: ĐỎ NHẠT | Chưa xét: màu gốc
            if pos in path_set:
                color = PATH_COLOR
            elif pos in explored or pos in frontier:
                color = PATH_WRONG_COLOR
            else:
                color = CELL_COLORS.get(ct, (240, 240, 240))

        elif pos in frontier:
            # ── Đang chạy: frontier màu vàng ──
            color = FRONTIER_COLOR

        elif pos in explored:
            # ── Đang chạy: explored màu xanh nhạt ──
            color = EXPLORED_COLOR

        else:
            color = CELL_COLORS.get(ct, (240, 240, 240))

        self._blit_cell(surface, row, col, color, ct)

    def _draw_path_line(self, surface, path):
        """Vẽ đường line đỏ đậm nối các ô trong path."""
        pts = []
        for (r, c) in path:
            x = self.offset_x + c * (CELL_SIZE + MARGIN) + CELL_SIZE // 2
            y = self.offset_y + r * (CELL_SIZE + MARGIN) + CELL_SIZE // 2
            pts.append((x, y))
        if len(pts) >= 2:
            pygame.draw.lines(surface, (180, 0, 0), False, pts, 3)

    # ── Helper chung ──────────────────────────────────────────────────────

    def _blit_cell(self, surface, row, col, color, cell_type):
        x    = self.offset_x + col * (CELL_SIZE + MARGIN)
        y    = self.offset_y + row * (CELL_SIZE + MARGIN)
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, GRID_LINE, rect, 1)

        if cell_type in ('P', 'G', 'T', 'O'):
            text_surf = self.font_cell.render(cell_type, True, TEXT_DARK)
            surface.blit(text_surf, text_surf.get_rect(center=rect.center))

    def pixel_to_cell(self, px, py):
        col = (px - self.offset_x) // (CELL_SIZE + MARGIN)
        row = (py - self.offset_y) // (CELL_SIZE + MARGIN)
        if self.grid.in_bounds(row, col):
            return (row, col)
        return None

    @property
    def grid_pixel_width(self):
        return self.grid.cols * (CELL_SIZE + MARGIN)

    @property
    def grid_pixel_height(self):
        return self.grid.rows * (CELL_SIZE + MARGIN)


# ── Tiện ích màu ──────────────────────────────────────────────────────────

def _lighten(color: Tuple[int,int,int], factor: float) -> Tuple[int,int,int]:
    return tuple(min(255, int(c * factor)) for c in color)

def _darken(color: Tuple[int,int,int], factor: float) -> Tuple[int,int,int]:
    return tuple(max(0, int(c * factor)) for c in color)
