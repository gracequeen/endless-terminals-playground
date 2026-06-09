# Domain Rebasing for Task Generation

## What "rebasing" means

The current pipeline is domain-agnostic — it draws from generic Linux sysadmin categories and SCENARIO_CONTEXTS. Rebasing means substituting domain-specific signal at every prompt injection point so the LLM generates tasks grounded in your domain's tools, failure modes, file layouts, and personas — without changing the pipeline code structure.

---

## The four injection points (mapped to code)

| Stage | File | What gets injected |
|---|---|---|
| Task template | `task_template_gen.py` | `SYSTEM_MSG` append, `TASK_CATEGORIES`/`CATEGORY_BUCKETS` replacement, `SCENARIO_CONTEXTS` replacement, few-shot examples in user message |
| Initial state test | `initial_state_test_gen.py` | `SYSTEM_MSG` append (domain tool assumptions) |
| Final state test | `completion_test_gen.py` | `SYSTEM_MSG` append (domain-specific semantic checks) |
| Dockerfile | `dockerfile_gen.py` | `SYSTEM_MSG` append (install patterns, entrypoint patterns) |

`generate_harbor_tasks.py` already monkey-patches all four modules' `SYSTEM_MSG` values (it does this for the Apptainer → Docker substitution). Domain injection follows the same pattern.

---

## Domain materials format

A single directory, e.g. `domains/sap-cap/`, with four files:

```
domains/
└── sap-cap/
    ├── domain.toml          # metadata + config
    ├── context.md           # injected into task_template_gen SYSTEM_MSG
    ├── examples.jsonl       # few-shot task+truth pairs
    └── dockerfile_seeds.md  # injected into dockerfile_gen SYSTEM_MSG
```

---

### `domain.toml`

Metadata, category buckets (replaces `CATEGORY_BUCKETS`), and persona strings (replaces `SCENARIO_CONTEXTS`).

```toml
name = "sap-cap"
description = "SAP Cloud Application Programming Model development tasks"

# Replaces pick_balanced_categories() output
[categories]
cap_backend = [
    "CAP service definition and CDS modeling",
    "OData service debugging",
    "CAP handler logic and custom actions",
    "database migration with CDS",
]
cap_devops = [
    "BTP Cloud Foundry deployment",
    "MTA build and deploy",
    "cf CLI operations",
]
hana = [
    "HANA SQL debugging",
    "HDI container management",
    "CDS view optimization",
]
abap = [
    "ABAP to CAP migration",
    "RFC/BAPI integration",
]

# Replaces SCENARIO_CONTEXTS
[[personas]]
names = [
    "SAP developer migrating a legacy ABAP service to CAP",
    "BTP developer debugging an OData endpoint",
    "CAP backend engineer setting up a new service",
    "HANA database engineer investigating a slow CDS view",
]
```

Why TOML: it's already used in `task.toml` in the Harbor format, and is simpler than JSON for nested lists with comments.

---

### `context.md`

Appended verbatim to `task_template_gen.SYSTEM_MSG`. Tells the LLM what's realistically available in the container and how tasks present in this domain.

Three required sections:

**Environment** — exact paths, tools, versions, what's pre-installed, what's running at agent start.

**How tasks present** — 5–8 realistic trigger patterns written in the same casual engineer voice as the task format (not a spec list).

**What agents must NOT need** — constraints for the Dockerfile generator: no real credentials, no live cloud connectivity, no services that can't be started without systemd, etc.

Example:

```markdown
## Domain context: SAP CAP

### Environment
- Node.js 20, `@sap/cds-dk` installed globally (`cds` CLI available)
- `cf` CLI available for BTP Cloud Foundry interactions
- SQLite used as the local HANA substitute (`~/.cds-sandbox.db`)
- Project root: /home/user/app — a `cds init`-generated CAP project
- `package.json` present, `npm install` already run, `node_modules/` present
- `cds serve` starts the OData service on port 4004

### How tasks present in this domain
- A `cds deploy` or `cds serve` fails with a cryptic CDS compilation error
- An OData $filter query returns wrong results and the developer suspects the CDS view
- A `cf push` hangs or fails and the logs point somewhere non-obvious
- An HDI artifact was renamed and dependent views are broken
- A custom handler in `srv/` throws at runtime but works in isolation

### What agents must NOT need
- SAP BTP credentials (no real cloud connectivity)
- An actual HANA instance (use SQLite or mock)
- `cf login` (pre-authenticated state must be seeded in the container)
```

---

### `examples.jsonl`

3–7 hand-written examples. Each line is one JSON object with `task` and `truth` keys matching the format `parse_template()` expects. These get injected as additional few-shot examples appended to `SYSTEM_MSG`.

```jsonl
{"task": "cds serve keeps failing on startup — something about 'entity Books is not defined' but it's clearly in my schema.cds. Worked fine yesterday, only change was adding a new association to Authors.", "truth": "Initial state:\n- /home/user/app is a CAP project\n- /home/user/app/db/schema.cds defines entity Books with an association `author: Association to Authors`\n- /home/user/app/db/schema.cds does NOT define entity Authors — it was accidentally deleted\n- `cds serve` exits non-zero with error 'entity Authors is not defined'\n- Node 20, @sap/cds-dk installed\n\nExpected final state:\n- `cds serve` starts successfully and listens on port 4004\n- GET http://localhost:4004/catalog/Books returns HTTP 200\n\nInvariants:\n- Books entity definition unchanged\n- No package.json modifications\n\nAnti-shortcut guards:\n- Authors entity must be defined in a .cds file, not commented out or stubbed with an empty body\n- `grep -r 'entity Authors' /home/user/app/db` must match at least one real definition"}
```

**Critical:** The `truth` block must follow the four-section shape that the existing `SYSTEM_MSG` specifies — `Initial state`, `Expected final state`, `Invariants`, `Anti-shortcut guards` — because `completion_test_gen` and `initial_state_test_gen` both parse from it.

This is the highest-leverage input. A bad `truth` block cascades into bad tests and bad Dockerfiles. Budget 30–45 min per example. Start with 3, evaluate quality, add more if needed.

---

### `dockerfile_seeds.md`

Appended to `dockerfile_gen.SYSTEM_MSG`. Gives the LLM correct install and entrypoint patterns it won't know from general training data. Lift these from working Dockerfiles you already have if possible.

```markdown
## Domain: SAP CAP — Dockerfile patterns

### Install pattern
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y nodejs npm python3 python3-pip curl
RUN npm install -g @sap/cds-dk
RUN pip3 install hdbcli
RUN mkdir -p /home/user && chmod 0777 /home/user
```

### CAP project seed
```dockerfile
WORKDIR /home/user/app
RUN cds init . --add sqlite
RUN npm install
```

### Service entrypoint (when cds serve must be running at agent start)
```dockerfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
# entrypoint.sh: starts `cds serve &`, waits for port 4004, then exec bash
```
```

---

## How it wires into `generate_harbor_tasks.py`

The entry point already does monkey-patching. Domain loading adds four more patches before the generators are called:

```python
# After existing monkey-patches, before generate_templates_batch() calls:
if cfg.domain:
    domain = load_domain(cfg.domain)          # reads domains/<name>/
    ttg.SYSTEM_MSG += domain.context_md
    ttg.SYSTEM_MSG += domain.fewshot_block    # formatted from examples.jsonl
    ttg.SCENARIO_CONTEXTS = domain.personas   # replaces global list
    dfg.SYSTEM_MSG += domain.dockerfile_seeds
    categories_override = domain.categories   # passed to pick_balanced_categories
```

`pick_balanced_categories` already accepts an external bucket dict — it uses `CATEGORY_BUCKETS` by default. One small change needed: accept an optional `buckets` parameter.

---

## Preparation checklist

| File | Effort | Notes |
|---|---|---|
| `domain.toml` | ~30 min | 3–6 category buckets, 4–6 personas |
| `context.md` | ~1 hr | Environment + trigger patterns + agent constraints |
| `examples.jsonl` | 30–45 min each | Start with 3; highest leverage input |
| `dockerfile_seeds.md` | ~30 min | Lift from working Dockerfiles if available |

---

## Out of scope (not designed here)

**Solution generation rebasing** — `generate_harbor_solutions.py` uses `AICoreTerminus2`, an agent not a template generator. Domain rebasing there means a different agent system prompt. Design after evaluating solution quality on the first domain task batch.

**Test generation domain hints** — `initial_state_test_gen` and `completion_test_gen` may need domain-specific import hints (e.g. "you can use `requests` to hit OData endpoints"). Evaluate after seeing test quality on the first domain batch.
