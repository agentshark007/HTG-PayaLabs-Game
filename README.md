
# PayaLabs Game

**Description**
PayaLabs Game is an open-source project in early development. The current version is a technical demo for a future game about Greek gods, built with a custom graphics/input engine (`pgiud.py`) on top of Pygame.

When you run the game, it opens a window and displays a test scene image, sample heading and main text, and uses custom fonts. The game currently does not have gameplay, story, or interactive mechanics yet.

**Project Structure**

* `main.py` – Entry point for game.
* `app.py` – Main game class.
* `pgiud.py` – Graphics engine.
* `assets/` – Assets folder containing images, fonts, sounds, and other resources.

## Usage

1. Install Python (3.8+) and Pygame:

   ```bash
   pip install pygame
   ```
# PayaLabs Game

Description
-----------
PayaLabs Game is an early prototype and technical demo inspired by Greek mythology. It uses a small, custom graphics/input module built on top of Pygame and currently renders a static test scene with sample text and custom fonts.

Quick Start
-----------
Prerequisites:

- Python 3.8 or newer
- Pygame

Install Pygame:

```bash
pip install pygame
```

Run the game:

```bash
python main.py
```

Press Escape to close the window.

Project layout
--------------

- `main.py` — Entry point that creates and runs the application.
- `app.py` — The `App` class (game loop, assets, and draw/update logic).
- `pgiud.py` — Custom graphics/input module included in the repository (used for drawing and input helpers).
- `assets/` — Images and font files used by the demo.

Notes
-----
- The repository includes a lightweight engine in `pgiud.py`. `app.py` uses that module to perform drawing and input handling.
- The included `pgiud.py` corresponds to commit `9e7575f`.
- The codebase is regularly formatted with Black. To format the repository locally, run:

```bash
black .
```
- If you prefer a requirements file, you can create `requirements.txt` with a single line: `pygame`.

Contributing
------------
Contributions are not welcome. This is a private project by PayaLabs and is not open for external contributions at this time.

License
-------
This project is provided under a non-commercial license by PayaLabs. See [andrucupala.com/payalabs](https://andrucupala.com/payalabs/home.html) for more information.
