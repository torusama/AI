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
EXPLORED_COLOR  = (180, 210, 255)   # Node đã khám phá — xanh nhạt (fallback)
FRONTIER_COLOR  = (255, 230, 100)   # Frontier          — vàng (fallback)
PATH_COLOR      = (220,  40,  40)   # Đường đúng        — ĐỎ ĐẬM
PATH_WRONG_COLOR = (220, 160, 160)  # Nhánh sai         — ĐỎ NHẠT

# ── Màu khác ──────────────────────────────────────────────────────────────
BACKGROUND      = (30,  30,  30)    # Nền app
GRID_LINE       = (200, 200, 200)   # Đường kẻ ô
TEXT_COLOR      = (255, 255, 255)   # Chữ trắng
TEXT_DARK       = (30,  30,  30)    # Chữ tối (trên nền sáng)
PANEL_BG        = (45,  45,  45)    # Nền panel bên phải
BUTTON_COLOR    = (70,  130, 180)   # Nút bấm — xanh dương
BUTTON_HOVER    = (100, 160, 210)   # Nút hover
BUTTON_TEXT     = (255, 255, 255)   # Chữ trên nút

# ── Màu nhánh BFS (dùng khi đang animate, trước khi biết đường đúng) ──────
# Mỗi branch_id % len(BRANCH_COLORS) -> màu riêng
BRANCH_COLORS = [
    (120, 180, 255),  # xanh dương nhạt
    (255, 200, 100),  # vàng
    (150, 220, 150),  # xanh lá nhạt
    (220, 150, 255),  # tím nhạt
    (255, 180, 140),  # cam nhạt
    (140, 230, 220),  # teal nhạt
    (255, 160, 200),  # hồng nhạt
    (200, 200, 140),  # vàng xanh nhạt
]
