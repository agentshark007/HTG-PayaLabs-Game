
# PayaLabs Game

**Description**
PayaLabs Game is an open-source project in early development. The current version is a technical demo for a future game about Greek gods, built with a custom graphics/input engine (`panda2d.py`) on top of Pygame.

When you run the game, it opens a window and displays a test scene image, sample heading and main text, and uses custom fonts. The game currently does not have gameplay, story, or interactive mechanics yet.

**Project Structure**

* `panda2d.py` – Custom graphics and input module (built on Pygame).
* `app.py` – Main game class (`App`), sets up images, fonts, and handles drawing logic.
* `main.py` – Entry point, runs the game loop.
* `assets/` – Contains images and fonts used for rendering (e.g., `ares.png`, `test-scene.png`, `Khmer MN.ttc`, `Silkscreen-Regular.ttf`, `VT323-Regular.ttf`).

---

## Current Features

* Windowed game with black background.
* Renders a test scene image and sample text using custom fonts.
* Drawing API supports rectangles, circles, ellipses, triangles, lines, images, and text.
* Keyboard and mouse input support (Escape key exits the game).
* Centered coordinate system for game objects.
* Assets and fonts loaded from the `assets/` folder.

---

## Usage

1. Install Python (3.8+) and Pygame:

   ```bash
   pip install pygame
   ```

2. Run the game:

   ```bash
   python main.py
   ```

3. Press Escape to exit the game window.

---

## Contribution

Contributions are welcome! You can submit pull requests for bug fixes, improvements, or new features. Please note the game is in a prototype stage and only displays a static scene and text for now.

---

## License

**PayaLabs Non-Commercial Open Source License v1.0**

1. **Permission:** Use, modify, and distribute this software **for non-commercial purposes only**.
2. **Attribution:** Any use, distribution, or derivative work must give **credit to PayaLabs**.
3. **No Commercial Use:** You may **not sell, license, or profit** from this software or derivatives.
4. **Disclaimer:** Provided “as-is” without warranty. PayaLabs is not liable for any damages resulting from its use.

By using or distributing this software, you agree to these terms.

---

## Contact

For questions or collaboration inquiries, contact **PayaLabs**.

**Note:** The game is in early development. Currently, it displays a window with a test scene image and sample text. Story, art, music, and gameplay mechanics will be added in future updates.

This project remains open-source and non-commercial, with proper attribution to PayaLabs required.
