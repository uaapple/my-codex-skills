# Windows UTF-8 Rules

This reference distills the useful parts of the user's linked post together with Windows-safe editing guidance for Codex.

## What The Post Helps With

The post is useful because it separates three problems that are often confused:

- Console display encoding
- PowerShell read/write defaults
- Real file-content corruption

That distinction is the most important guardrail. A terminal that renders Chinese badly does not prove the file bytes are wrong.

## Recommended Operating Rules

### 1. Normalize the shell session when text inspection matters

When you need to inspect Chinese text in PowerShell, prefer a UTF-8 oriented session setup first. Typical ingredients:

- Set console input/output encoding to UTF-8
- Prefer tools and commands that are known to behave well with UTF-8

This improves display reliability but does not, by itself, guarantee file-write safety.

### 2. Prefer patch edits over shell rewrites

For Codex work, this is the single highest-value rule.

- Safe default: `apply_patch`
- Risky default: `Set-Content`, `Out-File`, bulk replace scripts, or full-file rewrites

If only a few lines need changes, use a patch.

### 3. Explicitly control encoding on scripted reads and writes

If a shell command must read or write text:

- Read with explicit UTF-8 behavior when available
- Write with explicit UTF-8 behavior
- Preserve the original newline style if possible

Never depend on Windows PowerShell legacy defaults for multilingual files.

### 4. Be BOM-aware

Some files are UTF-8 with BOM. If content seems wrong:

- First suspect a BOM/display mismatch
- Try a BOM-aware read path
- Avoid saving the file in a different encoding just because the terminal looked wrong

### 5. Treat existing mojibake as evidence, not proof of cause

If you see garbled text:

- Check whether the corruption is already present in the file
- Compare with a trusted editor
- Avoid compounding damage by saving again through an unsafe path

## Decision Guide

### Safe to proceed

- ASCII-only edit
- Patch-based edit
- File encoding already known
- UTF-8 explicit read/write path in place

### Use extra caution

- Chinese comments or strings near the edit
- Full-file rewrite
- Mixed tooling across editor, PowerShell, and scripts
- Unknown original encoding

### Stop and change approach

- Terminal output is garbled and you were about to overwrite the file
- You cannot confirm the source encoding
- The planned command depends on PowerShell defaults

## Good Defaults For A Future Agent

- Assume `apply_patch` is safer than shell write commands
- Assume Chinese text is high risk for accidental corruption
- Assume terminal rendering can lie
- Assume explicit UTF-8 is required whenever PowerShell writes text
