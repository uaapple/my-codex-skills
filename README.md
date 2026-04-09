# my-codex-skills

Personal Codex skills repository.

This repo is organized as:

- one repository
- multiple skills
- one skill per subdirectory

## Skills

- `windows-utf8-guard`: Prevent file corruption and mojibake when Codex edits text files on Windows, especially with Chinese or other non-ASCII text.

## Repository Layout

```text
my-codex-skills/
  windows-utf8-guard/
    SKILL.md
    agents/
      openai.yaml
    references/
      windows-utf8-rules.md
```

## Install A Skill

Install a single skill by repository path.

Example:

```powershell
python "C:\Users\YOUR_NAME\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo uaapple/my-codex-skills --path windows-utf8-guard
```

After installation, restart Codex so the new skill is discovered.

## Add More Skills

Add each new skill as another top-level folder in this repository.

Example:

```text
my-codex-skills/
  windows-utf8-guard/
  simulink-pdf-parser/
  another-skill/
```

Then install only the skill you want by passing its folder name with `--path`.
