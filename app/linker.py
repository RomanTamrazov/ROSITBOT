from __future__ import annotations
import re
import difflib
from dataclasses import dataclass
import pymorphy3
from .types import LinkedLocation

morph = pymorphy3.MorphAnalyzer()

def _get_lemmas(text: str) -> set[str]:
    words = re.sub(r"[^0-9a-zа-я\s]", " ", text.lower()).split()
    return {morph.parse(w)[0].normal_form for w in words}

@dataclass
class EntityLinker:
    locations: dict[str, str]
    use_embeddings: bool = False

    def __post_init__(self) -> None:
        self.loc_data = []
        for lid, name in self.locations.items():
            self.loc_data.append({
                "id": lid,
                "name": name,
                "lemmas": _get_lemmas(name)
            })

    def link(self, text: str) -> LinkedLocation:
        query_lemmas = _get_lemmas(text)
        best_id = None
        best_score = 0.0

        for loc in self.loc_data:
            intersection = query_lemmas.intersection(loc["lemmas"])
            score = len(intersection) / max(len(query_lemmas), 1)
            
            str_sim = difflib.SequenceMatcher(None, text.lower(), loc["name"].lower()).ratio()
            final_score = max(score, str_sim)

            if final_score > best_score:
                best_score = final_score
                best_id = loc["id"]

        return LinkedLocation(text=text, id=best_id or "UNKNOWN", score=float(best_score))