"""
panel.py
Panel bên phải: hiển thị thông tin + nút bấm điều khiển.
"""

import os
import pygame
from gui.colors import (
    PANEL_BG, TEXT_COLOR,
    BUTTON_COLOR, BUTTON_HOVER, BUTTON_TEXT
)


class Button:
    """Nút bấm đơn giản."""

    def __init__(self, rect: pygame.Rect, label: str):
        self.rect    = rect
        self.label   = label
        self.hovered = False
        self.font    = pygame.font.SysFont('Arial', 14, bold=True)

    def draw(self, surface: pygame.Surface):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        text = self.font.render(self.label, True, BUTTON_TEXT)
        surface.blit(text, text.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, event) -> bool:
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )


class Panel:
    """Panel bên phải màn hình."""

    MAP_LIST = [
        ('Open',      'maps/Open.txt'),
        ('Cost Trap', 'maps/Cost_trap.txt'),
        ('Dead End',  'maps/Dead_end.txt'),
    ]

    def __init__(self, x: int, y: int, width: int, height: int, base_dir: str = ''):
        self.x        = x
        self.y        = y
        self.width    = width
        self.height   = height
        self.base_dir = base_dir

        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 15, bold=True)
        self.font_text  = pygame.font.SysFont('Arial', 13)
        self.font_small = pygame.font.SysFont('Arial', 11)

        # ── Nút chọn map ──────────────────────────────────────────────────
        map_btn_w   = width - 20
        map_btn_h   = 26
        map_start_y = y + 44
        self.map_buttons = []
        for i, (label, filepath) in enumerate(self.MAP_LIST):
            rect = pygame.Rect(
                x + 10,
                map_start_y + i * (map_btn_h + 4),
                map_btn_w, map_btn_h
            )
            self.map_buttons.append({
                'rect': rect, 'label': label,
                'path': filepath, 'hovered': False
            })

        self.selected_map_idx = 0

        # ── Nút Run và Reset ──────────────────────────────────────────────
        btn_y  = map_start_y + len(self.MAP_LIST) * (map_btn_h + 4) + 12
        btn_w, btn_h = width - 20, 36
        self.btn_run   = Button(pygame.Rect(x + 10, btn_y,             btn_w, btn_h), 'Run')
        self.btn_reset = Button(pygame.Rect(x + 10, btn_y + btn_h + 8, btn_w, btn_h), 'Reset')

        self._below_btns_y = btn_y + (btn_h + 8) * 2 + 8

        # Stats
        self.stats = {
            'Algorithm':      '—',
            'Path cost':      '—',
            'Path length':    '—',
            'Nodes explored': '—',
            'Time (ms)':      '—',
        }

    @property
    def selected_map_path(self) -> str:
        """Trả về đường dẫn tuyệt đối của map đang chọn."""
        rel = self.MAP_LIST[self.selected_map_idx][1]
        if self.base_dir:
            return os.path.join(self.base_dir, rel)
        return rel

    # ── Stats ──────────────────────────────────────────────────────────────

    def update_stats(self, algorithm: str, cost, length, nodes, time_ms):
        self.stats['Algorithm']       = algorithm
        self.stats['Path cost']       = str(cost)
        self.stats['Path length']     = str(length)
        self.stats['Nodes explored']  = str(nodes)
        self.stats['Time (ms)']       = f'{time_ms:.2f}'

    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = '—'

    # ── Sự kiện ────────────────────────────────────────────────────────────

    def handle_hover(self, mouse_pos):
        self.btn_run.update(mouse_pos)
        self.btn_reset.update(mouse_pos)
        for btn in self.map_buttons:
            btn['hovered'] = btn['rect'].collidepoint(mouse_pos)

    def handle_map_click(self, event) -> bool:
        """Trả về True nếu người dùng chọn map mới."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, btn in enumerate(self.map_buttons):
                if btn['rect'].collidepoint(event.pos):
                    if self.selected_map_idx != i:
                        self.selected_map_idx = i
                        self.reset_stats()
                        return True
        return False

    # ── Vẽ ─────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        pygame.draw.rect(surface, PANEL_BG,
                         pygame.Rect(self.x, self.y, self.width, self.height))

        title = self.font_title.render('Select Map', True, TEXT_COLOR)
        surface.blit(title, (self.x + 10, self.y + 16))

        self._draw_map_buttons(surface)
        self.btn_run.draw(surface)
        self.btn_reset.draw(surface)
        self._draw_stats(surface)
        self._draw_legend(surface)

    def _draw_map_buttons(self, surface: pygame.Surface):
        font = pygame.font.SysFont('Arial', 12, bold=True)
        for i, btn in enumerate(self.map_buttons):
            selected = (i == self.selected_map_idx)
            if selected:
                color, border = (40, 120, 200), (100, 180, 255)
            elif btn['hovered']:
                color, border = (70, 90, 120), (120, 150, 190)
            else:
                color, border = (55, 65, 80), (90, 100, 115)

            pygame.draw.rect(surface, color,  btn['rect'], border_radius=5)
            pygame.draw.rect(surface, border, btn['rect'], 1, border_radius=5)

            label = ('✓ ' if selected else '  ') + btn['label']
            text  = font.render(label, True, TEXT_COLOR)
            surface.blit(text, text.get_rect(center=btn['rect'].center))

    def _draw_stats(self, surface: pygame.Surface):
        title = self.font_title.render('Results', True, TEXT_COLOR)
        surface.blit(title, (self.x + 10, self._below_btns_y))

        y_cur = self._below_btns_y + 24
        for key, val in self.stats.items():
            label = self.font_text.render(f'{key}:', True, (180, 180, 180))
            value = self.font_text.render(val, True, TEXT_COLOR)
            surface.blit(label, (self.x + 10, y_cur))
            surface.blit(value, (self.x + 10, y_cur + 16))
            y_cur += 38

    def _draw_legend(self, surface: pygame.Surface):
        from gui.colors import (
            CELL_COLORS, EXPLORED_COLOR, FRONTIER_COLOR, PATH_COLOR
        )
        legend_items = [
            ('Start (P)',  CELL_COLORS['P']),
            ('Goal (G)',   CELL_COLORS['G']),
            ('Wall (W)',   CELL_COLORS['W']),
            ('Empty (E)',  CELL_COLORS['E']),
            ('O ga (O)',   CELL_COLORS['O']),
            ('Goods (T)',  CELL_COLORS['T']),
            ('Explored',   EXPLORED_COLOR),
            ('Frontier',   FRONTIER_COLOR),
            ('Path',       PATH_COLOR),
        ]
        y_cur = self._below_btns_y + 24 + len(self.stats) * 38 + 10
        title = self.font_title.render('Legend', True, TEXT_COLOR)
        surface.blit(title, (self.x + 10, y_cur))
        y_cur += 22
        for label_text, color in legend_items:
            swatch = pygame.Rect(self.x + 10, y_cur + 2, 13, 13)
            pygame.draw.rect(surface, color, swatch)
            pygame.draw.rect(surface, (150, 150, 150), swatch, 1)
            label = self.font_small.render(label_text, True, TEXT_COLOR)
            surface.blit(label, (self.x + 28, y_cur))
            y_cur += 18