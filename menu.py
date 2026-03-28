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
try:
    import cv2
    import numpy as np
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

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

ALGO_ORDER = list(ALGORITHMS.keys())


def _empty_algo_result(algo_name: str) -> dict:
    return {
        'algorithm': algo_name,
        'cost': '_',
        'path_length': '_',
        'nodes_found': '_',
        'speed': '_',
        'time': '_',
    }


def _empty_map_results() -> dict:
    return {algo: _empty_algo_result(algo) for algo in ALGO_ORDER}


def _get_map_results(map_results: dict, map_path: str) -> dict:
    merged = _empty_map_results()
    existing = map_results.get(map_path, {})
    for algo, row in existing.items():
        if algo in merged:
            merged[algo].update(row)
    return merged


def _update_map_results(map_results: dict, map_path: str, algorithm: str,
                        cost, path_length: int, nodes_found: int, time_ms: float,
                        selected_speed: str):
    if map_path not in map_results:
        map_results[map_path] = _empty_map_results()

    time_ms = max(0.0, float(time_ms or 0.0))
    nodes_found = int(nodes_found or 0)
    speed = str(selected_speed) if selected_speed else '_'

    map_results[map_path][algorithm] = {
        'algorithm': algorithm,
        'cost': str(cost),
        'path_length': str(path_length),
        'nodes_found': str(nodes_found),
        'speed': speed,
        'time': f'{time_ms:.1f} ms',
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


class VideoPlayer:
    """
    Stream video frame-by-frame — không preload, không lag lúc khởi động.
    Tự động sync theo FPS gốc của video và loop lại khi hết.
    """
    def __init__(self, path: str, size):
        self._path    = path
        self._size    = size
        self._cap     = None
        self._fps     = 30.0
        self._ms_per_frame = 1000 / 30.0
        self._last_ms = 0
        self._current = None
        self.available = False

        if _CV2_AVAILABLE and os.path.exists(path):
            self._cap = cv2.VideoCapture(path)
            self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
            self._ms_per_frame = 1000.0 / self._fps
            self.available = True
            self._read_next()   # load frame đầu tiên ngay

    def _read_next(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret:                          # hết video -> loop
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self._cap.read()
        if ret:
            W, H = self._size
            frame = cv2.resize(frame, (W, H))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self._current = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def get_frame(self):
        """Gọi mỗi game loop — trả về frame hiện tại, tự advance khi đủ thời gian."""
        now = pygame.time.get_ticks()
        if now - self._last_ms >= self._ms_per_frame:
            self._last_ms = now
            self._read_next()
        return self._current

    def release(self):
        if self._cap:
            self._cap.release()
            self._cap = None


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

    btn_w   = int(W * 0.36)
    btn_h_s = int(img_start.get_height() * btn_w / img_start.get_width())
    btn_h_e = int(img_exit.get_height()  * btn_w / img_exit.get_width())
    img_start = pygame.transform.smoothscale(img_start, (btn_w, btn_h_s))
    img_exit  = pygame.transform.smoothscale(img_exit,  (btn_w, btn_h_e))

    rect_start = img_start.get_rect(center=(int(W * 0.626), int(H * 0.57)))
    rect_exit  = img_exit.get_rect(center=(int(W * 0.648),  int(H * 0.72)))

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
                      base_dir: str, map_results: dict) -> str | None:
    """Returns: map filepath | 'back' | None (quit)"""
    W, H = screen.get_size()
    pic  = lambda name: os.path.join(base_dir, "picture", name)

    # Try video first, fallback to static image
    video_path = pic("choose_map.mp4")
    video      = VideoPlayer(video_path, (W, H))
    bg         = load_img(pic("choose_map.png"), (W, H)) if not video.available else None

    img_back = load_img(pic("back_button.png"))

    back_w   = int(W * 0.42)
    back_h   = int(img_back.get_height() * back_w / img_back.get_width())
    img_back = pygame.transform.smoothscale(img_back, (back_w, back_h))
    rect_back = img_back.get_rect()

    rect_back.x = -rect_back.width * 0.215
    rect_back.y = H - rect_back.height * 0.71

    grid_w  = int(W * 0.565)
    grid_x  = (W - grid_w) // 2
    grid_y  = int(H * 0.24)
    grid_h  = H - grid_y - int(H * 0.24)
    cols, rows = 3, 2
    gap_x   = int(W * 0.09)
    gap_y   = int(H * 0.01)
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

    # Stats table controls
    font_btn = pygame.font.SysFont('Arial Black', 24, bold=True)
    font_title = pygame.font.SysFont('Arial Black', 28, bold=True)
    font_header = pygame.font.SysFont('Arial Black', 16, bold=True)
    font_header_algo = pygame.font.SysFont('Arial Black', 12, bold=True)
    font_body = pygame.font.SysFont('Verdana', 16, bold=True)
    font_hint = pygame.font.SysFont('Verdana', 15, bold=True)

    rect_stats = pygame.Rect(W - 212, H - 70, 180, 44)
    show_stats = False
    stats_map_idx = 0

    rect_prev = pygame.Rect(0, 0, 0, 0)
    rect_next = pygame.Rect(0, 0, 0, 0)
    rect_close = pygame.Rect(0, 0, 0, 0)
    rect_popup = pygame.Rect(0, 0, 0, 0)

    def draw_bg():
        if video.available:
            frame = video.get_frame()
            if frame:
                screen.blit(frame, (0, 0))
        else:
            screen.blit(bg, (0, 0))

    def draw_btn(rect, label, hovered, base_color=(0, 125, 205)):
        color = tuple(max(0, c - 25) for c in base_color) if hovered else base_color
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2)
        txt = font_btn.render(label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_stats_overlay():
        nonlocal rect_prev, rect_next, rect_close, rect_popup

        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 20, 50, 165))
        screen.blit(overlay, (0, 0))

        box_w, box_h = int(W * 0.88), int(H * 0.62)
        box_x, box_y = (W - box_w) // 2, (H - box_h) // 2
        box = pygame.Rect(box_x, box_y, box_w, box_h)
        rect_popup = box

        pygame.draw.rect(screen, (0, 116, 188), box)
        pygame.draw.rect(screen, (255, 255, 255), box, 3)

        map_name, rel_map = MAP_LIST[stats_map_idx]
        abs_map = os.path.join(base_dir, rel_map)
        rows_by_algo = _get_map_results(map_results, abs_map)

        title = font_title.render(f'STATS - {map_name}', True, (255, 255, 255))
        screen.blit(title, (box_x + 24, box_y + 16))

        hint = font_hint.render('Use < and > to switch map table', True, (215, 240, 255))
        screen.blit(hint, (box_x + 24, box_y + 52))

        rect_close = pygame.Rect(box.right - 44, box.y + 10, 30, 30)
        pygame.draw.rect(screen, (0, 88, 150), rect_close)
        pygame.draw.rect(screen, (255, 255, 255), rect_close, 2)
        close_txt = font_header.render('X', True, (255, 255, 255))
        screen.blit(close_txt, close_txt.get_rect(center=rect_close.center))

        table_x = box_x + 20
        table_y = box_y + 82
        table_w = box_w - 40
        row_h = 34

        metrics = [
            ('cost', 'Cost'),
            ('path_length', 'Path Length'),
            ('nodes_found', 'Nodes Found'),
            ('speed', 'Speed'),
            ('time', 'Time'),
        ]

        metric_col_w = 170
        algo_col_w = (table_w - metric_col_w) // len(ALGO_ORDER)
        col_edges = [table_x, table_x + metric_col_w]
        for _ in range(len(ALGO_ORDER) - 1):
            col_edges.append(col_edges[-1] + algo_col_w)
        col_edges.append(table_x + table_w)

        # Header row: first column is metric label, other columns are algorithm names
        header_rect = pygame.Rect(table_x, table_y, table_w, row_h)
        pygame.draw.rect(screen, (0, 95, 160), header_rect)
        pygame.draw.rect(screen, (255, 255, 255), header_rect, 1)

        txt_metric = font_header.render('Metric', True, (230, 247, 255))
        screen.blit(txt_metric, (col_edges[0] + 8, table_y + (row_h - txt_metric.get_height()) // 2))

        for idx, algo_name in enumerate(ALGO_ORDER):
            x1 = col_edges[idx + 1]
            x2 = col_edges[idx + 2]
            txt = font_header_algo.render(algo_name, True, (230, 247, 255))
            screen.blit(txt, txt.get_rect(center=((x1 + x2) // 2, table_y + row_h // 2)))

        # Body: each row is one metric, each column is one algorithm
        y = table_y + row_h
        for row_idx, (metric_key, metric_label) in enumerate(metrics):
            row_rect = pygame.Rect(table_x, y, table_w, row_h)
            pygame.draw.rect(screen, (0, 126, 198) if row_idx % 2 == 0 else (0, 118, 190), row_rect)
            pygame.draw.rect(screen, (255, 255, 255), row_rect, 1)

            txt_row = font_header.render(metric_label, True, (240, 252, 255))
            screen.blit(txt_row, (col_edges[0] + 8, y + (row_h - txt_row.get_height()) // 2))

            for col_idx, algo_name in enumerate(ALGO_ORDER):
                x1 = col_edges[col_idx + 1]
                x2 = col_edges[col_idx + 2]
                val = str(rows_by_algo.get(algo_name, _empty_algo_result(algo_name)).get(metric_key, '_'))
                txt_val = font_body.render(val, True, (255, 255, 255))
                screen.blit(txt_val, txt_val.get_rect(center=((x1 + x2) // 2, y + row_h // 2)))

            y += row_h

        rect_prev = pygame.Rect(box_x + 20, box.bottom - 46, 50, 30)
        rect_next = pygame.Rect(box.right - 70, box.bottom - 46, 50, 30)
        draw_btn(rect_prev, '<', rect_prev.collidepoint(pygame.mouse.get_pos()), (0, 95, 160))
        draw_btn(rect_next, '>', rect_next.collidepoint(pygame.mouse.get_pos()), (0, 95, 160))

    def draw_scene():
        """Draw background → thumbnails → buttons → optional stats overlay."""
        draw_bg()
        for rect, thumb in zip(card_rects, thumbs):
            screen.blit(thumb, rect)
        draw_btn(rect_stats, 'STATS', rect_stats.collidepoint(pygame.mouse.get_pos()))
        screen.blit(img_back, rect_back)
        if show_stats:
            draw_stats_overlay()

    # Draw once before fade-in
    draw_scene()
    fade(screen, clock, fade_out=False)

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                video.release()
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if show_stats:
                    if rect_close.collidepoint(event.pos):
                        show_stats = False
                        continue
                    if rect_prev.collidepoint(event.pos):
                        stats_map_idx = (stats_map_idx - 1) % len(MAP_LIST)
                        continue
                    if rect_next.collidepoint(event.pos):
                        stats_map_idx = (stats_map_idx + 1) % len(MAP_LIST)
                        continue
                    if not rect_popup.collidepoint(event.pos):
                        show_stats = False
                    continue

                # Back button luôn hoạt động
                if rect_back.collidepoint(event.pos):
                    draw_scene()
                    fade(screen, clock, fade_out=True)
                    video.release()
                    return 'back'

                if rect_stats.collidepoint(event.pos):
                    show_stats = not show_stats
                    continue

                map_clicked = None
                for i, r in enumerate(card_rects):
                    if r.collidepoint(event.pos):
                        map_clicked = i
                        break

                if map_clicked is not None:
                    draw_scene()
                    fade(screen, clock, fade_out=True)
                    video.release()
                    return os.path.join(base_dir, MAP_LIST[map_clicked][1])

        draw_scene()
        pygame.display.flip()


# ══════════════════════════════════════════════════════════════════════════════
#  SCREEN 3 — GAME
# ══════════════════════════════════════════════════════════════════════════════

def screen_game(screen: pygame.Surface, clock: pygame.time.Clock,
                base_dir: str, map_path: str, map_results: dict) -> str:
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
    run_speed_label = '_'

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
        nonlocal stepper, current_step, animating, paused, last_step_ms, phase, run_speed_label
        algo_name    = panel.selected_algo
        algo_fn      = ALGORITHMS[algo_name]
        stepper      = algo_fn(grid, panel.selected_heuristic) \
                       if algo_name in ('A*', 'IDA*') else algo_fn(grid)
        current_step = next(stepper, None)
        run_speed_label = panel.selected_speed_label
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
                        _update_map_results(
                            map_results=map_results,
                            map_path=map_path,
                            algorithm=panel.selected_algo,
                            cost=current_step.get('cost', 0),
                            path_length=len(saved_path),
                            nodes_found=len(current_step.get('explored', set())),
                            time_ms=current_step.get('time_ms', 0),
                            selected_speed=run_speed_label,
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
    map_results = {}

    current_screen = 'main_menu'

    while True:
        if current_screen == 'main_menu':
            result = screen_main_menu(screen, clock, base_dir)
            if result == 'exit':
                break
            current_screen = 'choose_map'

        elif current_screen == 'choose_map':
            result = screen_choose_map(screen, clock, base_dir, map_results)
            if result is None:
                break
            if result == 'back':
                current_screen = 'main_menu'
            else:
                map_path = result
                current_screen = 'game'

        elif current_screen == 'game':
            result = screen_game(screen, clock, base_dir, map_path, map_results)
            if result == 'exit':
                break
            if result == 'choose_map':
                current_screen = 'choose_map'

    pygame.quit()
    sys.exit()


# Keep run_menu for backward compatibility (not used anymore)
def run_menu(base_dir: str):
    run_app(base_dir)