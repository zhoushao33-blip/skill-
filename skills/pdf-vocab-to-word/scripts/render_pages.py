#!/usr/bin/env python3
"""Render inclusive PDF physical pages. Human must still inspect hand-drawn marks."""
import argparse
from pathlib import Path
import fitz

p = argparse.ArgumentParser()
p.add_argument("--pdf", type=Path, required=True)
p.add_argument("--start", type=int, required=True)
p.add_argument("--end", type=int, required=True)
p.add_argument("--out", type=Path, required=True)
p.add_argument("--dpi", type=int, default=180)
args = p.parse_args()
with fitz.open(args.pdf) as doc:
    if not (1 <= args.start <= args.end <= len(doc)):
        p.error(f"Page range invalid: PDF has {len(doc)} pages")
    args.out.mkdir(parents=True, exist_ok=True)
    for n in range(args.start, args.end + 1):
        pix = doc.load_page(n-1).get_pixmap(dpi=args.dpi, alpha=False)
        path = args.out / f"page-{n:03d}.png"
        pix.save(path)
        print(path)
