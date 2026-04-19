---
name: plan-to-todo
description: Turn an agreed solution from the current conversation into a persisted project todo list and keep that todo list updated across later turns. Use only when the user explicitly asks to activate this skill by name or slash-style command; do not auto-trigger it from general planning requests.
---

# Plan To Todo

## Overview

Freeze the currently agreed solution into a project-local markdown todo file, then keep that same file updated as work progresses. This skill is manual-only: use it only when the user explicitly asks for `plan-to-todo`.

## Fixed Output Path

Always write to this project-local path:

`<repo-root>/.codex/active-todo.md`

If `.codex/` does not exist in the project root, create it.

## When To Use

Use this skill only in either of these situations:

- The user explicitly asks to activate `plan-to-todo`, or uses slash-style wording to convert the agreed plan into a todo file.
- The user explicitly asks to refresh or update the existing todo file after some tasks were completed.

Do not auto-trigger this skill for ordinary planning, brainstorming, or implementation work.

## Workflow

### 1. Identify the source plan

Look at the current conversation and find the most recent assistant answer that the user accepted as the plan or solution.

If the accepted solution is ambiguous, ask one short question to confirm which answer should be frozen into the todo file.

### 2. Summarize the agreed plan

Write a short summary of the accepted solution at the top of the file. This summary should capture the overall approach, not every implementation detail.

### 3. Derive sensible sub-tasks

Split the agreed solution into practical, ordered sub-tasks that make sense to execute one by one.

Requirements:

- Keep tasks concrete and action-oriented.
- Prefer 4-10 tasks unless the work is genuinely larger.
- Order tasks by dependency.
- Avoid mixing multiple unrelated actions into one checkbox.
- Include verification or cleanup tasks only when they materially help complete the work.

### 4. Persist the todo file

Create or overwrite `<repo-root>/.codex/active-todo.md` with the current plan and task list when the user asks to freeze a new plan.

When the user asks to update progress later, edit the same file instead of creating a new one.

### 5. Reuse the file in later turns

On later manual activations of this skill:

- Read `<repo-root>/.codex/active-todo.md` first.
- Mark completed tasks as done.
- Update progress notes if needed.
- Keep unfinished tasks in order.
- If a completed task changes the next steps, revise the remaining tasks to stay sensible.

## File Format

Always use this markdown structure:

```md
# Active Todo

## Agreed Plan
<2-6 sentence summary of the solution the user accepted>

## Task List
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Progress Notes
- Created from conversation on YYYY-MM-DD.
- Optional: short note about what changed during later updates.
```

Rules:

- Use `- [ ]` for pending tasks.
- Use `- [x]` for completed tasks.
- Keep the plan summary above the task list.
- Keep the wording compact and readable.

## Update Rules

When asked to continue from the todo file:

- Read the file before deciding the next step.
- Prefer the first unfinished task unless the user explicitly reprioritizes.
- After completing meaningful work, update the checkbox state in the file.
- If a task is too large once implementation starts, split it into smaller follow-up tasks in the same file.

## Output Behavior

After writing or updating the file:

- Tell the user which file was written.
- Briefly summarize the plan and the number of tasks.
- Mention the next unfinished task when relevant.

## Boundaries

- Do not create multiple competing todo files.
- Do not invent a plan if the conversation has not converged on one.
- Do not auto-activate this skill without explicit user instruction.
