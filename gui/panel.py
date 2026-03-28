"""
panel.py  –  HUD sidebar – flat 2D, compact & clean layout
"""

import os, math, random
import pygame

# ── Palette ────────────────────────────────────────────────────────────────────
PANEL_BG      = (0, 185, 255)
ACCENT        = (255, 255, 255)
ACCENT2       = (0, 230, 215)
ACCENT3       = (200, 245, 255)
TEXT_BRIGHT   = (255, 255, 255)
TEXT_DIM      = (50, 130, 180)
TEXT_LABEL    = (255, 255, 255)
LINE_COLOR    = (255, 255, 255)
BTN_DISABLED  = (160, 210, 235)
BTN_TEXT_DIS  = (200, 225, 240)
BTN_RUN_C     = (0, 140, 220)
BTN_PAUSE_C   = (0, 170, 190)
BTN_RESET_C   = (20, 100, 200)
BTN_SPEED_UNS = (80, 175, 225)
BTN_SPEED_SEL = (0, 100, 200)
CARD_BG       = (0, 100, 175)
CARD_BORDER   = (255, 255, 255)

SPEED_LEVELS = [
    ('Slow',   600),
    ('Normal', 300),
    ('Fast',   100),
    ('Max',      2),
]
ALGO_KEYS       = ['BFS', 'DFS', 'UCS', 'A*', 'Greedy Search', 'Beam Search', 'Bidirectional Search', 'IDA*']
HEURISTIC_ALGOS = {'A*', 'Greedy Search', 'Beam Search', 'IDA*'}
BEAM_WIDTH_OPTIONS = [1, 2, 3, 5]


# ── Font helper ────────────────────────────────────────────────────────────────
def _game_font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ('Bangers', 'Lilita One', 'Fredoka One', 'Boogaloo',
                 'Arial Black', 'Impact', 'Rajdhani', 'Exo 2', 'Verdana'):
        try:
            f = pygame.font.SysFont(name, size, bold=bold)
            if f:
                return f
        except Exception:
            pass
    return pygame.font.SysFont(None, size, bold=bold)


# ── Image loader ───────────────────────────────────────────────────────────────
def _load_img(path: str, size: tuple) -> pygame.Surface:
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill((20, 130, 200, 200))
    return surf


# ── Particle system ────────────────────────────────────────────────────────────
class _Particle:
    __slots__ = ('x', 'y', 'vy', 'r', 'alpha', 'color')

    def __init__(self, w, h):
        self.x     = random.uniform(0, w)
        self.y     = random.uniform(0, h)
        self.vy    = random.uniform(-0.15, -0.45)
        self.r     = random.randint(1, 2)
        self.alpha = random.randint(30, 90)
        self.color = random.choice([(255, 255, 255), (200, 240, 255), (180, 230, 255)])

    def update(self, h):
        self.y += self.vy
        if self.y < -4:
            self.y = h + 4
            self.alpha = random.randint(30, 90)

    def draw(self, surf, ox, oy):
        s = pygame.Surface((self.r * 2 + 1, self.r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), (self.r, self.r), self.r)
        surf.blit(s, (ox + int(self.x) - self.r, oy + int(self.y) - self.r))


# ── Background ─────────────────────────────────────────────────────────────────
_panel_bg_cache = {}

def _draw_panel_bg(surface, rect, t, base_dir=''):
    global _panel_bg_cache
    key = (rect.width, rect.height)
    if key not in _panel_bg_cache:
        path = os.path.join(base_dir, 'picture', 'panel.png')
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            img = pygame.transform.smoothscale(img, key)
        else:
            img = pygame.Surface(key)
            img.fill((0, 110, 180))
        _panel_bg_cache[key] = img
    surface.blit(_panel_bg_cache[key], rect.topleft)


# ── Card background ────────────────────────────────────────────────────────────
def _draw_card(surface, rect, alpha=180):
    card = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    card.fill((*CARD_BG, alpha))
    surface.blit(card, rect.topleft)
    pygame.draw.rect(surface, (*CARD_BORDER, 80), rect, 1)


# ── Section label ──────────────────────────────────────────────────────────────
def _draw_section_label(surface, x, y, label, font):
    lbl = font.render(label, True, (200, 235, 255))
    surface.blit(lbl, (x, y))


# ── Button flat ────────────────────────────────────────────────────────────────
class FlatButton:
    def __init__(self, rect, label, color, text_color=TEXT_BRIGHT, font_size=14):
        self.rect       = rect
        self.label      = label
        self.color      = color
        self.text_color = text_color
        self.hovered    = False
        self.font       = _game_font(font_size, bold=True)

    def draw(self, surface, disabled=False, t=0.0):
        if disabled:
            pygame.draw.rect(surface, BTN_DISABLED, self.rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=6)
            txt = self.font.render(self.label, True, BTN_TEXT_DIS)
            surface.blit(txt, txt.get_rect(center=self.rect.center))
            return
        c = tuple(max(0, v - 25) for v in self.color) if self.hovered else self.color
        pygame.draw.rect(surface, c, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=6)
        txt = self.font.render(self.label, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Panel ──────────────────────────────────────────────────────────────────────
class Panel:
    _PAD     = 16   # outer padding
    _IG      = 6    # inner gap (giữa các item trong cùng section)
    _SG      = 12   # section gap (giữa các section)
    _LBL_H   = 18   # chiều cao label section
    _BTN_H   = 38   # nút lớn (RUN/PAUSE/RESET)
    _ROW_H   = 30   # nút nhỏ (heuristic, speed, beam)

    def __init__(self, x, y, width, height, base_dir=''):
        self.x        = x
        self.y        = y
        self.width    = width
        self.height   = height
        self.base_dir = base_dir
        self._t       = 0.0

        pygame.font.init()
        self.f_section = _game_font(14, bold=True)
        self.f_algo    = _game_font(20, bold=True)
        self.f_btn     = _game_font(16, bold=True)
        self.f_body    = _game_font(16, bold=True)
        self.f_val     = _game_font(15)
        self.f_arrow   = _game_font(22, bold=True)

        self.algo_idx                = 0
        self.heuristic_options       = ['manhattan', 'euclidean']
        self.selected_heuristic_idx  = 0
        self.selected_beam_width_idx = 1
        self.speed_idx               = 1
        self.stats = {
            'Algorithm':   '--',
            'Cost':        '--',
            'Path Length': '--',
            'Nodes Found': '--',
            'Time':        '--',
        }

        self._particles = [_Particle(width, height) for _ in range(28)]
        self._build_layout()

    def _build_layout(self):
        P  = self._PAD
        IG = self._IG
        SG = self._SG
        LH = self._LBL_H
        BH = self._BTN_H
        RH = self._ROW_H
        x, y, w = self.x, self.y, self.width
        bw  = w - P * 2
        cur = y + P + 8

        # ── ALGORITHM ─────────────────────────────────────────────────────
        self._div_algo_y = cur
        cur += LH + IG
        arrow_w = 34
        algo_mid_w = bw - (arrow_w + 4) * 2
        self._rect_arrow_l   = pygame.Rect(x + P, cur, arrow_w, BH)
        self._algo_name_rect = pygame.Rect(x + P + arrow_w + 4, cur, algo_mid_w, BH)
        self._rect_arrow_r   = pygame.Rect(x + P + arrow_w + 4 + algo_mid_w + 4, cur, arrow_w, BH)
        cur += BH + SG

        # ── HEURISTIC + BEAM (đặt cùng 1 row nếu cần) ────────────────────
        self._div_heur_y = cur
        cur += LH + IG
        hw = bw // 2 - 3
        self._btn_manhattan = FlatButton(
            pygame.Rect(x + P, cur, hw, RH), 'Manhattan', BTN_SPEED_UNS, font_size=15)
        self._btn_euclidean = FlatButton(
            pygame.Rect(x + P + hw + 6, cur, hw, RH), 'Euclidean', BTN_SPEED_UNS, font_size=15)
        cur += RH + SG

        # ── BEAM WIDTH ────────────────────────────────────────────────────
        self._div_beam_y = cur
        cur += LH + IG
        beam_w = (bw - 3 * 3) // 4
        self._beam_rects = [
            pygame.Rect(x + P + i * (beam_w + 3), cur, beam_w, RH)
            for i in range(len(BEAM_WIDTH_OPTIONS))
        ]
        cur += RH + SG

        # ── SPEED ─────────────────────────────────────────────────────────
        self._div_speed_y = cur
        cur += LH + IG
        spd_w = (bw - 3 * 3) // 4
        self._speed_rects = [
            pygame.Rect(x + P + i * (spd_w + 3), cur, spd_w, RH)
            for i in range(4)
        ]
        cur += RH + SG

        # ── CONTROLS (RUN / PAUSE / RESET) ───────────────────────────────
        self._div_ctrl_y = cur
        cur += LH + IG
        third = (bw - 8) // 3
        self.btn_run   = FlatButton(pygame.Rect(x + P, cur, third, BH),
                                    'RUN', BTN_RUN_C, font_size=16)
        self.btn_pause = FlatButton(pygame.Rect(x + P + third + 4, cur, third, BH),
                                    'PAUSE', BTN_PAUSE_C, font_size=15)
        self.btn_reset = FlatButton(pygame.Rect(x + P + (third + 4) * 2, cur, third, BH),
                                    'RESET', BTN_RESET_C, font_size=15)
        cur += BH + SG

        # ── RESULTS ───────────────────────────────────────────────────────
        self._div_res_y  = cur
        cur += LH + IG
        self._stats_top  = cur
        self._stat_row_h = 23

        # ── BACK MAP ──────────────────────────────────────────────────────
        _orig_path = os.path.join(self.base_dir, 'picture', 'back_map.png')
        bm_h = int((w - P * 2) * 0.11)
        if os.path.exists(_orig_path):
            _tmp = pygame.image.load(_orig_path)
            _ow, _oh = _tmp.get_size()
            bm_w = int(bm_h * _ow / _oh) if _oh else bm_h * 3
        else:
            bm_w = bm_h * 3
        self._back_map_img  = _load_img(_orig_path, (bm_w, bm_h))
        self._back_map_rect = pygame.Rect(
            x + P + ((w - P * 2) - bm_w) // 2,
            self.y + self.height - bm_h - 12, bm_w, bm_h)

    # ── Properties ────────────────────────────────────────────────────────
    @property
    def selected_algo(self):
        return ALGO_KEYS[self.algo_idx]

    @property
    def selected_heuristic(self):
        return self.heuristic_options[self.selected_heuristic_idx]

    @property
    def step_delay_ms(self):
        return SPEED_LEVELS[self.speed_idx][1]

    @property
    def selected_speed_label(self):
        return SPEED_LEVELS[self.speed_idx][0]

    @property
    def needs_heuristic(self):
        return self.selected_algo in HEURISTIC_ALGOS

    @property
    def needs_beam_width(self):
        return self.selected_algo == 'Beam Search'

    @property
    def selected_beam_width(self):
        return BEAM_WIDTH_OPTIONS[self.selected_beam_width_idx]

    # ── Stats ─────────────────────────────────────────────────────────────
    def update_stats(self, algorithm, cost, length, nodes, time_ms):
        self.stats['Algorithm']   = str(algorithm)
        self.stats['Cost']        = str(cost)
        self.stats['Path Length'] = str(length)
        self.stats['Nodes Found'] = str(nodes)
        self.stats['Time']        = f'{time_ms:.1f} ms'

    def reset_stats(self):
        for k in self.stats:
            self.stats[k] = '--'

    # ── Events ────────────────────────────────────────────────────────────
    def handle_hover(self, pos):
        for b in [self.btn_run, self.btn_pause, self.btn_reset,
                  self._btn_manhattan, self._btn_euclidean]:
            b.update(pos)

    def handle_keydown(self, event):
        return self.handle_event(event)

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.algo_idx = (self.algo_idx - 1) % len(ALGO_KEYS)
                return True
            if event.key == pygame.K_RIGHT:
                self.algo_idx = (self.algo_idx + 1) % len(ALGO_KEYS)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._rect_arrow_l.collidepoint(event.pos):
                self.algo_idx = (self.algo_idx - 1) % len(ALGO_KEYS)
                return True
            if self._rect_arrow_r.collidepoint(event.pos):
                self.algo_idx = (self.algo_idx + 1) % len(ALGO_KEYS)
                return True
        return False

    def handle_heuristic_click(self, event):
        if not self.needs_heuristic:
            return False
        if self._btn_manhattan.is_clicked(event):
            self.selected_heuristic_idx = 0
            return True
        if self._btn_euclidean.is_clicked(event):
            self.selected_heuristic_idx = 1
            return True
        return False

    def handle_speed_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._speed_rects):
                if r.collidepoint(event.pos):
                    self.speed_idx = i
                    return True
        return False

    def handle_beam_width_click(self, event):
        if not self.needs_beam_width:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self._beam_rects):
                if r.collidepoint(event.pos):
                    self.selected_beam_width_idx = i
                    return True
        return False

    def is_back_map_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self._back_map_rect.collidepoint(event.pos))

    def reposition(self, grid_pixel_w):
        dx = grid_pixel_w - self.x
        self.x = grid_pixel_w
        self._shift(dx)

    def _shift(self, dx):
        for attr in ['_algo_name_rect', '_rect_arrow_l', '_rect_arrow_r', '_back_map_rect']:
            getattr(self, attr).x += dx
        for r in self._beam_rects:
            r.x += dx
        for r in self._speed_rects:
            r.x += dx
        for b in [self.btn_run, self.btn_pause, self.btn_reset,
                  self._btn_manhattan, self._btn_euclidean]:
            b.rect.x += dx

    def tick(self, dt=0.016):
        self._t += dt
        for p in self._particles:
            p.update(self.height)

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self, surface, animating=False, paused=False):
        t  = self._t
        P  = self._PAD
        bw = self.width - P * 2
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        _draw_panel_bg(surface, panel_rect, t, self.base_dir)

        for p in self._particles:
            p.draw(surface, self.x, self.y)

        mouse = pygame.mouse.get_pos()

        # ── ALGORITHM ────────────────────────────────────────────────────
        _draw_section_label(surface, self.x + P, self._div_algo_y, 'ALGORITHM', self.f_section)

        for btn_r, sym in [(self._rect_arrow_l, '<'), (self._rect_arrow_r, '>')]:
            hov = btn_r.collidepoint(mouse)
            pygame.draw.rect(surface, (0, 100, 190) if hov else (0, 140, 220), btn_r, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), btn_r, 2, border_radius=6)
            ts = self.f_arrow.render(sym, True, (255, 255, 255))
            surface.blit(ts, ts.get_rect(center=btn_r.center))

        pygame.draw.rect(surface, (0, 130, 210), self._algo_name_rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self._algo_name_rect, 2, border_radius=6)
        at = self.f_algo.render(self.selected_algo, True, TEXT_BRIGHT)
        surface.blit(at, at.get_rect(center=self._algo_name_rect.center))

        # ── HEURISTIC ────────────────────────────────────────────────────
        _draw_section_label(surface, self.x + P, self._div_heur_y, 'HEURISTIC', self.f_section)

        if self.needs_heuristic:
            for btn, idx in [(self._btn_manhattan, 0), (self._btn_euclidean, 1)]:
                sel = (self.selected_heuristic_idx == idx)
                btn.color      = BTN_SPEED_SEL if sel else BTN_SPEED_UNS
                btn.text_color = TEXT_BRIGHT
                btn.draw(surface, t=t)
        else:
            na_rect = pygame.Rect(self.x + P, self._btn_manhattan.rect.y, bw, self._ROW_H)
            pygame.draw.rect(surface, BTN_SPEED_UNS, na_rect, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), na_rect, 2, border_radius=6)
            msg = self.f_body.render('N/A for this algorithm', True, TEXT_BRIGHT)
            surface.blit(msg, msg.get_rect(center=na_rect.center))

        # ── BEAM WIDTH ───────────────────────────────────────────────────
        if self.needs_beam_width:
            _draw_section_label(surface, self.x + P, self._div_beam_y, 'BEAM WIDTH', self.f_section)
            for i, (r, value) in enumerate(zip(self._beam_rects, BEAM_WIDTH_OPTIONS)):
                sel = (i == self.selected_beam_width_idx)
                pygame.draw.rect(surface, BTN_SPEED_SEL if sel else BTN_SPEED_UNS, r, border_radius=6)
                pygame.draw.rect(surface, (255, 255, 255), r, 2, border_radius=6)
                tc = TEXT_BRIGHT if sel else (20, 60, 120)
                ts = self.f_btn.render(f'K={value}', True, tc)
                surface.blit(ts, ts.get_rect(center=r.center))

        # ── SPEED ────────────────────────────────────────────────────────
        _draw_section_label(surface, self.x + P, self._div_speed_y, 'SPEED', self.f_section)

        speed_labels = ['SLOW', 'NORM', 'FAST', 'MAX']
        for i, (r, lbl) in enumerate(zip(self._speed_rects, speed_labels)):
            sel = (i == self.speed_idx)
            pygame.draw.rect(surface, BTN_SPEED_SEL if sel else BTN_SPEED_UNS, r, border_radius=6)
            pygame.draw.rect(surface, (255, 255, 255), r, 2, border_radius=6)
            tc = TEXT_BRIGHT if sel else (20, 60, 120)
            ts = self.f_btn.render(lbl, True, tc)
            surface.blit(ts, ts.get_rect(center=r.center))

        # ── CONTROLS ─────────────────────────────────────────────────────
        _draw_section_label(surface, self.x + P, self._div_ctrl_y, 'CONTROLS', self.f_section)

        self.btn_run.draw(surface, disabled=(animating and not paused), t=t)
        self.btn_pause.color = BTN_DISABLED if not animating else BTN_PAUSE_C
        self.btn_pause.draw(surface, disabled=not animating, t=t)
        self.btn_reset.draw(surface, t=t)

        # ── RESULTS ──────────────────────────────────────────────────────
        _draw_section_label(surface, self.x + P, self._div_res_y, 'RESULTS', self.f_section)

        # Card nền cho results
        stats_list = list(self.stats.items())
        card_h = len(stats_list) * self._stat_row_h + 6
        card_rect = pygame.Rect(self.x + P, self._stats_top - 3, bw, card_h)
        _draw_card(surface, card_rect)

        y_cur  = self._stats_top + 1
        col2_x = self.x + P + bw // 2 + 8
        for key, val in stats_list:
            k_surf = self.f_body.render(key + ':', True, (200, 235, 255))
            v_surf = self.f_val.render(val, True,
                                       (255, 255, 255) if val != '--' else (150, 200, 230))
            surface.blit(k_surf, (self.x + P + 6, y_cur))
            surface.blit(v_surf, (col2_x, y_cur))
            y_cur += self._stat_row_h

        # ── BACK MAP ─────────────────────────────────────────────────────
        hov = self._back_map_rect.collidepoint(mouse)
        bm  = self._back_map_img
        if hov:
            bm = pygame.transform.smoothscale(
                bm, (int(bm.get_width() * 1.05), int(bm.get_height() * 1.05)))
        surface.blit(bm, bm.get_rect(center=self._back_map_rect.center))