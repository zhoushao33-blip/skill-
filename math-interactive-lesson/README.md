# Math Interactive Lesson Skill（初中数学互动解题网页）

把数学题图片转化为**先讲解题思路、点击一次推进一步**的离线 HTML 教学课件。

## 功能
- 解题思路先于计算步骤；独立验算数学答案，检查分类、范围、退化与漏解。
- SVG 坐标图及辅助线、滑块动点、数值和图形同步反馈。
- 纯 HTML/CSS/JavaScript，单文件离线运行；支持手机和投影。
- 附三份成品示例、空白课件模板、脚手架与验收脚本。

## 用法
1. 将此文件夹作为 Codex/Agent Skill 使用，阅读 `SKILL.md`。
2. 上传数学题照片，要求“用 math-interactive-lesson 做成互动 HTML，先讲解题思路，再点击一步讲一步”。
3. 生成模板：`python scripts/new_lesson.py --title "数学题" --out index.html`。
4. 替换题目、步骤、SVG 和数学模型，**不可把示例公式当成当前题答案**。
5. 检查：`python scripts/check_lesson.py index.html`；可选 `python scripts/browser_smoke.py index.html`。
6. 确认文件存在后，把完整 HTML 和 ZIP 交付用户。

## 文件说明
- `SKILL.md`：核心工作流程与质量要求
- `templates/lesson_starter.html`：离线交互模板
- `examples/`：三个实际互动课件
- `scripts/`：新建模板、静态检查、浏览器冒烟测试
- `references/`：教学设计、视觉验收和备份规范
- `tests/`：单元测试

v1.0.0 / 2026-11-08。代码备份不包含学生照片或密钥。
