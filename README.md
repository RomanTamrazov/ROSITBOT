# ROSIT — Миллабот NL → команды

Репозиторий реализует детерминированный пайплайн преобразования русского текста пользователя в машинный план команд робота.

## Что внутри
- Preprocessing: нормализация текста и синонимы
- NER: извлечение действий и локаций (Hugging Face, при наличии модели)
- Entity Linking: привязка локаций к ID из БД (embeddings + cosine)
- Planner: детерминированная FSM/правила
- API: FastAPI `POST /parse_command`

## Архитектура
```
User text
  ↓
Preprocessing
  ↓
Intent & Entity extraction
  ↓
Entity linking (embeddings + cosine)
  ↓
Command planner (FSM / rules)
  ↓
JSON command list
```

## Быстрый старт
1. Установка зависимостей:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Запуск API:

```bash
uvicorn app.main:app --reload
```

3. Пример запроса:

```bash
curl -X POST http://127.0.0.1:8000/parse_command \
  -H "Content-Type: application/json" \
  -d '{"text":"Съезди на разгрузку, забери груз и отвези его на выдачу, потом вернись на зарядку"}'
```

Ответ:

```json
{
  "status": "ok",
  "plan": [
    {"cmd":"GO","from":null,"to":"A1"},
    {"cmd":"PICK"},
    {"cmd":"GO","from":"A1","to":"B3"},
    {"cmd":"DROP"},
    {"cmd":"GO","from":"B3","to":"CHARGE"}
  ]
}
```

## Конфигурация
- Локации: `data/locations.json`
- Синонимы: `data/synonyms.json`
- Порог связки локаций: `LINK_THRESHOLD` (env), по умолчанию 0.75
- Включить HF NER: `USE_HF_NER=1` (если модель есть локально)
- Включить HF Embeddings: `USE_HF_EMBEDDINGS=1` (если модель есть локально)
- Режим строгой валидации локаций: `STRICT_LOCATION_MATCH=1` (если нужно только ID из БД)
- По умолчанию неизвестные локации допускаются и получают ID вида `FREE_<NAME>`

## Логика Planner
- `GO` всегда требует локацию.
- `PICK`, `DROP` без параметров.
- `отвези`/`привези` реализуются как `GO` + `DROP`.

## Важные ограничения
- Не используется LLM для генерации команд.
- Логика робота отделена от NLP.
- Если локация не найдена (score < threshold), возвращается ошибка и запрос уточнения.


## Пример со свободными локациями

Ввод:

```
"Возьми груз с точки Москва и пойди до точки Париж и выброси его"
```

Вывод (пример):

```json
[
  {"cmd":"GO","from":null,"to":"FREE_МОСКВА"},
  {"cmd":"PICK"},
  {"cmd":"GO","from":"FREE_МОСКВА","to":"FREE_ПАРИЖ"},
  {"cmd":"DROP"}
]
```


## Поддерживаемые паттерны (эвристики)
- "из/с/со/от <X>" -> `LOC_FROM`
- "в/во/на/до/к/ко <Y>" -> `LOC_TO`
- "точка/город/станция/склад/пункт/зона <Z>" -> `LOC`
- Любые неизвестные локации допускаются и получают `FREE_<NAME>` (если `STRICT_LOCATION_MATCH=0`)


## Веб-интерфейс
Запусти сервер и открой в браузере: `http://127.0.0.1:8000`

Горячая клавиша: `Cmd/Ctrl + Enter` — отправить команду.
# ROSITBOT
