---
name: conversation-logger
description: |
  Logs key conversation Q&A content to organized markdown files with JSON metadata. Use this skill whenever the user asks to "log this", "remember this", "save this talk", or "save this conversation". Also trigger when users want to preserve technical discussions, code solutions, or important decisions for future reference. All logs go directly into `conversation-logs/logs/`.
---

# Conversation Logger

When a user asks you to log, remember, or save the current conversation, capture the key content from the recent discussion and store it in an organized format for future reference.

## When to Use This Skill

Trigger this skill when the user says:
- "log this"
- "remember this"
- "save this talk"
- "save this conversation"
- Similar phrases indicating they want to preserve the current discussion

## What to Log

Extract and save:
1. **The user's question or request** - What they asked or what problem they were trying to solve
2. **The key solution or answer** - A concise summary of what was accomplished or explained
3. **Code snippets** - Any important code that was written, with proper syntax highlighting
4. **Important decisions or insights** - Key takeaways or lessons learned

Focus on the substance, not minutiae. Think about what would be useful if someone (including the user) reads this log 3 months from now.

## How to Organize Logs

### Directory Structure

All logs are stored directly under `conversation-logs/` in the current working directory — no subdirectory per project or "random" category:

```
conversation-logs/
├── metadata.json
└── logs/
    ├── 2026-03-03_discussion-about-x.md
    ├── 2026-03-04_another-topic.md
    └── 2026-03-05_bug-fix-authentication.md
```


### File Naming

Name the markdown file: `YYYY-MM-DD_brief-topic-slug.md`

- Use today's date
- Create a short slug (3-5 words) that captures the topic
- Use lowercase with hyphens
- Example: `2026-03-03_authentication-bug-fix.md`

## Log Format

### Markdown File Structure

```markdown
# [Brief Title]

**Date**: YYYY-MM-DD

## Question

[What the user asked or the problem they were trying to solve]

## Solution

[Summary of the answer or solution provided]

## Code

[If applicable, include important code snippets with proper markdown code fences]

\`\`\`language
// code here
\`\`\`

## Key Takeaways

- [Important points to remember]
- [Decisions made]
- [Lessons learned]
```

### Metadata JSON

The `metadata.json` file at `conversation-logs/metadata.json` tracks all logs:

```json
{
  "project": "project-name",
  "logs": [
    {
      "date": "2026-03-03",
      "filename": "2026-03-03_authentication-bug-fix.md",
      "title": "Authentication Bug Fix",
      "tags": ["bug-fix", "authentication", "security"],
      "created_at": "2026-03-03T14:30:00Z"
    }
  ]
}
```

When adding a new log:
1. Read the existing `metadata.json` (create if doesn't exist)
2. Append the new log entry
3. Write back to `metadata.json`

## Workflow

1. **Analyze the conversation** - Review the last 5-10 messages to understand what was discussed
2. **Extract key content** - Pull out the question, solution, code, and insights
3. **Generate filename** - Create a descriptive slug based on the topic
4. **Write markdown file** - Format the content cleanly in the structure above at `conversation-logs/logs/`
5. **Update metadata.json** - Add the entry to `conversation-logs/metadata.json`
6. **Confirm completion** - Tell the user where the log was saved

## Tips for Writing Good Logs

- **Be concise but complete** - Future readers should understand the context without reading the full conversation
- **Include enough code** - Show the important parts, but you don't need to log every single line if it's lengthy. Focus on the key logic.
- **Extract the "why"** - Don't just describe what was done, explain why it matters or what problem it solved
- **Use clear titles** - The filename slug and markdown title should immediately convey what the log is about
- **Add useful tags** - In metadata.json, include tags that would help searching later (e.g., "bug-fix", "feature", "refactoring", "debugging")

## Example

User says: "This was super helpful, can you save this conversation?"

You respond: "I'll save this to `conversation-logs/eval-engine/`. Let me create a log of our discussion about fixing the OOM issue with concurrent evaluations."

Then create:
- `conversation-logs/logs/2026-03-03_oom-fix-concurrent-evals.md`
- Update `conversation-logs/metadata.json`

And confirm: "✓ Saved to `conversation-logs/logs/2026-03-03_oom-fix-concurrent-evals.md`"
