print("panda2d package initialized")

import pygame
import sys
from enum import Enum
from typing import Optional, Tuple


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
    NONE = "none"
    WIDTH = "width"
    HEIGHT = "height"
    BOTH = "both"
    ASPECT = "aspect"


class Image:
    MAX_CACHE_SIZE = 10

    def __init__(self, path: str):
        try:
            self.surface = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Error loading image '{path}': {e}")
            self.surface = pygame.Surface((32, 32), pygame.SRCALPHA)
            self.surface.fill((255, 0, 0))
            pygame.draw.line(self.surface, (0, 0, 0), (0, 0), (31, 31), 2)
            pygame.draw.line(self.surface, (0, 0, 0), (31, 0), (0, 31), 2)
        self.width = self.surface.get_width()
        self.height = self.surface.get_height()
        self._resize_cache: dict[Tuple[int, int], pygame.Surface] = {}

    def resize(self, width: int, height: int):
        self.surface = pygame.transform.scale(self.surface, (width, height))
        self.width = width
        self.height = height


class DrawAPI:
    def __init__(self, app: "PandaApp"):
        self._app = app

    def _cts(self, x: float, y: float) -> Tuple[int, int]:
        return self._app.center_to_screen(x, y)

    def fill_tri(self, ax, ay, bx, by, cx, cy, color):
        pygame.draw.polygon(self._app.screen, color, [self._cts(ax, ay), self._cts(bx, by), self._cts(cx, cy)])

    def draw_tri(self, ax, ay, bx, by, cx, cy, color, thickness=1):
        pygame.draw.polygon(self._app.screen, color, [self._cts(ax, ay), self._cts(bx, by), self._cts(cx, cy)], thickness)

    def draw_line(self, ax, ay, bx, by, color, thickness=1):
        pygame.draw.line(self._app.screen, color, self._cts(ax, ay), self._cts(bx, by), thickness)

    def fill_circle(self, x, y, radius, color):
        pygame.draw.circle(self._app.screen, color, self._cts(x, y), int(radius))

    def draw_circle(self, x, y, radius, color, thickness=1):
        pygame.draw.circle(self._app.screen, color, self._cts(x, y), int(radius), thickness)

    def fill_ellipse(self, x, y, width, height, color):
        sx, sy = self._cts(x, y)
        pygame.draw.ellipse(self._app.screen, color, pygame.Rect(int(sx - width / 2), int(sy - height / 2), int(width), int(height)))

    def draw_ellipse(self, x, y, width, height, color, thickness=1):
        sx, sy = self._cts(x, y)
        pygame.draw.ellipse(self._app.screen, color, pygame.Rect(int(sx - width / 2), int(sy - height / 2), int(width), int(height)), thickness)


class PandaApp:
    def __init__(self, width: int = 800, height: int = 600, title: str = "Panda2D", resizable: Resizable = Resizable.NONE):
        print("PandaApp instance created")
        if not pygame.get_init():
            pygame.init()

        self.width = width
        self.height = height
        self._initial_aspect = width / height if height else 1.0
        self.resizable = resizable

        self.mousex = 0
        self.mousey = 0
        self.mousedown = False
        self.deltatime = 0.0

        flags = pygame.RESIZABLE if resizable in (Resizable.BOTH, Resizable.WIDTH, Resizable.HEIGHT, Resizable.ASPECT) else 0
        self.screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(title)
        try:
            pygame.event.get()
        except Exception:
            pass

        self.clock = pygame.time.Clock()
        self.running = True

        self.keys = pygame.key.get_pressed()
        self.prev_keys = self.keys

        self._text_cache: dict = {}
        self._font_cache: dict[Tuple[Optional[str], int], pygame.font.Font] = {}
        self.font: Optional[pygame.font.Font] = None

        self.draw_api = DrawAPI(self)
        self.initialize()

    def center_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        return int(x + self.width / 2), int(self.height / 2 - y)

    def screen_to_center(self, sx: float, sy: float) -> Tuple[int, int]:
        return int(sx - self.width / 2), int(self.height / 2 - sy)

    def initialize(self):
        pass

    def __del__(self):
        try:
            self._text_cache.clear()
        except Exception:
            pass
        try:
            if pygame.get_init():
                pygame.quit()
        except Exception:
            pass

    def update(self, dt=None):
        pass

    def draw(self):
        pass

    def is_key_down(self, key):
        return bool(self.keys[key])

    def is_key_pressed(self, key):
        return bool(self.keys[key]) and not bool(self.prev_keys[key])

    def fill_rect(self, ax, ay, bx, by, color):
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
        # Resolve font
        resolved_font: Optional[pygame.font.Font] = None
        if isinstance(font, pygame.font.Font):
            resolved_font = font
        elif font is not None:
            try:
                key = (font[0], int(font[1])) if isinstance(font, tuple) else (font, int(size) if size else 36)
                if key not in self._font_cache:
                    self._font_cache[key] = pygame.font.Font(*key)
                resolved_font = self._font_cache[key]
            except Exception:
                resolved_font = None

        if resolved_font is None and size is not None:
            key = (None, int(size))
            if key not in self._font_cache:
                self._font_cache[key] = pygame.font.Font(None, int(size))
            resolved_font = self._font_cache[key]

        if resolved_font is None:
            key = (None, 36)
            if key not in self._font_cache:
                self._font_cache[key] = pygame.font.Font(None, 36)
            resolved_font = self._font_cache[key]

        # Use cached rendered text
        font_key = next((k for k, f in self._font_cache.items() if f is resolved_font), (None, 36))
        cache_key = (str(text), color, font_key)
        if cache_key not in self._text_cache:
            self._text_cache[cache_key] = resolved_font.render(text, True, color)
        text_surface = self._text_cache[cache_key]
        text_rect = text_surface.get_rect()

        sx, sy = self.center_to_screen(x, y)
        if align in [Align.TOP_LEFT, Align.CENTER_LEFT, Align.BOTTOM_LEFT]:
            text_rect.left = sx
        elif align in [Align.TOP_CENTER, Align.CENTER, Align.BOTTOM_CENTER]:
            text_rect.centerx = sx
        else:
            text_rect.right = sx

        if align in [Align.TOP_LEFT, Align.TOP_CENTER, Align.TOP_RIGHT]:
            text_rect.top = sy
        elif align in [Align.CENTER_LEFT, Align.CENTER, Align.CENTER_RIGHT]:
            text_rect.centery = sy
        else:
            text_rect.bottom = sy

        self.screen.blit(text_surface, text_rect)

    def draw_image(self, image: Image, x, y, width=None, height=None, align=Align.TOP_LEFT):
        surface = image.surface
        if width is not None or height is not None:
            width = int(width if width else image.width * (height / image.height))
            height = int(height if height else image.height * (width / image.width))
            key = (width, height)
            if key not in image._resize_cache:
                image._resize_cache[key] = pygame.transform.scale(image.surface, (width, height))
            surface = image._resize_cache[key]

        rect = surface.get_rect()
        sx, sy = self.center_to_screen(x, y)

        if align in [Align.TOP_LEFT, Align.CENTER_LEFT, Align.BOTTOM_LEFT]:
            rect.left = sx
        elif align in [Align.TOP_CENTER, Align.CENTER, Align.BOTTOM_CENTER]:
            rect.centerx = sx
        else:
            rect.right = sx

        if align in [Align.TOP_LEFT, Align.TOP_CENTER, Align.TOP_RIGHT]:
            rect.top = sy
        elif align in [Align.CENTER_LEFT, Align.CENTER, Align.CENTER_RIGHT]:
            rect.centery = sy
        else:
            rect.bottom = sy

        self.screen.blit(surface, rect)

    def clear(self, color=(0, 0, 0)):
        self.screen.fill(color)

    def run(self, fps=60):
        print('PandaApp: entering run loop')
        try:
            while self.running:
                self.deltatime = self.clock.tick(fps) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        print('PandaApp: received QUIT event')
                        self.running = False
                    elif event.type == pygame.VIDEORESIZE:
                        w, h = event.w, event.h
                        if self.resizable == Resizable.NONE:
                            continue
                        elif self.resizable == Resizable.WIDTH:
                            h = self.height
                        elif self.resizable == Resizable.HEIGHT:
                            w = self.width
                        elif self.resizable == Resizable.ASPECT:
                            if h == 0: h = 1
                            aspect = self._initial_aspect
                            if (w / h) > aspect:
                                w = int(h * aspect)
                            else:
                                h = int(w / aspect)
                        self.width, self.height = int(w), int(h)
                        self.screen = pygame.display.set_mode((self.width, self.height), self.screen.get_flags())

                self.prev_keys = self.keys
                self.keys = pygame.key.get_pressed()
                if self.is_key_pressed(pygame.K_ESCAPE):
                    print('PandaApp: ESC pressed, quitting')
                    self.running = False

                mx, my = pygame.mouse.get_pos()
                self.mousex, self.mousey = self.screen_to_center(mx, my)
                self.mousedown = pygame.mouse.get_pressed()[0]

                self.update()
                self.clear()
                self.draw()
                pygame.display.flip()
        finally:
            pygame.event.get()
            pygame.quit()
            print('PandaApp: exiting')
            sys.exit()
