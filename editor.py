import copy
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GODS_DIR = os.path.join(BASE_DIR, "assets", "data", "gods")
GOD_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images", "god")
SCENE_IMAGE_DIR = os.path.join(BASE_DIR, "assets", "images", "scene")


class GodEditor:
    def __init__(self, root):
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.current_file = None
        self.dirty = False

        self.data = {
            "info": {"name": "", "info": "", "image": ""},
            "scenes": {},
            "scene_order": [],
        }

        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None
        self._selection_guard_enabled = True
        self._suspend_dirty_tracking = False

        self.god_image_keys = self._list_image_keys(GOD_IMAGE_DIR)
        self.scene_image_keys = self._list_image_keys(SCENE_IMAGE_DIR)

        self._build_ui()
        self.new_file(skip_prompt=True)

    def _build_ui(self):
        self.status_var = tk.StringVar(value="Ready")
        self.title_var = "God Editor"

        top = tk.LabelFrame(self.root, text="God Info", padx=8, pady=6)
        top.pack(fill="x", padx=8, pady=(8, 4))

        tk.Label(top, text="Name").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(top, width=36)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(6, 12))
        self.name_entry.bind("<KeyRelease>", self.on_field_edited)

        tk.Label(top, text="Info").grid(row=1, column=0, sticky="w")
        self.info_entry = tk.Entry(top, width=36)
        self.info_entry.grid(row=1, column=1, sticky="ew", padx=(6, 12))
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

        main = tk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=8, pady=4)

        left = tk.LabelFrame(main, text="Scenes", padx=6, pady=6)
        left.pack(side="left", fill="y")

        self.scene_list = tk.Listbox(left, width=22, height=22)
        self.scene_list.pack(fill="y")
        self.scene_list.bind("<<ListboxSelect>>", self.on_scene_selected)

        left_btns = tk.Frame(left)
        left_btns.pack(fill="x", pady=(6, 0))
        tk.Button(left_btns, text="New Root", command=self.create_root).pack(fill="x")
        tk.Button(left_btns, text="New Scene", command=self.create_scene).pack(fill="x")
        tk.Button(left_btns, text="Add Child", command=self.add_child).pack(fill="x")
        tk.Button(left_btns, text="Duplicate", command=self.duplicate_scene).pack(fill="x")
        tk.Button(left_btns, text="Rename", command=self.rename_scene).pack(fill="x")
        tk.Button(left_btns, text="Delete", command=self.delete_scene).pack(fill="x")
        tk.Button(left_btns, text="Move Up", command=lambda: self.move_scene(-1)).pack(fill="x")
        tk.Button(left_btns, text="Move Down", command=lambda: self.move_scene(1)).pack(fill="x")

        right = tk.LabelFrame(main, text="Scene Editor", padx=8, pady=6)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        row1 = tk.Frame(right)
        row1.pack(fill="x")
        tk.Label(row1, text="Scene ID").pack(side="left")
        self.scene_id_entry = tk.Entry(row1, width=18)
        self.scene_id_entry.pack(side="left", padx=(6, 12))
        self.scene_id_entry.bind("<KeyRelease>", self.on_field_edited)

        tk.Label(row1, text="Image key").pack(side="left")
        self.scene_image_entry = ttk.Combobox(row1, values=self.scene_image_keys, width=24)
        self.scene_image_entry.pack(side="left", padx=(6, 0))
        self.scene_image_entry.bind("<<ComboboxSelected>>", self.on_field_edited)
        self.scene_image_entry.bind("<KeyRelease>", self.on_field_edited)

        tk.Label(right, text="Text").pack(anchor="w", pady=(8, 2))
        self.scene_text = tk.Text(right, height=7, width=60)
        self.scene_text.pack(fill="x")
        self.scene_text.bind("<KeyRelease>", self.on_field_edited)

        choices_box = tk.LabelFrame(right, text="Choices", padx=6, pady=6)
        choices_box.pack(fill="both", expand=True, pady=(8, 0))

        self.choice_list = tk.Listbox(choices_box, height=8)
        self.choice_list.pack(fill="both", expand=True)
        self.choice_list.bind("<<ListboxSelect>>", self.on_choice_selected)

        choice_editor = tk.Frame(choices_box)
        choice_editor.pack(fill="x", pady=(6, 0))
        tk.Label(choice_editor, text="Targets").grid(row=0, column=0, sticky="w")
        self.choice_targets_entry = tk.Entry(choice_editor)
        self.choice_targets_entry.grid(row=0, column=1, sticky="ew", padx=(6, 10))
        tk.Label(choice_editor, text="Label").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.choice_text_entry = tk.Entry(choice_editor)
        self.choice_text_entry.grid(row=1, column=1, sticky="ew", padx=(6, 10), pady=(4, 0))
        choice_editor.columnconfigure(1, weight=1)

        choice_btns = tk.Frame(choices_box)
        choice_btns.pack(fill="x", pady=(6, 0))
        tk.Button(choice_btns, text="New", command=self.new_choice).pack(side="left")
        tk.Button(choice_btns, text="Apply", command=self.apply_choice).pack(side="left", padx=(4, 0))
        tk.Button(choice_btns, text="Delete", command=self.delete_choice).pack(side="left", padx=(4, 0))
        tk.Button(choice_btns, text="Up", command=lambda: self.move_choice(-1)).pack(side="left", padx=(12, 0))
        tk.Button(choice_btns, text="Down", command=lambda: self.move_choice(1)).pack(side="left", padx=(4, 0))
        tk.Button(choice_btns, text="Go To", command=self.jump_to_choice_target).pack(side="left", padx=(12, 0))

        scene_btns = tk.Frame(right)
        scene_btns.pack(fill="x", pady=(8, 0))
        tk.Button(scene_btns, text="Save Scene", command=self.save_scene).pack(side="left")
        tk.Button(scene_btns, text="Validate", command=self.validate_and_show).pack(side="left", padx=(6, 0))

        bottom = tk.Frame(self.root)
        bottom.pack(fill="x", padx=8, pady=(4, 8))

        tk.Button(bottom, text="New", command=self.new_file).pack(side="left")
        tk.Button(bottom, text="Load", command=self.load_file).pack(side="left", padx=(4, 0))
        tk.Button(bottom, text="Save", command=self.save_file).pack(side="left", padx=(4, 0))
        tk.Button(bottom, text="Save As", command=self.save_file_as).pack(side="left", padx=(4, 0))
        tk.Label(bottom, textvariable=self.status_var, anchor="w").pack(
            side="left", fill="x", expand=True, padx=(12, 0)
        )

    def _list_image_keys(self, folder):
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

    def on_field_edited(self, _event=None):
        if self._suspend_dirty_tracking:
            return
        self.set_dirty(True)

    def _update_title(self):
        name = os.path.basename(self.current_file) if self.current_file else "untitled"
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
        if not skip_prompt and not self.confirm_discard_changes():
            return

        self.current_file = None
        self.data = {
            "info": {"name": "", "info": "", "image": ""},
            "scenes": {},
            "scene_order": [],
        }
        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None

        self.load_info_from_data()
        self.refresh_scene_list()
        self.clear_scene_editor()
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
        self.data["scenes"]["a1"] = {"text": "", "image": "", "choices": []}
        self.data["scene_order"].insert(0, "a1")
        self.refresh_scene_list(select_id="a1")
        self.set_dirty(True)
        self.set_status("Created root scene a1")

    def create_scene(self):
        if not self._ensure_current_scene_saved():
            return
        suggested = self._next_scene_id("a")
        scene_id = simpledialog.askstring("New Scene", "Scene ID:", initialvalue=suggested)
        if scene_id is None:
            return
        scene_id = scene_id.strip()
        if not scene_id:
            messagebox.showerror("Invalid ID", "Scene ID cannot be empty.")
            return
        if scene_id in self.data["scenes"]:
            messagebox.showerror("Duplicate ID", f"Scene {scene_id} already exists.")
            return
        self.data["scenes"][scene_id] = {"text": "", "image": "", "choices": []}
        self.data["scene_order"].append(scene_id)
        self.refresh_scene_list(select_id=scene_id)
        self.set_dirty(True)
        self.set_status(f"Created scene {scene_id}")

    def add_child(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            messagebox.showinfo("Select Scene", "Select a parent scene first.")
            return
        parent = self.current_scene
        first_char = parent[0].lower() if parent else "a"
        next_prefix = chr(min(ord(first_char) + 1, ord("z"))) if first_char.isalpha() else "b"
        new_id = self._next_scene_id(next_prefix)

        self.data["scenes"][new_id] = {"text": "", "image": "", "choices": []}
        self.data["scene_order"].append(new_id)
        self.data["scenes"][parent]["choices"].append(
            {"targets": [new_id], "text": f"Go to {new_id}"}
        )
        self.refresh_scene_list(select_id=new_id)
        self.set_dirty(True)
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
        self.set_dirty(True)
        self.set_status(f"Duplicated {source_id} -> {new_id}")

    def _split_weighted_target(self, token):
        token = token.strip()
        if "*" in token:
            base, weight = token.rsplit("*", 1)
            return base.strip(), weight.strip()
        return token, None

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
        self.current_scene = new_id if self.current_scene == old_id else self.current_scene

    def rename_scene(self):
        if not self._ensure_current_scene_saved():
            return
        if not self.current_scene:
            return
        old_id = self.current_scene
        new_id = simpledialog.askstring("Rename Scene", "New Scene ID:", initialvalue=old_id)
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
            self.set_dirty(True)
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
                    new_choices.append({"targets": kept, "text": choice.get("text", "")})
            scene["choices"] = new_choices

        self.current_scene = None
        self.current_choices = []
        self.refresh_scene_list()
        self.clear_scene_editor()
        self.set_dirty(True)
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
        order[idx], order[new_idx] = order[new_idx], order[idx]
        self.refresh_scene_list(select_id=self.current_scene)
        self.set_dirty(True)

    def refresh_scene_list(self, select_id=None, load_editor=True):
        self._selection_guard_enabled = False
        self.scene_list.delete(0, tk.END)
        for scene_id in self.data["scene_order"]:
            self.scene_list.insert(tk.END, scene_id)
        if select_id and select_id in self.data["scene_order"]:
            idx = self.data["scene_order"].index(select_id)
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
        self.set_status(f"Editing scene {sid}")

    def _format_choice_line(self, idx, choice):
        targets = ", ".join(choice.get("targets", []))
        text = choice.get("text", "")
        return f"{idx + 1:02d}. [{targets}] {text}"

    def refresh_choice_list(self):
        self.choice_list.delete(0, tk.END)
        for idx, choice in enumerate(self.current_choices):
            self.choice_list.insert(tk.END, self._format_choice_line(idx, choice))
        if self.selected_choice_index is not None and 0 <= self.selected_choice_index < len(
            self.current_choices
        ):
            self.choice_list.selection_set(self.selected_choice_index)

    def clear_choice_editor(self):
        self.choice_targets_entry.delete(0, tk.END)
        self.choice_text_entry.delete(0, tk.END)

    def on_choice_selected(self, _event):
        sel = self.choice_list.curselection()
        if not sel:
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
            messagebox.showerror("Invalid Choice", "Choice must have at least one target.")
            return
        choice = {"targets": targets, "text": text}
        if self.selected_choice_index is None:
            self.current_choices.append(choice)
            self.selected_choice_index = len(self.current_choices) - 1
        else:
            self.current_choices[self.selected_choice_index] = choice
        self.refresh_choice_list()
        self.set_dirty(True)

    def delete_choice(self):
        if self.selected_choice_index is None:
            return
        del self.current_choices[self.selected_choice_index]
        self.selected_choice_index = None
        self.refresh_choice_list()
        self.clear_choice_editor()
        self.set_dirty(True)

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
        self.set_dirty(True)

    def jump_to_choice_target(self):
        if self.selected_choice_index is None:
            return
        choice = self.current_choices[self.selected_choice_index]
        if not choice.get("targets"):
            return
        base, _weight = self._split_weighted_target(choice["targets"][0])
        if base not in self.data["scenes"]:
            messagebox.showinfo("Missing Target", f"Target scene {base} does not exist.")
            return
        self.refresh_scene_list(select_id=base)

    def _scene_payload_from_editor(self):
        scene_id = self.scene_id_entry.get().strip()
        text = self.scene_text.get("1.0", tk.END).rstrip("\n")
        image = self.scene_image_entry.get().strip()
        choices = copy.deepcopy(self.current_choices)
        return scene_id, {"text": text, "image": image, "choices": choices}

    def save_scene(self):
        if self.current_scene is None and not self.scene_id_entry.get().strip():
            messagebox.showinfo("No Scene", "Select or create a scene first.")
            return False

        scene_id, payload = self._scene_payload_from_editor()
        if not scene_id:
            messagebox.showerror("Invalid ID", "Scene ID cannot be empty.")
            return False

        old_id = self.current_scene
        if old_id is None:
            if scene_id in self.data["scenes"]:
                messagebox.showerror("Duplicate ID", f"Scene {scene_id} already exists.")
                return False
            self.data["scenes"][scene_id] = payload
            self.data["scene_order"].append(scene_id)
        else:
            if scene_id != old_id:
                if scene_id in self.data["scenes"]:
                    messagebox.showerror("Duplicate ID", f"Scene {scene_id} already exists.")
                    return False
                self._rename_scene_id(old_id, scene_id)
            self.data["scenes"][scene_id] = payload

        self.current_scene = scene_id
        self.refresh_scene_list(select_id=scene_id)
        self.set_dirty(True)
        self.set_status(f"Saved scene {scene_id}")
        return True

    def _parse_god_file(self, text):
        data = {
            "info": {"name": "", "info": "", "image": ""},
            "scenes": {},
            "scene_order": [],
        }
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
                    data["scenes"][current_id] = {"text": "", "image": "", "choices": []}
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
                            scene["choices"].append({"targets": targets, "text": label.strip()})
                    elif scene["text"]:
                        scene["text"] += "\n" + line
                    else:
                        scene["text"] = line

        return data

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
            with open(path, "r", encoding="utf-8") as f:
                self.data = self._parse_god_file(f.read())
        except Exception as exc:
            messagebox.showerror("Load Failed", str(exc))
            return

        self.current_file = path
        self.current_scene = None
        self.current_choices = []
        self.selected_choice_index = None
        self.load_info_from_data()
        self.refresh_scene_list()
        self.clear_scene_editor()
        self.set_dirty(False)
        self.set_status(f"Loaded {os.path.basename(path)}")

    def _reachable_scenes(self):
        if not self.data["scene_order"]:
            return set()
        start = self.data["scene_order"][0]
        visited = set()
        stack = [start]
        while stack:
            current = stack.pop()
            if current in visited or current not in self.data["scenes"]:
                continue
            visited.add(current)
            for choice in self.data["scenes"][current].get("choices", []):
                for token in choice.get("targets", []):
                    target, _weight = self._split_weighted_target(token)
                    if target in self.data["scenes"] and target not in visited:
                        stack.append(target)
        return visited

    def _detect_loop(self):
        temp_mark = set()
        perm_mark = set()

        def visit(node):
            if node in perm_mark:
                return False
            if node in temp_mark:
                return True
            temp_mark.add(node)
            for choice in self.data["scenes"][node].get("choices", []):
                for token in choice.get("targets", []):
                    target, _weight = self._split_weighted_target(token)
                    if target in self.data["scenes"] and visit(target):
                        return True
            temp_mark.remove(node)
            perm_mark.add(node)
            return False

        for scene_id in self.data["scene_order"]:
            if scene_id in self.data["scenes"] and visit(scene_id):
                return True
        return False

    def validate_data(self):
        self.sync_info_to_data()
        errors = []
        warnings = []

        info = self.data["info"]
        if not info.get("name", "").strip():
            errors.append("Missing god name.")
        if not info.get("info", "").strip():
            warnings.append("God info/description is empty.")

        god_image = info.get("image", "").strip()
        if not god_image:
            errors.append("Missing god image key.")
        elif self.god_image_keys and god_image not in self.god_image_keys:
            warnings.append(f"God image '{god_image}' is not found in assets/images/god.")

        if not self.data["scene_order"]:
            errors.append("No scenes defined.")
            return errors, warnings

        if self.data["scene_order"][0] != "a1":
            warnings.append(
                f"First scene is '{self.data['scene_order'][0]}', not 'a1'. The first listed scene is the start scene."
            )

        for scene_id in self.data["scene_order"]:
            scene = self.data["scenes"].get(scene_id)
            if scene is None:
                errors.append(f"Scene order references missing scene '{scene_id}'.")
                continue
            if not scene.get("text", "").strip():
                warnings.append(f"Scene '{scene_id}' has no text.")
            image_key = scene.get("image", "").strip()
            if not image_key:
                warnings.append(f"Scene '{scene_id}' has no image key.")
            elif self.scene_image_keys and image_key not in self.scene_image_keys:
                warnings.append(
                    f"Scene '{scene_id}' image '{image_key}' is not found in assets/images/scene."
                )

            choices = scene.get("choices", [])
            if len(choices) > 26:
                errors.append(
                    f"Scene '{scene_id}' has {len(choices)} choices. Game only supports up to 26 (A-Z)."
                )
            for choice_idx, choice in enumerate(choices, start=1):
                label = choice.get("text", "")
                targets = choice.get("targets", [])
                if not targets:
                    errors.append(f"Scene '{scene_id}' choice #{choice_idx} has no targets.")
                if not label.strip():
                    warnings.append(f"Scene '{scene_id}' choice #{choice_idx} has empty label.")
                for token in targets:
                    target_id, weight = self._split_weighted_target(token)
                    if not target_id:
                        errors.append(
                            f"Scene '{scene_id}' choice #{choice_idx} has invalid target token '{token}'."
                        )
                        continue
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
                    if target_id not in self.data["scenes"]:
                        errors.append(
                            f"Scene '{scene_id}' choice #{choice_idx} targets missing scene '{target_id}'."
                        )

        reachable = self._reachable_scenes()
        unreachable = [sid for sid in self.data["scene_order"] if sid not in reachable]
        if unreachable:
            warnings.append("Unreachable scenes: " + ", ".join(unreachable))

        if self._detect_loop():
            warnings.append("Loop detected in scene graph (allowed, but verify it is intentional).")

        return errors, warnings

    def validate_and_show(self):
        errors, warnings = self.validate_data()
        if not errors and not warnings:
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
            lines.append(f"text: {text_lines[0] if text_lines else ''}")
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

    def _write_file(self, path):
        if not self._ensure_current_scene_saved():
            return False

        errors, warnings = self.validate_data()
        if errors:
            messagebox.showerror("Cannot Save", "- " + "\n- ".join(errors))
            return False
        if warnings:
            proceed = messagebox.askyesno(
                "Validation Warnings",
                "Warnings found:\n- " + "\n- ".join(warnings) + "\n\nSave anyway?",
            )
            if not proceed:
                return False

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.export_text())
        except Exception as exc:
            messagebox.showerror("Save Failed", str(exc))
            return False

        self.current_file = path
        self.set_dirty(False)
        self.set_status(f"Saved {os.path.basename(path)}")
        return True

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

    def on_close(self):
        if not self._ensure_current_scene_saved():
            return
        if self.confirm_discard_changes():
            self.root.destroy()


root = tk.Tk()
app = GodEditor(root)
root.mainloop()