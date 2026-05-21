# my-codex-skills

Personal Codex skills repository.

This repo is organized as:

- one repository
- multiple skills
- one skill per subdirectory

## Skills

- `windows-utf8-guard`: Prevent file corruption and mojibake when Codex edits text files on Windows, especially with Chinese or other non-ASCII text.
- `plan-to-todo`: 手动把当前已确认方案整理成中文任务清单，保存到工程内的 `plan-to-do/` 目录，支持并行维护多个 todo 文件，也支持手动审核指定 markdown 文件并更新勾选状态。
- `simulink-hil-tcsd-generator`: Generate and repair coverage-oriented HIL TCSD Excel test cases from Simulink `.slx` models and matching `.mat` files.

## Repository Layout

```text
my-codex-skills/
  windows-utf8-guard/
    SKILL.md
    agents/
      openai.yaml
    references/
      windows-utf8-rules.md
  plan-to-todo/
    SKILL.md
    agents/
      openai.yaml
    references/
      example-todo.md
  simulink-hil-tcsd-generator/
    SKILL.md
    agents/
      openai.yaml
    references/
    scripts/
    assets/
```

## Install A Skill

Install a single skill by repository path.

Examples:

```powershell
python "C:\Users\YOUR_NAME\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo uaapple/my-codex-skills --path windows-utf8-guard
python "C:\Users\YOUR_NAME\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo uaapple/my-codex-skills --path plan-to-todo
python "C:\Users\YOUR_NAME\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo uaapple/my-codex-skills --path simulink-hil-tcsd-generator
```

After installation, restart Codex so the new skill is discovered.

## Add More Skills

Add each new skill as another top-level folder in this repository.

Example:

```text
my-codex-skills/
  windows-utf8-guard/
  plan-to-todo/
  simulink-pdf-parser/
  another-skill/
```

Then install only the skill you want by passing its folder name with `--path`.
