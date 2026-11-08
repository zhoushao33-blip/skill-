#!/usr/bin/env python3
"""Optional Playwright smoke test: desktop/mobile, offline load, button, overflow."""
import argparse
import shutil
import sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("html")
    parser.add_argument("--screenshot-dir")
    a=parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright, Error as BrowserError
    except ImportError:
        print("Playwright not installed. Install playwright + Chromium.")
        return 2
    content=Path(a.html).read_text(encoding="utf-8")
    with sync_playwright() as pw:
        executable=shutil.which("chromium") or shutil.which("google-chrome")
        opts={"headless":True,"args":["--no-sandbox"]}
        if executable:opts["executable_path"]=executable
        browser=pw.chromium.launch(**opts)
        try:
            for width,height in ((1366,768),(390,844)):
                page=browser.new_page(viewport={"width":width,"height":height})
                errors=[]
                page.on("pageerror",lambda err:errors.append(str(err)))
                try:
                    page.goto(Path(a.html).resolve().as_uri(),wait_until="load",timeout=15000)
                    mode="file://"
                except BrowserError as err:
                    if "ERR_BLOCKED_BY_ADMINISTRATOR" not in str(err):raise
                    page.set_content(content,wait_until="load")
                    mode="set_content (file:// blocked by test environment)"
                assert page.locator("body").inner_text().strip(),"blank screen"
                assert not errors,errors
                assert not page.evaluate("document.documentElement.scrollWidth>window.innerWidth+2"),"horizontal overflow"
                nxt=page.get_by_role("button",name="下一步")
                if nxt.count()==0:nxt=page.locator("#next")
                assert nxt.count(),"next missing"
                before=page.locator("body").inner_text()
                nxt.first.click()
                assert before!=page.locator("body").inner_text(),"next did not advance"
                if a.screenshot_dir:
                    output=Path(a.screenshot_dir);output.mkdir(parents=True,exist_ok=True)
                    page.screenshot(path=str(output/(str(width)+".png")),full_page=True)
                print(f"PASS {width}x{height}: {mode}, no JS errors, no overflow, next advances")
                page.close()
        finally:browser.close()
    return 0

if __name__=="__main__":
    sys.exit(main())
