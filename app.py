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
        self.test_scene = Image(asset("images/scene/trees.png"))

        self.heading_font = Font(asset("fonts/Silkscreen-Regular.ttf"))
        self.main_font = Font(asset("fonts/VT323-Regular.ttf"))

        self.intro_payalabs_logo = Image(asset("images/intro/payalabs.png"))
        self.intro_pgiud_logo = Image(asset("images/intro/pgiud.png"))
        self.intro_pygame_logo = Image(asset("images/intro/pygame.png"))

        # Timing: 1s initial delay, each logo 1s, 2s post delay
        self.intro_pre_delay = 1.0
        self.intro_each_length = 1.0
        self.intro_post_delay = 2.0

        # Combined duration for convenience
        self._intro_total_duration = (
            self.intro_pre_delay + self.intro_each_length * 3 + self.intro_post_delay
        )

        # Timer and brightness
        self.intro_timer = 0.0
        self.intro_brightness = 0.0

        # Faster fade speed (units: brightness per second)
        self.intro_fade_speed = 400.0

        # Load intro boom sound (assumes assets/sounds/intro_boom.mp3 exists)
        self.intro_boom_sound = Sound(asset("sounds/intro_boom.mp3"))

        self.scale = 1.0

        self.state = State.INTRO

    def update(self):
        if self.keydown(Key.SPACE):
            # Reset intro timer for debugging
            self.intro_timer = 0.0

        scale_x = self.width / self._original_width
        scale_y = self.height / self._original_height
        self.scale = (scale_x + scale_y) / 2.0

        if self.state == State.INTRO:
            # Advance timer
            self.intro_timer += self.deltatime

            # Compute a relative time that excludes the pre-delay
            t_rel = self.intro_timer - self.intro_pre_delay

            # Fade brightness over time (simple linear fade)
            # Use configured fade speed (units: brightness per second)
            self.intro_brightness = max(0.0, self.intro_brightness - self.intro_fade_speed * self.deltatime)

            # Detect the start of each logo (only when within 0..3*each)
            if 0.0 <= t_rel < self.intro_each_length * 3:
                current_logo_index = int(t_rel / self.intro_each_length)
                prev_logo_index = int((t_rel - self.deltatime) / self.intro_each_length) if t_rel - self.deltatime >= 0.0 else -1

                if current_logo_index != prev_logo_index:
                    # Spike brightness at logo start
                    self.intro_brightness = 255.0

                    # Play the boom sound effect
                    self.intro_boom_sound.play()

            # After the total intro duration, switch to PLAYING
            if self.intro_timer >= self._intro_total_duration:
                self.state = State.PLAYING

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
        # Clear with current intro brightness (clamped to 0-255)
        b = int(max(0.0, min(255.0, self.intro_brightness)))
        self.clear(Color(b, b, b, 255))

        if self.state == State.INTRO:
            # Compute scale interpolation for logo (same as before but based on relative time)
            # Use t_rel to decide which logo to draw
            t_rel = self.intro_timer - self.intro_pre_delay

            # scale is small and subtle
            interp_t = 0.0
            if 0.0 <= t_rel:
                # When in a logo window, compute a normalized [0,1] for that window
                if 0.0 <= t_rel < self.intro_each_length * 3:
                    logo_local_t = (t_rel % self.intro_each_length) / self.intro_each_length
                    interp_t = util.inverse_lerp(logo_local_t, 0.0, 1.0)
                else:
                    interp_t = 0.0

            scale = self.scale * util.lerp(
                interp_t,
                0.1,
                0.15,
                util.InterpolationMethod.EASE_OUT,
            )

            # Draw logos only during their windows. Respect the 1s pre-delay.
            if 0.0 <= t_rel < self.intro_each_length:
                self.draw_image(
                    self.intro_payalabs_logo,
                    V(self.screen_center_x, self.screen_center_y),
                    origin=Origin.CENTER,
                    scale_x=scale,
                    scale_y=scale,
                )

            if self.intro_each_length <= t_rel < self.intro_each_length * 2:
                self.draw_image(
                    self.intro_pgiud_logo,
                    V(self.screen_center_x, self.screen_center_y),
                    origin=Origin.CENTER,
                    scale_x=scale,
                    scale_y=scale,
                )

            if self.intro_each_length * 2 <= t_rel < self.intro_each_length * 3:
                self.draw_image(
                    self.intro_pygame_logo,
                    V(self.screen_center_x, self.screen_center_y),
                    origin=Origin.CENTER,
                    scale_x=scale,
                    scale_y=scale,
                )

            # If we're into the post-delay after the third logo, keep drawing the third logo but fade it out
            if self.intro_each_length * 3 <= t_rel < self.intro_each_length * 3 + self.intro_post_delay:
                # compute fade alpha from 255 -> 0 across the post delay
                fade_t = (t_rel - self.intro_each_length * 3) / self.intro_post_delay
                alpha = int(max(0.0, min(1.0, 1.0 - fade_t)) * 255)
                self.draw_image(
                    self.intro_pygame_logo,
                    V(self.screen_center_x, self.screen_center_y),
                    origin=Origin.CENTER,
                    image_filter=Color(255, 255, 255, alpha),
                    scale_x=scale,
                    scale_y=scale,
                )

        elif self.state == State.MAIN_MENU:
            pass

        elif self.state == State.LOAD_GAME_MENU:
            pass

        elif self.state == State.SETTINGS:
            pass

        elif self.state == State.PLAYING:
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

        elif self.state == State.LOAD_GAME_PLAYING:
            pass

        elif self.state == State.CREDITS:
            pass


def main():
    App().start()


if __name__ == "__main__":
    main()
