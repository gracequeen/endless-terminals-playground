---
name: task
description: Load a task spec from claude-input/<name>.md, plan the implementation, get user approval, execute, and save the solution to cc-tasks-solutions/<name>-solution.md
---

You are executing a structured task workflow. Follow these steps exactly:

## Step 1 — Load the task spec

The task name is provided as `args`. Read the file:
```
claude-input/<args>.md
```
If the file does not exist, report the error and stop.

## Step 2 — Explore and plan

Explore the codebase as needed to understand what needs to change. Then write a concrete implementation plan covering:
- What the task requires
- Which files will be created or modified
- Step-by-step implementation approach
- How you will verify the solution works

Present the plan clearly to the user. Do NOT implement yet.

## Step 3 — Get approval

Use `ExitPlanMode` to present the plan and wait for user approval before proceeding.

## Step 4 — Implement

Execute the approved plan. Make all necessary code changes.

## Step 5 — Save the solution

Write a solution document to:
```
cc-tasks-solutions/<args>-solution.md
```

The solution document must include:
- **Problem** — what the task asked for
- **Changes made** — files modified/created, with key decisions explained
- **Behavior summary** — how the solution works
- **Verification** — how to confirm it works
