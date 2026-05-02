from path import *
from pgiud import *
from screens import Screen


class IntroScreen:
    def initialize(self, app):
        self.logos = [
            Image(get_absolute_path("assets/intro/payalabs.png")),
            Image(get_absolute_path("assets/intro/pgiud.png")),
            Image(get_absolute_path("assets/intro/pygame.png")),
        ]
        self.boom_sound = Sound(get_absolute_path("assets/sounds/intro_boom.mp3"))
        self.pre_delay = 1.5
        self.logo_time = 1.0
        self.post_delay = 2.0
        self.logo_scale = 0.15
        self.current_logo_index = 0
        self.current_logo_time = 0

    def update(self, app):
        self.current_logo_time += app.deltatime
        num_logos = len(self.logos)
        if self.current_logo_index == 0:
            if self.current_logo_time > self.pre_delay:
                self.current_logo_index = 1
                self.current_logo_time = 0
                if "--disable-sound" not in app.argv:
                    self.boom_sound.play()
        elif 1 <= self.current_logo_index <= num_logos:
            if self.current_logo_time > self.logo_time:
                self.current_logo_index += 1
                self.current_logo_time = 0
                if 1 <= self.current_logo_index <= num_logos:
                    self.boom_sound.play()
        elif self.current_logo_index == num_logos + 1:
            if self.current_logo_time > self.post_delay:
                app.screen = Screen.MAIN_MENU

    def draw(self, app):
        num_logos = len(self.logos)
        index = self.current_logo_index
        if 1 <= index <= num_logos:
            image = self.logos[index - 1]
            total = self.logo_time
            time = self.current_logo_time
            fade = min(0.3, total / 2.0)
            if time == 0:
                alpha = 0
            elif total <= 0 or time <= 0:
                alpha = 255
            elif time < fade:
                alpha = int(255 * (time / fade))
            elif time > total - fade:
                alpha = int(255 * ((total - time) / fade))
            else:
                alpha = 255
            alpha = max(0, min(255, alpha))
            logo_scale = app.scale * self.logo_scale
            app.draw_image(
                image,
                app.screen_center,
                origin=Origin.CENTER,
                image_filter=Color(255, 255, 255, alpha),
                scale_x=logo_scale,
                scale_y=logo_scale,
                antialiasing=True,
            )
