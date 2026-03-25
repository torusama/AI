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
from Algorithm.bfs import bfs
from Algorithm.dfs import dfs

# ── Cấu hình cửa sổ ───────────────────────────────────────────────────────
MAP_FILE   = 'maps/easy.txt'
PANEL_W    = 200
FPS        = 60

# Danh sách thuật toán — thêm vào đây nếu có thuật toán mới
ALGORITHMS = {
    'BFS': bfs,
    'DFS': dfs,
}
ALGO_KEYS   = list(ALGORITHMS.keys())  # ['BFS', 'DFS', ...]
current_algo_idx = 0                   # index thuật toán đang chọn


def main():
    global current_algo_idx

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

    # Trạng thái hiển thị
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

            # Nút Run — chạy thuật toán đang chọn
            if panel.btn_run.is_clicked(event):
                algo_name = ALGO_KEYS[current_algo_idx]
                algo_fn   = ALGORITHMS[algo_name]

                result   = algo_fn(grid)
                path     = result['path']
                explored = result['explored']
                frontier = set()

                if path:
                    panel.update_stats(
                        algorithm = algo_name,
                        cost      = result['cost'],
                        length    = len(path),
                        nodes     = len(explored),
                        time_ms   = result['time_ms'],
                    )
                    print(f'[{algo_name}] Path found: {len(path)} steps, '
                          f'{len(explored)} nodes explored, '
                          f'{result["time_ms"]:.2f} ms')
                else:
                    panel.update_stats(algo_name, 'N/A', 0, len(explored), result['time_ms'])
                    print(f'[{algo_name}] No path found.')

            # Nút chọn thuật toán (click vào tên algo trên panel — dùng phím Tab hoặc click)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    current_algo_idx = (current_algo_idx + 1) % len(ALGO_KEYS)
                    print(f'Algorithm switched to: {ALGO_KEYS[current_algo_idx]}')

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

        # Hiện tên thuật toán đang chọn lên panel
        font = pygame.font.SysFont('Arial', 13)
        algo_label = font.render(f'Algo: {ALGO_KEYS[current_algo_idx]}  (Tab)', True, (200, 200, 200))
        screen.blit(algo_label, (grid_pixel_w + 10, win_h - 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()