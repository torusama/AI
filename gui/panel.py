"""
panel.py  –  HUD-style sidebar, no glass, no rounded borders
  • Nền: scanlines + floating particles animated
  • Section dividers: đường kẻ ngang cyan mỏng + label trái
  • Khoảng cách section rộng rãi
  • Heuristic row luôn có trong layout, chỉ ẩn khi không cần
  • Font: Orbitron → Exo → Verdana (game-style)
  • Không emoji – ASCII only
"""

import os, math, random
import pygame

# ── Palette ────────────────────────────────────────────────────────────────────
PANEL_BG      = (12, 8, 28)           # deep purple-black
ACCENT        = (0, 255, 220)         # neon mint
ACCENT2       = (255, 60, 180)        # hot pink
ACCENT3       = (255, 230, 0)         # electric yellow
TEXT_BRIGHT   = (230, 245, 255)
TEXT_DIM      = (120, 140, 180)
TEXT_LABEL    = (0, 255, 220)
LINE_COLOR    = (0, 255, 220)
BTN_DISABLED  = (30, 28, 55)
BTN_TEXT_DIS  = (80, 80, 120)
BTN_RUN_C     = (255, 220, 0)
BTN_PAUSE_C   = (255, 50, 170)
BTN_RESET_C   = (255, 30, 80)
BTN_SPEED_UNS = (22, 18, 50)

SPEED_LEVELS = [
    ('Slow',   60),
    ('Normal', 30),
    ('Fast',   10),
    ('Max',     2),
]
ALGO_KEYS       = ['BFS', 'DFS', 'UCS', 'A*', 'Bidirectional', 'IDA*']
HEURISTIC_ALGOS = {'A*', 'IDA*'}


# ── Font helper ────────────────────────────────────────────────────────────────
def _game_font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ('Orbitron', 'Exo 2', 'Exo', 'Rajdhani', 'Verdana', 'Segoe UI'):
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
    surf.fill((20, 30, 50, 200))
    return surf


# ── Particle system ────────────────────────────────────────────────────────────
class _Particle:
    __slots__ = ('x', 'y', 'vy', 'r', 'alpha', 'color')

    def __init__(self, w, h):
        self.x     = random.uniform(0, w)
        self.y     = random.uniform(0, h)
        self.vy    = random.uniform(-0.15, -0.45)
        self.r     = random.randint(1, 2)
        self.alpha = random.randint(40, 130)
        self.color = random.choice([(0, 220, 255), (0, 160, 200), (80, 200, 255)])

    def update(self, h):
        self.y += self.vy
        if self.y < -4:
            self.y = h + 4
            self.alpha = random.randint(40, 130)

    def draw(self, surf, ox, oy):
        s = pygame.Surface((self.r * 2 + 1, self.r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), (self.r, self.r), self.r)
        surf.blit(s, (ox + int(self.x) - self.r, oy + int(self.y) - self.r))


def _glow_line(surface, p1, p2, color, width=2, layers=4):
    """Vẽ đường thẳng có bloom glow nhiều lớp – kiểu anime lightsaber."""
    r, g, b = color
    for i in range(layers, 0, -1):
        a   = int(60 * (i / layers) ** 2)
        w   = width + (layers - i) * 3
        s   = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        pygame.draw.line(s, (r, g, b, a), p1, p2, w)
        surface.blit(s, (0, 0))
    pygame.draw.line(surface, (min(255, r + 80), min(255, g + 80), min(255, b + 80)),
                     p1, p2, width)


def _glow_rect_border(surface, rect, color, width=2, layers=5):
    """Viền rect có anime glow bloom."""
    r, g, b = color
    s = pygame.Surface((rect.width + layers * 6, rect.height + layers * 6), pygame.SRCALPHA)
    ox, oy = layers * 3, layers * 3
    for i in range(layers, 0, -1):
        a  = int(80 * (i / layers) ** 2)
        ex = layers - i
        pygame.draw.rect(s, (r, g, b, a),
                         pygame.Rect(ox - ex, oy - ex,
                                     rect.width + ex * 2, rect.height + ex * 2), width + 1)
    pygame.draw.rect(s, (min(255, r + 100), min(255, g + 100), min(255, b + 100)),
                     pygame.Rect(ox, oy, rect.width, rect.height), width)
    surface.blit(s, (rect.x - layers * 3, rect.y - layers * 3))


def _draw_pixel_grid(surface, rect, t):
    """Lưới pixel nhỏ mờ – flat pixel art texture."""
    gs = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    step = 8
    drift_x = int(t * 4) % step
    drift_y = int(t * 2) % step
    x = -step + drift_x
    while x < rect.width:
        pygame.draw.line(gs, (0, 255, 220, 10), (x, 0), (x, rect.height), 1)
        x += step
    y = -step + drift_y
    while y < rect.height:
        pygame.draw.line(gs, (0, 255, 220, 8), (0, y), (rect.width, y), 1)
        y += step
    surface.blit(gs, rect.topleft)


def _draw_neon_scanline(surface, rect, t):
    """Một dải sáng neon chạy từ trên xuống dưới lặp lại – kiểu anime CRT scan."""
    h    = rect.height
    scan_y = int((t * 90) % (h + 60)) - 30
    band = 28
    s    = pygame.Surface((rect.width, band * 2), pygame.SRCALPHA)
    for dy in range(band):
        fade = 1.0 - dy / band
        a    = int(55 * fade * fade)
        pygame.draw.line(s, (0, 255, 220, a), (0, dy), (rect.width, dy))
        pygame.draw.line(s, (0, 255, 220, a), (0, band * 2 - 1 - dy), (rect.width, band * 2 - 1 - dy))
    if 0 <= scan_y < h:
        surface.blit(s, (rect.x, rect.y + scan_y - band))


def _draw_anime_glow_bg(surface, rect, t):
    """Nền: gradient tím-đen + neon glow viền + pixel grid + scanline chạy."""
    w, h = rect.width, rect.height

    # Gradient nền: tím đậm trên → đen tím dưới
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        progress = y / h
        r = int(18  + 6  * (1 - progress))
        g = int(8   + 4  * (1 - progress))
        b = int(45  + 15 * (1 - progress))
        pygame.draw.line(bg, (r, g, b, 255), (0, y), (w, y))
    surface.blit(bg, rect.topleft)

    # Pixel grid
    _draw_pixel_grid(surface, rect, t)

    # Neon scanline chạy
    _draw_neon_scanline(surface, rect, t)

    # Viền neon glow mint pulse
    pulse_a = int(190 + 60 * math.sin(t * 2.2))
    mint = (0, min(255, pulse_a), 200)
    _glow_rect_border(surface, rect, mint, width=2, layers=6)

    # Góc accent: pixel brackets kiểu retro game, màu hot pink
    arm = 20
    pk  = (255, 60, 180)
    bk  = pygame.Surface((w, h), pygame.SRCALPHA)
    pulse_pk = int(180 + 70 * math.sin(t * 1.7 + 1.0))
    for cx, cy, sx, sy in [(0,0,1,1),(w-1,0,-1,1),(0,h-1,1,-1),(w-1,h-1,-1,-1)]:
        for i in range(3):   # 3-pixel thick bracket = pixel style
            pygame.draw.line(bk, (*pk, pulse_pk - i*30),
                             (cx + i*sx, cy), (cx + sx*(arm - i), cy), 1)
            pygame.draw.line(bk, (*pk, pulse_pk - i*30),
                             (cx, cy + i*sy), (cx, cy + sy*(arm - i)), 1)
    surface.blit(bk, rect.topleft)


def _draw_panel_bg(surface, rect, t):
    _draw_anime_glow_bg(surface, rect, t)


def _draw_divider(surface, x, y, w, label, font, t=0.0):
    """Divider với anime glow bloom."""
    pulse = int(190 + 60 * math.sin(t * 1.8))
    color = (0, pulse, 200)
    # glow bloom layers
    for layer in range(4, 0, -1):
        a  = int(50 * (layer / 4) ** 2)
        lw = layer * 2
        s  = pygame.Surface((w, lw * 2 + 2), pygame.SRCALPHA)
        pygame.draw.line(s, (0, 255, 210, a), (0, lw), (w, lw), lw)
        surface.blit(s, (x, y - lw))
    # core bright line
    pygame.draw.line(surface, color, (x, y), (x + w, y), 1)
    if label:
        lbl = font.render(label, True, TEXT_LABEL)
        bg  = pygame.Surface((lbl.get_width() + 10, lbl.get_height() + 2), pygame.SRCALPHA)
        bg.fill((12, 8, 28, 240))
        surface.blit(bg, (x, y - lbl.get_height() // 2 - 1))
        surface.blit(lbl, (x + 5, y - lbl.get_height() // 2))


# ── Button ─────────────────────────────────────────────────────────────────────
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
            pygame.draw.rect(surface, BTN_DISABLED, self.rect)
            pygame.draw.rect(surface, (50, 45, 90), self.rect, 1)
            txt = self.font.render(self.label, True, BTN_TEXT_DIS)
        else:
            c = tuple(min(255, v + 35) for v in self.color) if self.hovered else self.color
            # glow bloom behind button when hovered
            if self.hovered:
                gs = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
                for i in range(5, 0, -1):
                    a = int(40 * (i / 5) ** 2)
                    pygame.draw.rect(gs, (*c, a),
                                     pygame.Rect(10 - i*2, 10 - i*2,
                                                 self.rect.width + i*4, self.rect.height + i*4))
                surface.blit(gs, (self.rect.x - 10, self.rect.y - 10))
            pygame.draw.rect(surface, c, self.rect)
            # shine top strip
            shine = pygame.Surface((self.rect.width, max(1, self.rect.height // 3)), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 30))
            surface.blit(shine, self.rect.topleft)
            # pixel-style 1px bright border
            r, g, b = c
            pygame.draw.rect(surface,
                             (min(255,r+120), min(255,g+120), min(255,b+120)),
                             self.rect, 1)
            txt = self.font.render(self.label, True, self.text_color)
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Panel ─────────────────────────────────────────────────────────────────────
class Panel:
    _PAD       = 22
    _SEC_GAP   = 30
    _INNER_GAP = 10
    _BTN_H     = 40
    _SMALL_H   = 34

    def __init__(self, x, y, width, height, base_dir=''):
        self.x        = x
        self.y        = y
        self.width    = width
        self.height   = height
        self.base_dir = base_dir
        self._t       = 0.0

        pygame.font.init()
        self.f_section = _game_font(18, bold=True)
        self.f_algo    = _game_font(22, bold=True)
        self.f_btn     = _game_font(18, bold=True)
        self.f_body    = _game_font(17, bold=True)
        self.f_val     = _game_font(17)
        self.f_arrow   = _game_font(22, bold=True)

        self.algo_idx               = 0
        self.heuristic_options      = ['manhattan', 'euclidean']
        self.selected_heuristic_idx = 0
        self.speed_idx              = 1
        self.stats = {
            'Algorithm':   '--',
            'Cost':        '--',
            'Path Length': '--',
            'Nodes Found': '--',
            'Time':        '--',
        }

        self._particles = [_Particle(width, height) for _ in range(38)]
        self._build_layout()

    def _build_layout(self):
        P  = self._PAD
        SG = self._SEC_GAP
        IG = self._INNER_GAP
        BH = self._BTN_H
        SH = self._SMALL_H
        x, y, w = self.x, self.y, self.width
        bw  = w - P * 2
        cur = y + P + 10

        # ALGORITHM
        self._div_algo_y     = cur + 10
        cur += 28 + IG
        arrow_w = 38
        self._rect_arrow_l   = pygame.Rect(x + P, cur, arrow_w, BH)
        self._algo_name_rect = pygame.Rect(x + P + arrow_w + 6, cur,
                                           bw - (arrow_w + 6) * 2, BH)
        self._rect_arrow_r   = pygame.Rect(x + P + bw - arrow_w, cur, arrow_w, BH)
        cur += BH + SG

        # HEURISTIC
        self._div_heur_y  = cur + 10
        cur += 28 + IG
        hw = bw // 2 - 5
        self._btn_manhattan = FlatButton(
            pygame.Rect(x + P, cur, hw, SH), 'Manhattan', (0, 100, 180), font_size=17)
        self._btn_euclidean = FlatButton(
            pygame.Rect(x + P + hw + 10, cur, hw, SH), 'Euclidean', (50, 50, 160), font_size=17)
        cur += SH + SG

        # SPEED
        self._div_speed_y = cur + 10
        cur += 28 + IG
        spd_w = (bw - 9) // 4
        self._speed_rects = [
            pygame.Rect(x + P + i * (spd_w + 3), cur, spd_w, SH)
            for i in range(4)
        ]
        cur += SH + SG

        # CONTROLS
        self._div_ctrl_y = cur + 10
        cur += 28 + IG
        third = (bw - 12) // 3
        self.btn_run   = FlatButton(pygame.Rect(x + P, cur, third, BH),
                                    'RUN', BTN_RUN_C, text_color=(30, 15, 0), font_size=14)
        self.btn_pause = FlatButton(pygame.Rect(x + P + third + 6, cur, third, BH),
                                    'PAUSE', BTN_PAUSE_C, font_size=13)
        self.btn_reset = FlatButton(pygame.Rect(x + P + (third + 6) * 2, cur, third, BH),
                                    'RESET', BTN_RESET_C, font_size=13)
        cur += BH + SG

        # RESULTS
        self._div_res_y  = cur + 10
        cur += 28 + IG
        self._stats_top  = cur
        self._stat_row_h = 26

        # Back map – giữ aspect ratio gốc, scale theo chiều cao
        _orig_path = os.path.join(self.base_dir, 'picture', 'back_map.png')
        bm_h = int((w - P * 2) * 0.08)
        if os.path.exists(_orig_path):
            _tmp = pygame.image.load(_orig_path)
            _ow, _oh = _tmp.get_size()
            bm_w = int(bm_h * _ow / _oh) if _oh else bm_h * 3
        else:
            bm_w = bm_h * 3
        self._back_map_img  = _load_img(_orig_path, (bm_w, bm_h))
        self._back_map_rect = pygame.Rect(
            x + P + ((w - P * 2) - bm_w) // 2,
            self.y + self.height - bm_h - 16, bm_w, bm_h)

    # Properties
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
    def needs_heuristic(self):
        return self.selected_algo in HEURISTIC_ALGOS

    # Stats
    def update_stats(self, algorithm, cost, length, nodes, time_ms):
        self.stats['Algorithm']   = str(algorithm)
        self.stats['Cost']        = str(cost)
        self.stats['Path Length'] = str(length)
        self.stats['Nodes Found'] = str(nodes)
        self.stats['Time']        = f'{time_ms:.1f} ms'

    def reset_stats(self):
        for k in self.stats:
            self.stats[k] = '--'

    # Events
    def handle_hover(self, pos):
        for b in [self.btn_run, self.btn_pause, self.btn_reset,
                  self._btn_manhattan, self._btn_euclidean]:
            b.update(pos)

    def handle_keydown(self, event):
        """Backward-compat wrapper."""
        return self.handle_event(event)

    def handle_event(self, event) -> bool:
        """Xử lý cả keyboard (LEFT/RIGHT) lẫn click chuột vào mũi tên algo."""
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
        for r in self._speed_rects:
            r.x += dx
        for b in [self.btn_run, self.btn_pause, self.btn_reset,
                  self._btn_manhattan, self._btn_euclidean]:
            b.rect.x += dx

    def tick(self, dt=0.016):
        self._t += dt
        for p in self._particles:
            p.update(self.height)

    # Draw
    def draw(self, surface, animating=False, paused=False):
        t   = self._t
        P   = self._PAD
        bw  = self.width - P * 2
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        _draw_panel_bg(surface, panel_rect, t)
        for p in self._particles:
            p.draw(surface, self.x, self.y)

        mouse = pygame.mouse.get_pos()

        # ── ALGORITHM ────────────────────────────────────────────────────
        _draw_divider(surface, self.x + P, self._div_algo_y, bw, 'ALGORITHM', self.f_section, t)

        for btn_r, sym in [(self._rect_arrow_l, '<'), (self._rect_arrow_r, '>')]:
            hov = btn_r.collidepoint(mouse)
            pygame.draw.rect(surface, (0, 120, 190) if hov else (150, 185, 215), btn_r)
            pygame.draw.line(surface, (0, 255, 220), btn_r.topleft, btn_r.bottomleft, 2)
            ts = self.f_arrow.render(sym, True, (12,8,28) if hov else (0,255,220))
            surface.blit(ts, ts.get_rect(center=btn_r.center))

        pygame.draw.rect(surface, (20, 14, 50), self._algo_name_rect)
        pulse_c = int(190 + 60 * math.sin(t * 2.2))
        _glow_rect_border(surface, self._algo_name_rect,
                          (0, pulse_c, 200), width=1, layers=5)
        at = self.f_algo.render(self.selected_algo, True, TEXT_BRIGHT)
        surface.blit(at, at.get_rect(center=self._algo_name_rect.center))

        # ── HEURISTIC ────────────────────────────────────────────────────
        _draw_divider(surface, self.x + P, self._div_heur_y, bw, 'HEURISTIC', self.f_section, t)

        if self.needs_heuristic:
            for btn, idx in [(self._btn_manhattan, 0), (self._btn_euclidean, 1)]:
                sel = (self.selected_heuristic_idx == idx)
                btn.color      = (0, 170, 210) if sel else (18, 28, 55)
                btn.text_color = (5, 5, 5) if sel else TEXT_DIM
                btn.draw(surface, t=t)
                if sel:
                    pygame.draw.line(surface, ACCENT,
                                     (btn.rect.x, btn.rect.bottom - 2),
                                     (btn.rect.right, btn.rect.bottom - 2), 2)
        else:
            ph = pygame.Surface((bw, self._SMALL_H), pygame.SRCALPHA)
            ph.fill((20, 14, 50, 200))
            surface.blit(ph, (self.x + P, self._btn_manhattan.rect.y))
            msg = self.f_body.render('N/A for this algorithm', True, (50, 70, 95))
            surface.blit(msg, msg.get_rect(
                center=(self.x + P + bw // 2, self._btn_manhattan.rect.centery)))

        # ── SPEED ────────────────────────────────────────────────────────
        _draw_divider(surface, self.x + P, self._div_speed_y, bw, 'SPEED', self.f_section, t)

        for i, (r, lbl) in enumerate(zip(self._speed_rects, ['SLOW', 'NORMAL', 'FAST', 'MAX'])):
            sel = (i == self.speed_idx)
            if sel:
                sh = int(175 + 45 * math.sin(t * 3.0))
                pygame.draw.rect(surface, (0, sh, min(255, sh + 25)), r)
                _glow_line(surface, r.bottomleft, r.bottomright, (0,255,220), width=2, layers=3)
                r_top = (min(255,sh+80), min(255,sh+80), min(255,sh+100))
                pygame.draw.rect(surface, r_top,
                                 pygame.Rect(r.x, r.y, r.width, max(1, r.height//3)), 0)
                tc = (5, 5, 5)
            else:
                pygame.draw.rect(surface, (22, 18, 50), r)
                tc = TEXT_DIM
            ts = self.f_btn.render(lbl, True, tc)
            surface.blit(ts, ts.get_rect(center=r.center))

        # ── CONTROLS ─────────────────────────────────────────────────────
        _draw_divider(surface, self.x + P, self._div_ctrl_y, bw, 'CONTROLS', self.f_section, t)

        self.btn_run.draw(surface, disabled=(animating and not paused), t=t)
        self.btn_pause.color = BTN_DISABLED if not animating else BTN_PAUSE_C
        self.btn_pause.draw(surface, disabled=not animating, t=t)
        self.btn_reset.draw(surface, t=t)

        # ── RESULTS ──────────────────────────────────────────────────────
        _draw_divider(surface, self.x + P, self._div_res_y, bw, 'RESULTS', self.f_section, t)

        y_cur  = self._stats_top
        col2_x = self.x + P + bw // 2 + 10
        for key, val in self.stats.items():
            k_surf = self.f_body.render(key + ':', True, TEXT_DIM)
            v_surf = self.f_val.render(val, True,
                                       TEXT_BRIGHT if val != '--' else (70, 80, 120))
            surface.blit(k_surf, (self.x + P, y_cur))
            surface.blit(v_surf, (col2_x, y_cur))
            y_cur += self._stat_row_h

        # ── Back map ─────────────────────────────────────────────────────
        hov   = self._back_map_rect.collidepoint(mouse)
        scale = 1.05 if hov else 1.0
        bm = self._back_map_img
        if scale != 1.0:
            bm = pygame.transform.smoothscale(
                bm, (int(bm.get_width() * scale), int(bm.get_height() * scale)))
        surface.blit(bm, bm.get_rect(center=self._back_map_rect.center))