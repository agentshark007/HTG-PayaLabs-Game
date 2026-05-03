import random

from path import *
from pgiud import *
from utility import *


class Link:
    def __init__(self, target, label):
        self.target = target
        self.label = label


class Scene:
    def __init__(self, encoded: str, scene_id: str = None):
        self.id = scene_id
        lines = split_nonempty_lines(encoded)
        links = []
        self.text = ""
        self.image = ""
        for line in lines:
            if line.startswith("text: "):
                self.text = line[len("text: ") :].strip()
            elif line.startswith("image: "):
                self.image = line[len("image: ") :].strip()
            else:
                if ": " in line:
                    target, _, link_text = line.partition(": ")
                    links.append(Link(target.strip(), link_text.strip()))
                else:
                    if self.text:
                        self.text += "\n" + line.strip()
                    else:
                        self.text = line.strip()
        self.links = links
        self.image = Image(
            get_absolute_path(os.path.join("assets/data/scenes", self.image + ".png"))
        )


class Tree:
    def __init__(self, encoded):
        lines = split_nonempty_lines(encoded)
        scenes = []
        ready = False
        scene_text = ""
        scene_id = None
        first_scene_index = None
        for line in lines:
            if line.startswith("#tree"):
                ready = True
                continue
            if not ready:
                continue
            if line.startswith("##"):
                if scene_id is not None:
                    scenes.append(Scene(scene_text, scene_id))
                scene_id = line.removeprefix("##").strip()
                scene_text = ""
                if first_scene_index is None:
                    first_scene_index = len(scenes)
            else:
                scene_text += line + "\n"
        if scene_id is not None and scene_text:
            scenes.append(Scene(scene_text, scene_id))
        self.scenes = scenes
        self.first_scene_index = (
            first_scene_index if first_scene_index is not None else 0
        )


class God:
    def __init__(self, encoded: str):
        self.name: str = ""
        self.info: str = ""
        self.image: str = ""
        lines = split_nonempty_lines(encoded)
        for line in lines:
            if line.startswith("name: "):
                self.name = line.removeprefix("name: ")
            elif line.startswith("info: "):
                self.info = line.removeprefix("info: ")
            elif line.startswith("image: "):
                self.image = line.removeprefix("image: ")
            elif line == "#tree":
                break
        self.tree = Tree(encoded)
        self.start_scene_index = self.tree.first_scene_index


class Game:
    def __init__(
        self,
        god: God,
        scene_id: str = None,
        seed: int = None,
        rng_draws: int = 0,
        previous_scene_index: int = None,
    ):
        self.god = god
        self.seed = (
            seed if seed is not None else random.SystemRandom().randrange(1, 2**63)
        )
        self.rng_draws = int(rng_draws)
        self.rng = random.Random(self.seed)
        for _ in range(max(0, self.rng_draws)):
            self.rng.random()
        self.current_scene_index = god.start_scene_index
        self.previous_scene_index = None
        if scene_id is not None:
            for idx, scene in enumerate(god.tree.scenes):
                if scene.id == scene_id:
                    self.current_scene_index = idx
                    break
        if previous_scene_index is not None:
            try:
                previous_scene_index = int(previous_scene_index)
            except Exception:
                previous_scene_index = None
            if (
                previous_scene_index is not None
                and 0 <= previous_scene_index < len(god.tree.scenes)
                and previous_scene_index != self.current_scene_index
            ):
                self.previous_scene_index = previous_scene_index
