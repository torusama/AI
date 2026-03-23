import pygame
from gui.colors import (
    PANEL_BG, TEXT_COLOR, TEXT_DARK,
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
    """
    Panel bên phải màn hình.
    Hiển thị: tên thuật toán, stats, chú thích màu, nút Run/Reset.
 
    Attributes:
        x (int): Tọa độ x bắt đầu panel.
        y (int): Tọa độ y bắt đầu panel.
        width (int): Chiều rộng panel.
        height (int): Chiều cao panel.
    """
 
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x      = x
        self.y      = y
        self.width  = width
        self.height = height
 
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Arial', 16, bold=True)
        self.font_text  = pygame.font.SysFont('Arial', 13)
        self.font_small = pygame.font.SysFont('Arial', 11)
 
        # Nút Run và Reset
        btn_w, btn_h = width - 20, 36
        self.btn_run   = Button(pygame.Rect(x + 10, y + 20,  btn_w, btn_h), 'Run')
        self.btn_reset = Button(pygame.Rect(x + 10, y + 64,  btn_w, btn_h), 'Reset')
 
        # Stats hiển thị
        self.stats = {
            'Algorithm':    '—',
            'Path cost':    '—',
            'Path length':  '—',
            'Nodes explored': '—',
            'Time (ms)':    '—',
        }
 
    # ── Cập nhật stats ─────────────────────────────────────────────────────
 
    def update_stats(self, algorithm: str, cost, length, nodes, time_ms):
        self.stats['Algorithm']       = algorithm
        self.stats['Path cost']       = str(cost)
        self.stats['Path length']     = str(length)
        self.stats['Nodes explored']  = str(nodes)
        self.stats['Time (ms)']       = f'{time_ms:.2f}'
 
    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = '—'
 
    # ── Vẽ panel ───────────────────────────────────────────────────────────
 
    def draw(self, surface: pygame.Surface):
        # Nền panel
        panel_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, PANEL_BG, panel_rect)
 
        # Nút
        self.btn_run.draw(surface)
        self.btn_reset.draw(surface)
 
        # Stats
        self._draw_stats(surface)
 
        # Chú thích màu
        self._draw_legend(surface)
 
    def _draw_stats(self, surface: pygame.Surface):
        title = self.font_title.render('Results', True, TEXT_COLOR)
        surface.blit(title, (self.x + 10, self.y + 115))
 
        y_cur = self.y + 140
        for key, val in self.stats.items():
            label = self.font_text.render(f'{key}:', True, (180, 180, 180))
            value = self.font_text.render(val, True, TEXT_COLOR)
            surface.blit(label, (self.x + 10, y_cur))
            surface.blit(value, (self.x + 10, y_cur + 16))
            y_cur += 40
 
    def _draw_legend(self, surface: pygame.Surface):
        from gui.colors import (
            CELL_COLORS, EXPLORED_COLOR, FRONTIER_COLOR, PATH_COLOR
        )
 
        legend_items = [
            ('Start (P)',   CELL_COLORS['P']),
            ('Goal (G)',    CELL_COLORS['G']),
            ('Wall (W)',    CELL_COLORS['W']),
            ('Empty (E)',   CELL_COLORS['E']),
            ('Ổ gà (O)',    CELL_COLORS['O']),
            ('Goods (T)',   CELL_COLORS['T']),
            ('Explored',    EXPLORED_COLOR),
            ('Frontier',    FRONTIER_COLOR),
            ('Path',        PATH_COLOR),
        ]
 
        title = self.font_title.render('Legend', True, TEXT_COLOR)
        y_cur = self.y + 360
        surface.blit(title, (self.x + 10, y_cur))
        y_cur += 24
 
        for label_text, color in legend_items:
            # Ô màu nhỏ
            swatch = pygame.Rect(self.x + 10, y_cur + 2, 14, 14)
            pygame.draw.rect(surface, color, swatch)
            pygame.draw.rect(surface, (150, 150, 150), swatch, 1)
            # Nhãn
            label = self.font_small.render(label_text, True, TEXT_COLOR)
            surface.blit(label, (self.x + 30, y_cur))
            y_cur += 20
 
    # ── Xử lý sự kiện ──────────────────────────────────────────────────────
 
    def handle_hover(self, mouse_pos):
        self.btn_run.update(mouse_pos)
        self.btn_reset.update(mouse_pos)