"""Quản lý thư mục run, artifact và manifest (cho phép resume)."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(text: str, max_len: int = 48) -> str:
    normalized = unicodedata.normalize("NFD", text)
    ascii_text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    ascii_text = ascii_text.replace("đ", "d").replace("Đ", "D")
    ascii_text = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text).strip("-").lower()
    return ascii_text[:max_len] or "research"


class RunState:
    """Một lần chạy pipeline = một thư mục dưới `runs/`."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.artifacts_dir = root / "artifacts"
        self.raw_dir = root / "raw"
        self.paper_dir = root / "paper"
        for directory in (self.artifacts_dir, self.raw_dir, self.paper_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self.manifest_path = root / "manifest.json"
        self.manifest: dict[str, Any] = self._load_manifest()

    # -- khởi tạo -------------------------------------------------------
    @classmethod
    def create(cls, topic: dict[str, Any], runs_dir: Path) -> "RunState":
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        root = runs_dir / (slugify(topic.get("slug") or topic["title"]) + "-" + stamp)
        state = cls(root)
        state.manifest.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        state.manifest["topic"] = topic
        state.manifest.setdefault("stages", {})
        state.save_manifest()
        return state

    @classmethod
    def resume(cls, root: Path) -> "RunState":
        if not (root / "manifest.json").exists():
            raise FileNotFoundError("Không tìm thấy manifest.json trong " + str(root))
        return cls(root)

    def _load_manifest(self) -> dict[str, Any]:
        path = self.root / "manifest.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"stages": {}}

    def save_manifest(self) -> None:
        self.manifest_path.write_text(
            json.dumps(self.manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # -- artifact -------------------------------------------------------
    def artifact_path(self, num: int, key: str) -> Path:
        return self.artifacts_dir / (f"{num:02d}_{key}.json")

    def has(self, num: int, key: str) -> bool:
        return self.artifact_path(num, key).exists()

    def write(self, num: int, key: str, data: dict[str, Any]) -> Path:
        path = self.artifact_path(num, key)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def read(self, key: str) -> dict[str, Any]:
        matches = sorted(self.artifacts_dir.glob("*_" + key + ".json"))
        if not matches:
            raise FileNotFoundError(
                "Chưa có artifact `" + key + "`. Hãy chạy stage tạo ra nó trước."
            )
        return json.loads(matches[-1].read_text(encoding="utf-8"))

    # -- file văn bản ---------------------------------------------------
    def write_text(self, name: str, text: str, folder: str = "paper") -> Path:
        base = {"paper": self.paper_dir, "raw": self.raw_dir, "root": self.root}[folder]
        path = base / name
        path.write_text(text, encoding="utf-8")
        return path

    def read_text(self, name: str, folder: str = "paper") -> str:
        base = {"paper": self.paper_dir, "raw": self.raw_dir, "root": self.root}[folder]
        return (base / name).read_text(encoding="utf-8")

    # -- ghi nhận tiến độ ------------------------------------------------
    def record(self, num: int, key: str, title: str, status: str,
               seconds: float, usage: dict[str, Any] | None = None,
               error: str | None = None) -> None:
        self.manifest.setdefault("stages", {})[key] = {
            "num": num,
            "title": title,
            "status": status,
            "seconds": round(seconds, 1),
            "usage": usage or {},
            "error": error,
            "at": datetime.now().isoformat(timespec="seconds"),
        }
        self.save_manifest()

    def totals(self) -> dict[str, Any]:
        total_cost = 0.0
        total_seconds = 0.0
        for stage in self.manifest.get("stages", {}).values():
            total_cost += float(stage.get("usage", {}).get("cost_usd_est", 0) or 0)
            total_seconds += float(stage.get("seconds", 0) or 0)
        return {"cost_usd_est": round(total_cost, 3), "seconds": round(total_seconds, 1)}
