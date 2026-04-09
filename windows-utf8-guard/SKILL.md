---
name: windows-utf8-guard
description: Prevent file corruption and mojibake when Codex edits text files on Windows, especially through PowerShell or when files contain Chinese or other non-ASCII text. Use when reading, patching, creating, or rewriting files may involve UTF-8, BOM, Unicode, console encoding, or suspected encoding damage.
---

# Windows UTF-8 Guard

Use this skill when working on Windows and any of the following are true:

- Files contain Chinese, Japanese, Korean, emoji, or other non-ASCII text
- PowerShell commands will read or write text files
- A file already shows mojibake, replacement characters, or garbled comments
- A user explicitly mentions UTF-8, BOM, encoding, charset, mojibake, or garbled console output

## Goal

Preserve file contents exactly while editing. Treat encoding safety as part of correctness, not formatting.

## Rules

1. Prefer `apply_patch` for text edits. Do not rewrite whole files via PowerShell unless necessary.
2. Treat console output and file bytes as different layers. If Chinese looks wrong in terminal output, do not assume the file is corrupted.
3. When using PowerShell to read text, explicitly specify UTF-8 capable behavior when possible. Avoid relying on defaults.
4. When using PowerShell to write text, never rely on default encoding. Write UTF-8 explicitly and preserve existing newlines when practical.
5. When a file may include a BOM, first try a BOM-aware read path before concluding the content is broken.
6. If the original encoding is uncertain and the file already contains non-ASCII text, minimize edits and avoid full-file rewrites.
7. If a command would replace an entire file containing Chinese text, pause and choose a byte-safe or patch-based approach instead.

## Practical Workflow

1. Inspect before editing.
2. Make the smallest possible change.
3. Prefer patch-based edits over generated full rewrites.
4. If you must script a rewrite, read the guidance in `references/windows-utf8-rules.md` first.
5. After editing, verify that nearby Chinese text still renders correctly in a UTF-8 aware viewer or editor.

## Red Flags

- `Set-Content` or `Out-File` used without explicit encoding
- Rewriting a file only to change a few lines
- Assuming terminal mojibake means source-file corruption
- Mixing cmd, old PowerShell defaults, and editor saves without checking encoding

## Expected Behavior

When this skill applies, bias toward safer edits even if they are slower:

- Use patch edits instead of shell rewrites
- Preserve existing text around Chinese content
- Call out encoding uncertainty before doing a risky rewrite
- Keep the user's original characters intact
