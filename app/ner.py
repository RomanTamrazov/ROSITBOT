from __future__ import annotations
import re
import pymorphy3
from .types import Entity

morph = pymorphy3.MorphAnalyzer()

class NERExtractor:
    def __init__(self, use_hf: bool = False):
        self.use_hf = use_hf
        self.action_map = {
            "GO": [r"съезд\w*", r"поед\w*", r"ед\w*", r"иди", r"направ\w*", r"двигай\w*", r"подъе\w*"],
            "PICK": [r"забер\w*", r"возьм\w*", r"взят\w*", r"подбер\w*", r"погруз\w*"],
            "DELIVER": [r"отвез\w*", r"достав\w*", r"перевез\w*", r"привез\w*"],
            "DROP": [r"выгруз\w*", r"разгруз\w*", r"остав\w*", r"отдай\w*", r"сдай\w*"],
            "RETURN": [r"верн\w*", r"возвращ\w*"]
        }
        self.prep_from = {"из", "от", "с", "со"}
        self.prep_to = {"в", "на", "к", "до"}

    def extract(self, text: str) -> list[Entity]:
        entities = []
        text_lower = text.lower()
        # Токенизация: ищем слова и числа
        tokens = list(re.finditer(r"[a-zа-я0-9-]+", text_lower))
        words_data = []

        for m in tokens:
            word = m.group()
            p = morph.parse(word)[0]
            words_data.append({
                "word": word,
                "lemma": p.normal_form,
                "pos": p.tag.POS,
                "start": m.start(),
                "end": m.end()
            })

        i = 0
        while i < len(words_data):
            wd = words_data[i]
            
            found_act = False
            for cmd, patterns in self.action_map.items():
                if any(re.match(p, wd["word"]) for p in patterns):
                    entities.append(Entity(type="ACT", text=cmd, start=wd["start"], end=wd["end"]))
                    found_act = True
                    break
            
            if found_act:
                i += 1
                continue

            if wd["lemma"] in (self.prep_from | self.prep_to):
                role = "LOC_FROM" if wd["lemma"] in self.prep_from else "LOC_TO"
                if i + 1 < len(words_data):
                    loc_words = []
                    curr_j = i + 1
                    while curr_j < len(words_data) and len(loc_words) < 2:
                        test_wd = words_data[curr_j]
                        if test_wd["pos"] in ("VERB", "INFN") or test_wd["lemma"] in (self.prep_from | self.prep_to):
                            break
                        loc_words.append(test_wd)
                        curr_j += 1
                    
                    if loc_words:
                        entities.append(Entity(
                            type=role, 
                            text=" ".join([w["word"] for w in loc_words]), 
                            start=loc_words[0]["start"], 
                            end=loc_words[-1]["end"]
                        ))
                        i = curr_j
                        continue
            i += 1

        entities.sort(key=lambda e: e.start)
        return entities