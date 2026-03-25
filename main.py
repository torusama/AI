"""
main.py
Entry point — Pacman AI Pathfinding GUI với animation từng bước.

Điều khiển:
  Run        → bắt đầu animation (nếu chưa chạy) / resume nếu đang pause
  Pause      → tạm dừng giữa chừng
  Reset      → xóa kết quả, về trạng thái ban đầu
  Speed      → đổi tốc độ: Chậm / Bình thường / Nhanh / Rất nhanh
  Tab        → đổi thuật toán (BFS ↔ DFS)
"""

import pygame
import sys
import os
from core.grid import Grid
from Algorithm.bfs import bfs_steps
from Algorithm.dfs import dfs_steps
from gui.renderer import Renderer, CELL_SIZE, MARGIN
from gui.panel import Panel
from gui.colors import BACKGROUND

# ── Cấu hình ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def map_path(filename: str) -> str:
    return os.path.join(BASE_DIR, filename)

MAP_FILE = map_path('maps/Open.txt')
PANEL_W  = 220
FPS      = 60

ALGORITHMS = {
    'BFS': bfs_steps,
    'DFS': dfs_steps,
}
ALGO_KEYS = list(ALGORITHMS.keys())


def build_window(grid: Grid):
    grid_pixel_w = grid.cols * (CELL_SIZE + MARGIN)
    grid_pixel_h = grid.rows * (CELL_SIZE + MARGIN)
    win_w = grid_pixel_w + PANEL_W
    win_h = max(grid_pixel_h, 680)
    return win_w, win_h, grid_pixel_w, grid_pixel_h


def main():
    pygame.init()

    grid = Grid.from_file(MAP_FILE)
    win_w, win_h, grid_pixel_w, grid_pixel_h = build_window(grid)

    screen = pygame.display.set_mode((win_w, win_h))
    clock  = pygame.time.Clock()

    renderer = Renderer(grid, offset_x=0, offset_y=0)
    panel    = Panel(x=grid_pixel_w, y=0, width=PANEL_W, height=win_h,
                     base_dir=BASE_DIR)

    algo_idx     = 0
    stepper      = None
    current_step = None
    animating    = False
    paused       = False
    last_step_ms = 0
    font_algo    = pygame.font.SysFont('Arial', 13)

    def reset():
        nonlocal stepper, current_step, animating, paused, last_step_ms
        stepper      = None
        current_step = None
        animating    = False
        paused       = False
        last_step_ms = 0
        panel.reset_stats()

    def start_animation():
        nonlocal stepper, current_step, animating, paused, last_step_ms
        algo_fn      = ALGORITHMS[ALGO_KEYS[algo_idx]]
        stepper      = algo_fn(grid)
        current_step = next(stepper, None)
        animating    = True
        paused       = False
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

            # ── Chọn map: reset toàn bộ trạng thái ──────────────────────
            if panel.handle_map_click(event):
                reset()                                          # ← FIX: xóa kết quả cũ
                grid = Grid.from_file(panel.selected_map_path)
                win_w, win_h, grid_pixel_w, grid_pixel_h = build_window(grid)
                screen = pygame.display.set_mode((win_w, win_h))
                renderer = Renderer(grid, offset_x=0, offset_y=0)
                panel.reposition(grid_pixel_w)
                print(f'[Map] Đã load: {panel.selected_map_path}')

            # ── Nút Run: bắt đầu hoặc resume ─────────────────────────────
            if panel.btn_run.is_clicked(event):
                if stepper is None:
                    start_animation()
                elif paused:
                    paused = False          # resume từ chỗ dừng
                    animating = True

            # ── Nút Pause ─────────────────────────────────────────────────
            if panel.btn_pause.is_clicked(event):
                if animating and not paused:
                    paused    = True
                    animating = False

            # ── Nút Reset ─────────────────────────────────────────────────
            if panel.btn_reset.is_clicked(event):
                reset()

            # ── Nút Speed ─────────────────────────────────────────────────
            if panel.btn_speed.is_clicked(event):
                panel.cycle_speed()

            # ── Tab: đổi thuật toán ───────────────────────────────────────
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                algo_idx = (algo_idx + 1) % len(ALGO_KEYS)
                reset()
                update_caption()

        # ── Tiến bước animate ─────────────────────────────────────────────
        if animating and not paused and stepper is not None:
            if now - last_step_ms >= panel.step_delay_ms:
                last_step_ms = now
                nxt = next(stepper, None)
                if nxt is not None:
                    current_step = nxt
                    if current_step.get('done'):
                        animating = False
                        paused    = False
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

        panel.draw(screen, animating=animating, paused=paused)

        algo_label = font_algo.render(
            f'{ALGO_KEYS[algo_idx]}  [Tab]', True, (180, 180, 180)
        )
        screen.blit(algo_label, (grid_pixel_w + 10, win_h - 28))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()