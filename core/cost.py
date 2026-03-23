 
# Loại ô
CELL_PACMAN   = 'P'   # Vị trí bắt đầu của Pacman
CELL_GOAL     = 'G'   # Đích đến
CELL_WALL     = 'W'   # Tường - không đi được
CELL_EMPTY    = 'E'   # Đường bình thường
CELL_POTHOLE  = 'O'   # Ổ gà
CELL_GOODS    = 'T'   # Hàng hóa cần lấy
 
# Chi phí di chuyển vào từng loại ô
TERRAIN_COST = {
    CELL_EMPTY:   1,
    CELL_POTHOLE: 3,
    CELL_GOAL:    1,
    CELL_GOODS:   1,
    CELL_PACMAN:  1,
    CELL_WALL:    float('inf'),  # Không thể đi qua
}
 
# Các hướng di chuyển: (delta_row, delta_col, tên)
DIRECTIONS = [
    (-1,  0, 'Up'),
    ( 1,  0, 'Down'),
    ( 0, -1, 'Left'),
    ( 0,  1, 'Right'),
]
 
 
def get_cost(cell_type: str) -> float:
    """
    Trả về chi phí khi di chuyển vào ô có loại cell_type.
    Nếu không nhận ra loại ô, trả về inf (an toàn).
    """
    return TERRAIN_COST.get(cell_type, float('inf'))
 
 
def is_passable(cell_type: str) -> bool:
    """Kiểm tra ô có thể đi qua không."""
    return get_cost(cell_type) < float('inf')
 