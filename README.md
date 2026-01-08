
# PayaLabs Game

**Description**
PayaLabs Game is an open-source project in early development. The current version is a technical demo for a future game about Greek gods, built with a custom graphics/input engine (`panda2d.py`) on top of Pygame.

When you run the game, it opens a window and displays a test scene image, sample heading and main text, and uses custom fonts. The game currently does not have gameplay, story, or interactive mechanics yet.

**Project Structure**

* `main.py` – Entry point, runs the game loop by calling the main function in `app.py`.
* `app.py` – Main game class (`App`), sets up images (`ares.png`, `test-scene.png`), custom fonts (`Khmer MN.ttc`, `Silkscreen-Regular.ttf`, `VT323-Regular.ttf`), and handles drawing logic. Assets are loaded using the `asset()` helper function.
* `panda2d.py` – Custom graphics and input module (built on Pygame), provides drawing and input APIs.
* `assets/` – Contains images and fonts used for rendering:
   * `ares.png`, `test-scene.png` – Scene and character images.
   * `Khmer MN.ttc`, `Silkscreen-Regular.ttf`, `VT323-Regular.ttf` – Custom font files.
* `__pycache__/` – Python bytecode cache (auto-generated).

## Current Features

* Windowed game with black background.
* Renders a test scene image and sample text using custom fonts.
* Drawing API supports rectangles, circles, ellipses, triangles, lines, images, and text.
* Keyboard and mouse input support (Escape key exits the game).
* Centered coordinate system for game objects.
* Assets and fonts loaded from the `assets/` folder.
* Main game logic is handled in the `App` class in `app.py`, which loads images and fonts, and draws them each frame.
* Asset loading is managed by the `asset()` helper function in `app.py` for consistent path resolution.


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
Contributions are welcome. Open an issue or submit a pull request for fixes, improvements, or new features. This project is a prototype; expect the code and APIs to change.

License
-------
This project is provided under a non-commercial license by PayaLabs. See the repository or contact the authors for full terms.

Contact
-------
For questions or collaboration inquiries, contact PayaLabs.
