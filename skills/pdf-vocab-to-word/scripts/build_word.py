#!/usr/bin/env python3
"""Place visually verified vocabulary entries into the original Word template."""
import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from docx import Document

p = argparse.ArgumentParser()
p.add_argument("--template", type=Path, required=True)
p.add_argument("--entries", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--zip", dest="zip_path", type=Path)
args = p.parse_args()
data = json.loads(args.entries.read_text(encoding="utf-8"))
start, end = data["pdf_page_start"], data["pdf_page_end"]
entries = data["entries"]
assert 1 <= start <= end
assert entries and all(start <= e["page"] <= end for e in entries)
assert all(a["page"] <= b["page"] for a,b in zip(entries, entries[1:]))
counts = Counter()
for e in entries:
    kind, val = e["mark"], e["text"]
    assert kind in {"number", "star", "half_check"}
    assert e["source"].strip() and val.strip()
    if kind in {"number", "star"}:
        assert re.search(r"[\u3400-\u9fff]", val), (kind, val)
    else:
        assert re.search("[A-Za-z]", val) and not re.search(r"[\u3400-\u9fff]", val)
    counts[kind] += 1

covered = {e["page"] for e in entries} | set(data.get("empty_pages", []))
assert covered == set(range(start, end+1)), "Unaccounted PDF page(s)"
assert args.template.resolve() != args.output.resolve(), "Do not overwrite template"
doc = Document(args.template)
assert doc.tables and len(doc.tables[0].rows) >= 2, "Need original table with example row"
tbl = doc.tables[0]
assert len(tbl.rows[1].cells) >= 3
sample = deepcopy(tbl.rows[1]._tr)
while len(tbl.rows) > 1:
    tbl._tbl.remove(tbl.rows[-1]._tr)
for e in entries:
    tbl._tbl.append(deepcopy(sample))
    cells = tbl.rows[-1].cells
    for col, content in enumerate([e["text"], "", ""]):
        paragraphs = cells[col].paragraphs
        assert paragraphs and paragraphs[0].runs, "Template needs pre-styled runs"
        paragraphs[0].runs[0].text = content
        for run in paragraphs[0].runs[1:]:
            run.text = ""
        for paragraph in paragraphs[1:]:
            for run in paragraph.runs:
                run.text = ""
args.output.parent.mkdir(parents=True, exist_ok=True)
doc.save(args.output)
check = Document(args.output)
assert len(check.tables[0].rows) == len(entries)+1
for idx, e in enumerate(entries, start=1):
    assert check.tables[0].rows[idx].cells[0].text == e["text"]
if args.zip_path:
    with ZipFile(args.zip_path, "w", compression=ZIP_DEFLATED) as z:
        z.write(args.output, args.output.name)
    with ZipFile(args.zip_path) as z:
        assert z.testzip() is None
print({"pages": [start,end], "total": len(entries), "counts": dict(counts), "output":str(args.output)})
