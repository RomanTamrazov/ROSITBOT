from __future__ import annotations

import json
import re
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from .linker import EntityLinker
from .ner import NERExtractor
from .planner import Planner, PlannerError
from .preprocess import Preprocessor
from .types import Command, Entity, LinkedLocation


class ClarificationNeeded(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class ParserPipeline:
    data_dir: Path
    link_threshold: float = 0.75
    use_hf_ner: bool = False
    use_hf_embeddings: bool = False
    strict_location_match: bool = False

    def __post_init__(self) -> None:
        synonyms_path = self.data_dir / "synonyms.json"
        locations_path = self.data_dir / "locations.json"

        self.pre = Preprocessor.from_json(synonyms_path)

        with open(locations_path, "r", encoding="utf-8") as f:
            self.locations = json.load(f)

        self.ner = NERExtractor(use_hf=self.use_hf_ner)
        self.linker = EntityLinker(self.locations, use_embeddings=self.use_hf_embeddings)
        self.planner = Planner.default()

    def parse(self, text: str, strict_override: "Optional[bool]" = None) -> list[Command]:
        cleaned = self.pre.normalize(text)
        entities = self.ner.extract(cleaned)

        linked: dict[int, LinkedLocation] = {}
        for idx, ent in enumerate(entities):
            if not ent.type.startswith("LOC"):
                continue
            link = self.linker.link(ent.text)
            if link.score < self.link_threshold:
                strict = self.strict_location_match if strict_override is None else strict_override
                if strict:
                    raise ClarificationNeeded(
                        f"Не удалось уверенно определить локацию '{ent.text}' (score={link.score:.2f})."
                    )
                link = LinkedLocation(text=ent.text, id=self._fallback_id(ent.text), score=1.0)
            linked[idx] = link

        try:
            plan = self.planner.plan(entities, linked)
        except PlannerError as e:
            raise ClarificationNeeded(str(e))

        return plan

    def _fallback_id(self, text: str) -> str:
        slug = text.lower().replace("ё", "е")
        slug = re.sub(r"[^0-9a-zа-я]+", "_", slug).strip("_")
        if not slug:
            slug = "UNKNOWN"
        return f"FREE_{slug.upper()}"



def build_pipeline() -> ParserPipeline:
    data_dir = Path(__file__).resolve().parent.parent / "data"
    threshold = float(os.getenv("LINK_THRESHOLD", "0.75"))
    use_hf_ner = os.getenv("USE_HF_NER", "0") == "1"
    use_hf_embeddings = os.getenv("USE_HF_EMBEDDINGS", "0") == "1"
    strict_location_match = os.getenv("STRICT_LOCATION_MATCH", "0") == "1"
    return ParserPipeline(
        data_dir=data_dir,
        link_threshold=threshold,
        use_hf_ner=use_hf_ner,
        use_hf_embeddings=use_hf_embeddings,
        strict_location_match=strict_location_match,
    )
