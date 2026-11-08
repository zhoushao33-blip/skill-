#!/usr/bin/env python3
"""Static no-dependency validator for offline single-file HTML lessons."""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from html.parser import HTMLParser

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts=[];self.in_script=False
        self.buttons=0;self.svg=0;self.styles=0;self.viewport=False;self.externals=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="script":
            self.in_script=True
            if a.get("src"):self.externals.append(a["src"])
        if tag=="link" and a.get("href"):self.externals.append(a["href"])
        if tag in ("img","iframe","source") and a.get("src"):self.externals.append(a["src"])
        if tag=="style":self.styles+=1
        if tag=="svg":self.svg+=1
        if tag=="button":self.buttons+=1
        if tag=="meta" and a.get("name")=="viewport":self.viewport=True
    def handle_endtag(self,tag):
        if tag=="script":self.in_script=False
    def handle_data(self,value):
        if self.in_script:self.scripts.append(value)

def check(path):
    page=Path(path).read_text(encoding="utf-8")
    p=Inspector();p.feed(page)
    errors=[]
    if "<!doctype html>" not in page.lower():errors.append("Missing doctype")
    if not p.viewport:errors.append("Missing viewport")
    if not p.scripts:errors.append("Missing inline script")
    if not p.styles:errors.append("Missing inline styles")
    if p.buttons<2:errors.append("At least two buttons required")
    if p.externals:errors.append("External references: "+str(p.externals))
    if shutil.which("node") and p.scripts:
        with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False) as fh:
            fh.write("\n;\n".join(p.scripts));tmp=fh.name
        try:
            result=subprocess.run(["node","--check",tmp],capture_output=True,text=True)
            if result.returncode:errors.append("JS syntax error "+result.stderr[-400:])
        finally:Path(tmp).unlink(missing_ok=True)
    for problem in errors:print("ERROR:",problem)
    print(f"Checked {Path(path).name}: {p.buttons} buttons, {p.svg} SVG, {len(p.scripts)} scripts")
    return len(errors)==0

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("html")
    args=parser.parse_args()
    sys.exit(0 if check(args.html) else 1)
