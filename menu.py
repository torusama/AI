"""
menu.py
All screens unified — share the same pygame window and clock for smooth transitions.

Screen 1: Main Menu
Screen 2: Choose Map
Screen 3: Game (pathfinding)

Flow:
    run_app(base_dir)  ← called by main.py, never returns until user exits
"""

import os
import sys
import pygame

from core.grid import Grid
from Algorithm.bfs import bfs_steps
from Algorithm.dfs import dfs_steps
from Algorithm.UCS import ucs_steps
from Algorithm.ASTAR import astar_steps
from Algorithm.bidirectional import bidirectional_steps
from Algorithm.idastar import ida_star_steps
from gui.renderer import Renderer, CELL_SIZE, MARGIN
from gui.panel import Panel
from gui.colors import BACKGROUND

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_W = 1280
TARGET_H = 720
PANEL_W  = 576
FPS      = 60

MAP_LIST = [
    ("Open Map",        "maps/Open.txt"),
    ("Cost Trap Map",   "maps/Cost_trap.txt"),
    ("Dead End Map",    "maps/Dead_end.txt"),
    ("Dead End Maze",   "maps/Map4_Dead_End_Maze.txt"),
    ("Symmetric Map",   "maps/Map5_Symmetric.txt"),
    ("Realistic Map",   "maps/Map6_Realistic_Mixed.txt"),
]

MAP_THUMBS = [
    "open_map.png",
    "costtrap_map.png",
    "deadend_map.png",
    "deadend_maze_map.png",
    "symmetric_map.png",
    "realistic_map.png",
]

ALGORITHMS = {
    'BFS':                  bfs_steps,
    'DFS':                  dfs_steps,
    'UCS':                  ucs_steps,
    'A*':                   astar_steps,
    'Bidirectional Search': bidirectional_steps,
    'IDA*':                 ida_star_steps,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_img(path: str, size=None) -> pygame.Surface:
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    surf = pygame.Surface(size or (100, 100), pygame.SRCALPHA)
    surf.fill((80, 80, 80))
    return surf


def fade(screen: pygame.Surface, clock: pygame.time.Clock,
         fade_out=True, duration_ms=280):
    """Fade to/from black. Uses the current screen content as base."""
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    steps   = 18
    delay   = duration_ms // steps
    snap    = screen.copy()
    for i in range(steps + 1):
        t     = i / steps
        alpha = int(255 * t) if fade_out else int(255 * (1 - t))
        screen.blit(snap, (0, 0))
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def infer_direction(path):
    if not path or len(path) < 2:
        return 'x'
    dx = dy = 0
    for i in range(len(path) - 1):
        dy += abs(path[i+1][0] - path[i][0])
        dx += abs(path[i+1][1] - path[i][1])
    return 'y' if dy > dx else 'x'


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 1 — MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

def screen_main_menu(screen: pygame.Surface, clock: pygame.time.Clock,
                     base_dir: str) -> str:
    """Returns: 'start' | 'exit'"""
    W, H = screen.get_size()
    pic  = lambda name: os.path.join(base_dir, "picture", name)

    bg        = load_img(pic("mani_backgr.png"), (W, H))
    img_start = load_img(pic("start_button.png"))
    img_exit  = load_img(pic("exit_button.png"))

    btn_w   = int(W * 0.20)
    btn_h_s = int(img_start.get_height() * btn_w / img_start.get_width())
    btn_h_e = int(img_exit.get_height()  * btn_w / img_exit.get_width())
    img_start = pygame.transform.smoothscale(img_start, (btn_w, btn_h_s))
    img_exit  = pygame.transform.smoothscale(img_exit,  (btn_w, btn_h_e))

    rect_start = img_start.get_rect(center=(W // 2, int(H * 0.57)))
    rect_exit  = img_exit.get_rect(center=(W // 2,  int(H * 0.72)))

    # Draw once before fade-in
    screen.blit(bg, (0, 0))
    screen.blit(img_start, rect_start)
    screen.blit(img_exit,  rect_exit)
    fade(screen, clock, fade_out=False)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'exit'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if rect_start.collidepoint(event.pos):
                    screen.blit(bg, (0, 0))
                    screen.blit(img_start, rect_start)
                    screen.blit(img_exit,  rect_exit)
                    fade(screen, clock, fade_out=True)
                    return 'start'
                if rect_exit.collidepoint(event.pos):
                    screen.blit(bg, (0, 0))
                    fade(screen, clock, fade_out=True)
                    return 'exit'

        screen.blit(bg, (0, 0))
        screen.blit(img_start, rect_start)
        screen.blit(img_exit,  rect_exit)
        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 2 — CHOOSE MAP
# ══════════════════════════════════════════════════════════════════════════════

def screen_choose_map(screen: pygame.Surface, clock: pygame.time.Clock,
                      base_dir: str) -> str | None:
    """Returns: map filepath | 'back' | None (quit)"""
    W, H = screen.get_size()
    pic  = lambda name: os.path.join(base_dir, "picture", name)

    bg       = load_img(pic("choose_map.png"), (W, H))
    img_back = load_img(pic("back_button.png"))

    back_w   = int(W * 0.07)
    back_h   = int(img_back.get_height() * back_w / img_back.get_width())
    img_back = pygame.transform.smoothscale(img_back, (back_w, back_h))
    rect_back = img_back.get_rect(topleft=(int(W * 0.025), int(H * 0.035)))

    grid_w  = int(W * 0.72)
    grid_x  = (W - grid_w) // 2
    grid_y  = int(H * 0.14)
    grid_h  = H - grid_y - int(H * 0.06)
    cols, rows = 3, 2
    gap_x   = int(W * 0.015)
    gap_y   = int(H * 0.025)
    card_w  = (grid_w - gap_x * (cols - 1)) // cols
    card_h  = (grid_h - gap_y * (rows - 1)) // rows

    thumbs = [load_img(pic(t), (card_w, card_h)) for t in MAP_THUMBS]
    card_rects = []
    for i in range(6):
        r, c = divmod(i, cols)
        card_rects.append(pygame.Rect(
            grid_x + c * (card_w + gap_x),
            grid_y + r * (card_h + gap_y),
            card_w, card_h
        ))

    # Draw once before fade-in
    screen.blit(bg, (0, 0))
    fade(screen, clock, fade_out=False)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if rect_back.collidepoint(event.pos):
                    screen.blit(bg, (0, 0))
                    fade(screen, clock, fade_out=True)
                    return 'back'
                for i, r in enumerate(card_rects):
                    if r.collidepoint(event.pos):
                        screen.blit(bg, (0, 0))
                        fade(screen, clock, fade_out=True)
                        return os.path.join(base_dir, MAP_LIST[i][1])

        screen.blit(bg, (0, 0))
        screen.blit(img_back, rect_back)

        for rect, thumb in zip(card_rects, thumbs):
            screen.blit(thumb, rect)

        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 3 — GAME
# ══════════════════════════════════════════════════════════════════════════════

def screen_game(screen: pygame.Surface, clock: pygame.time.Clock,
                base_dir: str, map_path: str) -> str:
    """
    Runs the pathfinding game.
    Returns: 'choose_map' | 'exit'
    """
    grid               = Grid.from_file(map_path)
    gw                 = grid.cols * (CELL_SIZE + MARGIN)
    gh                 = grid.rows * (CELL_SIZE + MARGIN)
    win_w              = gw + PANEL_W
    win_h              = max(gh, TARGET_H)

    screen = pygame.display.set_mode((win_w, win_h))
    pygame.display.set_caption('Shipper AI – Pathfinding')

    renderer = Renderer(grid, offset_x=0, offset_y=0, base_dir=base_dir)
    panel    = Panel(x=gw, y=0, width=PANEL_W, height=win_h, base_dir=base_dir)

    # Draw first frame before fade-in
    screen.fill(BACKGROUND)
    renderer.draw(screen)
    panel.draw(screen)
    fade(screen, clock, fade_out=False)

    # ── Game state ────────────────────────────────────────────────────────
    stepper      = None
    current_step = None
    animating    = False
    paused       = False
    last_step_ms = 0
    phase        = 'idle'
    saved_path   = []
    walk_timer   = 0

    def reset():
        nonlocal stepper, current_step, animating, paused, last_step_ms
        nonlocal phase, saved_path, walk_timer
        stepper = current_step = None
        animating = paused = False
        last_step_ms = walk_timer = 0
        phase      = 'idle'
        saved_path = []
        renderer.reset_state()
        panel.reset_stats()

    def start_search():
        nonlocal stepper, current_step, animating, paused, last_step_ms, phase
        algo_name    = panel.selected_algo
        algo_fn      = ALGORITHMS[algo_name]
        stepper      = algo_fn(grid, panel.selected_heuristic) \
                       if algo_name in ('A*', 'IDA*') else algo_fn(grid)
        current_step = next(stepper, None)
        animating    = True
        paused       = False
        last_step_ms = pygame.time.get_ticks()
        phase        = 'searching'

    # ── Game loop ─────────────────────────────────────────────────────────
    while True:
        now       = pygame.time.get_ticks()
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'exit'

            if panel.handle_keydown(event):
                reset()
            if panel.handle_heuristic_click(event):
                reset()
            panel.handle_speed_click(event)

            # ── Back → Choose Map (with fade) ─────────────────────────────
            if panel.is_back_map_clicked(event):
                reset()
                screen.fill(BACKGROUND)
                renderer.draw(screen)
                panel.draw(screen)
                fade(screen, clock, fade_out=True)
                # Resize back to menu resolution
                screen = pygame.display.set_mode((TARGET_W, TARGET_H))
                pygame.display.set_caption('Shipper AI – Menu')
                return 'choose_map'

            if panel.btn_run.is_clicked(event):
                if phase == 'idle':
                    start_search()
                elif paused:
                    paused    = False
                    animating = True

            if panel.btn_pause.is_clicked(event):
                if animating:
                    paused    = True
                    animating = False

            if panel.btn_reset.is_clicked(event):
                reset()

        # ── Search tick ───────────────────────────────────────────────────
        if phase == 'searching' and animating and not paused and stepper is not None:
            if now - last_step_ms >= panel.step_delay_ms:
                last_step_ms = now
                nxt = next(stepper, None)
                if nxt is not None:
                    current_step = nxt
                    explored  = current_step.get('explored', set())
                    frontier  = current_step.get('frontier', set())
                    direction = infer_direction(current_step.get('path', []))
                    renderer.set_phase_searching(explored, frontier, direction)

                    if current_step.get('done'):
                        animating  = False
                        found      = current_step.get('found', False)
                        saved_path = current_step.get('path', [])
                        panel.update_stats(
                            algorithm = panel.selected_algo,
                            cost      = current_step.get('cost', 0),
                            length    = len(saved_path),
                            nodes     = len(current_step.get('explored', set())),
                            time_ms   = current_step.get('time_ms', 0),
                        )
                        if found and saved_path:
                            phase      = 'walking'
                            animating  = True
                            walk_timer = now
                            renderer.set_phase_walking(saved_path)
                        else:
                            phase = 'idle'
                else:
                    animating = False

        # ── Walk tick ─────────────────────────────────────────────────────
        if phase == 'walking' and animating and not paused:
            if now - walk_timer >= panel.step_delay_ms * 3:
                walk_timer    = now
                still_walking = renderer.advance_shipper()
                if not still_walking:
                    animating = False
                    phase     = 'done'

        panel.handle_hover(mouse_pos)

        screen.fill(BACKGROUND)
        renderer.draw(screen)
        panel.draw(screen, animating=animating, paused=paused)
        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def run_app(base_dir: str):
    """Main app loop — all screens share one window and clock."""
    pygame.init()
    screen = pygame.display.set_mode((TARGET_W, TARGET_H))
    pygame.display.set_caption('Shipper AI')
    clock  = pygame.time.Clock()

    current_screen = 'main_menu'

    while True:
        if current_screen == 'main_menu':
            result = screen_main_menu(screen, clock, base_dir)
            if result == 'exit':
                break
            current_screen = 'choose_map'

        elif current_screen == 'choose_map':
            result = screen_choose_map(screen, clock, base_dir)
            if result is None:
                break
            if result == 'back':
                current_screen = 'main_menu'
            else:
                map_path = result
                current_screen = 'game'

        elif current_screen == 'game':
            result = screen_game(screen, clock, base_dir, map_path)
            if result == 'exit':
                break
            if result == 'choose_map':
                current_screen = 'choose_map'

    pygame.quit()
    sys.exit()


# Keep run_menu for backward compatibility (not used anymore)
def run_menu(base_dir: str):
    run_app(base_dir)