"""
sound_manager.py
Quản lý toàn bộ âm thanh: nhạc nền loop tuần tự + sound effects.
"""

import os
import pygame

# ── Cấu hình ──────────────────────────────────────────────────────────────────
MUSIC_VOLUME   = 0.30   # âm lượng nhạc nền mặc định (0.0 – 1.0)
SFX_VOLUME     = 0.70   # âm lượng SFX mặc định

MUSIC_PLAYLIST = ['song1.mp3', 'song2.mp3']   # tuần tự, loop mãi

# Custom pygame event để biết khi nhạc kết thúc
MUSIC_END_EVENT = pygame.USEREVENT + 1


class SoundManager:
    """Singleton-style manager; tạo 1 lần, dùng toàn app."""

    def __init__(self, base_dir: str):
        self.base_dir      = base_dir
        self._music_idx    = 0
        self._volume       = MUSIC_VOLUME   # 0.0 – 1.0, được lưu để volume-slider dùng
        self._sfx: dict[str, pygame.mixer.Sound] = {}
        self._music_ready  = False

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except Exception:
                return

        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
        self._load_sfx()
        self._start_playlist()

    # ── Private ───────────────────────────────────────────────────────────────

    def _snd(self, name: str) -> str:
        return os.path.join(self.base_dir, 'sound', name)

    def _load_sfx(self):
        sfx_files = {
            'click': 'click sound.MP3',
            'goal':  'goal.MP3',
            'panel': 'panel.MP3',
        }
        for key, fname in sfx_files.items():
            path = self._snd(fname)
            if os.path.exists(path):
                try:
                    s = pygame.mixer.Sound(path)
                    s.set_volume(SFX_VOLUME)
                    self._sfx[key] = s
                except Exception:
                    pass

    def _start_playlist(self):
        path = self._snd(MUSIC_PLAYLIST[self._music_idx])
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            self._music_ready = True
        except Exception:
            pass

    def _next_track(self):
        self._music_idx = (self._music_idx + 1) % len(MUSIC_PLAYLIST)
        self._start_playlist()

    # ── Public API ────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event):
        """Gọi trong event loop chính để bắt sự kiện hết bài."""
        if event.type == MUSIC_END_EVENT:
            self._next_track()

    def play(self, key: str):
        """Phát sound effect theo key: 'click' | 'goal' | 'panel'."""
        if key in self._sfx:
            self._sfx[key].play()

    # ── Volume ────────────────────────────────────────────────────────────────

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, val: float):
        self._volume = max(0.0, min(1.0, val))
        if self._music_ready:
            pygame.mixer.music.set_volume(self._volume)


# ── Volume Slider Widget ──────────────────────────────────────────────────────

class VolumeButton:
    """
    Nút nhỏ ở góc trái dưới Screen 1.
    Click mở/đóng thanh slider dọc.
    Kéo slider để chỉnh âm lượng nhạc nền.
    """

    _SLIDER_W   = 36
    _SLIDER_H   = 160
    _KNOB_R     = 11
    _BTN_SIZE   = 48

    def __init__(self, base_dir: str, sound_manager: SoundManager,
                 screen_w: int, screen_h: int):
        self.sm      = sound_manager
        self._open   = False
        self._drag   = False

        # Vị trí nút: góc trái dưới
        margin = 14
        sz = self._BTN_SIZE
        self._btn_rect = pygame.Rect(margin, screen_h - sz - margin, sz, sz)

        # Slider hiện ra phía trên nút
        sw = self._SLIDER_W
        sh = self._SLIDER_H
        cx = self._btn_rect.centerx
        self._slider_rect = pygame.Rect(cx - sw // 2,
                                        self._btn_rect.top - sh - 10,
                                        sw, sh)

        # Load icon — giữ đúng tỉ lệ ảnh gốc, fit trong vùng (sz-8) x (sz-8)
        icon_path = os.path.join(base_dir, 'picture', 'sound.png')
        if os.path.exists(icon_path):
            img = pygame.image.load(icon_path).convert_alpha()
            iw, ih = img.get_size()
            max_side = sz - 8
            scale = min(max_side / iw, max_side / ih)
            self._icon = pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))
        else:
            self._icon = None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _knob_y(self) -> int:
        """Y tâm knob theo volume (top = max, bottom = min)."""
        r  = self._KNOB_R
        top    = self._slider_rect.top + r + 4
        bottom = self._slider_rect.bottom - r - 4
        return int(bottom - self.sm.volume * (bottom - top))

    def _vol_from_y(self, y: int) -> float:
        r      = self._KNOB_R
        top    = self._slider_rect.top + r + 4
        bottom = self._slider_rect.bottom - r - 4
        return max(0.0, min(1.0, (bottom - y) / max(1, bottom - top)))

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Trả về True nếu event đã được consume (không truyền xuống nữa).
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._btn_rect.collidepoint(event.pos):
                self._open = not self._open
                return True
            if self._open:
                knob_y = self._knob_y()
                cx     = self._slider_rect.centerx
                knob_hit = ((event.pos[0] - cx) ** 2 +
                            (event.pos[1] - knob_y) ** 2) <= (self._KNOB_R + 4) ** 2
                if knob_hit or self._slider_rect.collidepoint(event.pos):
                    self._drag = True
                    self.sm.volume = self._vol_from_y(event.pos[1])
                    return True
                # Click ngoài slider → đóng
                self._open = False

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._drag:
                self._drag = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self._drag:
                self.sm.volume = self._vol_from_y(event.pos[1])
                return True

        return False

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        # ── Nút icon ──────────────────────────────────────────────────────────
        hov = self._btn_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = (0, 120, 200, 200) if not hov else (0, 160, 240, 220)

        # Nền tròn bán trong suốt
        btn_surf = pygame.Surface((self._BTN_SIZE, self._BTN_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(btn_surf, btn_color,
                           (self._BTN_SIZE // 2, self._BTN_SIZE // 2),
                           self._BTN_SIZE // 2)
        pygame.draw.circle(btn_surf, (255, 255, 255, 80),
                           (self._BTN_SIZE // 2, self._BTN_SIZE // 2),
                           self._BTN_SIZE // 2, 2)
        surface.blit(btn_surf, self._btn_rect.topleft)

        if self._icon:
            ir = self._icon.get_rect(center=self._btn_rect.center)
            surface.blit(self._icon, ir)
        else:
            # Fallback: vẽ ký hiệu loa đơn giản bằng polygon
            cx, cy = self._btn_rect.center
            s = 10
            # Hình chữ nhật loa
            pygame.draw.rect(surface, (255, 255, 255),
                             (cx - s, cy - s // 2, s, s))
            # Tam giác loa
            pts = [(cx, cy - s), (cx + s + 2, cy - s * 2), (cx + s + 2, cy + s)]
            pygame.draw.polygon(surface, (255, 255, 255), pts)

        if not self._open:
            return

        # ── Slider panel ──────────────────────────────────────────────────────
        sr   = self._slider_rect
        panel_surf = pygame.Surface((sr.width + 16, sr.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (0, 20, 60, 200),
                         panel_surf.get_rect(), border_radius=12)
        pygame.draw.rect(panel_surf, (255, 255, 255, 60),
                         panel_surf.get_rect(), width=1, border_radius=12)
        surface.blit(panel_surf, (sr.x - 8, sr.y - 8))

        # Track dọc
        cx_s   = sr.centerx
        top_y  = sr.top + self._KNOB_R + 4
        bot_y  = sr.bottom - self._KNOB_R - 4
        pygame.draw.line(surface, (180, 220, 255, 120), (cx_s, top_y), (cx_s, bot_y), 3)

        # Fill phần đã chọn (dưới knob → bottom = 0 volume)
        ky = self._knob_y()
        if ky < bot_y:
            pygame.draw.line(surface, (0, 200, 255), (cx_s, ky), (cx_s, bot_y), 4)

        # Knob
        pygame.draw.circle(surface, (255, 255, 255), (cx_s, ky), self._KNOB_R)
        pygame.draw.circle(surface, (0, 160, 240), (cx_s, ky), self._KNOB_R - 3)