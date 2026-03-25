"""
main.py
Entry point — khởi chạy Pacman AI Pathfinding GUI.
Chạy: python main.py
"""

import pygame
import sys
import os
from core.grid import Grid
from gui.renderer import Renderer, CELL_SIZE, MARGIN
from gui.panel import Panel
from gui.colors import BACKGROUND

# Thư mục gốc project (nơi chứa main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def map_path(filename: str) -> str:
    """Chuyển đường dẫn map thành tuyệt đối."""
    return os.path.join(BASE_DIR, filename)

PANEL_W = 220
FPS     = 60


def build_window(grid: Grid):
    """Tính kích thước cửa sổ theo grid hiện tại."""
    grid_pixel_w = grid.cols * (CELL_SIZE + MARGIN)
    grid_pixel_h = grid.rows * (CELL_SIZE + MARGIN)
    win_w = grid_pixel_w + PANEL_W
    win_h = max(grid_pixel_h, 680)
    return win_w, win_h, grid_pixel_w, grid_pixel_h


def main():
    pygame.init()

    # Load map mặc định
    grid = Grid.from_file(map_path('maps/Open.txt'))
    win_w, win_h, grid_pixel_w, grid_pixel_h = build_window(grid)

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Pacman AI Pathfinding')
    clock = pygame.time.Clock()

    renderer = Renderer(grid, offset_x=0, offset_y=0)
    panel    = Panel(x=grid_pixel_w, y=0, width=PANEL_W, height=win_h,
                     base_dir=BASE_DIR)

    explored = set()
    frontier = set()
    path     = []

    # ── Main loop ─────────────────────────────────────────────────────────
    running = True
    while running:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Chọn map — reload grid + renderer khi đổi map
            if panel.handle_map_click(event):
                grid = Grid.from_file(panel.selected_map_path)
                win_w, win_h, grid_pixel_w, grid_pixel_h = build_window(grid)
                screen = pygame.display.set_mode((win_w, win_h))
                renderer = Renderer(grid, offset_x=0, offset_y=0)
                panel.x = grid_pixel_w
                panel.btn_run.rect.x   = grid_pixel_w + 10
                panel.btn_reset.rect.x = grid_pixel_w + 10
                for mb in panel.map_buttons:
                    mb['rect'].x = grid_pixel_w + 10
                explored = set()
                frontier = set()
                path     = []
                print(f'[Map] Đã load: {panel.selected_map_path}')

            # Nút Run
            if panel.btn_run.is_clicked(event):
                print('[Run] Chưa gắn thuật toán — sẽ implement sau!')

            # Nút Reset
            if panel.btn_reset.is_clicked(event):
                explored = set()
                frontier = set()
                path     = []
                panel.reset_stats()
                print('[Reset] Đã xóa kết quả.')

        panel.handle_hover(mouse_pos)

        screen.fill(BACKGROUND)
        renderer.draw(screen, explored=explored, frontier=frontier, path=path)
        panel.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()