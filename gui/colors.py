"""
colors.py
Bảng màu cho từng loại ô và trạng thái hiển thị trong GUI.
Định dạng: (R, G, B)
"""

# ── Màu nền các loại ô ────────────────────────────────────────────────────
CELL_COLORS = {
    'E': (240, 240, 240),   # Empty      — xám nhạt
    'W': (50,  50,  50),    # Wall       — xám đen
    'O': (210, 140,  40),   # Ổ gà       — cam đất
    'T': (100, 200, 100),   # Goods      — xanh lá
    'P': (80,  120, 220),   # Pacman     — xanh dương
    'G': (220,  60,  60),   # Goal       — đỏ
}

# ── Màu trạng thái thuật toán ─────────────────────────────────────────────
EXPLORED_COLOR  = (180, 210, 255)   # Node đã khám phá — xanh nhạt
FRONTIER_COLOR  = (255, 230, 100)   # Frontier          — vàng
PATH_COLOR      = (255,  80,  80)   # Đường đi cuối     — đỏ tươi

# ── Màu khác ──────────────────────────────────────────────────────────────
BACKGROUND      = (30,  30,  30)    # Nền app
GRID_LINE       = (200, 200, 200)   # Đường kẻ ô
TEXT_COLOR      = (255, 255, 255)   # Chữ trắng
TEXT_DARK       = (30,  30,  30)    # Chữ tối (trên nền sáng)
PANEL_BG        = (45,  45,  45)    # Nền panel bên phải
BUTTON_COLOR    = (70,  130, 180)   # Nút bấm — xanh dương
BUTTON_HOVER    = (100, 160, 210)   # Nút hover
BUTTON_TEXT     = (255, 255, 255)   # Chữ trên nút