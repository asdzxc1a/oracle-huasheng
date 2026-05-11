# Oracle — Actor Intelligence System

> **"Every claim is tagged. Every contradiction is preserved. Every uncertainty is named."**

The Oracle is a casting intelligence system for film producers. Given an actor's name and a casting question, it autonomously harvests video evidence, runs multimodal analysis, preserves contradictions, and produces a tier-marked brief with adversarial validation.

## Architecture

Built on Anthropic's Financial Agents layer-cake pattern:

```
Commands → Named Agents → Skills → Kernel
```

| Layer | What It Is | Examples |
|---|---|---|
| **Commands** | User-facing actions | `/assess`, `/harvest`, `/compare` |
| **Agents** | Workflow orchestrators | `video_analysis`, `actor_harvester`, `comparable_mapper` |
| **Skills** | Atomic expertise units | `contradiction-detection`, `tier-marking`, `body-language` |
| **Kernel** | Core engine | LLM client, formatters, Huasheng enforcement |

## Quick Start

```bash
cd oracle
uvicorn api.main:app --reload --port 8000

cd ui && npm run dev
```

Then open http://localhost:5173 and type:

```
/assess Zendaya — Can she carry a $25M non-franchise drama lead?
```

## The 12 Skills

| Skill | What It Does |
|---|---|
| `contradiction-detection` | Find and preserve ≥2 tension pairs |
| `tier-marking` | Tag claims A/B/C/F with auto-downgrade |
| `adversarial-pass` | Devil's advocate against the thesis |
| `body-language` | Extract behavioral signals from video |
| `voice-analysis` | Analyze vocal register and stress markers |
| `clinical-diagnostic` | 5-category psychological assessment |
| `archaeological-strata` | Excavate identity layers over time |
| `intelligence-fusion` | Career strategy and risk appetite analysis |
| `source-evaluation` | Rate sources by access level and signal density |
| `anti-pattern-enforcement` | Check 7 cognitive biases |
| `pre-ship-validation` | 8-item quality gate (score 0-100) |
| `brief-writer` | Compile final 6-section deliverable |

## Huasheng Pattern

Every brief is produced under the Huasheng Six Moves:

1. **Evidence** — Observable claims only, no generic praise
2. **Doubt** — Every claim questioned
3. **Triangulation** — Multiple sources converge
4. **Contradiction** — ≥2 tension pairs preserved, never resolved
5. **Adversarial Search** — ≥20% effort arguing against the thesis
6. **Uncertainty** — ≥3 explicit unknowns named

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/commands/assess` | Full actor assessment |
| POST | `/api/commands/harvest` | Source catalog only |
| POST | `/api/commands/compare` | Compare two actors |
| GET | `/api/skills` | List all skills |
| GET | `/api/skills/{name}` | Load skill documentation |
| GET | `/api/agents` | List available agents |
| POST | `/api/investigations` | Create investigation |
| GET | `/api/investigations/{id}` | Get investigation state |

## Governance

```bash
# Validate the skill ecosystem
python scripts/check.py

# Check agent skill references
python scripts/sync-agent-skills.py

# Run unit tests
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Invariants

- **File-system kernel** — No database. JSON + Markdown on disk.
- **Human is the oracle** — Agents amplify. Humans adjudicate.
- **LLM agnostic** — Claude → OpenAI → Gemini → heuristic fallback.
- **No build step** — Markdown + JSON + YAML only.

## License

Proprietary — Dmytr New AI Mastery
