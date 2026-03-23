"""
main.py
Entry point — khởi chạy Pacman AI Pathfinding GUI.
Chạy: python main.py
"""

import pygame
import sys
from core.grid import Grid
from gui.renderer import Renderer, CELL_SIZE, MARGIN
from gui.panel import Panel
from gui.colors import BACKGROUND

# ── Cấu hình cửa sổ ───────────────────────────────────────────────────────
MAP_FILE   = 'maps/easy.txt'
PANEL_W    = 200
FPS        = 60


def main():
    pygame.init()

    # Load map
    grid = Grid.from_file(MAP_FILE)

    # Tính kích thước cửa sổ theo map
    grid_pixel_w = grid.cols * (CELL_SIZE + MARGIN)
    grid_pixel_h = grid.rows * (CELL_SIZE + MARGIN)
    win_w = grid_pixel_w + PANEL_W
    win_h = max(grid_pixel_h, 600)

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Pacman AI Pathfinding')
    clock = pygame.time.Clock()

    # Khởi tạo Renderer và Panel
    renderer = Renderer(grid, offset_x=0, offset_y=0)
    panel    = Panel(x=grid_pixel_w, y=0, width=PANEL_W, height=win_h)

    # Trạng thái hiển thị (sẽ được cập nhật khi chạy thuật toán)
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

            # Nút Run — placeholder, sẽ gắn thuật toán sau
            if panel.btn_run.is_clicked(event):
                print('[Run] Chưa gắn thuật toán — sẽ implement sau!')
                # TODO: gọi thuật toán ở đây
                # result = run_algorithm(grid)
                # explored = result['explored']
                # frontier = result['frontier']
                # path     = result['path']
                # panel.update_stats(...)

            # Nút Reset
            if panel.btn_reset.is_clicked(event):
                explored = set()
                frontier = set()
                path     = []
                panel.reset_stats()
                print('[Reset] Đã xóa kết quả.')

        # Cập nhật hover
        panel.handle_hover(mouse_pos)

        # Vẽ
        screen.fill(BACKGROUND)
        renderer.draw(screen, explored=explored, frontier=frontier, path=path)
        panel.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()