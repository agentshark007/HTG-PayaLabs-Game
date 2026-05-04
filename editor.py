import argparse
import copy
import os
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any, cast

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GODS_DIR = os.path.join(BASE_DIR, "assets", "data", "gods")
GOD_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "data", "thumbnails")
SCENE_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "data", "scenes")


@dataclass
class ChoiceBlock:
    targets: list[str] = field(default_factory=list)
    text: str = ""


@dataclass
class SceneBlock:
    original_id: str
    text_lines: list[str] = field(default_factory=list)
    image: str = ""
    choices: list[ChoiceBlock] = field(default_factory=list)


@dataclass
class ParsedGod:
    info: dict[str, str] = field(
        default_factory=lambda: {"name": "", "info": "", "image": ""}
    )
    scenes: list[SceneBlock] = field(default_factory=list)
    seen_info_header: bool = False
    seen_tree_header: bool = False


@dataclass
class RepairReport:
    fixes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def clean_god_name(raw: str) -> str:
    name = raw.strip()
    if name.lower().endswith(".txt"):
        name = name[:-4]
    return name.strip()


def resolve_god_file(name: str) -> Path:
    clean_name = clean_god_name(name)
    if not clean_name:
        raise ValueError("God name cannot be empty.")
    gods_dir = Path(BASE_DIR) / "assets" / "data" / "gods"
    exact = gods_dir / f"{clean_name}.txt"
    if exact.exists():
        return exact
    lower = clean_name.lower()
    for candidate in gods_dir.glob("*.txt"):
        if candidate.stem.lower() == lower:
            return candidate
    return exact


def split_weighted_target(token: str) -> tuple[str, str | None]:
    token = token.strip()
    if "*" in token:
        base, weight = token.rsplit("*", 1)
        return (base.strip(), weight.strip())
    return (token, None)


def replace_scene_target(token: str, old_id: str, new_id: str) -> str:
    base, weight = split_weighted_target(token)
    if base != old_id:
        return token
    if weight is None or weight == "":
        return new_id
    return f"{new_id}*{weight}"


def depth_prefix(depth: int) -> str:
    label = ""
    n = max(0, int(depth))
    while True:
        label = chr(ord("a") + n % 26) + label
        n = n // 26 - 1
        if n < 0:
            break
    return label


def parse_god_text(text: str, report: RepairReport) -> ParsedGod:
    parsed = ParsedGod()
    current_scene: SceneBlock | None = None
    section: str | None = None

    def start_scene(scene_id: str) -> None:
        nonlocal current_scene, section
        scene_id = scene_id.strip()
        if not scene_id:
            report.warnings.append("Ignored a scene header with an empty id.")
            current_scene = None
            return
        scene = SceneBlock(original_id=scene_id)
        current_scene = scene
        parsed.scenes.append(scene)
        section = "tree"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if line == "#info":
            parsed.seen_info_header = True
            section = "info"
            continue
        if line == "#tree":
            parsed.seen_tree_header = True
            section = "tree"
            continue
        if line.startswith("##"):
            if not parsed.seen_tree_header:
                parsed.seen_tree_header = True
            start_scene(line[2:])
            continue
        if section == "info" or (section is None and (not parsed.scenes)):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()
                parsed.info[key] = value
                continue
            if parsed.info["info"]:
                parsed.info["info"] += "\n" + line
            else:
                parsed.info["info"] = line
            continue
        if current_scene is None:
            continue
        if lower.startswith("text:"):
            current_scene.text_lines = [line.split(":", 1)[1].strip()]
            continue
        if lower.startswith("image:"):
            current_scene.image = line.split(":", 1)[1].strip()
            continue
        if ":" in line:
            targets_raw, label = line.split(":", 1)
            targets = [
                token.strip() for token in targets_raw.split(",") if token.strip()
            ]
            if targets:
                current_scene.choices.append(
                    ChoiceBlock(targets=targets, text=label.strip())
                )
                continue
        if current_scene.text_lines:
            current_scene.text_lines.append(line)
        else:
            current_scene.text_lines = [line]
    return parsed


def normalize_god(
    parsed: ParsedGod, report: RepairReport
) -> tuple[dict[str, str], list[tuple[str, SceneBlock]]]:
    if not parsed.scenes:
        report.errors.append("No scenes were found in the file.")
        return (parsed.info, [])
    if not parsed.seen_info_header:
        report.fixes.append("Added missing #info section header.")
    if not parsed.seen_tree_header:
        report.fixes.append("Added missing #tree section header.")
    ordered_indices = list(range(len(parsed.scenes)))
    root_index = ordered_indices[0]
    id_to_indices: dict[str, list[int]] = {}
    for idx, scene in enumerate(parsed.scenes):
        id_to_indices.setdefault(scene.original_id, []).append(idx)
    duplicate_ids = [
        scene_id for scene_id, indices in id_to_indices.items() if len(indices) > 1
    ]
    if duplicate_ids:
        report.warnings.append(
            "Duplicate scene ids found; the first occurrence of each id was used for reference repair: "
            + ", ".join(sorted(duplicate_ids))
        )

    def resolve_scene_id(scene_id: str) -> int | None:
        indices = id_to_indices.get(scene_id)
        return indices[0] if indices else None

    depth_by_index = {root_index: 0}
    layers: dict[int, list[int]] = {0: [root_index]}
    discovered = {root_index}
    queue = [root_index]
    while queue:
        current = queue.pop(0)
        current_depth = depth_by_index[current]
        for choice in parsed.scenes[current].choices:
            for token in choice.targets:
                target_id, _weight = split_weighted_target(token)
                target_index = resolve_scene_id(target_id)
                if target_index is None:
                    continue
                if target_index not in depth_by_index:
                    depth_by_index[target_index] = current_depth + 1
                if target_index not in discovered:
                    discovered.add(target_index)
                    layers.setdefault(depth_by_index[target_index], []).append(
                        target_index
                    )
                    queue.append(target_index)
    unreachable = [idx for idx in ordered_indices if idx not in discovered]
    if unreachable:
        layers[max(layers) + 1] = unreachable
        report.warnings.append(
            "Unreachable scenes were moved to the final layer: "
            + ", ".join((parsed.scenes[idx].original_id for idx in unreachable))
        )
    ordered_indices_by_layer: list[int] = []
    for layer in sorted(layers):
        ordered_indices_by_layer.extend(layers[layer])
    id_map: dict[int, str] = {}
    for layer in sorted(layers):
        prefix = depth_prefix(layer)
        for idx, scene_index in enumerate(layers[layer], start=1):
            id_map[scene_index] = f"{prefix}{idx}"
    old_id_to_new_id: dict[str, str] = {}
    for old_id, indices in id_to_indices.items():
        mapped_index = indices[0]
        if mapped_index in id_map:
            old_id_to_new_id[old_id] = id_map[mapped_index]
    repaired_scenes: list[tuple[str, SceneBlock]] = []
    for scene_index in ordered_indices_by_layer:
        scene = copy.deepcopy(parsed.scenes[scene_index])
        new_id = id_map[scene_index]
        if scene.original_id != new_id:
            report.fixes.append(f"Renamed scene {scene.original_id} -> {new_id}.")
        scene.original_id = new_id
        repaired_choices: list[ChoiceBlock] = []
        for choice in scene.choices:
            remapped_targets: list[str] = []
            for token in choice.targets:
                base, weight = split_weighted_target(token)
                mapped_base = old_id_to_new_id.get(base)
                if mapped_base is None:
                    report.warnings.append(
                        f"Removed missing choice target '{token}' from scene {scene.original_id}."
                    )
                    continue
                if weight is not None and weight != "":
                    try:
                        if float(weight) <= 0:
                            report.warnings.append(
                                f"Normalized non-positive weight '{token}' in scene {scene.original_id} to 1."
                            )
                            weight = "1"
                    except Exception:
                        report.warnings.append(
                            f"Normalized invalid weight '{token}' in scene {scene.original_id} to 1."
                        )
                        weight = "1"
                remapped_targets.append(
                    mapped_base
                    if weight is None or weight == ""
                    else f"{mapped_base}*{weight}"
                )
            if not remapped_targets:
                report.warnings.append(
                    f"Removed empty choice '{choice.text}' from scene {scene.original_id}."
                )
                continue
            repaired_choices.append(
                ChoiceBlock(targets=remapped_targets, text=choice.text.strip())
            )
        scene.choices = repaired_choices
        scene.text_lines = [line.rstrip() for line in scene.text_lines]
        scene.image = scene.image.strip()
        repaired_scenes.append((new_id, scene))
    if not parsed.info.get("name", "").strip():
        report.warnings.append("God name is missing.")
    if not parsed.info.get("info", "").strip():
        report.warnings.append("God description is empty.")
    if not parsed.info.get("image", "").strip():
        report.warnings.append("God image key is missing.")
    normalized_info = {
        "name": parsed.info.get("name", "").strip(),
        "info": parsed.info.get("info", "").strip(),
        "image": parsed.info.get("image", "").strip(),
    }
    return (normalized_info, repaired_scenes)


def export_god_text(info: dict[str, str], scenes: list[tuple[str, SceneBlock]]) -> str:
    lines = [
        "#info",
        f"name: {info.get('name', '').strip()}",
        f"info: {info.get('info', '').strip()}",
        f"image: {info.get('image', '').strip()}",
        "",
        "#tree",
        "",
    ]
    for scene_id, scene in scenes:
        lines.append(f"##{scene_id}")
        text_lines = scene.text_lines if scene.text_lines else [""]
        lines.append(f"text: {(text_lines[0] if text_lines else '')}")
        for extra in text_lines[1:]:
            lines.append(extra)
        lines.append(f"image: {scene.image.strip()}")
        for choice in scene.choices:
            targets = ", ".join(choice.targets)
            lines.append(f"{targets}: {choice.text}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def validate_repaired_data(
    info: dict[str, str], scenes: list[tuple[str, SceneBlock]]
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not info.get("name", "").strip():
        errors.append("Missing god name.")
    if not info.get("image", "").strip():
        errors.append("Missing god image key.")
    if not scenes:
        errors.append("No scenes defined.")
        return (errors, warnings)
    scene_map = {scene_id: scene for scene_id, scene in scenes}
    if scenes[0][0] != "a1":
        warnings.append(f"First scene is '{scenes[0][0]}', not 'a1'.")
    for scene_id, scene in scenes:
        if not scene.text_lines or not "\n".join(scene.text_lines).strip():
            warnings.append(f"Scene '{scene_id}' has no text.")
        if not scene.image.strip():
            warnings.append(f"Scene '{scene_id}' has no image key.")
        for choice_idx, choice in enumerate(scene.choices, start=1):
            if not choice.targets:
                errors.append(
                    f"Scene '{scene_id}' choice #{choice_idx} has no targets."
                )
            for token in choice.targets:
                target_id, weight = split_weighted_target(token)
                if target_id not in scene_map:
                    errors.append(
                        f"Scene '{scene_id}' choice #{choice_idx} targets missing scene '{target_id}'."
                    )
                if weight is not None:
                    try:
                        if float(weight) <= 0:
                            errors.append(
                                f"Scene '{scene_id}' choice #{choice_idx} has non-positive weight in '{token}'."
                            )
                    except Exception:
                        errors.append(
                            f"Scene '{scene_id}' choice #{choice_idx} has invalid weight in '{token}'."
                        )
    return (errors, warnings)


def repair_god_file(path: Path) -> tuple[int, RepairReport, str, str]:
    report = RepairReport()
    if not path.exists():
        report.errors.append(f"File not found: {path}")
        return (1, report, "", "")
    original_text = path.read_text(encoding="utf-8")
    parsed = parse_god_text(original_text, report)
    info, scenes = normalize_god(parsed, report)
    if report.errors:
        return (1, report, original_text, original_text)
    repaired_text = export_god_text(info, scenes)
    validation_errors, validation_warnings = validate_repaired_data(info, scenes)
    report.errors.extend(validation_errors)
    report.warnings.extend(validation_warnings)
    if original_text != repaired_text:
        path.write_text(repaired_text, encoding="utf-8")
        report.fixes.append(f"Wrote repaired file.")
    return (0 if not report.errors else 1, report, original_text, repaired_text)


def prompt_for_god_name() -> str:
    try:
        return input("Which god do you want to repair? (no .txt needed): ")
    except EOFError:
        return ""


def repair_main() -> int:
    parser = argparse.ArgumentParser(description="Repair a god story text file.")
    parser.add_argument("god", nargs="?", help="God file name without .txt")
    args = parser.parse_args()
    god_name = clean_god_name(args.god or prompt_for_god_name())
    if not god_name:
        print("No god name provided.")
        return 1
    path = resolve_god_file(god_name)
    code, report, original_text, repaired_text = repair_god_file(path)
    if code != 0 and (not path.exists()):
        for err in report.errors:
            print(err)
        return 1
    if report.errors:
        print("Repair finished with unresolved errors:")
        for err in report.errors:
            print(f"- {err}")
    if original_text == repaired_text:
        print(f"No changes needed for {path.name}.")
    else:
        print(f"Repaired {path.name}.")
    if report.fixes:
        print("Fixes applied:")
        for fix in report.fixes:
            print(f"- {fix}")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"- {warning}")
    return code


class GodEditor:

    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.current_file = None
        self.dirty = False
        self.data: dict[str, Any] = self._blank_data()
        self.current_scene: str | None = None
        self.current_choices: list[dict[str, Any]] = []
        self.selected_choice_index: int | None = None
        self._selection_guard_enabled = True
        self._suspend_dirty_tracking = False
        self.scene_summary_var = tk.StringVar(value="Scenes: 0 total · 0 shown")
        self.scene_search_var = tk.StringVar(value="")
        self.scene_issues_only_var = tk.BooleanVar(value=False)
        self.god_image_keys = self._list_image_keys(GOD_IMAGE_DIR)
        self.scene_image_keys = self._list_image_keys(SCENE_IMAGE_DIR)
        self._build_ui()
        self.new_file(skip_prompt=True)

    def _blank_scene(self) -> dict[str, Any]:
        return {"text": "", "image": "", "choices": []}

    def _blank_data(self) -> dict[str, Any]:
        return {
            "info": {"name": "", "info": "", "image": ""},
            "scenes": {},
            "scene_order": [],
        }

    def _build_ui(self):
        self.status_var = tk.StringVar(value="Ready")
        self.validation_summary_var = tk.StringVar(
            value="Validation: 0 errors, 0 warnings"
        )
        self.title_var = "God Editor"
        self.root.minsize(1080, 720)
        top = tk.LabelFrame(self.root, text="God Metadata", padx=10, pady=8)
        top.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(top, text="Name").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.name_entry = tk.Entry(top, width=36)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(6, 12), pady=(0, 4))
        self.name_entry.bind("<KeyRelease>", self.on_field_edited)
        tk.Label(top, text="Description").grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.info_entry = tk.Entry(top, width=36)
        self.info_entry.grid(row=1, column=1, sticky="ew", padx=(6, 12), pady=(0, 4))
        self.info_entry.bind("<KeyRelease>", self.on_field_edited)
        tk.Label(top, text="Image key").grid(row=2, column=0, sticky="w")
        self.image_entry = ttk.Combobox(top, values=self.god_image_keys, width=33)
        self.image_entry.grid(row=2, column=1, sticky="ew", padx=(6, 12))
        self.image_entry.bind("<<ComboboxSelected>>", self.on_field_edited)
        self.image_entry.bind("<KeyRelease>", self.on_field_edited)
        tk.Button(top, text="Refresh Images", command=self.refresh_image_lists).grid(
            row=2, column=2, sticky="w"
        )
        top.columnconfigure(1, weight=1)
        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=4)
        left = tk.LabelFrame(main, text="Scene Navigator", padx=8, pady=8)
        main.add(left, weight=1)
        tk.Label(left, textvariable=self.scene_summary_var, anchor="w").pack(
            fill="x", pady=(0, 6)
        )
        scene_search = tk.Frame(left)
        scene_search.pack(fill="x", pady=(0, 6))
        tk.Label(scene_search, text="Find").pack(side="left")
        self.scene_search_entry = tk.Entry(
            scene_search, textvariable=self.scene_search_var, width=14
        )
        self.scene_search_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self.scene_search_entry.bind("<KeyRelease>", self.on_scene_search_changed)
        self.scene_search_entry.bind("<Return>", self.open_first_scene_match)
        self.scene_search_entry.bind("<Escape>", self.clear_scene_search)
        tk.Button(
            scene_search, text="X", width=2, command=self.clear_scene_search
        ).pack(side="left", padx=(4, 0))
        scene_filters = tk.Frame(left)
        scene_filters.pack(fill="x", pady=(0, 4))
        tk.Checkbutton(
            scene_filters,
            text="Show only scenes with errors",
            variable=self.scene_issues_only_var,
            command=self.on_scene_filter_changed,
        ).pack(side="left")
        scene_list_box = tk.Frame(left)
        scene_list_box.pack(fill="both", expand=True)
        self.scene_list = tk.Listbox(scene_list_box, width=24, height=24)
        self.scene_list.pack(side="left", fill="both", expand=True)
        scene_scroll = tk.Scrollbar(scene_list_box, command=self.scene_list.yview)
        scene_scroll.pack(side="right", fill="y")
        self.scene_list.configure(yscrollcommand=scene_scroll.set)
        self.scene_list.bind("<<ListboxSelect>>", self.on_scene_selected)
        self.root.bind_all("<Command-f>", self.focus_scene_search)
        self.root.bind_all("<Control-f>", self.focus_scene_search)
        scene_actions = tk.LabelFrame(left, text="Scene Actions", padx=6, pady=6)
        scene_actions.pack(fill="x", pady=(8, 0))
        create_buttons = tk.Frame(scene_actions)
        create_buttons.pack(fill="x")
        tk.Button(
            create_buttons, width=12, text="New Root", command=self.create_root
        ).pack(side="left")
        tk.Button(
            create_buttons, width=12, text="New Scene", command=self.create_scene
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            create_buttons, width=12, text="Add Child", command=self.add_child
        ).pack(side="left", padx=(6, 0))
        manage_buttons = tk.Frame(scene_actions)
        manage_buttons.pack(fill="x", pady=(6, 0))
        tk.Button(
            manage_buttons, width=12, text="Duplicate", command=self.duplicate_scene
        ).pack(side="left")
        tk.Button(
            manage_buttons, width=12, text="Rename", command=self.rename_scene
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            manage_buttons, width=12, text="Delete", command=self.delete_scene
        ).pack(side="left", padx=(6, 0))
        order_buttons = tk.Frame(scene_actions)
        order_buttons.pack(fill="x", pady=(6, 0))
        tk.Button(
            order_buttons, width=12, text="Move Up", command=lambda: self.move_scene(-1)
        ).pack(side="left")
        tk.Button(
            order_buttons,
            width=12,
            text="Move Down",
            command=lambda: self.move_scene(1),
        ).pack(side="left", padx=(6, 0))
        right = tk.Frame(main)
        main.add(right, weight=3)
        scene_editor_box = tk.LabelFrame(right, text="Scene Editor", padx=8, pady=8)
        scene_editor_box.pack(fill="both", expand=True)
        row1 = tk.Frame(scene_editor_box)
        row1.pack(fill="x")
        tk.Label(row1, text="Scene ID").pack(side="left")
        self.scene_id_entry = tk.Entry(row1, width=14)
        self.scene_id_entry.pack(side="left", padx=(6, 12))
        self.scene_id_entry.bind("<KeyRelease>", self.on_field_edited)
        tk.Label(row1, text="Image key").pack(side="left")
        self.scene_image_entry = ttk.Combobox(
            row1, values=self.scene_image_keys, width=24
        )
        self.scene_image_entry.pack(side="left", fill="x", expand=True, padx=(6, 8))
        self.scene_image_entry.bind("<<ComboboxSelected>>", self.on_field_edited)
        self.scene_image_entry.bind("<KeyRelease>", self.on_field_edited)
        tk.Button(row1, text="Save Scene", command=self.save_scene).pack(side="left")
        tk.Button(row1, text="Validate", command=self.validate_and_show).pack(
            side="left", padx=(6, 0)
        )
        tk.Label(scene_editor_box, text="Scene Text").pack(anchor="w", pady=(8, 2))
        self.scene_text = tk.Text(scene_editor_box, height=8, width=60)
        self.scene_text.pack(fill="x")
        self.scene_text.bind("<KeyRelease>", self.on_field_edited)
        choices_box = tk.LabelFrame(scene_editor_box, text="Choices", padx=6, pady=6)
        choices_box.pack(fill="both", expand=True, pady=(8, 0))
        choice_list_row = tk.Frame(choices_box)
        choice_list_row.pack(fill="both", expand=True)
        self.choice_list = tk.Listbox(choice_list_row, height=8, exportselection=False)
        self.choice_list.pack(side="left", fill="both", expand=True)
        choice_scroll = tk.Scrollbar(choice_list_row, command=self.choice_list.yview)
        choice_scroll.pack(side="right", fill="y")
        self.choice_list.configure(yscrollcommand=choice_scroll.set)
        self.choice_list.bind("<<ListboxSelect>>", self.on_choice_selected)
        choice_editor = tk.Frame(choices_box)
        choice_editor.pack(fill="x", pady=(6, 0))
        tk.Label(choice_editor, text="Targets").grid(row=0, column=0, sticky="w")
        self.choice_targets_entry = tk.Entry(choice_editor)
        self.choice_targets_entry.grid(row=0, column=1, sticky="ew", padx=(6, 10))
        tk.Label(choice_editor, text="Label").grid(
            row=1, column=0, sticky="w", pady=(4, 0)
        )
        self.choice_text_entry = tk.Entry(choice_editor)
        self.choice_text_entry.grid(
            row=1, column=1, sticky="ew", padx=(6, 10), pady=(4, 0)
        )
        choice_editor.columnconfigure(1, weight=1)
        choice_buttons = tk.Frame(choices_box)
        choice_buttons.pack(fill="x", pady=(6, 0))
        tk.Button(choice_buttons, text="New", command=self.new_choice).pack(side="left")
        tk.Button(choice_buttons, text="Apply", command=self.apply_choice).pack(
            side="left", padx=(4, 0)
        )
        tk.Button(choice_buttons, text="Delete", command=self.delete_choice).pack(
            side="left", padx=(4, 0)
        )
        tk.Button(choice_buttons, text="Up", command=lambda: self.move_choice(-1)).pack(
            side="left", padx=(12, 0)
        )
        tk.Button(
            choice_buttons, text="Down", command=lambda: self.move_choice(1)
        ).pack(side="left", padx=(4, 0))
        tk.Button(
            choice_buttons, text="Go To", command=self.jump_to_choice_target
        ).pack(side="left", padx=(12, 0))
        validation_box = tk.LabelFrame(right, text="Validation", padx=8, pady=8)
        validation_box.pack(fill="both", expand=True, pady=(8, 0))
        tk.Label(
            validation_box, textvariable=self.validation_summary_var, anchor="w"
        ).pack(fill="x", pady=(0, 6))
        validation_tabs = ttk.Notebook(validation_box)
        validation_tabs.pack(fill="both", expand=True)
        project_tab = tk.Frame(validation_tabs)
        scene_tab = tk.Frame(validation_tabs)
        validation_tabs.add(project_tab, text="Project")
        validation_tabs.add(scene_tab, text="Selected Scene")
        self.project_console = tk.Text(project_tab, height=6, wrap="word")
        self.project_console.pack(fill="both", expand=True)
        self.project_console.configure(state="disabled")
        self.scene_console = tk.Text(scene_tab, height=6, wrap="word")
        self.scene_console.pack(fill="both", expand=True)
        self.scene_console.configure(state="disabled")
        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=8, pady=(4, 8))
        file_actions = tk.Frame(bottom)
        file_actions.pack(side="left")
        tk.Button(file_actions, text="New", command=self.new_file).pack(side="left")
        tk.Button(file_actions, text="Load", command=self.load_file).pack(
            side="left", padx=(4, 0)
        )
        tk.Button(file_actions, text="Save", command=self.save_file).pack(
            side="left", padx=(4, 0)
        )
        tk.Button(file_actions, text="Save As", command=self.save_file_as).pack(
            side="left", padx=(4, 0)
        )
        tk.Button(file_actions, text="Repair", command=self.repair_file).pack(
            side="left", padx=(4, 0)
        )
        tk.Label(bottom, textvariable=self.status_var, anchor="w").pack(
            side="left", fill="x", expand=True, padx=(12, 0)
        )
        tk.Label(bottom, textvariable=self.validation_summary_var, anchor="e").pack(
            side="right"
        )

    def _list_image_keys(self, folder: str) -> list[str]:
        keys = []
        if os.path.isdir(folder):
            for file_name in sorted(os.listdir(folder)):
                path = os.path.join(folder, file_name)
                if os.path.isfile(path):
                    name, _ext = os.path.splitext(file_name)
                    keys.append(name)
        return keys

    def refresh_image_lists(self):
        self.god_image_keys = self._list_image_keys(GOD_IMAGE_DIR)
        self.scene_image_keys = self._list_image_keys(SCENE_IMAGE_DIR)
        self.image_entry["values"] = self.god_image_keys
        self.scene_image_entry["values"] = self.scene_image_keys
        self.set_status("Image lists refreshed")

    def set_status(self, text):
        self.status_var.set(text)

    def set_dirty(self, dirty=True):
        self.dirty = dirty
        self._update_title()

    def _filtered_scene_ids(self):
        query = self.scene_search_var.get().strip().lower()
        scene_ids = list(self.data["scene_order"])
        if query:
            scene_ids = [
                scene_id for scene_id in scene_ids if query in scene_id.lower()
            ]
        if self.scene_issues_only_var.get():
            issue_map = self._scene_issue_map()
            scene_ids = [scene_id for scene_id in scene_ids if issue_map.get(scene_id)]
        return scene_ids

    def _scene_issue_map(self):
        _errors, _warnings, scene_errors = self._validate_data_details()
        return scene_errors

    def _set_console_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def _refresh_error_consoles(self):
        errors, warnings, scene_errors = self._validate_data_details()
        self.validation_summary_var.set(
            f"Validation: {len(errors)} error(s), {len(warnings)} warning(s)"
        )
        chunks = []
        if errors:
            chunks.append("Errors:\n- " + "\n- ".join(errors))
        if warnings:
            chunks.append("Warnings:\n- " + "\n- ".join(warnings))
        if not chunks:
            chunks.append("No issues found.")
        self._set_console_text(self.project_console, "\n\n".join(chunks))
        selected_scene_id = self.scene_id_entry.get().strip() or self.current_scene
        if not selected_scene_id:
            self._set_console_text(
                self.scene_console, "Select a scene to see scene-specific errors."
            )
            return
        current_scene_errors = scene_errors.get(selected_scene_id, [])
        if current_scene_errors:
            self._set_console_text(
                self.scene_console,
                f"Errors for {selected_scene_id}:\n- "
                + "\n- ".join(current_scene_errors),
            )
        else:
            self._set_console_text(
                self.scene_console,
                f"No errors in selected scene ({selected_scene_id}).",
            )

    def on_scene_filter_changed(self):
        matching_ids = self._filtered_scene_ids()
        select_id = self.current_scene if self.current_scene in matching_ids else None
        self.refresh_scene_list(select_id=select_id, load_editor=False)
        if self.scene_issues_only_var.get():
            self.set_status(f"Showing {len(matching_ids)} scene(s) with errors")
        else:
            self.set_status("Showing all scenes")

    def focus_scene_search(self, _event=None):
        self.scene_search_entry.focus_set()
        self.scene_search_entry.selection_range(0, tk.END)
        return "break"

    def clear_scene_search(self, _event=None):
        had_query = bool(self.scene_search_var.get().strip())
        self.scene_search_var.set("")
        self.refresh_scene_list(select_id=self.current_scene, load_editor=False)
        if had_query:
            self.set_status("Scene search cleared")
        if _event is not None:
            return "break"
        return None

    def on_scene_search_changed(self, _event=None):
        matching_ids = self._filtered_scene_ids()
        select_id = self.current_scene if self.current_scene in matching_ids else None
        self.refresh_scene_list(select_id=select_id, load_editor=False)
        if self.scene_search_var.get().strip():
            self.set_status(f"Found {len(matching_ids)} matching scene(s)")

    def open_first_scene_match(self, _event=None):
        matching_ids = self._filtered_scene_ids()
        if not matching_ids:
            self.set_status("No scenes match the current search")
            return "break"
        self.refresh_scene_list(select_id=matching_ids[0])
        return "break"

    def on_field_edited(self, _event=None):
        if self._suspend_dirty_tracking:
            return
        self.set_dirty()
        self._refresh_error_consoles()

    def _update_title(self):
        name = Path(self.current_file).name if self.current_file else "untitled"
        marker = " *" if self.dirty else ""
        self.root.title(f"{self.title_var} - {name}{marker}")

    def sync_info_to_data(self):
        self.data["info"]["name"] = self.name_entry.get().strip()
        self.data["info"]["info"] = self.info_entry.get().strip()
        self.data["info"]["image"] = self.image_entry.get().strip()

    def load_info_from_data(self):
        self._suspend_dirty_tracking = True
        info = self.data["info"]
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, info.get("name", ""))
        self.info_entry.delete(0, tk.END)
        self.info_entry.insert(0, info.get("info", ""))
        self.image_entry.set(info.get("image", ""))
        self._suspend_dirty_tracking = False

    def confirm_discard_changes(self):
        if not self._ensure_current_scene_saved():
            return False
        if not self.dirty:
            return True
        return messagebox.askyesno("Unsaved Changes", "Discard unsaved changes?")

    def new_file(self, skip_prompt=False):
        if not skip_prompt and (not self.confirm_discard_changes()):
            return
        self.current_file = None
        self.data = self._blank_data()
        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None
        self.scene_search_var.set("")
        self.scene_issues_only_var.set(False)
        self.load_info_from_data()
        self.refresh_scene_list()
        self.clear_scene_editor()
        self._refresh_error_consoles()
        self.set_dirty(False)
        self.set_status("New god file")

    def _next_scene_id(self, prefix="a"):
        prefix = (prefix or "a").strip().lower()[:1]
        if not prefix.isalpha():
            prefix = "a"
        idx = 1
        while f"{prefix}{idx}" in self.data["scenes"]:
            idx += 1
        return f"{prefix}{idx}"

    def create_root(self):
        if not self._ensure_current_scene_saved():
            return
        if "a1" in self.data["scenes"]:
            messagebox.showinfo("Root Exists", "Scene a1 already exists.")
            return
        self.data["scenes"]["a1"] = self._blank_scene()
        self.data["scene_order"].insert(0, "a1")
        self.refresh_scene_list(select_id="a1")
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status("Created root scene a1")

    def create_scene(self):
        if not self._ensure_current_scene_saved():
            return
        suggested = self._next_scene_id()
        scene_id = simpledialog.askstring(
            "New Scene", "Scene ID:", initialvalue=suggested
        )
        if scene_id is None:
            return
        scene_id = scene_id.strip()
        if not scene_id:
            messagebox.showerror("Invalid ID", "Scene ID cannot be empty.")
            return
        if scene_id in self.data["scenes"]:
            messagebox.showerror("Duplicate ID", f"Scene {scene_id} already exists.")
            return
        self.data["scenes"][scene_id] = self._blank_scene()
        self.data["scene_order"].append(scene_id)
        self.refresh_scene_list(select_id=scene_id)
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status(f"Created scene {scene_id}")

    def add_child(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            messagebox.showinfo("Select Scene", "Select a parent scene first.")
            return
        parent = self.current_scene
        first_char = parent[0].lower() if parent else "a"
        next_prefix = (
            chr(min(ord(first_char) + 1, ord("z"))) if first_char.isalpha() else "b"
        )
        new_id = self._next_scene_id(next_prefix)
        self.data["scenes"][new_id] = self._blank_scene()
        self.data["scene_order"].append(new_id)
        self.data["scenes"][parent]["choices"].append(
            {"targets": [new_id], "text": f"Go to {new_id}"}
        )
        self.refresh_scene_list(select_id=new_id)
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status(f"Added child scene {new_id} from {parent}")

    def duplicate_scene(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            return
        source_id = self.current_scene
        suggested = self._next_scene_id(source_id[0] if source_id else "a")
        new_id = simpledialog.askstring(
            "Duplicate Scene", "New Scene ID:", initialvalue=suggested
        )
        if new_id is None:
            return
        new_id = new_id.strip()
        if not new_id or new_id in self.data["scenes"]:
            messagebox.showerror("Invalid ID", "Choose a unique non-empty scene ID.")
            return
        self.data["scenes"][new_id] = copy.deepcopy(self.data["scenes"][source_id])
        insert_at = self.data["scene_order"].index(source_id) + 1
        self.data["scene_order"].insert(insert_at, new_id)
        self.refresh_scene_list(select_id=new_id)
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status(f"Duplicated {source_id} -> {new_id}")

    def _split_weighted_target(self, token):
        token = token.strip()
        if "*" in token:
            base, weight = token.rsplit("*", 1)
            return (base.strip(), weight.strip())
        return (token, None)

    def _replace_scene_target(self, token, old_id, new_id):
        base, weight = self._split_weighted_target(token)
        if base != old_id:
            return token
        if weight is None or weight == "":
            return new_id
        return f"{new_id}*{weight}"

    def _rename_scene_id(self, old_id, new_id):
        self.data["scenes"][new_id] = self.data["scenes"].pop(old_id)
        for idx, sid in enumerate(self.data["scene_order"]):
            if sid == old_id:
                self.data["scene_order"][idx] = new_id
                break
        for scene in self.data["scenes"].values():
            for choice in scene["choices"]:
                choice["targets"] = [
                    self._replace_scene_target(token, old_id, new_id)
                    for token in choice.get("targets", [])
                ]
        self.current_scene = (
            new_id if self.current_scene == old_id else self.current_scene
        )

    def rename_scene(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            return
        old_id = self.current_scene
        new_id = simpledialog.askstring(
            "Rename Scene", "New Scene ID:", initialvalue=old_id
        )
        if new_id is None:
            return
        new_id = new_id.strip()
        if not new_id:
            messagebox.showerror("Invalid ID", "Scene ID cannot be empty.")
            return
        if new_id != old_id and new_id in self.data["scenes"]:
            messagebox.showerror("Duplicate ID", f"Scene {new_id} already exists.")
            return
        if new_id != old_id:
            self._rename_scene_id(old_id, new_id)
            self.refresh_scene_list(select_id=new_id)
            self.load_scene_into_editor(new_id)
            self.set_dirty()
            self._refresh_error_consoles()
            self.set_status(f"Renamed {old_id} -> {new_id}")

    def delete_scene(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            return
        sid = self.current_scene
        if not messagebox.askyesno("Delete Scene", f"Delete scene {sid}?"):
            return
        del self.data["scenes"][sid]
        self.data["scene_order"] = [x for x in self.data["scene_order"] if x != sid]
        for scene in self.data["scenes"].values():
            new_choices = []
            for choice in scene["choices"]:
                kept = []
                for token in choice.get("targets", []):
                    base, _weight = self._split_weighted_target(token)
                    if base != sid:
                        kept.append(token)
                if kept:
                    new_choices.append(
                        {"targets": kept, "text": choice.get("text", "")}
                    )
            scene["choices"] = new_choices
        self.current_scene = None
        self.current_choices = []
        self.refresh_scene_list()
        self.clear_scene_editor()
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status(f"Deleted scene {sid}")

    def move_scene(self, direction):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            return
        order = self.data["scene_order"]
        idx = order.index(self.current_scene)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(order):
            return
        order[idx], order[new_idx] = (order[new_idx], order[idx])
        self.refresh_scene_list(select_id=self.current_scene)
        self.set_dirty()
        self._refresh_error_consoles()

    def refresh_scene_list(self, select_id=None, load_editor=True):
        self._selection_guard_enabled = False
        scene_ids = self._filtered_scene_ids()
        if (
            select_id
            and select_id not in scene_ids
            and self.scene_search_var.get().strip()
        ):
            self.scene_search_var.set("")
            scene_ids = list(self.data["scene_order"])
        self.scene_summary_var.set(
            f"Scenes: {len(self.data['scenes'])} total · {len(scene_ids)} shown"
        )
        self.scene_list.delete(0, tk.END)
        for scene_id in scene_ids:
            self.scene_list.insert(tk.END, scene_id)
        if select_id and select_id in scene_ids:
            idx = scene_ids.index(select_id)
            self.scene_list.selection_set(idx)
            self.scene_list.activate(idx)
            self.scene_list.see(idx)
            if load_editor:
                self.on_scene_selected(None)
        self._selection_guard_enabled = True

    def clear_scene_editor(self):
        self._suspend_dirty_tracking = True
        self.scene_id_entry.delete(0, tk.END)
        self.scene_image_entry.set("")
        self.scene_text.delete("1.0", tk.END)
        self.current_choices = []
        self.selected_choice_index = None
        self.refresh_choice_list()
        self.clear_choice_editor()
        self._suspend_dirty_tracking = False
        self._refresh_error_consoles()

    def load_scene_into_editor(self, scene_id):
        self._suspend_dirty_tracking = True
        scene = self.data["scenes"][scene_id]
        self.current_scene = scene_id
        self.scene_id_entry.delete(0, tk.END)
        self.scene_id_entry.insert(0, scene_id)
        self.scene_image_entry.set(scene.get("image", ""))
        self.scene_text.delete("1.0", tk.END)
        self.scene_text.insert("1.0", scene.get("text", ""))
        self.current_choices = copy.deepcopy(scene.get("choices", []))
        self.selected_choice_index = None
        self.refresh_choice_list()
        self.clear_choice_editor()
        self._suspend_dirty_tracking = False
        self._refresh_error_consoles()

    def on_scene_selected(self, _event):
        sel = self.scene_list.curselection()
        if not sel:
            return
        sid = self.scene_list.get(sel[0])
        if self._selection_guard_enabled and sid != self.current_scene:
            if not self._ensure_current_scene_saved():
                self.refresh_scene_list(select_id=self.current_scene, load_editor=False)
                return
        self.load_scene_into_editor(sid)
        self._refresh_error_consoles()
        self.set_status(f"Editing scene {sid}")

    def _format_choice_line(self, idx, choice):
        targets = ", ".join(choice.get("targets", []))
        text = choice.get("text", "")
        return f"{idx + 1:02d}. [{targets}] {text}"

    def refresh_choice_list(self):
        self.choice_list.delete(0, tk.END)
        for idx, choice in enumerate(self.current_choices):
            self.choice_list.insert(tk.END, self._format_choice_line(idx, choice))
        if (
            self.selected_choice_index is not None
            and 0 <= self.selected_choice_index < len(self.current_choices)
        ):
            self.choice_list.selection_set(self.selected_choice_index)

    def clear_choice_editor(self):
        self.choice_targets_entry.delete(0, tk.END)
        self.choice_text_entry.delete(0, tk.END)

    def on_choice_selected(self, _event):
        sel = self.choice_list.curselection()
        if not sel:
            if (
                self.selected_choice_index is not None
                and 0 <= self.selected_choice_index < len(self.current_choices)
            ):
                return
            self.selected_choice_index = None
            self.clear_choice_editor()
            return
        idx = sel[0]
        self.selected_choice_index = idx
        choice = self.current_choices[idx]
        self.choice_targets_entry.delete(0, tk.END)
        self.choice_targets_entry.insert(0, ", ".join(choice.get("targets", [])))
        self.choice_text_entry.delete(0, tk.END)
        self.choice_text_entry.insert(0, choice.get("text", ""))

    def _parse_targets(self, raw):
        return [token.strip() for token in raw.split(",") if token.strip()]

    def new_choice(self):
        self.selected_choice_index = None
        self.choice_list.selection_clear(0, tk.END)
        self.clear_choice_editor()

    def apply_choice(self):
        targets = self._parse_targets(self.choice_targets_entry.get())
        text = self.choice_text_entry.get().strip()
        if not targets:
            messagebox.showerror(
                "Invalid Choice", "Choice must have at least one target."
            )
            return
        choice = {"targets": targets, "text": text}
        if self.selected_choice_index is None:
            self.current_choices.append(choice)
            self.selected_choice_index = len(self.current_choices) - 1
        else:
            self.current_choices[self.selected_choice_index] = choice
        self.refresh_choice_list()
        self.set_dirty()
        self._refresh_error_consoles()

    def delete_choice(self):
        if self.selected_choice_index is None:
            return
        del self.current_choices[self.selected_choice_index]
        self.selected_choice_index = None
        self.refresh_choice_list()
        self.clear_choice_editor()
        self.set_dirty()
        self._refresh_error_consoles()

    def move_choice(self, direction):
        if self.selected_choice_index is None:
            return
        idx = self.selected_choice_index
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self.current_choices):
            return
        self.current_choices[idx], self.current_choices[new_idx] = (
            self.current_choices[new_idx],
            self.current_choices[idx],
        )
        self.selected_choice_index = new_idx
        self.refresh_choice_list()
        self.set_dirty()
        self._refresh_error_consoles()

    def jump_to_choice_target(self):
        if self.selected_choice_index is None:
            return
        choice = self.current_choices[self.selected_choice_index]
        targets = cast(list[str], choice.get("targets", []))
        if not targets:
            return
        base, _weight = self._split_weighted_target(targets[0])
        if base not in self.data["scenes"]:
            messagebox.showinfo(
                "Missing Target", f"Target scene {base} does not exist."
            )
            return
        self.refresh_scene_list(select_id=base)

    def _scene_payload_from_editor(self):
        scene_id = self.scene_id_entry.get().strip()
        text = self.scene_text.get("1.0", tk.END).rstrip("\n")
        image = self.scene_image_entry.get().strip()
        choices = copy.deepcopy(self.current_choices)
        return (scene_id, {"text": text, "image": image, "choices": choices})

    def save_scene(self):
        if self.current_scene is None and (not self.scene_id_entry.get().strip()):
            messagebox.showinfo("No Scene", "Select or create a scene first.")
            return False
        scene_id, payload = self._scene_payload_from_editor()
        if not scene_id:
            messagebox.showerror("Invalid ID", "Scene ID cannot be empty.")
            return False
        old_id = self.current_scene
        if old_id is None:
            if scene_id in self.data["scenes"]:
                messagebox.showerror(
                    "Duplicate ID", f"Scene {scene_id} already exists."
                )
                return False
            self.data["scenes"][scene_id] = payload
            self.data["scene_order"].append(scene_id)
        else:
            if scene_id != old_id:
                if scene_id in self.data["scenes"]:
                    messagebox.showerror(
                        "Duplicate ID", f"Scene {scene_id} already exists."
                    )
                    return False
                self._rename_scene_id(old_id, scene_id)
            self.data["scenes"][scene_id] = payload
        self.current_scene = scene_id
        self.refresh_scene_list(select_id=scene_id)
        self.set_dirty()
        self._refresh_error_consoles()
        self.set_status(f"Saved scene {scene_id}")
        return True

    def load_file(self):
        if not self.confirm_discard_changes():
            return
        path = filedialog.askopenfilename(
            initialdir=DEFAULT_GODS_DIR,
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                self.data = self._parse_god_file(f.read())
        except Exception as exc:
            messagebox.showerror("Load Failed", str(exc))
            return
        self.current_file = path
        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None
        self.scene_search_var.set("")
        self.scene_issues_only_var.set(False)
        self.load_info_from_data()
        self.refresh_scene_list()
        self.clear_scene_editor()
        self._refresh_error_consoles()
        self.set_dirty(False)
        self.set_status(f"Loaded {Path(path).name}")

    def save_file(self):
        if self.current_file:
            self._write_file(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            initialdir=DEFAULT_GODS_DIR,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._write_file(path)

    def repair_file(self):
        if not self._ensure_current_scene_saved():
            return False
        source_text = self.export_text()
        report = RepairReport()
        parsed = parse_god_text(source_text, report)
        info, scenes = normalize_god(parsed, report)
        if report.errors:
            messagebox.showerror(
                "Repair Failed",
                "Repair could not continue:\n- " + "\n- ".join(report.errors),
            )
            return False
        repaired_text = export_god_text(info, scenes)
        validation_errors, validation_warnings = validate_repaired_data(info, scenes)
        report.errors.extend(validation_errors)
        report.warnings.extend(validation_warnings)
        unresolved_errors = list(report.errors)
        previous_file = self.current_file
        previous_dirty = self.dirty
        repaired_path = Path(previous_file) if previous_file else None
        if repaired_path is not None:
            try:
                disk_text = repaired_path.read_text(encoding="utf-8")
            except Exception as exc:
                messagebox.showerror(
                    "Repair Failed", f"Failed to read {repaired_path.name}: {exc}"
                )
                return False
            if disk_text != repaired_text:
                try:
                    repaired_path.write_text(repaired_text, encoding="utf-8")
                except Exception as exc:
                    messagebox.showerror("Repair Failed", str(exc))
                    return False
        old_scene_id = self.current_scene
        try:
            self.data = self._parse_god_file(repaired_text)
        except Exception as exc:
            messagebox.showerror(
                "Repair Failed", f"Repaired data could not be reloaded: {exc}"
            )
            return False
        self.load_info_from_data()
        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None
        selected_scene_id = (
            old_scene_id if old_scene_id in self.data["scenes"] else None
        )
        if selected_scene_id is None and self.data["scene_order"]:
            selected_scene_id = self.data["scene_order"][0]
        if selected_scene_id is not None:
            self.refresh_scene_list(select_id=selected_scene_id)
        else:
            self.refresh_scene_list()
            self.clear_scene_editor()
        if repaired_path is not None:
            self.set_dirty(False)
        else:
            self.set_dirty(previous_dirty or source_text != repaired_text)
        self._refresh_error_consoles()
        fix_count = len(report.fixes)
        warning_count = len(report.warnings)
        if source_text == repaired_text:
            self.set_status(
                f"Repair checked {(repaired_path.name if repaired_path else 'current file')}"
            )
        else:
            self.set_status(
                f"Repaired {(repaired_path.name if repaired_path else 'current file')}"
                + (
                    f" ({fix_count} fix(es), {warning_count} warning(s))"
                    if fix_count or warning_count
                    else ""
                )
            )
        if unresolved_errors:
            messagebox.showwarning(
                "Repair Completed with Errors",
                "Repair applied, but unresolved errors remain:\n- "
                + "\n- ".join(unresolved_errors),
            )
        elif report.fixes:
            messagebox.showinfo(
                "Repair Complete",
                "Fixes applied:\n- "
                + "\n- ".join(report.fixes)
                + (
                    "\n\nWarnings:\n- " + "\n- ".join(report.warnings)
                    if report.warnings
                    else ""
                ),
            )
        elif report.warnings and source_text != repaired_text:
            messagebox.showinfo(
                "Repair Complete", "Warnings:\n- " + "\n- ".join(report.warnings)
            )
        return True

    def _write_file(self, path: str) -> bool:
        if not self._ensure_current_scene_saved():
            return False
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.export_text())
        except Exception as exc:
            messagebox.showerror("Save Failed", str(exc))
            return False
        self.current_file = path
        self.set_dirty(False)
        self.set_status(f"Saved {Path(path).name}")
        return True

    def _parse_god_file(self, text):
        data: dict[str, Any] = self._blank_data()
        mode = None
        current_id = None
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line == "#info":
                mode = "info"
                continue
            if line == "#tree":
                mode = "tree"
                continue
            if mode == "info":
                if line.startswith("name: "):
                    data["info"]["name"] = line[len("name: ") :].strip()
                elif line.startswith("info: "):
                    data["info"]["info"] = line[len("info: ") :].strip()
                elif line.startswith("image: "):
                    data["info"]["image"] = line[len("image: ") :].strip()
                elif ":" in line:
                    key, value = line.split(":", 1)
                    data["info"][key.strip()] = value.strip()
                continue
            if mode == "tree":
                if line.startswith("##"):
                    current_id = line[2:].strip()
                    if not current_id:
                        continue
                    data["scenes"][current_id] = self._blank_scene()
                    data["scene_order"].append(current_id)
                elif current_id:
                    scene = data["scenes"][current_id]
                    if line.startswith("text: "):
                        scene["text"] = line[len("text: ") :].strip()
                    elif line.startswith("text:"):
                        scene["text"] = line[len("text:") :].strip()
                    elif line.startswith("image: "):
                        scene["image"] = line[len("image: ") :].strip()
                    elif line.startswith("image:"):
                        scene["image"] = line[len("image:") :].strip()
                    elif ": " in line:
                        target_raw, label = line.split(": ", 1)
                        targets = self._parse_targets(target_raw)
                        if targets:
                            scene["choices"].append(
                                {"targets": targets, "text": label.strip()}
                            )
                    elif scene["text"]:
                        scene["text"] += "\n" + line
                    else:
                        scene["text"] = line
        return data

    def _reachable_scenes(self, data=None):
        data = data or self.data
        if not data["scene_order"]:
            return set()
        start = data["scene_order"][0]
        visited = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited or current not in data["scenes"]:
                continue
            visited.add(current)
            for choice in data["scenes"][current].get("choices", []):
                for token in choice.get("targets", []):
                    target, _weight = self._split_weighted_target(token)
                    if target in data["scenes"] and target not in visited:
                        stack.append(target)
        return visited

    def _detect_loop(self, data=None):
        data = data or self.data
        temp_mark = set()
        perm_mark = set()

        def visit(node):
            if node in perm_mark:
                return False
            if node in temp_mark:
                return True
            temp_mark.add(node)
            for choice in data["scenes"][node].get("choices", []):
                for token in choice.get("targets", []):
                    target, _weight = self._split_weighted_target(token)
                    if target in data["scenes"] and visit(target):
                        return True
            temp_mark.remove(node)
            perm_mark.add(node)
            return False

        for scene_id in data["scene_order"]:
            if scene_id in data["scenes"] and visit(scene_id):
                return True
        return False

    def validate_data(self):
        errors, warnings, _scene_errors = self._validate_data_details()
        return (errors, warnings)

    def _validation_snapshot_data(self):
        data: dict[str, Any] = copy.deepcopy(self.data)
        data["info"]["name"] = self.name_entry.get().strip()
        data["info"]["info"] = self.info_entry.get().strip()
        data["info"]["image"] = self.image_entry.get().strip()
        scene_id, payload = self._scene_payload_from_editor()
        if not scene_id:
            return data
        old_id = self.current_scene
        if old_id and old_id in data["scenes"] and (old_id != scene_id):
            data["scenes"].pop(old_id, None)
            data["scenes"][scene_id] = payload
            data["scene_order"] = [
                scene_id if sid == old_id else sid for sid in data["scene_order"]
            ]
        else:
            data["scenes"][scene_id] = payload
            if scene_id not in data["scene_order"]:
                data["scene_order"].append(scene_id)
        return data

    def _validate_data_details(self):
        data = self._validation_snapshot_data()
        errors = []
        warnings = []
        scene_errors = {scene_id: [] for scene_id in data["scene_order"]}
        info = data["info"]
        if not info.get("name", "").strip():
            errors.append("Missing god name.")
        if not info.get("info", "").strip():
            warnings.append("God info/description is empty.")
        god_image = info.get("image", "").strip()
        if not god_image:
            errors.append("Missing god image key.")
        elif self.god_image_keys and god_image not in self.god_image_keys:
            warnings.append(
                f"God image '{god_image}' is not found in assets/data/thumbnails."
            )
        if not data["scene_order"]:
            errors.append("No scenes defined.")
            return (errors, warnings, scene_errors)
        if data["scene_order"][0] != "a1":
            warnings.append(
                f"First scene is '{data['scene_order'][0]}', not 'a1'. The first listed scene is the start scene."
            )
        for scene_id in data["scene_order"]:
            scene = data["scenes"].get(scene_id)
            if scene is None:
                msg = f"Scene order references missing scene '{scene_id}'."
                errors.append(msg)
                scene_errors.setdefault(scene_id, []).append(msg)
                continue
            if not scene.get("text", "").strip():
                warnings.append(f"Scene '{scene_id}' has no text.")
            image_key = scene.get("image", "").strip()
            if not image_key:
                warnings.append(f"Scene '{scene_id}' has no image key.")
            elif self.scene_image_keys and image_key not in self.scene_image_keys:
                warnings.append(
                    f"Scene '{scene_id}' image '{image_key}' is not found in assets/data/scenes."
                )
            choices = scene.get("choices", [])
            if len(choices) > 26:
                msg = f"Scene '{scene_id}' has {len(choices)} choices. Game only supports up to 26 (A-Z)."
                errors.append(msg)
                scene_errors.setdefault(scene_id, []).append(msg)
            for choice_idx, choice in enumerate(choices, start=1):
                label = choice.get("text", "")
                targets = choice.get("targets", [])
                if not targets:
                    msg = f"Scene '{scene_id}' choice #{choice_idx} has no targets."
                    errors.append(msg)
                    scene_errors.setdefault(scene_id, []).append(msg)
                if not label.strip():
                    warnings.append(
                        f"Scene '{scene_id}' choice #{choice_idx} has empty label."
                    )
                for token in targets:
                    target_id, weight = self._split_weighted_target(token)
                    if not target_id:
                        msg = f"Scene '{scene_id}' choice #{choice_idx} has invalid target token '{token}'."
                        errors.append(msg)
                        scene_errors.setdefault(scene_id, []).append(msg)
                        continue
                    if weight is not None:
                        try:
                            if float(weight) <= 0:
                                msg = f"Scene '{scene_id}' choice #{choice_idx} has non-positive weight in '{token}'."
                                errors.append(msg)
                                scene_errors.setdefault(scene_id, []).append(msg)
                        except Exception:
                            msg = f"Scene '{scene_id}' choice #{choice_idx} has invalid weight in '{token}'."
                            errors.append(msg)
                            scene_errors.setdefault(scene_id, []).append(msg)
                    if target_id not in data["scenes"]:
                        msg = f"Scene '{scene_id}' choice #{choice_idx} targets missing scene '{target_id}'."
                        errors.append(msg)
                        scene_errors.setdefault(scene_id, []).append(msg)
        reachable = self._reachable_scenes(data)
        unreachable = [sid for sid in data["scene_order"] if sid not in reachable]
        if unreachable:
            warnings.append("Unreachable scenes: " + ", ".join(unreachable))
        if self._detect_loop(data):
            warnings.append(
                "Loop detected in scene graph (allowed, but verify it is intentional)."
            )
        return (errors, warnings, scene_errors)

    def validate_and_show(self):
        errors, warnings = self.validate_data()
        if not errors and (not warnings):
            messagebox.showinfo("Validation", "No issues found.")
            return True
        chunks = []
        if errors:
            chunks.append("Errors:\n- " + "\n- ".join(errors))
        if warnings:
            chunks.append("Warnings:\n- " + "\n- ".join(warnings))
        messagebox.showwarning("Validation Results", "\n\n".join(chunks))
        return not errors

    def export_text(self):
        self.sync_info_to_data()
        lines = [
            "#info",
            f"name: {self.data['info'].get('name', '').strip()}",
            f"info: {self.data['info'].get('info', '').strip()}",
            f"image: {self.data['info'].get('image', '').strip()}",
            "",
            "#tree",
            "",
        ]
        for scene_id in self.data["scene_order"]:
            scene = self.data["scenes"][scene_id]
            lines.append(f"##{scene_id}")
            text = scene.get("text", "")
            text_lines = text.splitlines() if text else [""]
            lines.append(f"text: {(text_lines[0] if text_lines else '')}")
            for extra in text_lines[1:]:
                lines.append(extra)
            lines.append(f"image: {scene.get('image', '').strip()}")
            for choice in scene.get("choices", []):
                targets = ", ".join(choice.get("targets", []))
                label = choice.get("text", "")
                lines.append(f"{targets}: {label}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def _ensure_current_scene_saved(self):
        if not self.current_scene:
            return True
        current_in_data = self.data["scenes"].get(self.current_scene, {})
        editor_id, editor_payload = self._scene_payload_from_editor()
        if editor_id != self.current_scene or editor_payload != current_in_data:
            should_save = messagebox.askyesnocancel(
                "Unsaved Scene",
                f"Scene {self.current_scene} has unsaved edits. Save it before continuing?",
            )
            if should_save is None:
                return False
            if should_save:
                return self.save_scene()
        return True

    def on_close(self):
        if self.confirm_discard_changes():
            self.root.destroy()


def main():
    root = tk.Tk()
    GodEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
