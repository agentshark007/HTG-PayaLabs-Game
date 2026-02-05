import os
from enum import Enum
from pgiud import *
import utilities as util

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def asset(path):
    return str(os.path.join(BASE_PATH, "assets", path))


class State(Enum):
    INTRO = 1
    MAIN_MENU = 2
    NEW_GAME = 3
    LOAD_GAME_MENU = 4
    SETTINGS = 5
    PLAYING = 6
    LOAD_GAME_PLAYING = 7
    CREDITS = 8


class App(Window):
    def __init__(self):
        super().__init__(
            width=480,
            height=360,
            title="HTG PayaLabs Game",
            resizable=Resizable.ASPECT,
            origin=Origin.CENTER,
        )

    def initialize(self):
        # --- assets ---
        self.test_scene = Image(asset("images/scene/trees.png"))

        self.heading_font = Font(asset("fonts/Silkscreen-Regular.ttf"))
        self.main_font = Font(asset("fonts/VT323-Regular.ttf"))

        self.intro_payalabs_logo = Image(asset("images/intro/payalabs.png"))
        self.intro_pgiud_logo = Image(asset("images/intro/pgiud.png"))
        self.intro_pygame_logo = Image(asset("images/intro/pygame.png"))

        # sound (optional)
        self.intro_boom_sound = Sound(asset("sounds/intro_boom.mp3"))

        # --- intro sequence configuration ---
        # Use a data-driven sequence: pre-delay, three logos, post-fade
        self.intro_each_length = 1.0
        self.intro_pre_delay = 1.0
        self.intro_post_delay = 2.0

        # build a simple sequence list of segments
        self._intro_sequence = [
            {"type": "delay", "duration": self.intro_pre_delay},
            {"type": "logo", "image": self.intro_payalabs_logo, "duration": self.intro_each_length},
            {"type": "logo", "image": self.intro_pgiud_logo, "duration": self.intro_each_length},
            {"type": "logo", "image": self.intro_pygame_logo, "duration": self.intro_each_length},
            {"type": "post_fade", "image": self.intro_pygame_logo, "duration": self.intro_post_delay},
        ]

        # runtime intro state
        self._intro_index = 0
        self._intro_segment_time = 0.0
        self._intro_segment_started = False

        # visual brightness spike/fade
        self.intro_brightness = 0.0
        # faster fade speed (brightness units per second)
        self.intro_fade_speed = 400.0

        # scale
        self.scale = 1.0

        # starting state
        self.state = State.INTRO

    # helper to advance intro to next segment
    def _intro_advance(self):
        self._intro_index += 1
        self._intro_segment_time = 0.0
        self._intro_segment_started = False

    def update(self):
        # debug: space to restart intro (keeps prior behavior)
        if self.keydown(Key.SPACE):
            # restart the intro
            self._intro_index = 0
            self._intro_segment_time = 0.0
            self._intro_segment_started = False
            self.intro_brightness = 0.0
            self.state = State.INTRO

        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0

        if self.state == State.INTRO:
            # advance timers
            dt = self.deltatime
            self._intro_segment_time += dt

            # Apply brightness decay each frame
            self.intro_brightness = max(0.0, self.intro_brightness - self.intro_fade_speed * dt)

            # Bounds-check sequence index
            if self._intro_index >= len(self._intro_sequence):
                # sequence finished -> go to playing
                self.state = State.PLAYING
                return

            seg = self._intro_sequence[self._intro_index]

            # on-enter logic for segments
            if not self._intro_segment_started:
                self._intro_segment_started = True
                if seg["type"] == "logo":
                    # spike brightness and play sound
                    self.intro_brightness = 255.0
                    try:
                        self.intro_boom_sound.play()
                    except Exception:
                        pass

            # If current segment finished, advance
            if self._intro_segment_time >= seg["duration"]:
                self._intro_advance()

        elif self.state == State.MAIN_MENU:
            pass

        elif self.state == State.LOAD_GAME_MENU:
            pass

        elif self.state == State.SETTINGS:
            pass

        elif self.state == State.PLAYING:
            pass

        elif self.state == State.LOAD_GAME_PLAYING:
            pass

    def draw(self):
        # Clear the screen according to the current intro brightness (clamped)
        b = int(max(0.0, min(255.0, self.intro_brightness)))
        self.clear(Color(b, b, b, 255))

        if self.state == State.INTRO:
            # determine what to draw based on the current sequence index
            t_rel = self._intro_segment_time
            # compute scale easing for logos when visible
            interp_t = 0.0
            seg = None
            if 0 <= self._intro_index < len(self._intro_sequence):
                seg = self._intro_sequence[self._intro_index]

            # base scale for logos
            if seg and seg.get("type") in ("logo", "post_fade"):
                if seg.get("type") == "logo":
                    # local normalized time for easing inside a logo segment
                    local_t = 0.0
                    if seg["duration"] > 0:
                        local_t = min(1.0, t_rel / seg["duration"])
                    interp_t = util.inverse_lerp(local_t, 0.0, 1.0)
                    logo_scale = self.scale * util.lerp(
                        interp_t, 0.1, 0.15, util.InterpolationMethod.EASE_OUT
                    )
                else:
                    # For post_fade, keep the large size achieved by the last logo
                    logo_scale = self.scale * 0.15
            else:
                logo_scale = self.scale * 0.1

            # Draw the current logo (logo segments) or handle post_fade
            # For the post_fade segment, draw the final logo with decreasing alpha
            if seg:
                if seg["type"] == "logo":
                    img = seg.get("image")
                    if isinstance(img, Image):
                        self.draw_image(
                            img,
                            V(self.screen_center_x, self.screen_center_y),
                            origin=Origin.CENTER,
                            scale_x=logo_scale,
                            scale_y=logo_scale,
                        )

                elif seg["type"] == "post_fade":
                    # draw the image with alpha fading out across the post_fade duration
                    dur = seg["duration"] if seg["duration"] > 0 else 1.0
                    fade_t = min(1.0, t_rel / dur)
                    alpha = int(max(0.0, 1.0 - fade_t) * 255)
                    img = seg.get("image")
                    if isinstance(img, Image):
                        self.draw_image(
                            img,
                            V(self.screen_center_x, self.screen_center_y),
                            origin=Origin.CENTER,
                            image_filter=Color(255, 255, 255, alpha),
                            scale_x=logo_scale,
                            scale_y=logo_scale,
                        )

        elif self.state == State.PLAYING:
            # normal playing rendering
            self.clear(Color(0, 0, 0))  # Black background

            # Context image
            self.draw_image(
                self.test_scene,
                V(0 * self.scale, 110 * self.scale),
                origin=Origin.CENTER,
                scale_x=self.scale,
                scale_y=self.scale,
                antialiasing=False,
            )

            # Heading text
            self.draw_text(
                "Heading text",
                V(-230 * self.scale, 40 * self.scale),
                font=self.heading_font.new_size(
                    int(self.heading_font.size * self.scale)
                ),
                color=Color(255, 255, 255),
                origin=Origin.TOPLEFT,
            )

            # Main text
            self.draw_text(
                "Main text. The quick brown fox jumps over the lazy dog.",
                V(-230 * self.scale, 10 * self.scale),
                self.main_font.new_size(int(self.main_font.size * self.scale)),
                Color(255, 255, 255),
                Origin.TOPLEFT,
            )

        # other states unchanged

    def on_quit(self):
        # ensure sound stops if playing
        try:
            if hasattr(self, "intro_boom_sound") and self.intro_boom_sound:
                self.intro_boom_sound.stop()
        except Exception:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
