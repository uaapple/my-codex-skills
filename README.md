# my-codex-skills

Personal Codex skills repository.

This repo is organized as:

- one repository
- multiple skills
- one skill per subdirectory

## Skills

- `windows-utf8-guard`: Prevent file corruption and mojibake when Codex edits text files on Windows, especially with Chinese or other non-ASCII text.
- `plan-to-todo`: 手动把当前已确认方案整理成中文任务清单，保存到工程内的 `plan-to-do/` 目录，支持并行维护多个 todo 文件，也支持手动审核指定 markdown 文件并更新勾选状态。
- `simulink-ut-tcsd-generator`: Generate and repair coverage-oriented Simulink unit-test TCSD Excel cases from `.slx` models and matching `.mat` files.

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
  simulink-ut-tcsd-generator/
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
python "C:\Users\YOUR_NAME\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo uaapple/my-codex-skills --path simulink-ut-tcsd-generator
```

After installation, restart Codex so the new skill is discovered.

## Use The Simulink UT Skill

After installing `simulink-ut-tcsd-generator`, the standard generation contract is part of the skill. You only need to name the skill and provide the model files.

Example:

```text
使用 simulink-ut-tcsd-generator，为 /path/to/Model.slx 和 /path/to/Model.mat 生成单元测试 TCSD 用例。
```

The skill defaults include copying the bundled support package, reading the model with SATK, prioritizing decision coverage, filling expected values only for top-level Outports, simulation-based stable-output backfill, and writing workbook/spec/result/report files under `outputs/`.

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
