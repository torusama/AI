"""
main.py
Entry point — Pacman AI Pathfinding GUI với animation từng bước.

Điều khiển:
  Run        → bắt đầu / pause animation
  Reset      → xóa kết quả, về trạng thái ban đầu
  Tab        → đổi thuật toán (BFS ↔ DFS)
  STEP_DELAY_MS → tốc độ animate (ms giữa 2 bước)
"""

import pygame
import sys
from core.grid import Grid
from Algorithm.bfs import bfs, bfs_steps
from Algorithm.dfs import dfs, dfs_steps
from gui.renderer import Renderer, CELL_SIZE, MARGIN
from gui.panel import Panel
from gui.colors import BACKGROUND

# ── Cấu hình ─────────────────────────────────────────────────────────────────
MAP_FILE      = 'maps/easy.txt'
PANEL_W       = 200
FPS           = 60
STEP_DELAY_MS = 30   # ms giữa 2 bước animate (nhỏ = nhanh hơn)

ALGORITHMS = {
    'BFS': bfs_steps,
    'DFS': dfs_steps,
}
ALGO_KEYS = list(ALGORITHMS.keys())


def main():
    pygame.init()

    grid = Grid.from_file(MAP_FILE)

    grid_pixel_w = grid.cols * (CELL_SIZE + MARGIN)
    grid_pixel_h = grid.rows * (CELL_SIZE + MARGIN)
    win_w = grid_pixel_w + PANEL_W
    win_h = max(grid_pixel_h, 600)

    screen = pygame.display.set_mode((win_w, win_h))
    clock  = pygame.time.Clock()

    renderer = Renderer(grid, offset_x=0, offset_y=0)
    panel    = Panel(x=grid_pixel_w, y=0, width=PANEL_W, height=win_h)

    algo_idx     = 0       # thuật toán đang chọn
    stepper      = None    # generator steps
    current_step = None    # step đang vẽ
    animating    = False
    last_step_ms = 0
    font_algo    = pygame.font.SysFont('Arial', 13)

    def reset():
        nonlocal stepper, current_step, animating, last_step_ms
        stepper      = None
        current_step = None
        animating    = False
        last_step_ms = 0
        panel.reset_stats()

    def start_animation():
        nonlocal stepper, current_step, animating, last_step_ms
        algo_fn      = ALGORITHMS[ALGO_KEYS[algo_idx]]
        stepper      = algo_fn(grid)
        current_step = next(stepper, None)
        animating    = True
        last_step_ms = pygame.time.get_ticks()

    def update_caption():
        pygame.display.set_caption(
            f'Pacman AI — {ALGO_KEYS[algo_idx]}  (Tab để đổi thuật toán)'
        )

    update_caption()

    running = True
    while running:
        now = pygame.time.get_ticks()
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if panel.btn_run.is_clicked(event):
                if stepper is None:
                    start_animation()
                else:
                    animating = not animating   # pause / resume

            if panel.btn_reset.is_clicked(event):
                reset()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                algo_idx = (algo_idx + 1) % len(ALGO_KEYS)   # đổi thuật toán
                reset()
                update_caption()

        # ── Tiến bước animate ─────────────────────────────────────────────
        if animating and stepper is not None:
            if now - last_step_ms >= STEP_DELAY_MS:
                last_step_ms = now
                nxt = next(stepper, None)
                if nxt is not None:
                    current_step = nxt
                    if current_step.get('done'):
                        animating = False
                        panel.update_stats(
                            algorithm = ALGO_KEYS[algo_idx],
                            cost      = current_step.get('cost', 0),
                            length    = len(current_step.get('path', [])),
                            nodes     = len(current_step.get('explored', set())),
                            time_ms   = current_step.get('time_ms', 0),
                        )
                else:
                    animating = False

        panel.handle_hover(mouse_pos)

        # ── Vẽ ───────────────────────────────────────────────────────────
        screen.fill(BACKGROUND)

        if current_step is not None:
            renderer.draw_step(screen, current_step)
        else:
            renderer.draw(screen)

        panel.draw(screen)

        # Tên thuật toán góc dưới panel
        algo_label = font_algo.render(
            f'{ALGO_KEYS[algo_idx]}  [Tab]', True, (180, 180, 180)
        )
        screen.blit(algo_label, (grid_pixel_w + 10, win_h - 28))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
