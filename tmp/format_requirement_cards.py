from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\TH")
SCRATCH = ROOT / "tmp" / "requirement-card-formatting"
SCRATCH.mkdir(parents=True, exist_ok=True)
FILES = {
    1: ROOT / "ЗАДАНИЕ 1 Информационный обмен" / "Требование.md",
    2: ROOT / "ЗАДАНИЕ 2 Определение значения" / "Требование.md",
}
ORIGINAL = {
    key: (SCRATCH / f"task-{key}-original.md").read_bytes()
    if (SCRATCH / f"task-{key}-original.md").exists()
    else path.read_bytes()
    for key, path in FILES.items()
}
TASK3 = ROOT / "ЗАДАНИЕ 3 Процедура" / "Требование.md"
task3_hash = hashlib.sha256(TASK3.read_bytes()).hexdigest()
TEXT = {key: raw.decode("utf-8-sig") for key, raw in ORIGINAL.items()}

PIV = "[ПИВ ВВСП-У с БВМ](</C:/TH/ЗАДАНИЕ 1 Информационный обмен/ПИВ ВВСП-У с БВМ.docx>)"
ICAO = "[Приложение 5 ИКАО](</C:/TH/ЗАДАНИЕ 2 Определение значения/5 Приложение ИКАО.pdf>)"


def section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = lines.index(heading) + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^#{1,3}\s", lines[index]) or lines[index].strip() == "---":
            end = index
            break
    return "\n".join(lines[start:end])


def statement(text: str, prefix: str) -> str:
    lines = text.splitlines()
    matches = [index for index, line in enumerate(lines) if line.lstrip().startswith(prefix)]
    assert len(matches) == 1, (prefix, matches)
    index = matches[0]
    first_indent = len(lines[index].expandtabs(4)) - len(lines[index].expandtabs(4).lstrip())
    first = lines[index].lstrip().removeprefix("- ").rstrip()
    result = [first]
    for line in lines[index + 1:]:
        if not line.strip():
            break
        indent = len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())
        if indent > first_indent and line.lstrip().startswith("- "):
            if len(result) == 1:
                result.append("")
            result.append(line.lstrip().rstrip())
        else:
            break
    return "\n".join(result)


def first_table(text: str) -> str:
    rows = []
    collecting = False
    for line in text.splitlines():
        if line.startswith("|"):
            collecting = True
            rows.append(line.rstrip())
        elif collecting:
            break
    assert len(rows) >= 3
    return "\n".join(rows)


def card(name: str, body: str, source: str = "-", note: str = "-") -> str:
    fields = [
        ("Идентификатор", "-"),
        ("Наименование", name),
        ("Вид требования", "-"),
        ("Тип требования", "-"),
        ("Источник", source),
        ("Обоснование", "-"),
        ("Версия требования", "-"),
        ("Алокация", "ПО БВМ"),
        ("Метод верификации", "-"),
        ("Метод валидации", "-"),
        ("Примечание", note),
    ]
    table = []
    for index, (key, value) in enumerate(fields):
        value = value.replace("|", "\\|").replace("\n", "<br>")
        table.append(f"| {key} | {value} |")
        if index == 0:
            table.append("| --- | --- |")
    quoted = "\n".join(
        "> " + line if line else ">" for line in table + [""] + body.splitlines()
    )
    return f"## {name} [-]\n\n---\n\n{quoted}\n\n---"


cards1 = []
for name, prefix, table_number, note in [
    (
        "Приём информации от ВВСП-У",
        "- ПО БВМ должно принимать от ВВСП-У информацию",
        4,
        "Вопрос автора: нужно ли включать таблицу 4 ПИВ в требование?",
    ),
    (
        "Выдача информации в ВВСП-У",
        "- ПО БВМ должно выдавать в ВВСП-У информацию",
        5,
        "Вопрос автора: нужно ли включать таблицу 5 ПИВ в требование?",
    ),
]:
    cards1.append(card(name, statement(TEXT[1], prefix), f"{PIV}, таблица {table_number}", note))

cards2 = []
for heading, name, symbol in [
    ("### Высота стандартная, Набс", "Определение стандартной барометрической высоты Hабс", "Hабс"),
    ("### Относительная барометрическая высота, Нотн1 (QNH)", "Определение относительной барометрической высоты Нотн1 (QNH)", "Нотн1 (QNH)"),
    ("### Относительная барометрическая высота, Нотн2 (QFE)", "Определение относительной барометрической высоты Нотн2 (QFE)", "Нотн2 (QFE)"),
    ("### Вертикальная барометрическая скорость, Vyб", "Определение вертикальной барометрической скорости Vyб", "Vyб"),
    ("### Приборная скорость, Vпр", "Определение приборной скорости Vпр", "Vпр"),
]:
    content = section(TEXT[2], heading)
    body = statement(content, f"- ПО БВМ должно определять параметр {symbol}:")
    note = "-"
    if symbol == "Vyб":
        body = body.replace(" (логика снижения точности не прописана)", "")
        table = first_table(content)
        table_lines = table.splitlines()
        table_lines[0] = "| Значение разряда 11 | Признак снижения точности |"
        body += "\n\n" + "\n".join(table_lines)
        note = "Логика снижения точности не прописана."
    elif symbol == "Vпр":
        assert "Примечание:" in content
        note = " ".join(content.split("Примечание:", 1)[1].split())
    cards2.append(card(name, body, f"{PIV}, таблица 4", note))

pressure_in = section(TEXT[2], "### Определения давлений")
for symbol in ("QNH", "QFE"):
    cards2.append(card(
        f"Определение барокоррекции {symbol}",
        statement(pressure_in, f"- ПО БВМ должно определять параметр {symbol}:"),
        f"{PIV}, таблица 4",
    ))

pressure_out = section(TEXT[2], "### Выдача давлений ")
calculation = statement(pressure_out, "- ПО БВМ должно рассчитать значение барокоррекции QNH")
calculation = calculation.replace(" (касается ли это требований **выдачи?**)", "")
cards2.append(card(
    "Расчёт барокоррекции QNH",
    calculation,
    note="Незавершённая формулировка. Вопрос автора: касается ли расчёт барокоррекции требований выдачи?",
))
parts = pressure_out.split("- Барокоррекция 2 QFE:")
assert len(parts) == 2
for symbol, content in zip(("QNH", "QFE"), parts):
    body = statement(content, f"- ПО БВМ должно выдавать заданное значение барокоррекции {symbol}")
    body += "\n\n" + first_table(content)
    cards2.append(card(
        f"Выдача барокоррекции {symbol}",
        body,
        f"{PIV}, таблицы 2 и 5",
        "Вопрос автора: требуется ли указать диапазон 525…1075 гПа в формулировке требования?",
    ))

conversion_parent = "- ПО БВМ должно осуществлять пересчет единиц измерения высотно-скоростных параметров:"
conversion_statement = statement(TEXT[2], conversion_parent)
conversion_items = [line for line in conversion_statement.splitlines() if line.startswith("- ")]
assert len(conversion_items) == 6
conversion_names = [
    "Пересчёт барометрических высот из метров в футы",
    "Пересчёт барометрических высот из футов в метры",
    "Пересчёт приборной скорости из км/ч в узлы",
    "Пересчёт приборной скорости из узлов в км/ч",
    "Пересчёт вертикальной скорости из м/с в фут/мин",
    "Пересчёт вертикальной скорости из фут/мин в м/с",
]
for name, item in zip(conversion_names, conversion_items):
    body = conversion_parent.removeprefix("- ") + "\n\n" + item
    cards2.append(card(name, body, ICAO))

assert len(cards1) == 2
assert len(cards2) == 16
all_cards = {1: cards1, 2: cards2}
prepared = {}
report = []
for key, path in FILES.items():
    original = ORIGINAL[key]
    assert TEXT[key].startswith("## .... [...]")
    separators = list(re.finditer(rb"(?m)^---[ \t]*(?:\r?\n|$)", original))
    assert len(separators) >= 2
    tail = original[separators[1].start():]
    prefix = "\n\n".join(all_cards[key])
    assert prefix.endswith("\n\n---")
    prefix = prefix[:-3]
    output = prefix.encode("utf-8") + tail
    assert output.endswith(tail)
    assert output.count(tail) == 1
    assert output.count(b"> | ") >= len(all_cards[key]) * 12
    (SCRATCH / f"task-{key}-original.md").write_bytes(original)
    (SCRATCH / f"task-{key}-lower-original.bin").write_bytes(tail)
    prepared[key] = (output, tail)
    report.append({
        "file": str(path),
        "cards": len(all_cards[key]),
        "preserved_lower_bytes": len(tail),
        "preserved_lower_sha256": hashlib.sha256(tail).hexdigest(),
    })

# Abort rather than overwrite any edit made while the new cards were being built.
for key, path in FILES.items():
    current = path.read_bytes()
    saved_tail = prepared[key][1]
    assert current == ORIGINAL[key] or current.endswith(saved_tail), f"File changed during formatting: {path}"
for key, path in FILES.items():
    output, tail = prepared[key]
    path.write_bytes(output)
    actual = path.read_bytes()
    assert actual == output
    assert actual[-len(tail):] == tail
    assert actual.count(b"## ") >= len(all_cards[key])
assert hashlib.sha256(TASK3.read_bytes()).hexdigest() == task3_hash

(SCRATCH / "verification.json").write_text(
    json.dumps({"files": report, "task_3_unchanged": True}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(json.dumps({"files": report, "task_3_unchanged": True}, ensure_ascii=False, indent=2))
