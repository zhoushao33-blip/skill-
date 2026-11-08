#!/usr/bin/env python3
"""Generate a standalone lesson from the Skill template."""
import argparse
import html
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--title", default="初中数学互动课堂")
    parser.add_argument("--out", default="index.html")
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]/"templates"/"lesson_starter.html"
    destination=Path(args.out).resolve()
    data=source.read_text(encoding="utf-8")
    data=data.replace("__LESSON_TITLE__", html.escape(args.title,quote=True))
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(data,encoding="utf-8")
    print(f"Created {destination}")
    print("Template is a demonstration: replace mathematics, steps and graph before teaching.")

if __name__=="__main__":
    main()
