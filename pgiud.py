from enum import Enum

import pygame


class Key(Enum):
    # Letters
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

    # Numbers
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

    # Function keys
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

    # Arrows
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN

    # Modifiers
    LSHIFT = pygame.K_LSHIFT
    RSHIFT = pygame.K_RSHIFT
    LCTRL = pygame.K_LCTRL
    RCTRL = pygame.K_RCTRL
    LALT = pygame.K_LALT
    RALT = pygame.K_RALT
    LSUPER = pygame.K_LSUPER
    RSUPER = pygame.K_RSUPER

    # Common keys
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

    # Symbols
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

    # Keypad
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
        # Note: all values must range from 0-255. Greater/lesser values will be
        # clamped.
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
        r = int(self.r * (1 - factor) + other.r * factor)
        g = int(self.g * (1 - factor) + other.g * factor)
        b = int(self.b * (1 - factor) + other.b * factor)
        a = int(self.a * (1 - factor) + other.a * factor)
        return Color(r, g, b, a)


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
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    TOPLEFT = "topleft"
    TOPRIGHT = "topright"
    BOTTOMLEFT = "bottomleft"
    BOTTOMRIGHT = "bottomright"


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
            origin: Origin = Origin.BOTTOMLEFT,
    ):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass

        self._width, self._height = width, height
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
        self._mousex = 0
        self._mousey = 0
        self._deltatime = 0.0
        self._fonts = {}
        self._mousedownprimary = False
        self._mousedownmiddle = False
        self._mousedownsecondary = False

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
    def mousex(self):
        return self._mousex

    @property
    def mousey(self):
        return self._mousey

    @property
    def mousedownprimary(self):
        return self._mousedownprimary

    @property
    def mousedownmiddle(self):
        return self._mousedownmiddle

    @property
    def mousedownsecondary(self):
        return self._mousedownsecondary

    @property
    def deltatime(self):
        return self._deltatime

    def keydown(self, key: Key):
        pressed = pygame.key.get_pressed()
        return bool(pressed[key.value])

    def _get_origin_position(self, origin: Origin):
        if origin == Origin.CENTER:
            return 0, 0
        elif origin == Origin.TOP:
            return 0, 1
        elif origin == Origin.BOTTOM:
            return 0, -1
        elif origin == Origin.LEFT:
            return -1, 0
        elif origin == Origin.RIGHT:
            return 1, 0
        elif origin == Origin.TOPLEFT:
            return -1, 1
        elif origin == Origin.TOPRIGHT:
            return 1, 1
        elif origin == Origin.BOTTOMLEFT:
            return -1, -1
        elif origin == Origin.BOTTOMRIGHT:
            return 1, -1
        else:
            # Defensive default
            return 0, 0

    def screen_position(self, origin: Origin):
        # Return the IUD coordinates that correspond to the given `origin`

        # Find pygame screen center
        cx, cy = self._width // 2, self._height // 2

        # Find the pygame position of the given origin
        ox, oy = self._get_origin_position(origin)
        px = cx + (ox * (self.width // 2))
        py = cy - (oy * (self.height // 2))
        # Convert to IUD coordinates and return
        return self._pg_to_iud(px, py)

    @property
    def screen_center_x(self):
        return self.screen_position(Origin.CENTER)[0]

    @property
    def screen_center_y(self):
        return self.screen_position(Origin.CENTER)[1]

    @property
    def screen_top_y(self):
        return self.screen_position(Origin.TOP)[1]

    @property
    def screen_bottom_y(self):
        return self.screen_position(Origin.BOTTOM)[1]

    @property
    def screen_left_x(self):
        return self.screen_position(Origin.LEFT)[0]

    @property
    def screen_right_x(self):
        return self.screen_position(Origin.RIGHT)[0]

    def _pg_to_iud(self, x: int, y: int):
        # Convert pygame (top-left origin) to IUD (custom origin)
        ox, oy = self._get_origin_position(self._origin)
        cx = self.width // 2 if ox == 0 else (0 if ox == -1 else self.width)
        cy = self.height // 2 if oy == 0 else (0 if oy == -1 else self.height)
        new_x = x - cx
        new_y = (self.height - y) - cy
        return new_x, new_y

    def _iud_to_pg(self, x: int, y: int):
        # Convert IUD (custom origin) to pygame (top-left origin)
        ox, oy = self._get_origin_position(self._origin)
        cx = self.width // 2 if ox == 0 else (0 if ox == -1 else self.width)
        cy = self.height // 2 if oy == 0 else (0 if oy == -1 else self.height)
        new_x = x + cx
        new_y = self.height - (y + cy)
        return new_x, new_y

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
        self.width, self.height = w, h
        self._screen = pygame.display.set_mode((w, h), self._flags)

    def start(self):
        self._running = True
        self.initialize()
        while self._running:
            self._deltatime = self._clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.on_quit()
                    self._running = False

                elif event.type == pygame.VIDEORESIZE:
                    self._handle_resize(event.w, event.h)
                    self.on_resize(event.w, event.h)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._mousedownprimary = True
                    elif event.button == 2:
                        self._mousedownmiddle = True
                    elif event.button == 3:
                        self._mousedownsecondary = True

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self._mousedownprimary = False
                    elif event.button == 2:
                        self._mousedownmiddle = False
                    elif event.button == 3:
                        self._mousedownsecondary = False

            self._mousex, self._mousey = self._pg_to_iud(*pygame.mouse.get_pos())

            self.update()
            self.draw()
            pygame.display.flip()

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
            ax: int,
            ay: int,
            bx: int,
            by: int,
            color: "Color",
            outline_thickness: int = 0,
            outline_color: "Color" = None,
    ):
        """Draw a filled rectangle from (ax, ay) to (bx, by) in IUD coordinates."""
        ax, ay = self._iud_to_pg(ax, ay)
        bx, by = self._iud_to_pg(bx, by)
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

    def draw_line(
            self, ax: int, ay: int, bx: int, by: int, color: "Color", width: int = 1
    ):
        """Draw a line from (ax, ay) to (bx, by) in IUD coordinates."""
        ax, ay = self._iud_to_pg(ax, ay)
        bx, by = self._iud_to_pg(bx, by)
        if color.a == 255:
            pygame.draw.line(self._screen, color.rgb_tuple(), (ax, ay), (bx, by), width)
        else:
            # Draw to a temporary surface so alpha is respected
            min_x = min(ax, bx) - width
            min_y = min(ay, by) - width
            max_x = max(ax, bx) + width
            max_y = max(ay, by) + width
            tw = max(1, max_x - min_x)
            th = max(1, max_y - min_y)
            temp = pygame.Surface((tw, th), pygame.SRCALPHA)
            sx1, sy1 = ax - min_x, ay - min_y
            sx2, sy2 = bx - min_x, by - min_y
            pygame.draw.line(temp, color.to_tuple(), (sx1, sy1), (sx2, sy2), width)
            self._screen.blit(temp, (min_x, min_y))

    def fill_polygon(self, points: list, color: "Color"):
        """Draw a filled polygon. Points should be a list of (x, y) in IUD coordinates."""
        pg_points = [self._iud_to_pg(x, y) for x, y in points]
        if color.a == 255:
            pygame.draw.polygon(self._screen, color.rgb_tuple(), pg_points)
        else:
            # Create a surface for alpha blending. Guard against zero-size.
            min_x = min(p[0] for p in pg_points)
            min_y = min(p[1] for p in pg_points)
            max_x = max(p[0] for p in pg_points)
            max_y = max(p[1] for p in pg_points)
            width = max_x - min_x
            height = max_y - min_y
            if width <= 0 or height <= 0:
                # Fallback: draw directly (alpha will be ignored), but avoid crash
                try:
                    pygame.draw.polygon(self._screen, color.rgb_tuple(), pg_points)
                except Exception:
                    pass
                return
            temp = pygame.Surface((width, height), pygame.SRCALPHA)
            shifted = [(x - min_x, y - min_y) for x, y in pg_points]
            pygame.draw.polygon(temp, color.to_tuple(), shifted)
            self._screen.blit(temp, (min_x, min_y))

    def draw_image(
            self,
            image: "Image",
            x: int,
            y: int,
            origin: Origin = Origin.BOTTOMLEFT,
            filter: "Color" = Color(255, 255, 255, 255),
            scalex: float = 1.0,
            scaley: float = 1.0,
            antialiasing: bool = True,
    ):
        """Draw an image at (x, y) in IUD coordinates.

        Optional:
          - filter: a `Color` to tint/multiply the image with (None = no tint)
          - scalex, scaley: scaling factors (scaley defaults to scalex)
          - antialiasing: whether to use smooth scaling when available
        """
        # Get pygame position
        px, py = self._iud_to_pg(x, y)

        # Get origin position and invert y for anchor calculations
        ox, oy = self._get_origin_position(origin)
        oy *= -1

        # Base surface
        surf = getattr(image, "surface", None)
        if surf is None:
            return

        # Default scaley to scalex when not provided
        if scaley is None:
            scaley = scalex

        # Scaling (with optional antialiasing)
        try:
            if scalex != 1.0 or scaley != 1.0:
                new_w = max(1, int(round(image.get_width() * scalex)))
                new_h = max(1, int(round(image.get_height() * scaley)))
                if antialiasing and hasattr(pygame.transform, "smoothscale"):
                    surf = pygame.transform.smoothscale(surf, (new_w, new_h))
                else:
                    surf = pygame.transform.scale(surf, (new_w, new_h))
        except Exception:
            # Fallback to original surface on any error
            surf = image.surface

        # Color filter / tint (multiply)
        if filter is not None:
            try:
                surf = surf.copy()
                tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
                tint.fill(filter.to_tuple())
                surf.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            except Exception:
                pass

        # Anchor center
        px -= surf.get_width() // 2
        py -= surf.get_height() // 2

        # Custom anchor (ox: -1 left, 0 center, 1 right; oy inverted to match screen space)
        px -= ox * surf.get_width() // 2
        py -= oy * surf.get_height() // 2

        self._screen.blit(surf, (px, py))

    def draw_text(
            self,
            text: str,
            x: int,
            y: int,
            font: "Font",
            color: "Color",
            origin: Origin = Origin.BOTTOMLEFT,
    ):
        """Draw text at (x, y) in IUD coordinates. `origin` specifies the text anchor."""
        surf = font.font.render(text, True, color.rgb_tuple())
        # Ensure the surface supports per-pixel alpha so per-surface alpha works
        try:
            surf = surf.convert_alpha()
        except Exception:
            try:
                surf = surf.convert()
            except Exception:
                pass

        # Get pygame position
        px, py = self._iud_to_pg(x, y)

        # Get origin position and invert y position
        ox, oy = self._get_origin_position(origin)
        oy *= -1

        # Anchor center
        px -= surf.get_width() // 2
        py -= surf.get_height() // 2

        # Custom anchor
        px -= ox * surf.get_width() // 2
        py -= oy * surf.get_height() // 2

        # Alpha
        # If color has alpha (<255), set surface alpha (per-surface) so blit respects it.
        if color.a != 255:
            try:
                surf.set_alpha(color.a)
            except Exception:
                pass

        self._screen.blit(surf, (px, py))
