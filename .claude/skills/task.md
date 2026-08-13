---
name: task
description: Load a task spec from claude-input/<name>.md, clarify requirements, plan, get approval, implement, and save design + solution to cc-tasks-solutions/
---

You are executing a structured task workflow. Follow these steps exactly, in order.

## Step 1 — Load the task spec

The task name is provided as `args`. Read the file:
```
claude-input/<args>.md
```
If the file does not exist, report the error and stop.

## Step 2 — Clarify requirements

Before exploring the codebase, state your understanding of the task in plain language:
- **Goal**: one sentence — what outcome is being achieved
- **Scope**: what is explicitly in scope and what is out of scope
- **Inputs / outputs**: what the solution takes as input and what it produces
- **Constraints**: performance, compatibility, style, or other hard requirements
- **Open questions**: anything ambiguous in the spec that could affect the design

If there are open questions, surface them now (before exploration). If the spec is clear, state that and proceed.

## Step 3 — Explore and design

Explore the codebase as needed to understand the current state. Then produce a design covering:
- **Approach**: chosen solution strategy and why (mention alternatives rejected and why)
- **Affected files**: each file to be created or modified, and what changes
- **Key design decisions**: non-obvious choices, tradeoffs, invariants to preserve
- **Implementation steps**: ordered list of concrete changes
- **Verification**: how to confirm the solution is correct (tests, manual checks, expected output)

Present the requirements summary (from Step 2) and the design together. Do NOT implement yet.

## Step 4 — Get approval

Use `ExitPlanMode` to present the full requirements + design and wait for user approval before proceeding.

**Auto mode bypass**: if the user has explicitly enabled auto/autonomous mode for this session, approval is optional — proceed directly to implementation after presenting the design.

## Step 5 — Implement

Execute the approved plan. Make all necessary code changes. Note any deviations from the approved design.

## Step 6 — Log design and implementation

Write two documents:

**Design log** — `cc-tasks-solutions/<args>-design.md`:
- Requirements summary (goal, scope, constraints, open questions resolved)
- Design: approach, alternatives considered, key decisions and rationale
- Affected files list

**Solution log** — `cc-tasks-solutions/<args>-solution.md`:
- Problem statement
- Implementation summary: what was changed, file by file
- Deviations from the approved design (if any)
- Verification: steps taken, results, how to re-verify
