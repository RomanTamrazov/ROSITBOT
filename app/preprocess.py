from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Preprocessor:
    synonyms: dict[str, str]

    @classmethod
    def from_json(cls, path: str | Path) -> "Preprocessor":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(synonyms=data)

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = self._apply_synonyms(text)
        text = re.sub(r"[^0-9a-zа-яё\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _apply_synonyms(self, text: str) -> str:
        for src, dst in self.synonyms.items():
            pattern = r"\b" + re.escape(src) + r"\b"
            text = re.sub(pattern, dst, text)
        return text
