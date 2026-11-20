"""Task files: tasks/<id>/task.toml holds the prompt, starting scene and checks."""
import base64
import hashlib
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .blender import SetupError

BRIEF_VIEWS = ("front", "side", "top", "three_quarter")  # order the views are attached in


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

    def brief_images(self, subdir: str) -> list[tuple[str, str]]:
        """(media type, base64) for each rendered view in <task>/<subdir>/, in BRIEF_VIEWS order.
        A missing view is a SetupError: the run would otherwise silently become the text arm."""
        out = []
        for v in BRIEF_VIEWS:
            f = self.folder / subdir / f"{v}.png"
            if not f.is_file():
                raise SetupError(f"missing brief view {f} (python -m rig.render_briefs {self.id})")
            out.append(("image/png", base64.b64encode(f.read_bytes()).decode("ascii")))
        return out

    def brief_digest(self, subdir: str) -> str:
        """Fingerprint of the attached views, folded into the prompt fingerprint."""
        h = hashlib.sha256()
        for _, data in self.brief_images(subdir):
            h.update(data.encode("ascii"))
        return h.hexdigest()


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
