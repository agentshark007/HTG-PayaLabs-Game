# PayaLabs Game

**Description**
PayaLabs Game is an open-source project currently under development. It lets players experience life as Greek gods, exploring their powers, interactions, and influence in a dynamic world.

The game uses a custom module, `panda2d.py`, built on top of Pygame for graphics and input handling. When imported, it prints:

```
panda2d package initialized
```

**Project Structure**

* `panda2d.py` – Custom graphics and input module.
* `app.py` – Main game class `App`, which inherits from `PandaApp` and handles initialization, updates, and drawing logic.
* `main.py` – Launches the game via `App.run()`.

---

## Features (Current)

* Windowed game with optional resizing modes.
* Drawing API supports rectangles, circles, ellipses, triangles, lines, images, and text.
* Keyboard and mouse input support.
* Centered coordinate system for game objects.

---

## Usage

1. Install Python and Pygame:

   ```bash
   pip install pygame
   ```

2. Run the game:

   ```bash
   python main.py
   ```

3. Press Escape to exit the game.

---

## Contribution

Contributions are welcome! Submit pull requests for bug fixes, improvements, or new features.

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

**Note:** The game is in early development. Currently, it only displays a window with a test square. Story, art, music, and gameplay mechanics will be added progressively.

This project remains open-source and non-commercial, with proper attribution to PayaLabs required.
