from __future__ import annotations

import math
from enum import Enum
from typing import Iterable, Optional, Tuple

import pygame

__version__ = "1.4"
__all__ = [
    "V",
    "Key",
    "Font",
    "Color",
    "Image",
    "Sound",
    "Origin",
    "Resizable",
    "Window",
    "__version__",
]


class V:

    def __init__(self, x: float, y: float):
        self.x: float = float(x)
        self.y: float = float(y)

    def __add__(self, other: V) -> V:
        return V(self.x + other.x, self.y + other.y)

    def __sub__(self, other: V) -> V:
        return V(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> V:
        return V(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> V:
        if scalar == 0:
            raise ZeroDivisionError("division by zero")
        return V(self.x / scalar, self.y / scalar)

    def __rmul__(self, scalar: float) -> V:
        return self.__mul__(scalar)

    def length(self) -> float:
        return (self.x * self.x + self.y * self.y) ** 0.5

    def normalized(self) -> V:
        length = self.length()
        if length == 0:
            return V(0, 0)
        return self / length

    def dot_to(self, other: V) -> float:
        return self.x * other.x + self.y * other.y

    @staticmethod
    def dot(a: V, b: V) -> float:
        return a.dot_to(b)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, V):
            return False
        try:
            return math.isclose(
                self.x, other.x, rel_tol=1e-09, abs_tol=1e-09
            ) and math.isclose(self.y, other.y, rel_tol=1e-09, abs_tol=1e-09)
        except Exception:
            return self.x == other.x and self.y == other.y

    def __repr__(self) -> str:
        return f"V({self.x}, {self.y})"

    def distance_to(self, other: V) -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @staticmethod
    def distance(a: V, b: V) -> float:
        return a.distance_to(b)


class Key(Enum):
    A = pygame.K_a
    B = pygame.K_b
    C = pygame.K_c
    D = pygame.K_d
    E = pygame.K_e
    F = pygame.K_f
    G = pygame.K_g
    H = pygame.K_h
    I = pygame.K_i
    J = pygame.K_j
    K = pygame.K_k
    L = pygame.K_l
    M = pygame.K_m
    N = pygame.K_n
    O = pygame.K_o
    P = pygame.K_p
    Q = pygame.K_q
    R = pygame.K_r
    S = pygame.K_s
    T = pygame.K_t
    U = pygame.K_u
    V = pygame.K_v
    W = pygame.K_w
    X = pygame.K_x
    Y = pygame.K_y
    Z = pygame.K_z
    NUM_0 = pygame.K_0
    NUM_1 = pygame.K_1
    NUM_2 = pygame.K_2
    NUM_3 = pygame.K_3
    NUM_4 = pygame.K_4
    NUM_5 = pygame.K_5
    NUM_6 = pygame.K_6
    NUM_7 = pygame.K_7
    NUM_8 = pygame.K_8
    NUM_9 = pygame.K_9
    F1 = pygame.K_F1
    F2 = pygame.K_F2
    F3 = pygame.K_F3
    F4 = pygame.K_F4
    F5 = pygame.K_F5
    F6 = pygame.K_F6
    F7 = pygame.K_F7
    F8 = pygame.K_F8
    F9 = pygame.K_F9
    F10 = pygame.K_F10
    F11 = pygame.K_F11
    F12 = pygame.K_F12
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    LSHIFT = pygame.K_LSHIFT
    RSHIFT = pygame.K_RSHIFT
    LCTRL = pygame.K_LCTRL
    RCTRL = pygame.K_RCTRL
    LALT = pygame.K_LALT
    RALT = pygame.K_RALT
    LSUPER = pygame.K_LSUPER
    RSUPER = pygame.K_RSUPER
    SPACE = pygame.K_SPACE
    RETURN = pygame.K_RETURN
    ENTER = pygame.K_RETURN
    ESCAPE = pygame.K_ESCAPE
    TAB = pygame.K_TAB
    BACKSPACE = pygame.K_BACKSPACE
    CAPSLOCK = pygame.K_CAPSLOCK
    INSERT = pygame.K_INSERT
    DELETE = pygame.K_DELETE
    HOME = pygame.K_HOME
    END = pygame.K_END
    PAGEUP = pygame.K_PAGEUP
    PAGEDOWN = pygame.K_PAGEDOWN
    MINUS = pygame.K_MINUS
    EQUALS = pygame.K_EQUALS
    LEFTBRACKET = pygame.K_LEFTBRACKET
    RIGHTBRACKET = pygame.K_RIGHTBRACKET
    BACKSLASH = pygame.K_BACKSLASH
    SEMICOLON = pygame.K_SEMICOLON
    APOSTROPHE = pygame.K_QUOTE
    GRAVE = pygame.K_BACKQUOTE
    COMMA = pygame.K_COMMA
    PERIOD = pygame.K_PERIOD
    SLASH = pygame.K_SLASH
    KP0 = pygame.K_KP0
    KP1 = pygame.K_KP1
    KP2 = pygame.K_KP2
    KP3 = pygame.K_KP3
    KP4 = pygame.K_KP4
    KP5 = pygame.K_KP5
    KP6 = pygame.K_KP6
    KP7 = pygame.K_KP7
    KP8 = pygame.K_KP8
    KP9 = pygame.K_KP9
    KP_PERIOD = pygame.K_KP_PERIOD
    KP_DIVIDE = pygame.K_KP_DIVIDE
    KP_MULTIPLY = pygame.K_KP_MULTIPLY
    KP_MINUS = pygame.K_KP_MINUS
    KP_PLUS = pygame.K_KP_PLUS
    KP_ENTER = pygame.K_KP_ENTER
    KP_EQUALS = pygame.K_KP_EQUALS


class Font:

    def __init__(self, file: str = None, size: int = 24):
        pygame.font.init()
        self.size = size
        self.file = file
        try:
            if file:
                self.font = pygame.font.Font(file, int(size))
            else:
                self.font = pygame.font.SysFont(None, int(size))
        except Exception:
            self.font = pygame.font.Font(pygame.font.get_default_font(), int(size))

    def set_size(self, size: int):
        self.size = size
        if self.file:
            self.font = pygame.font.Font(self.file, int(size))
        else:
            self.font = pygame.font.SysFont(None, int(size))

    def new_size(self, size: int):
        return Font(self.file, int(size))


class Color:

    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.r = max(0, min(255, int(r)))
        self.g = max(0, min(255, int(g)))
        self.b = max(0, min(255, int(b)))
        self.a = max(0, min(255, int(a)))

    def to_tuple(self):
        return (self.r, self.g, self.b, self.a)

    def rgb_tuple(self):
        return (self.r, self.g, self.b)

    def mix(self, other: "Color", factor: float = 0.5):
        factor = max(0.0, min(1.0, factor))
        r = int(round(self.r * (1 - factor) + other.r * factor))
        g = int(round(self.g * (1 - factor) + other.g * factor))
        b = int(round(self.b * (1 - factor) + other.b * factor))
        a = int(round(self.a * (1 - factor) + other.a * factor))
        return Color(r, g, b, a)

    def __repr__(self) -> str:
        return f"Color({self.r}, {self.g}, {self.b}, {self.a})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return False
        return (
                self.r == other.r
                and self.g == other.g
                and (self.b == other.b)
                and (self.a == other.a)
        )


class Image:

    def __init__(self, path: str):
        try:
            loaded = pygame.image.load(path)
            if loaded.get_alpha() or loaded.get_flags() & pygame.SRCALPHA:
                self.surface = loaded.convert_alpha()
            else:
                self.surface = loaded.convert()
        except Exception:
            self.surface = pygame.Surface((1, 1), pygame.SRCALPHA)
            self.surface.fill((0, 0, 0, 0))

    def get_width(self):
        return self.surface.get_width()

    def get_height(self):
        return self.surface.get_height()


class Sound:

    def __init__(self, path: str):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.sound = pygame.mixer.Sound(path)
        except Exception:
            self.sound = None

    def play(self):
        if self.sound:
            try:
                self.sound.play()
            except Exception:
                pass

    def stop(self):
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass

    def get_volume(self):
        if self.sound:
            try:
                return self.sound.get_volume()
            except Exception:
                return None
        else:
            return None

    def set_volume(self, volume: float):
        if self.sound:
            try:
                self.sound.set_volume(volume)
            except Exception:
                pass

    def get_length(self):
        if self.sound:
            try:
                return self.sound.get_length()
            except Exception:
                return None
        else:
            return None


class Origin(Enum):
    CENTER = (0, 0)
    TOP = (0, 1)
    BOTTOM = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    TOP_LEFT = (-1, 1)
    TOP_RIGHT = (1, 1)
    BOTTOM_LEFT = (-1, -1)
    BOTTOM_RIGHT = (1, -1)


class Resizable(Enum):
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    BOTH = "both"
    ASPECT = "aspect"


class Window:

    def __init__(
            self,
            width: int = 800,
            height: int = 600,
            title: str = "PGIUD Window",
            resizable: Resizable = Resizable.NONE,
            origin: Origin = Origin.BOTTOM_LEFT,
    ):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self._width, self._height = (width, height)
        self._title = title
        self._flags = pygame.RESIZABLE if resizable != Resizable.NONE else 0
        self._screen = pygame.display.set_mode((width, height), self._flags)
        pygame.display.set_caption(title)
        self._origin = origin
        self._resizable = resizable
        self._original_width = width
        self._original_height = height
        self._clock = pygame.time.Clock()
        self._running = False
        self._mouse_x = 0
        self._mouse_y = 0
        # Per-frame scroll delta (x = horizontal, y = vertical). Reset each frame in start().
        self._scroll_x = 0
        self._scroll_y = 0
        self._deltatime = 0.0
        self._fonts = {}
        self._mouse_down_primary = False
        self._mouse_down_middle = False
        self._mouse_down_secondary = False

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @width.setter
    def width(self, value: int):
        self._width = value

    @height.setter
    def height(self, value: int):
        self._height = value

    @property
    def mouse_pos(self):
        return V(self._mouse_x, self._mouse_y)

    @property
    def mouse_scroll(self):
        """Returns a V(x, y) with the scroll delta for the current frame.

        Vertical scroll is positive when scrolling up (wheel up / wheel away from user)
        and negative when scrolling down. Horizontal scroll follows event.x.
        """
        return V(self._scroll_x, self._scroll_y)

    @property
    def mouse_scroll_x(self):
        return self._scroll_x

    @property
    def mouse_scroll_y(self):
        return self._scroll_y

    @property
    def mouse_down_primary(self):
        return self._mouse_down_primary

    @property
    def mouse_down_middle(self):
        return self._mouse_down_middle

    @property
    def mouse_down_secondary(self):
        return self._mouse_down_secondary

    @property
    def deltatime(self):
        return self._deltatime

    def keydown(self, key: Key):
        pressed = pygame.key.get_pressed()
        return bool(pressed[key.value])

    def screen_position(self, origin: Origin):
        cx, cy = (self._width // 2, self._height // 2)
        ox, oy = origin.value
        px = cx + ox * (self.width // 2)
        py = cy - oy * (self.height // 2)
        return V(*self._pg_to_iud(px, py))

    @property
    def screen_center(self):
        return self.screen_position(Origin.CENTER)

    @property
    def screen_top(self):
        return self.screen_position(Origin.TOP)

    @property
    def screen_bottom(self):
        return self.screen_position(Origin.BOTTOM)

    @property
    def screen_left(self):
        return self.screen_position(Origin.LEFT)

    @property
    def screen_right(self):
        return self.screen_position(Origin.RIGHT)

    @property
    def screen_top_left(self):
        return self.screen_position(Origin.TOP_LEFT)

    @property
    def screen_top_right(self):
        return self.screen_position(Origin.TOP_RIGHT)

    @property
    def screen_bottom_left(self):
        return self.screen_position(Origin.BOTTOM_LEFT)

    @property
    def screen_bottom_right(self):
        return self.screen_position(Origin.BOTTOM_RIGHT)

    def _pg_to_iud(self, x: int, y: int):
        ox, oy = self._origin.value
        cx = self.width // 2 if ox == 0 else 0 if ox == -1 else self.width
        cy = self.height // 2 if oy == 0 else 0 if oy == -1 else self.height
        new_x = x - cx
        new_y = self.height - y - cy
        return (new_x, new_y)

    def _iud_to_pg(self, x: int, y: int):
        ox, oy = self._origin.value
        cx = self.width // 2 if ox == 0 else 0 if ox == -1 else self.width
        cy = self.height // 2 if oy == 0 else 0 if oy == -1 else self.height
        new_x = x + cx
        new_y = self.height - (y + cy)
        return (new_x, new_y)

    def _handle_resize(self, w, h):
        if self._resizable == Resizable.NONE:
            return
        elif self._resizable == Resizable.WIDTH:
            h = self.height
        elif self._resizable == Resizable.HEIGHT:
            w = self.width
        elif self._resizable == Resizable.ASPECT:
            ratio = (
                self._original_width / self._original_height
                if self._original_height != 0
                else 1
            )
            if w / h > ratio:
                w = int(h * ratio)
            else:
                h = int(w / ratio)
        self.width, self.height = (w, h)
        self._screen = pygame.display.set_mode((w, h), self._flags)

    def start(self):
        self._running = True
        self.initialize()
        while self._running:
            self._deltatime = self._clock.tick(60) / 1000.0
            # reset per-frame scroll deltas
            self._scroll_x = 0
            self._scroll_y = 0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.on_quit()
                    self._running = False
                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                    self.on_resize(event.w, event.h)
                elif event.type == pygame.MOUSEWHEEL:
                    # pygame 2 MOUSEWHEEL event (attributes: x, y)
                    try:
                        self._scroll_x += getattr(event, "x", 0)
                        self._scroll_y += getattr(event, "y", 0)
                    except Exception:
                        pass
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._mouse_down_primary = True
                    elif event.button == 2:
                        self._mouse_down_middle = True
                    elif event.button == 3:
                        self._mouse_down_secondary = True
                    elif event.button == 4:
                        # legacy wheel up
                        self._scroll_y += 1
                    elif event.button == 5:
                        # legacy wheel down
                        self._scroll_y -= 1
                    elif event.button == 6:
                        # legacy wheel left
                        self._scroll_x -= 1
                    elif event.button == 7:
                        # legacy wheel right
                        self._scroll_x += 1
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self._mouse_down_primary = False
                    elif event.button == 2:
                        self._mouse_down_middle = False
                    elif event.button == 3:
                        self._mouse_down_secondary = False
            self._mouse_x, self._mouse_y = self._pg_to_iud(*pygame.mouse.get_pos())
            # If any scroll happened this frame, notify and leave deltas available
            if self._scroll_x != 0 or self._scroll_y != 0:
                try:
                    self.on_scroll(self._scroll_x, self._scroll_y)
                except Exception:
                    pass
            self.update()
            self.draw()
            pygame.display.flip()

    def on_scroll(self, dx: int, dy: int):
        """Called when scrolling occurs during a frame.

        dx: horizontal scroll delta (positive = right)
        dy: vertical scroll delta (positive = up)

        Override this in subclasses to react to scroll input. The per-frame
        deltas remain available via the `mouse_scroll`, `mouse_scroll_x` and
        `mouse_scroll_y` properties until `reset_scroll()` is called or the next
        frame starts (the window resets scroll deltas at the start of each
        frame).
        """
        pass

    def reset_scroll(self):
        """Reset accumulated scroll deltas to zero for the current frame."""
        self._scroll_x = 0
        self._scroll_y = 0

    def toggle_fullscreen(self):
        """Toggles fullscreen mode."""
        pygame.display.toggle_fullscreen()

    def initialize(self):
        """Called once when the window is initialized."""
        pass

    def update(self):
        """Called every frame to update the window's state."""
        pass

    def draw(self):
        """Called every frame to draw the window's contents."""
        pass

    def on_quit(self):
        """Called when the window is closed."""
        pass

    def on_resize(self, width, height):
        """Called when the window is resized."""
        pass

    def clear(self, color: "Color"):
        """Clear the screen to the given color."""
        self._screen.fill(color.rgb_tuple() if color.a == 255 else color.to_tuple())

    def fill_rect(
            self,
            a: V,
            b: V,
            color: "Color",
            outline_thickness: int = 0,
            outline_color: "Color" = None,
    ):
        """Draw a filled rectangle from a to b in IUD coordinates."""
        outline_thickness = int(outline_thickness)
        ax, ay = a.to_tuple()
        bx, by = b.to_tuple()
        ax, ay = self._iud_to_pg(int(ax), int(ay))
        bx, by = self._iud_to_pg(int(bx), int(by))
        width = bx - ax
        height = by - ay
        x = ax
        y = ay
        if width < 0:
            x += width
            width = -width
        if height < 0:
            y += height
            height = -height
        rect = pygame.Rect(x, y, width, height)
        if color.a == 255:
            pygame.draw.rect(self._screen, color.rgb_tuple(), rect)
        else:
            temp = pygame.Surface((width, height), pygame.SRCALPHA)
            temp.fill(color.to_tuple())
            self._screen.blit(temp, (x, y))
        if outline_thickness > 0 and outline_color:
            col = (
                outline_color.rgb_tuple()
                if outline_color.a == 255
                else outline_color.to_tuple()
            )
            pygame.draw.rect(self._screen, col, rect, outline_thickness)

    def fill_rounded_rect(
            self,
            a: V,
            b: V,
            color: Color,
            outline_thickness: int = 0,
            outline_color: Color = None,
            top_left_roundness: float = 0.0,
            top_right_roundness: float = 0.0,
            bottom_left_roundness: float = 0.0,
            bottom_right_roundness: float = 0.0,
            steps: int = 10,
    ):
        """Draw a filled rounded rectangle with optional outline."""
        ax, ay = a.to_tuple()
        bx, by = b.to_tuple()
        left, right = (min(ax, bx), max(ax, bx))
        bottom, top = (min(ay, by), max(ay, by))
        w = right - left
        h = top - bottom
        outline_thickness = int(outline_thickness)
        steps = max(1, int(steps))
        max_radius = min(w, h) / 2 if w > 0 and h > 0 else 0
        tl = int(max(0, min(max_radius, top_left_roundness)))
        tr = int(max(0, min(max_radius, top_right_roundness)))
        bl = int(max(0, min(max_radius, bottom_left_roundness)))
        br = int(max(0, min(max_radius, bottom_right_roundness)))

        def arc(cx, cy, r, start_angle, end_angle):
            pts = []
            for i in range(steps + 1):
                t = i / steps
                theta = start_angle + (end_angle - start_angle) * t
                pts.append((cx + r * math.cos(theta), cy + r * math.sin(theta)))
            return pts

        points = []
        if tl > 0:
            points.append((left + tl, top))
        else:
            points.append((left, top))
        if tr > 0:
            points.append((right - tr, top))
            points.extend(arc(right - tr, top - tr, tr, math.pi / 2, 0)[1:])
        else:
            points.append((right, top))
        if br > 0:
            points.append((right, bottom + br))
            points.extend(arc(right - br, bottom + br, br, 0, -math.pi / 2)[1:])
        else:
            points.append((right, bottom))
        if bl > 0:
            points.append((left + bl, bottom))
            points.extend(arc(left + bl, bottom + bl, bl, -math.pi / 2, -math.pi)[1:])
        else:
            points.append((left, bottom))
        if tl > 0:
            points.append((left, top - tl))
            points.extend(arc(left + tl, top - tl, tl, math.pi, math.pi / 2)[1:])
        if len(points) < 3:
            return
        self.fill_polygon(points, color, outline_thickness, outline_color)

    def draw_line(self, a: V, b: V, color: "Color", width: int = 1):
        """Draw a line from (ax, ay) to (bx, by) in IUD coordinates."""
        ax, ay = a.to_tuple()
        bx, by = b.to_tuple()
        ax, ay = self._iud_to_pg(int(ax), int(ay))
        bx, by = self._iud_to_pg(int(bx), int(by))
        if color.a == 255:
            pygame.draw.line(self._screen, color.rgb_tuple(), (ax, ay), (bx, by), width)
        else:
            min_x = min(ax, bx) - width
            min_y = min(ay, by) - width
            max_x = max(ax, bx) + width
            max_y = max(ay, by) + width
            tw = max(1, max_x - min_x)
            th = max(1, max_y - min_y)
            temp = pygame.Surface((tw, th), pygame.SRCALPHA)
            sax, say = (ax - min_x, ay - min_y)
            sbx, sby = (bx - min_x, by - min_y)
            pygame.draw.line(temp, color.to_tuple(), (sax, say), (sbx, sby), width)
            self._screen.blit(temp, (min_x, min_y))

    def fill_polygon(
            self,
            points: Iterable[Tuple[float, float]],
            color: "Color",
            outline_thickness: int = 0,
            outline_color: "Color" = None,
    ):
        """Draw a filled polygon. Points should be an iterable of (x, y) pairs."""
        pg_points = [self._iud_to_pg(int(round(x)), int(round(y))) for x, y in points]
        if color.a == 255:
            try:
                pygame.draw.polygon(self._screen, color.rgb_tuple(), pg_points)
            except Exception:
                return
        else:
            min_x = min((p[0] for p in pg_points))
            min_y = min((p[1] for p in pg_points))
            max_x = max((p[0] for p in pg_points))
            max_y = max((p[1] for p in pg_points))
            width = max_x - min_x
            height = max_y - min_y
            if width <= 0 or height <= 0:
                return
            tw = max(1, int(round(width)))
            th = max(1, int(round(height)))
            temp = pygame.Surface((tw, th), pygame.SRCALPHA)
            shifted = [
                (int(round(x - min_x)), int(round(y - min_y))) for x, y in pg_points
            ]
            try:
                pygame.draw.polygon(temp, color.to_tuple(), shifted)
                self._screen.blit(temp, (min_x, min_y))
            except Exception:
                return
        if outline_thickness > 0 and outline_color is not None:
            try:
                pygame.draw.polygon(
                    self._screen,
                    outline_color.rgb_tuple(),
                    pg_points,
                    outline_thickness,
                )
            except Exception:
                pass

    def fill_circle(
            self,
            center: V,
            radius: float,
            color: "Color",
            outline_thickness: int = 0,
            outline_color: "Color" = None,
    ):
        """Draw a filled circle at center with the given radius in IUD coordinates."""
        cx, cy = center.to_tuple()
        px, py = self._iud_to_pg(int(cx), int(cy))
        r = max(0, int(round(radius)))
        if r <= 0:
            return
        if color.a == 255:
            pygame.draw.circle(self._screen, color.rgb_tuple(), (px, py), r)
        else:
            diameter = r * 2
            temp = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(temp, color.to_tuple(), (r, r), r)
            self._screen.blit(temp, (px - r, py - r))
        if outline_thickness > 0 and outline_color is not None:
            col = (
                outline_color.rgb_tuple()
                if outline_color.a == 255
                else outline_color.to_tuple()
            )
            pygame.draw.circle(self._screen, col, (px, py), r, outline_thickness)

    def draw_image(
            self,
            image: "Image",
            pos: V,
            origin: Origin = Origin.BOTTOM_LEFT,
            image_filter: Optional["Color"] = None,
            scale_x: float = 1.0,
            scale_y: float = 1.0,
            rotation: int = 0,
            antialiasing: bool = True,
    ):
        """Draw an image at (x, y) in IUD coordinates.

        Optional:
          - filter: a `Color` to tint/multiply the image with (None = no tint)
          - scale_x, scale_y: scaling factors (scale_y defaults to scalex)
          - rotation: rotation angle in degrees (clockwise)
          - antialiasing: whether to use smooth scaling when available
        """
        x, y = pos.to_tuple()
        px, py = self._iud_to_pg(int(x), int(y))
        ox, oy = origin.value
        oy *= -1
        surf = getattr(image, "surface", None)
        if surf is None:
            return
        if scale_y is None:
            scale_y = scale_x
        try:
            if scale_x != 1.0 or scale_y != 1.0:
                new_w = max(1, int(round(image.get_width() * scale_x)))
                new_h = max(1, int(round(image.get_height() * scale_y)))
                if antialiasing and hasattr(pygame.transform, "smoothscale"):
                    surf = pygame.transform.smoothscale(surf, (new_w, new_h))
                else:
                    surf = pygame.transform.scale(surf, (new_w, new_h))
        except Exception:
            surf = image.surface
        if rotation != 0:
            surf = pygame.transform.rotate(surf, -rotation)
        if image_filter is not None:
            try:
                surf = surf.copy()
                tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                tint.fill(image_filter.to_tuple())
                surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception:
                pass
        px -= surf.get_width() // 2
        py -= surf.get_height() // 2
        px -= ox * surf.get_width() // 2
        py -= oy * surf.get_height() // 2
        self._screen.blit(surf, (px, py))

    def draw_text(
            self,
            text: str,
            pos: V,
            font: "Font",
            color: "Color",
            origin: Origin = Origin.BOTTOM_LEFT,
    ):
        """Draw text at (x, y) in IUD coordinates. `origin` specifies the text anchor.

        Supports manual line breaks via \\n. Only Y changes between lines;
        X and origin/anchor stay fixed per line.
        """
        x, y = pos.to_tuple()
        lines = text.split("\n")
        if not lines:
            return
        rendered = []
        default_h = 0
        for ln in lines:
            render_text = ln if ln != "" else " "
            surf = font.font.render(render_text, True, color.rgb_tuple())
            try:
                surf = surf.convert_alpha()
            except Exception:
                try:
                    surf = surf.convert()
                except Exception:
                    pass
            w = surf.get_width()
            h = surf.get_height()
            rendered.append((surf, w, h))
            if h > default_h:
                default_h = h
        total_h = default_h * len(rendered)
        oy_val = origin.value[1]
        block_top_y = y + total_h // 2 - oy_val * total_h // 2
        for i, (surf, w, h) in enumerate(rendered):
            line_y = block_top_y - i * default_h
            px, py = self._iud_to_pg(int(x), int(line_y))
            oxv = origin.value[0]
            px -= w // 2 + oxv * w // 2
            if color.a != 255:
                try:
                    surf.set_alpha(color.a)
                except Exception:
                    pass
            self._screen.blit(surf, (px, py))

    def draw_text_word_wrap(
            self,
            text: str,
            pos: V,
            font: "Font",
            color: "Color",
            origin: Origin = Origin.BOTTOM_LEFT,
            wrap_distance: Optional[int] = None,
            line_height: Optional[int] = None,
            anchor_first_line: bool = False,
            max_lines: Optional[int] = None,
            max_line_ending: Optional[str] = None,
    ):
        """Draw word-wrapped text at (x, y) in IUD coordinates.

        Only Y changes between lines; X and origin/anchor stay fixed per line.

        If `wrap_distance` is provided (positive integer, in pixels) the text will be
        word-wrapped to fit within that pixel width. Newlines are accepted as
        explicit line breaks.
        If `line_height` is provided, it overrides the default font line height.
        If `anchor_first_line` is True, pos anchors the first line and subsequent
        lines extend downward. If False, pos and origin anchor the full text block.
        If `max_lines` is set, output is capped and `max_line_ending` is appended
        to the last visible line when truncated.
        """
        x, y = pos.to_tuple()
        lines = []
        if wrap_distance is not None and wrap_distance > 0:
            paragraphs = text.split("\n")
            for para in paragraphs:
                if para == "":
                    lines.append("")
                    continue
                words = para.split(" ")
                cur = ""
                for w in words:
                    candidate = w if cur == "" else cur + " " + w
                    try:
                        cand_w = font.font.size(candidate)[0]
                    except Exception:
                        cand_w = 0
                    if cand_w <= wrap_distance:
                        cur = candidate
                    else:
                        if cur != "":
                            lines.append(cur)
                        try:
                            word_w = font.font.size(w)[0]
                        except Exception:
                            word_w = 0
                        if word_w <= wrap_distance:
                            cur = w
                        else:
                            part = ""
                            for ch in w:
                                cand2 = part + ch
                                try:
                                    cand2_w = font.font.size(cand2)[0]
                                except Exception:
                                    cand2_w = 0
                                if cand2_w <= wrap_distance:
                                    part = cand2
                                else:
                                    if part != "":
                                        lines.append(part)
                                    part = ch
                            cur = part
                if cur != "":
                    lines.append(cur)
        else:
            lines = text.split("\n")
        if not lines:
            return
        truncated = False
        if max_lines is not None and len(lines) > max_lines:
            lines = lines[:max_lines]
            truncated = True
        if truncated and max_line_ending is not None and lines:
            if wrap_distance is not None and wrap_distance > 0:
                last = lines[-1]
                while last:
                    try:
                        candidate_w = font.font.size(last + max_line_ending)[0]
                    except Exception:
                        candidate_w = 0
                    if candidate_w <= wrap_distance:
                        break
                    last = last[:-1]
                lines[-1] = last + max_line_ending
            else:
                lines[-1] = lines[-1] + max_line_ending
        rendered = []
        default_h = 0
        for ln in lines:
            render_text = ln if ln != "" else " "
            surf = font.font.render(render_text, True, color.rgb_tuple())
            try:
                surf = surf.convert_alpha()
            except Exception:
                try:
                    surf = surf.convert()
                except Exception:
                    pass
            w = surf.get_width()
            h = surf.get_height()
            rendered.append((surf, w, h))
            if h > default_h:
                default_h = h
        step = line_height if line_height is not None else default_h
        for i, (surf, w, h) in enumerate(rendered):
            if anchor_first_line:
                line_y = y - i * step
            else:
                total_h = step * (len(rendered) - 1) + default_h
                oy_val = origin.value[1]
                block_top_y = y + total_h // 2 - oy_val * total_h // 2
                line_y = block_top_y - i * step
            px, py = self._iud_to_pg(int(x), int(line_y))
            oxv = origin.value[0]
            px -= w // 2 + oxv * w // 2
            if color.a != 255:
                try:
                    surf.set_alpha(color.a)
                except Exception:
                    pass
            self._screen.blit(surf, (px, py))
