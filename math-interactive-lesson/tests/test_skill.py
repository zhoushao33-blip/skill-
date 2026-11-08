import unittest
from pathlib import Path
from subprocess import run

ROOT=Path(__file__).resolve().parents[1]

class SkillTests(unittest.TestCase):
    def test_metadata(self):
        body=(ROOT/"SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(body.startswith("---\nname: math-interactive-lesson\n"))
        self.assertIn("description:",body)
    def test_template_controls(self):
        body=(ROOT/"templates/lesson_starter.html").read_text(encoding="utf-8")
        for term in ('id="next"','id="prev"','id="slider"','<svg','<style','<script'):
            self.assertIn(term,body)
    def test_static(self):
        paths=[ROOT/"templates/lesson_starter.html",*(ROOT/"examples").glob("*.html")]
        for p in paths:
            result=run(["python",str(ROOT/"scripts/check_lesson.py"),str(p)],text=True,capture_output=True)
            self.assertEqual(result.returncode,0, result.stdout+result.stderr)

if __name__=="__main__":
    unittest.main()
