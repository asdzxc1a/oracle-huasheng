# AGENTS.md — Oracle Architecture Decision Document

**Status:** Decision Record — Approved for Implementation  
**Scope:** Refactor existing `oracle/` codebase to Anthropic Financial Agents architecture  
**Invariants:** File-system kernel, Huasheng Six Moves, human-as-oracle, no database  

---

## 1. WHAT WE HAVE NOW

The Oracle is a working actor-intelligence system at `oracle/`:

- **Backend:** FastAPI (`api/main.py`) serving REST + static React SPA
- **Frontend:** React 19 + Vite + Tailwind (`ui/src/`) with investigation dashboard, pipeline viewer, brief viewer, chat panel
- **Agents:** 2 working agents in `agents/` — `actor_harvester` (source catalog) and `video_analysis` (multimodal brief generation)
- **Kernel:** `kernel/intelligence.py` (LLM client + Huasheng enforcement), `kernel/agent_runner.py` (dynamic import + execution), `kernel/manifest.py` (investigation state), `kernel/context_store.py` (actor profiles)
- **Data:** Investigations at `investigations/{id}/`, actor profiles at `context/actors/{slug}.json` — JSON + Markdown on disk, no database
- **LLM:** Multi-provider (Claude → OpenAI → Gemini → heuristic fallback)

The system works. It produces tier-marked, contradiction-preserving, adversarially-tested briefs. The problem: agents are monolithic Python modules (`video_analysis/agent.py` is 782 lines) bundling logic, prompts, and references together. They are not composable.

---

## 2. WHAT ANTHROPIC FINANCIAL AGENTS DOES THAT WE NEED

Anthropic's system has 5 layers with strict separation:

```
Commands → Named Agents → Vertical Plugins → Skills → Data Connectors
```

We adopt this exact structure with these exact mechanisms:

| Anthropic Pattern | What It Means for Oracle | Where It Lives |
|---|---|---|
| **Skills as atomic units** | Extract `contradiction-detection`, `tier-marking`, `adversarial-pass`, `body-language`, etc. from `video_analysis/agent.py` into standalone `SKILL.md` packages | `skills/` (new) |
| **Vertical plugins** | Domain libraries: `actor-analysis/`, `video-processing/`, `report-generation/` | `verticals/` (new) |
| **Named agents** | `actor-assessor`, `source-harvester`, `comparable-mapper` — each is a system prompt + bundled skill copies | `agents/` (evolved) |
| **Commands** | Slash-command endpoints: `/assess`, `/harvest`, `/compare` | `api/routers/commands.py` (new) |
| **Progressive disclosure** | Skills load in 3 tiers: metadata (100 words) → body (5k words) → references/scripts (on demand) | `kernel/skill_loader.py` (new) |
| **Vertical source of truth + sync** | Edit skills in `verticals/`. Run `sync-agent-skills.py` to propagate to agents. `check.py` prevents drift. | `scripts/` (new) |
| **No-build governance** | Everything is Markdown + JSON + YAML. Non-engineers edit skills. | `AGENTS.md` (this file) |

---

## 3. THE REFACTOR — EXACT CHANGES TO EXISTING FILES

### New Directories (alongside existing)

```
oracle/
├── skills/                 ← NEW: atomic expertise extracted from agents
│   ├── contradiction-detection/
│   │   ├── SKILL.md
│   │   └── scripts/detect.py
│   ├── tier-marking/
│   │   ├── SKILL.md
│   │   └── scripts/tagger.py
│   ├── adversarial-pass/
│   │   ├── SKILL.md
│   │   └── scripts/devil_advocate.py
│   ├── body-language/
│   │   ├── SKILL.md
│   │   └── references/framework.md
│   ├── source-evaluation/
│   │   ├── SKILL.md
│   │   └── references/reliability-matrix.md
│   ├── clinical-diagnostic/
│   ├── archaeological-strata/
│   ├── intelligence-fusion/
│   ├── anti-pattern-enforcement/
│   ├── pre-ship-validation/
│   ├── comparable-mapping/
│   ├── brief-writer/
│   ├── frame-extraction/
│   ├── transcript-generation/
│   └── video-catalog/
│
├── verticals/              ← NEW: domain libraries (source of truth)
│   ├── actor-analysis/
│   │   ├── plugin.json
│   │   ├── commands/
│   │   │   ├── assess.md
│   │   │   ├── harvest.md
│   │   │   └── compare.md
│   │   └── skills/         ← symlinks or copies to ../../skills/
│   ├── video-processing/
│   └── report-generation/
│
└── scripts/                ← NEW: governance
    ├── check.py            ← lint + drift detection
    └── sync-agent-skills.py  ← vertical → agent propagation
```

### Refactored Existing Files

| Current File | Change |
|---|---|
| `kernel/intelligence.py` | **Extract** `LLMClient` into `kernel/llm_client.py`. Keep Huasheng enforcement (`tier-marking`, `contradiction-detection`, etc.) as composable functions that skills call. |
| `kernel/agent_runner.py` | **Refactor** to load agent system prompt + bundled skills via `skill_loader.py`. Agent no longer contains monolithic logic — it orchestrates skill execution. |
| `agents/video_analysis/agent.py` | **Shrink** from 782 lines to ~150 lines. Extract 12 skill-sized chunks into `skills/`. Agent becomes a thin orchestrator: load skills → run workflow → validate. |
| `agents/actor_harvester/agent.py` | **Shrink** from 599 lines to ~100 lines. Extract `source-evaluation` and `video-catalog` skills. |
| `api/main.py` | **Add** `commands` and `skills` routers. Preserve existing `/investigations`, `/agents`, `/files`. |
| `ui/src/App.tsx` | **Add** routes for `/skills`, `/commands`. Preserve `/` (Dashboard) and `/investigation/:id`. |
| `ui/src/pages/Dashboard.tsx` | **Add** CommandBar component at top. Preserve investigation grid. |

### Preserved Exactly (No Changes)

| File | Why |
|---|---|
| `kernel/manifest.py` | Investigation state model is correct. |
| `kernel/context_store.py` | Actor/client storage is correct. |
| `kernel/video_pipeline.py` | yt-dlp + ffmpeg + Whisper pipeline is correct. |
| `kernel/human_hook.py` | Human-as-oracle pause points are correct. |
| `investigations/{id}/` structure | File layout already matches Huasheng + Anthropic patterns. |
| `context/actors/{slug}.json` | Actor profile format is correct. |
| `api/routers/investigations.py` | CRUD + human input endpoints are correct. |
| `api/routers/files.py` | File tree + content serving is correct. |

---

## 4. SKILL ANATOMY (EXACT FORMAT)

Every skill is a self-contained directory with this exact structure:

```
skills/skill-name/
├── SKILL.md              ← REQUIRED. YAML frontmatter + markdown body.
│   ├── ---               ← YAML frontmatter: name, description
│   └── body              ← Workflow, output format, quality checklist (<500 lines)
├── scripts/              ← OPTIONAL. Executable code.
└── references/           ← OPTIONAL. Docs loaded on demand.
```

**`SKILL.md` frontmatter (exact):**

```yaml
---
name: contradiction-detection
description: |
  Find and preserve ≥2 contradiction pairs across actor claims.
  Use before shipping the brief. Never smooth contradictions.
---
```

**Loading rules (exact):**

1. **Metadata** (`name` + `description`) — always in context (~100 words)
2. **Body** — loaded when skill triggers (<5,000 words)
3. **References/scripts** — loaded on demand

Implemented in `kernel/skill_loader.py` with `SkillLoader.load_metadata()`, `.load_body()`, `.load_full()`.

---

## 5. AGENT COMPOSITION (EXACT FORMAT)

An agent is **not** a model. It is a system prompt + bundled skills + guardrails.

**Agent system prompt (`agents/actor-assessor.md`):**

```markdown
---
name: actor-assessor
description: |
  End-to-end actor assessment. Harvest → Analyze → Brief → Validate.
tools: Read, Write, web_search, video_process
---

You are the Actor Assessor...

## What you produce
1. Video source catalog
2. Structured brief (6 sections)
3. Contradiction map (≥2 pairs)
4. Adversarial findings
5. Pre-ship validation report

## Workflow
1. Scope the ask
2. Harvest sources → `source-evaluation`
3. Process videos → `frame-extraction`, `transcript-generation`
4. Run clinical analysis → `clinical-diagnostic`, `body-language`
5. Run intelligence analysis → `intelligence-fusion`, `voice-analysis`
6. Run archaeological analysis → `archaeological-strata`
7. Detect contradictions → `contradiction-detection`
8. Run adversarial pass → `adversarial-pass`
9. Apply tier marking → `tier-marking`
10. Enforce anti-patterns → `anti-pattern-enforcement`
11. Validate → `pre-ship-validation`
12. Write brief → `brief-writer`

## Guardrails
- Never fabricate URLs
- Cite every claim
- Preserve contradictions
- Stop for human review after catalog and after brief

## Skills this agent uses
`source-evaluation` · `body-language` · `voice-analysis` · ...
```

**Key rule:** Workflow steps invoke skills by backtick name. The agent runner resolves skill names to `skills/{name}/SKILL.md` bodies and injects them into the LLM context.

---

## 6. COMMAND LAYER (EXACT FORMAT)

Commands are explicit user-initiated actions mapped to agents:

| Command | Agent | Input | Output |
|---|---|---|---|
| `/assess [actor] — [question]` | `actor-assessor` | Actor + casting question | Full investigation + brief |
| `/harvest [actor] — [focus]` | `source-harvester` | Actor + focus areas | Video catalog + facts |
| `/compare [A] vs [B] — [Q]` | `comparable-mapper` | Two actors + question | Comparative analysis |

**API:** `POST /api/commands/assess` → creates investigation + runs agent  
**Frontend:** CommandBar component at top of Dashboard parses prefix, shows autocomplete, submits to `/api/commands/{prefix}`

---

## 7. GOVERNANCE (EXACT TOOLS)

### `scripts/check.py`

Validates the entire plugin ecosystem:

1. All `SKILL.md` files parse (YAML frontmatter + body)
2. All agent `.md` files have valid frontmatter (`name`, `description`, `tools`)
3. All `plugin.json` files parse
4. Agent system prompts reference skills that exist in their bundle
5. Bundled skills match vertical source (drift detection)
6. No duplicate skill names

### `scripts/sync-agent-skills.py`

Propagates skill changes from `verticals/` to agent bundles:

```bash
# Edit skills in verticals/ only
# Then run:
python scripts/sync-agent-skills.py
# Verify:
python scripts/check.py
```

**Rule:** Vertical source of truth. Never edit bundled skills directly.

---

## 8. INVARIANTS — WHAT NEVER CHANGES

These are locked. Any refactor must preserve them:

1. **File-system kernel** — No database. JSON + Markdown on disk.
2. **Human is the oracle** — Agents amplify. Humans adjudicate. Every output staged for sign-off.
3. **Huasheng Six Moves** — Evidence, doubt, triangulation, contradiction, adversarial search, uncertainty.
4. **Tier A/B/C/F marking** — With auto-downgrade by access level (SCRIPTED → Tier C cap).
5. **≥2 contradiction pairs** — Mandatory. Preserved, not resolved.
6. **Anti-pattern enforcement** — 7 cognitive biases checked on every brief.
7. **Pre-ship validation gate** — 8-item checklist, score 0-100, critical blockers block shipment.
8. **LLM agnostic** — Claude → OpenAI → Gemini → heuristic fallback.
9. **No build step** — Markdown + JSON + YAML only. Non-engineers edit skills.
10. **Evidence to disk** — Every agent writes output before the next agent reads it.

---

## 9. IMPLEMENTATION ORDER

1. **Create `skills/`** — Extract first 3 skills from `video_analysis/agent.py`: `contradiction-detection`, `tier-marking`, `adversarial-pass`
2. **Create `kernel/skill_loader.py`** — Progressive disclosure implementation
3. **Shrink `video_analysis/agent.py`** — Replace extracted logic with skill orchestration
4. **Create `scripts/check.py` + `sync-agent-skills.py`** — Governance
5. **Create `api/routers/commands.py`** — `/assess`, `/harvest`, `/compare`
6. **Add CommandBar to UI** — Frontend command layer
7. **Extract remaining skills** — `body-language`, `clinical-diagnostic`, `source-evaluation`, etc.
8. **Create `verticals/` + agent system prompts** — Full layer-cake
9. **Write tests** — Unit per skill, integration per agent, golden path E2E
10. **Run `check.py`** — Verify zero drift, zero lint errors

---

*This document governs all code in `oracle/` and subdirectories. Deeper `AGENTS.md` files may override specific rules for their scope.*
