print("panda2d package initialized")

import pygame
import sys
from enum import Enum

class Align(Enum):
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class Resizable(Enum):
    """Window resize policies.

    - False: not resizable
    - Width: resizable only horizontally
    - Height: resizable only vertically
    - True: resizable on both axes
    - Aspect: resizable but preserves original aspect ratio
    """
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    BOTH = "both"
    ASPECT = "aspect"

class Image:
    MAX_CACHE_SIZE = 10  # Maximum number of cached resized versions

    def __init__(self, path):
        try:
            self.surface = pygame.image.load(path).convert_alpha()  # Add convert_alpha for better performance
        except pygame.error as e:
            print(f"Error loading image '{path}': {e}")
            # Create a small surface with an X to indicate error
            self.surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.surface.fill((255, 0, 0))
            pygame.draw.line(self.surface, (0, 0, 0), (0, 0), (31, 31), 2)
            pygame.draw.line(self.surface, (0, 0, 0), (31, 0), (0, 31), 2)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self._resize_cache = {}
    
    def resize(self, width, height):
        self.surface = pygame.transform.scale(self.surface, (width, height))
        self.width = width
        self.height = height


class DrawAPI:
    """A drawing proxy that exposes shape-drawing methods which operate
    on a provided PandaApp instance. Use as `self.draw.fill_tri(...)`.
    """
    def __init__(self, app):
        self._app = app

    def _cts(self, x, y):
        return self._app.center_to_screen(x, y)

    def fill_tri(self, ax, ay, bx, by, cx, cy, color):
        p0 = self._cts(ax, ay)
        p1 = self._cts(bx, by)
        p2 = self._cts(cx, cy)
        pygame.draw.polygon(self._app.screen, color, [p0, p1, p2])

    def draw_tri(self, ax, ay, bx, by, cx, cy, color, thickness=1):
        p0 = self._cts(ax, ay)
        p1 = self._cts(bx, by)
        p2 = self._cts(cx, cy)
        pygame.draw.polygon(self._app.screen, color, [p0, p1, p2], thickness)

    def draw_line(self, ax, ay, bx, by, color, thickness=1):
        p0 = self._cts(ax, ay)
        p1 = self._cts(bx, by)
        pygame.draw.line(self._app.screen, color, p0, p1, thickness)

    def fill_circle(self, x, y, radius, color):
        sx, sy = self._cts(x, y)
        pygame.draw.circle(self._app.screen, color, (sx, sy), int(radius))

    def draw_circle(self, x, y, radius, color, thickness=1):
        sx, sy = self._cts(x, y)
        pygame.draw.circle(self._app.screen, color, (sx, sy), int(radius), thickness)

    def fill_ellipse(self, x, y, width, height, color):
        sx, sy = self._cts(x, y)
        rect = pygame.Rect(int(sx - width / 2), int(sy - height / 2), int(width), int(height))
        pygame.draw.ellipse(self._app.screen, color, rect)

    def draw_ellipse(self, x, y, width, height, color, thickness=1):
        sx, sy = self._cts(x, y)
        rect = pygame.Rect(int(sx - width / 2), int(sy - height / 2), int(width), int(height))
        pygame.draw.ellipse(self._app.screen, color, rect, thickness)

class PandaApp:
    def __init__(self, width=800, height=600, title="Panda2D", resizable: Resizable = Resizable.NONE):
        print("PandaApp instance created")

        if not pygame.get_init():
            pygame.init()

        self.width = int(width)
        self.height = int(height)
        self._initial_aspect = float(self.width) / float(self.height) if self.height != 0 else 1.0
        self.resizable = resizable

        flags = 0
        # Map Resizable to pygame flags
        if self.resizable in (Resizable.BOTH, Resizable.WIDTH, Resizable.HEIGHT, Resizable.ASPECT):
            flags |= pygame.RESIZABLE

        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(title)
        # Flush any pending events created during initialization (prevents an immediate QUIT)
        try:
            pygame.event.get()
        except Exception:
            pass
        self.clock = pygame.time.Clock()
        self.running = True

        # Input state
        self.keys = pygame.key.get_pressed()
        self.prev_keys = self.keys

        # Initialize caches
        self._text_cache = {}
        # Cache loaded pygame Font objects: keys are (path_or_none, size)
        # path_or_none is None for the default font
        self._font_cache = {}
        self.font = None  # Will be initialized on first text draw

        # drawing proxy: call shape drawing via self.draw.<method>
        self.draw_api = DrawAPI(self)

        self.initialize()

    # Coordinate system helpers
    def center_to_screen(self, x: float, y: float) -> tuple:
        """Map centered coordinates (0,0 at center, +x right, +y up)
        to pygame screen coordinates (0,0 at top-left, +y down).

        With this mapping: centered (0,0) -> screen (width/2, height/2)
        centered (width/2, height/2) -> screen (width, 0) (top-right)
        """
        sx = x + (self.width / 2)
        sy = (self.height / 2) - y
        return int(sx), int(sy)

    def screen_to_center(self, sx: float, sy: float) -> tuple:
        """Map pygame screen coords back to centered coords."""
        x = sx - (self.width / 2)
        y = (self.height / 2) - sy
        return int(x), int(y)

    def initialize(self):
        pass

    def __del__(self):
        # Cleanup when the object is destroyed
        try:
            if hasattr(self, '_text_cache'):
                self._text_cache.clear()
        except Exception:
            pass
        try:
            if pygame.get_init():
                pygame.quit()
        except Exception:
            pass

    def update(self, dt):
        pass

    def draw(self):
        pass

    def is_key_down(self, key):
        return bool(self.keys[key])

    def is_key_pressed(self, key):
        return bool(self.keys[key]) and not bool(self.prev_keys[key])

    def fill_rect(self, ax, ay, bx, by, color):
        # Convert centered coordinates to screen coordinates
        sx0, sy0 = self.center_to_screen(ax, ay)
        sx1, sy1 = self.center_to_screen(bx, by)
        left, right = min(sx0, sx1), max(sx0, sx1)
        top, bottom = min(sy0, sy1), max(sy0, sy1)
        pygame.draw.rect(self.screen, color, (left, top, right - left, bottom - top))

    def draw_rect(self, ax, ay, bx, by, color, thickness):
        sx0, sy0 = self.center_to_screen(ax, ay)
        sx1, sy1 = self.center_to_screen(bx, by)
        left, right = min(sx0, sx1), max(sx0, sx1)
        top, bottom = min(sy0, sy1), max(sy0, sy1)
        pygame.draw.rect(self.screen, color, (left, top, right - left, bottom - top), thickness)

    def draw_text(self, x, y, text, color, align=Align.TOP_LEFT, font=None, size=None):
        """
        Draw text at centered coordinates (x, y).

        Parameters:
        - x, y: centered coordinates
        - text: string to render
        - color: (R, G, B) tuple (0-255 ints) or pygame.Color
        - align: Align enum value
        - font: optional pygame.font.Font instance or path to a font file or tuple(font_path, size)

        If font is None, the app's default font (created as pygame.font.Font(None, 36)) is used.
        The text cache key now includes the font identity so different fonts/sizes don't conflict.
        """

        # Resolve the font to a pygame.font.Font instance.
        # Priority:
        # 1) If a pygame.font.Font instance is passed in `font`, use it.
        # 2) If `font` is a tuple (path, size) or `font` is a str path, load it (use provided `size` if given).
        # 3) If `font` is None but `size` is provided, use default font face at that size.
        # 4) Otherwise use the cached default font (None, 36).

        resolved_font = None

        # If caller provided a Font instance
        if isinstance(font, pygame.font.Font):
            resolved_font = font

        # If caller provided a path or tuple
        if resolved_font is None and font is not None and not isinstance(font, pygame.font.Font):
            try:
                if isinstance(font, tuple) and len(font) == 2:
                    path, fsize = font
                    key = (path, int(fsize))
                elif isinstance(font, str):
                    key = (font, int(size) if size is not None else 36)
                else:
                    key = (None, int(size) if size is not None else 36)

                if key not in self._font_cache:
                    path_key, size_key = key
                    self._font_cache[key] = pygame.font.Font(path_key, size_key)
                resolved_font = self._font_cache[key]
            except Exception:
                resolved_font = None

        # If still none, consider size-only request for default font
        if resolved_font is None and font is None and size is not None:
            key = (None, int(size))
            if key not in self._font_cache:
                self._font_cache[key] = pygame.font.Font(None, int(size))
            resolved_font = self._font_cache[key]

        # Ensure a default font exists
        if resolved_font is None:
            # default font stored under (None, 36)
            key = (None, 36)
            if key not in self._font_cache:
                self._font_cache[key] = pygame.font.Font(None, 36)
            resolved_font = self._font_cache[key]

        # Include font identity in cache key. Use (text, color, font_key) where font_key is the (path_or_none,size)
        # to keep cache deterministic across runs.
        # Note: color should be a hashable type (tuple) already.
        # Use str(text) to ensure non-string types renderable as well.
        font_key = None
        # Find the font_key in cache by searching for the resolved_font reference
        for k, fobj in self._font_cache.items():
            if fobj is resolved_font:
                font_key = k
                break
        if font_key is None:
            # fallback to default key
            font_key = (None, 36)

        cache_key = (str(text), color, font_key)
        if cache_key not in self._text_cache:
            self._text_cache[cache_key] = resolved_font.render(text, True, color)

        text_surface = self._text_cache[cache_key]
        text_rect = text_surface.get_rect()

        # Convert centered coords to screen coords for alignment
        sx, sy = self.center_to_screen(x, y)

        # Horizontal alignment
        if align in [Align.TOP_LEFT, Align.CENTER_LEFT, Align.BOTTOM_LEFT]:
            text_rect.left = sx
        elif align in [Align.TOP_CENTER, Align.CENTER, Align.BOTTOM_CENTER]:
            text_rect.centerx = sx
        else:
            text_rect.right = sx

        # Vertical alignment
        if align in [Align.TOP_LEFT, Align.TOP_CENTER, Align.TOP_RIGHT]:
            text_rect.top = sy
        elif align in [Align.CENTER_LEFT, Align.CENTER, Align.CENTER_RIGHT]:
            text_rect.centery = sy
        else:
            text_rect.bottom = sy

        self.screen.blit(text_surface, text_rect)

    def draw_image(self, image, x, y, width=None, height=None, align=Align.TOP_LEFT):
        surface_to_draw = image.surface

        if width is not None or height is not None:
            if width is None:
                width = int(image.width * (height / image.height))
            if height is None:
                height = int(image.height * (width / image.width))
            width, height = int(width), int(height)

            cache_key = (width, height)
            if not hasattr(image, '_resize_cache'):
                image._resize_cache = {}

            if cache_key not in image._resize_cache:
                image._resize_cache[cache_key] = pygame.transform.scale(image.surface, (width, height))
            surface_to_draw = image._resize_cache[cache_key]

        image_rect = surface_to_draw.get_rect()

        # Convert centered coords to screen coords
        sx, sy = self.center_to_screen(x, y)

        if align in [Align.TOP_LEFT, Align.CENTER_LEFT, Align.BOTTOM_LEFT]:
            image_rect.left = sx
        elif align in [Align.TOP_CENTER, Align.CENTER, Align.BOTTOM_CENTER]:
            image_rect.centerx = sx
        else:
            image_rect.right = sx

        if align in [Align.TOP_LEFT, Align.TOP_CENTER, Align.TOP_RIGHT]:
            image_rect.top = sy
        elif align in [Align.CENTER_LEFT, Align.CENTER, Align.CENTER_RIGHT]:
            image_rect.centery = sy
        else:
            image_rect.bottom = sy

        self.screen.blit(surface_to_draw, image_rect)

    def clear(self, color=(0, 0, 0)):
        self.screen.fill(color)

    def run(self, fps=60):
        print('PandaApp: entering run loop')
        try:
            while self.running:
                dt = self.clock.tick(fps) / 1000.0

                events = pygame.event.get()
                # debug: print events length
                # print('events:', len(events))
                for event in events:
                    if event.type == pygame.QUIT:
                        print('PandaApp: received QUIT event')
                        self.running = False
                    # Handle window resize events
                    if event.type == pygame.VIDEORESIZE:
                        new_w, new_h = event.w, event.h
                        # Enforce resizable policy
                        if self.resizable == Resizable.NONE:
                            # ignore resize
                            continue

                        if self.resizable == Resizable.WIDTH:
                            new_h = self.height
                        elif self.resizable == Resizable.HEIGHT:
                            new_w = self.width
                        elif self.resizable == Resizable.ASPECT:
                            # keep original aspect ratio
                            if new_h == 0:
                                new_h = 1
                            desired_aspect = self._initial_aspect
                            # adjust one axis to preserve aspect
                            if (new_w / new_h) > desired_aspect:
                                # width too large, clamp width
                                new_w = int(new_h * desired_aspect)
                            else:
                                # height too large, clamp height
                                new_h = int(new_w / desired_aspect)

                        # Apply the new size and recreate the screen surface
                        self.width = int(new_w)
                        self.height = int(new_h)
                        flags = self.screen.get_flags()
                        self.screen = pygame.display.set_mode((self.width, self.height), flags)

                self.prev_keys = self.keys if self.keys is not None else pygame.key.get_pressed()
                self.keys = pygame.key.get_pressed()

                # debug: print key state for ESC to allow quitting
                if self.is_key_pressed(pygame.K_ESCAPE):
                    print('PandaApp: ESC pressed, quitting')
                    self.running = False

                self.update(dt)

                self.clear()
                self.draw()
                pygame.display.flip()
        finally:
            # Make sure to process any remaining events before quitting
            pygame.event.get()
            pygame.quit()
            print('PandaApp: exiting')
            sys.exit()
