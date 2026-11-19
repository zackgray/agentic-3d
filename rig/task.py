"""Task files: tasks/<id>/task.toml holds the prompt, starting scene and checks."""
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .blender import SetupError


@dataclass
class Task:
    id: str
    title: str
    prompt: str
    starting_scene: str
    checks: list[dict]
    folder: Path
    variants: dict[str, list[str]]  # reference variant -> checks it must fail

    @property
    def reference(self) -> Path:
        return self.folder / "reference.py"

    @property
    def scene_text(self) -> str:
        """Source of a scripted starting scene, folded into the prompt fingerprint so an edit to the
        starting model never mixes with older runs. Empty for the 'empty' scene."""
        if self.starting_scene == "empty":
            return ""
        return (self.folder / self.starting_scene).read_text(encoding="utf-8")


def load_task(path: str | Path) -> Task:
    folder = Path(path)
    if folder.is_file():
        folder = folder.parent
    toml = folder / "task.toml"
    try:
        data = tomllib.loads(toml.read_text(encoding="utf-8"))
        return Task(id=data["id"], title=data["title"], prompt=data["prompt"].strip(),
                    starting_scene=data["starting_scene"], checks=data["checks"], folder=folder,
                    variants=data.get("variants", {"good": []}))
    except (OSError, KeyError, tomllib.TOMLDecodeError) as e:
        raise SetupError(f"Bad task {toml}: {e!r}") from e
