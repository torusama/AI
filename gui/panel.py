"""
panel.py
Right sidebar — redesigned for wide 16:9 layout (panel width ~576px):
  • Algorithm selection via ← → (keyboard arrows)
  • Heuristic shown only when algo is A* or IDA*
  • White background, bold fonts, easy to read
  • back_map.png button near bottom to return to Choose Map
"""

import os
import pygame

# ── Sidebar colors ─────────────────────────────────────────────────────────────
PANEL_BG      = (248, 248, 248)
TEXT_DARK     = (30,  30,  30)
TEXT_GRAY     = (100, 100, 100)
ACCENT        = (50,  120, 220)
ACCENT_LIGHT  = (210, 225, 255)

# Pastel colors
BTN_RUN_C     = (255, 220, 100)   # Yellow pastel
BTN_PAUSE_C   = (220, 150, 200)   # Pink-purple pastel
BTN_RESET_C   = (210, 50,  50)
BTN_SPEED_C   = (130, 200, 210)   # Teal-blue pastel (selected speed)
BTN_DISABLED  = (180, 180, 180)
DIVIDER       = (210, 210, 210)

SPEED_LEVELS = [
    ('Slow',       60),
    ('Normal',     30),
    ('Fast',       10),
    ('Very Fast',   2),
]

ALGO_KEYS = ['BFS', 'DFS', 'UCS', 'A*', 'Bidirectional Search', 'IDA*']
HEURISTIC_ALGOS = {'A*', 'IDA*'}


def _load_img(path: str, size: tuple) -> pygame.Surface:
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((180, 180, 180, 200))
    return surf


class FlatButton:
    """Flat button with rounded corners."""

    def __init__(self, rect: pygame.Rect, label: str, color,
                 text_color=(40, 40, 40), font_size=16):
        self.rect       = rect
        self.label      = label
        self.color      = color
        self.text_color = text_color
        self.hovered    = False
        self.font       = pygame.font.SysFont('Arial', font_size, bold=True)

    def draw(self, surface: pygame.Surface, disabled=False):
        c = BTN_DISABLED if disabled else (
            tuple(min(255, v + 20) for v in self.color) if self.hovered else self.color
        )
        pygame.draw.rect(surface, c, self.rect, border_radius=8)
        tc = (160, 160, 160) if disabled else self.text_color
        txt = self.font.render(self.label, True, tc)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


class Panel:

    def __init__(self, x: int, y: int, width: int, height: int, base_dir: str = ''):
        self.x        = x
        self.y        = y
        self.width    = width
        self.height   = height
        self.base_dir = base_dir

        pygame.font.init()
        self.font_h1    = pygame.font.SysFont('Arial', 20, bold=True)
        self.font_h2    = pygame.font.SysFont('Arial', 17, bold=True)
        self.font_body  = pygame.font.SysFont('Arial', 15, bold=True)
        self.font_val   = pygame.font.SysFont('Arial', 15)
        self.font_small = pygame.font.SysFont('Arial', 13)

        # ── State ─────────────────────────────────────────────────────────
        self.algo_idx               = 0
        self.heuristic_options      = ['manhattan', 'euclidean']
        self.selected_heuristic_idx = 0
        self.speed_idx              = 1

        self.stats = {
            'Algorithm':   '—',
            'Cost':        '—',
            'Path Length': '—',
            'Nodes Found': '—',
            'Time':        '—',
        }

        # ── Layout ──────────────────────────────────────────────────────────
        pad   = 24
        bw    = width - pad * 2
        bh    = 42

        cur_y = y + pad

        # Title "ALGORITHM"
        self._algo_title_y = cur_y
        cur_y += 30

        # Arrow + algo name row
        arrow_w = 40
        self._algo_name_rect = pygame.Rect(x + pad + arrow_w + 6, cur_y,
                                            bw - (arrow_w + 6) * 2, bh)
        self._rect_arrow_l   = pygame.Rect(x + pad, cur_y, arrow_w, bh)
        self._rect_arrow_r   = pygame.Rect(x + pad + bw - arrow_w, cur_y, arrow_w, bh)
        cur_y += bh + 10

        # Heuristic row
        self._heuristic_y = cur_y
        hw = bw // 2 - 6
        self._btn_manhattan = FlatButton(
            pygame.Rect(x + pad, cur_y, hw, 34),
            'Manhattan', ACCENT, font_size=14)
        self._btn_euclidean = FlatButton(
            pygame.Rect(x + pad + hw + 12, cur_y, hw, 34),
            'Euclidean', (100, 100, 200), font_size=14)
        cur_y += 44

        # Divider
        self._div1_y = cur_y
        cur_y += 14

        # Speed
        self._speed_title_y = cur_y
        cur_y += 26
        spd_w = (bw - 9) // 4
        self._speed_rects = [
            pygame.Rect(x + pad + i * (spd_w + 3), cur_y, spd_w, 34)
            for i in range(4)
        ]
        cur_y += 44

        # Divider
        self._div2_y = cur_y
        cur_y += 14

        # Run / Pause / Reset
        third = (bw - 12) // 3
        self.btn_run   = FlatButton(
            pygame.Rect(x + pad, cur_y, third, bh),
            '▶  Run', BTN_RUN_C, text_color=(60, 40, 0), font_size=15)
        self.btn_pause = FlatButton(
            pygame.Rect(x + pad + third + 6, cur_y, third, bh),
            '⏸ Pause', BTN_PAUSE_C, text_color=(60, 20, 60), font_size=15)
        self.btn_reset = FlatButton(
            pygame.Rect(x + pad + (third + 6) * 2, cur_y, third, bh),
            '↺  Reset', BTN_RESET_C, text_color=(255, 255, 255), font_size=15)
        cur_y += bh + 12

        # Divider
        self._div3_y = cur_y
        cur_y += 14

        # Stats section
        self._stats_y = cur_y
        self._stat_row_h = 26
        cur_y += len(self.stats) * self._stat_row_h + 6

        # Divider
        self._div4_y = cur_y
        cur_y += 14

        # Back map button
        bm_h = int(bw * 0.22)
        self._back_map_img = _load_img(
            os.path.join(base_dir, 'picture', 'back_map.png'),
            (int(bw * 0.55), bm_h)
        )
        self._back_map_rect = pygame.Rect(
            x + pad + (bw - int(bw * 0.55)) // 2,
            y + height - bm_h - 20,
            int(bw * 0.55), bm_h
        )

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def selected_algo(self) -> str:
        return ALGO_KEYS[self.algo_idx]

    @property
    def selected_heuristic(self) -> str:
        return self.heuristic_options[self.selected_heuristic_idx]

    @property
    def step_delay_ms(self) -> int:
        return SPEED_LEVELS[self.speed_idx][1]

    @property
    def needs_heuristic(self) -> bool:
        return self.selected_algo in HEURISTIC_ALGOS

    # ── Stats ─────────────────────────────────────────────────────────────

    def update_stats(self, algorithm, cost, length, nodes, time_ms):
        self.stats['Algorithm']   = str(algorithm)
        self.stats['Cost']        = str(cost)
        self.stats['Path Length'] = str(length)
        self.stats['Nodes Found'] = str(nodes)
        self.stats['Time']        = f'{time_ms:.1f} ms'

    def reset_stats(self):
        for k in self.stats:
            self.stats[k] = '—'

    # ── Events ────────────────────────────────────────────────────────────

    def handle_hover(self, mouse_pos):
        self.btn_run.update(mouse_pos)
        self.btn_pause.update(mouse_pos)
        self.btn_reset.update(mouse_pos)
        self._btn_manhattan.update(mouse_pos)
        self._btn_euclidean.update(mouse_pos)

    def handle_keydown(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.algo_idx = (self.algo_idx - 1) % len(ALGO_KEYS)
                return True
            if event.key == pygame.K_RIGHT:
                self.algo_idx = (self.algo_idx + 1) % len(ALGO_KEYS)
                return True
        return False

    def handle_heuristic_click(self, event) -> bool:
        if not self.needs_heuristic:
            return False
        if self._btn_manhattan.is_clicked(event):
            self.selected_heuristic_idx = 0
            return True
        if self._btn_euclidean.is_clicked(event):
            self.selected_heuristic_idx = 1
            return True
        return False

    def handle_speed_click(self, event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._speed_rects):
                if r.collidepoint(event.pos):
                    self.speed_idx = i
                    return True
        return False

    def is_back_map_clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self._back_map_rect.collidepoint(event.pos))

    def reposition(self, grid_pixel_w: int):
        dx = grid_pixel_w - self.x
        self.x = grid_pixel_w
        self._shift(dx)

    def _shift(self, dx: int):
        for attr in ['_algo_name_rect', '_rect_arrow_l', '_rect_arrow_r', '_back_map_rect']:
            r = getattr(self, attr)
            r.x += dx
        for r in self._speed_rects:
            r.x += dx
        for btn in [self.btn_run, self.btn_pause, self.btn_reset,
                    self._btn_manhattan, self._btn_euclidean]:
            btn.rect.x += dx

    # ── Draw ──────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, animating=False, paused=False):
        pad = 24
        bw  = self.width - pad * 2

        pygame.draw.rect(surface, PANEL_BG,
                         pygame.Rect(self.x, self.y, self.width, self.height))

        # ── Algorithm ─────────────────────────────────────────────────────
        self._label(surface, 'ALGORITHM', self.x + pad, self._algo_title_y,
                    self.font_h1, TEXT_DARK)

        hover_l = self._rect_arrow_l.collidepoint(pygame.mouse.get_pos())
        hover_r = self._rect_arrow_r.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, ACCENT_LIGHT if hover_l else DIVIDER,
                         self._rect_arrow_l, border_radius=7)
        pygame.draw.rect(surface, ACCENT_LIGHT if hover_r else DIVIDER,
                         self._rect_arrow_r, border_radius=7)

        arr_font = pygame.font.SysFont('Arial', 20, bold=True)
        tl = arr_font.render('◀', True, ACCENT)
        tr = arr_font.render('▶', True, ACCENT)
        surface.blit(tl, tl.get_rect(center=self._rect_arrow_l.center))
        surface.blit(tr, tr.get_rect(center=self._rect_arrow_r.center))

        pygame.draw.rect(surface, ACCENT_LIGHT, self._algo_name_rect, border_radius=7)
        pygame.draw.rect(surface, ACCENT, self._algo_name_rect, 2, border_radius=7)
        algo_txt = self.font_h2.render(self.selected_algo, True, ACCENT)
        surface.blit(algo_txt, algo_txt.get_rect(center=self._algo_name_rect.center))

        # ── Heuristic ─────────────────────────────────────────────────────
        if self.needs_heuristic:
            man_c = ACCENT if self.selected_heuristic == 'manhattan' else (160, 160, 200)
            euc_c = (100, 100, 200) if self.selected_heuristic == 'euclidean' else (160, 160, 200)
            self._btn_manhattan.color = man_c
            self._btn_euclidean.color = euc_c
            self._btn_manhattan.draw(surface)
            self._btn_euclidean.draw(surface)

        self._divider(surface, self._div1_y)

        # ── Speed ─────────────────────────────────────────────────────────
        self._label(surface, 'SPEED', self.x + pad, self._speed_title_y,
                    self.font_body, TEXT_GRAY)
        speed_labels = ['🐢 Slow', '▶ Normal', '⚡ Fast', '🚀 Max']
        for i, (r, lbl) in enumerate(zip(self._speed_rects, speed_labels)):
            selected = (i == self.speed_idx)
            bg = BTN_SPEED_C if selected else DIVIDER
            tc = (255, 255, 255) if selected else TEXT_DARK
            pygame.draw.rect(surface, bg, r, border_radius=6)
            t = self.font_small.render(lbl, True, tc)
            surface.blit(t, t.get_rect(center=r.center))

        self._divider(surface, self._div2_y)

        # ── Control buttons ───────────────────────────────────────────────
        self.btn_run.draw(surface, disabled=(animating and not paused))
        pause_color = BTN_DISABLED if not animating else BTN_PAUSE_C
        self.btn_pause.color = pause_color
        self.btn_pause.draw(surface, disabled=not animating)
        self.btn_reset.draw(surface)

        self._divider(surface, self._div3_y)

        # ── Stats ─────────────────────────────────────────────────────────
        self._label(surface, 'RESULTS', self.x + pad, self._stats_y - 2,
                    self.font_h1, TEXT_DARK)
        y_cur = self._stats_y + 28
        col2_x = self.x + pad + bw // 2
        for key, val in self.stats.items():
            k_surf = self.font_body.render(key + ':', True, TEXT_GRAY)
            v_surf = self.font_val.render(val, True, TEXT_DARK)
            surface.blit(k_surf, (self.x + pad, y_cur))
            surface.blit(v_surf, (col2_x, y_cur))
            y_cur += self._stat_row_h

        self._divider(surface, self._div4_y)

        # ── Back map button ───────────────────────────────────────────────
        mouse = pygame.mouse.get_pos()
        scale = 1.04 if self._back_map_rect.collidepoint(mouse) else 1.0
        bm = self._back_map_img
        if scale != 1.0:
            w = int(bm.get_width()  * scale)
            h = int(bm.get_height() * scale)
            bm = pygame.transform.smoothscale(bm, (w, h))
        surface.blit(bm, bm.get_rect(center=self._back_map_rect.center))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _label(self, surface, text, x, y, font, color):
        s = font.render(text, True, color)
        surface.blit(s, (x, y))

    def _divider(self, surface, y):
        pygame.draw.line(surface, DIVIDER,
                         (self.x + 8, y),
                         (self.x + self.width - 8, y), 1)