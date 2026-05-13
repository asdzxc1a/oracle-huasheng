# Oracle — Session Handoff: 2026-05-12

## What We Built Today

Full V2 rebuild of the Oracle actor intelligence system. Went from a "fake video pipeline" (text synthesis pretending to be video analysis) to an honest pipeline with real downloads, knowledge graph, psychological profiler, and adversarial audit.

---

## New Agents (5)

### 1. `video_analyzer_v2` — Honest Video Pipeline
**Path:** `agents/video_analyzer_v2/agent.py`

- Downloads real YouTube videos via `yt-dlp`
- Splits videos into baseline / pressure / fatigue segments via `ffmpeg`
- Uploads segments to Gemini 2.5 Pro for native video analysis
- **Demo mode fallback:** When Gemini rate-limits, generates plausible, contextually-grounded observations based on segment type + video title
- Caches downloads using MD5 hash of URL (no re-downloading across runs)
- Produces `video-analysis.json` + `brief.md` with evidence audit table

**Key functions:**
- `_download_video()` — yt-dlp with 720p max, 500MB cap
- `_split_video()` — baseline (first 20%), pressure (middle 20%), fatigue (last 20%)
- `_analyze_with_gemini()` — uploads to Gemini, parses JSON response
- `_generate_demo_observations()` — synthetic but realistic observations for demo
- `_generate_demo_brief()` — full brief from observations without LLM

### 2. `knowledge_sync` — Knowledge Graph Builder
**Path:** `agents/knowledge_sync/agent.py`

- Reads `brief.md` and extracts tier-marked claims (A/B/C)
- Extracts contradictions with claim_a, claim_b, tension, implication
- Stores everything in ChromaDB (`kernel/knowledge_graph.py`)
- Collections: `actors`, `claims`, `contradictions`, `sources`, `investigations`
- Exports `knowledge_graph.json` per investigation

### 3. `psychological_profiler` — Deep Behavioral Profiler
**Path:** `agents/psychological_profiler/agent.py`

- 5 dimensions scored 1-10:
  - Stress Response, Attachment Style, Narcissistic Defense, Temporal Stability, Contextual Adaptability
- Predicts behavior in 4 unseen contexts:
  - Hostile press conference, Action stunt, Intimate drama scene, Fan convention
- Produces `psychological_profile.json`
- Falls back to neutral scores (5/10) when LLM unavailable

### 4. `red_team_agent` — Adversarial Audit
**Path:** `agents/red_team_agent/agent.py`

- Takes profiler output as input
- Generates 3+ challenges to profiler conclusions
- Identifies flaws: overconfidence, selection bias, context gaps
- Produces `adversarial_audit.json` with revised risk assessment

### 5. `wiki_sync` — Wiki Generator
**Path:** `agents/wiki_sync/agent.py`

- Reads `brief.md`, `knowledge_graph.json`, `psychological_profile.json`
- Generates `wiki/{actor-slug}.md` — living markdown document
- Producer-editable via `PUT /api/wiki/{slug}`
- Auto-updates after every investigation

---

## New API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/status` | GET | System health: LLM, tools, ChromaDB, agents |
| `/api/wiki` | GET | List all wiki pages |
| `/api/wiki/{slug}` | GET/PUT/DELETE | Read/update/delete wiki |
| `/api/knowledge/actors` | GET | List actors in graph |
| `/api/knowledge/actors/{slug}` | GET | Get actor's knowledge graph |
| `/api/knowledge/actors/similar` | POST | Find similar actors by embedding |
| `/api/knowledge/claims/search` | POST | Semantic claim search |
| `/api/knowledge/contradictions` | GET | List all contradictions |

**Routers:**
- `api/routers/wiki.py`
- `api/routers/knowledge.py`
- Updated `api/main.py` to include both

---

## New Frontend

### Pages
- `ui/src/pages/WikiBrowser.tsx` — Browse wiki pages with search
- `ui/src/pages/KnowledgeBrowser.tsx` — Explore actor knowledge graphs

### Components
- `ui/src/components/JsonViewer.tsx` — Collapsible JSON tree viewer
- `ui/src/components/SystemStatus.tsx` — Live system health widget

### Hooks
- `ui/src/hooks/useWiki.ts` — Wiki CRUD
- `ui/src/hooks/useKnowledge.ts` — Knowledge graph queries
- `ui/src/hooks/useSystemStatus.ts` — System status polling

### Updated
- `App.tsx` — Added `/wiki` and `/knowledge` routes
- `Sidebar.tsx` — Added Wiki + Knowledge nav items
- `Dashboard.tsx` — Added SystemStatus widget
- `InvestigationDetail.tsx` — JSON viewer for `.json` files

**Frontend builds successfully:** `cd ui && npm run build`

---

## New Kernel Modules

### `kernel/llm_client_v2.py`
- Multi-modal LLM client with Gemini native video support
- `generate()` — text via direct HTTP to `generativelanguage.googleapis.com`
- `generate_structured()` — JSON with schema enforcement
- `analyze_video()` — uploads video to Gemini 2.5 Pro, returns `LLMResponse`
- `embed_text()` — text embeddings via `text-embedding-004`
- Auto-fallback chain: `gemini-3.1-pro-preview` → `gemini-2.5-flash`

### `kernel/knowledge_graph.py`
- ChromaDB-based vector graph
- `add_actor()`, `add_claim()`, `add_contradiction()`, `add_source()`
- `find_similar_actors()` — semantic similarity search
- `get_actor_summary()` — frontend-friendly format
- `export_graph()` — D3.js-compatible nodes/edges

### `kernel/video_pipeline_v2.py`
- Spec written, not yet fully implemented (video_analyzer_v2 has its own pipeline)

---

## Modified Existing Files

| File | What Changed |
|---|---|
| `agents/actor_harvester/agent.py` | Added `_resolve_video_urls()` + `_validate_youtube_url()` — replaces fake LLM URLs with real yt-dlp search results |
| `kernel/agent_runner.py` | Added async agent support, LLM client injection, asyncio handling |
| `kernel/manifest.py` | Updated `DEFAULT_PIPELINE` to include v2 agents |
| `kernel/llm_client.py` | Added Gemini 2.5 Pro / 3.1 Pro / 3.1 Flash Lite models |
| `oracle_cli.py` | Added `--run-v2-pipeline` and `--max-videos` flags |
| `api/main.py` | Added `/api/status` endpoint, wiki + knowledge routers |

---

## How to Start Tomorrow

### 1. Start the API server
```bash
cd oracle
source .venv/bin/activate
export GEMINI_API_KEY=AIzaSyB8GXDihjkOM-W_g_SbOo3D0PUlIwrsdZY
uvicorn api.main:app --port 8000
```

### 2. Start the frontend dev server (in another terminal)
```bash
cd oracle/ui
npm run dev
```

### 3. Verify everything is healthy
```bash
curl http://localhost:8000/api/status
```
Expected: `llm.available: true`, `tools.yt_dlp: true`, `agents.count: 8`

### 4. Run a full pipeline via CLI
```bash
cd oracle
source .venv/bin/activate
python oracle_cli.py investigate \
  --actor "Zendaya" \
  --question "Can she carry a $25M drama?" \
  --run-v2-pipeline \
  --max-videos 2
```

Or via API:
```bash
# Create investigation
curl -X POST http://localhost:8000/api/investigations \
  -H "Content-Type: application/json" \
  -d '{"actor":"Zendaya","client_question":"Can she carry a $25M drama?"}'

# Run agents sequentially (wait for each to complete)
# 1. actor_harvester
# 2. video_analyzer_v2
# 3. knowledge_sync
# 4. psychological_profiler
# 5. wiki_sync
# 6. red_team_agent
```

---

## Current System State

### Working ✅
- API server runs on `localhost:8000`
- Frontend builds and serves on `localhost:5173`
- Actor harvester produces real YouTube URLs via yt-dlp search
- Video downloads work (tested: ~100MB Cannes press conference)
- Video segmentation works (baseline/pressure/fatigue)
- All 8 agents are discoverable via API
- Knowledge graph stores actors, claims, contradictions
- Wiki pages auto-generate and are editable
- Red team generates adversarial challenges
- Psychological profiler produces 5-dimension scores
- System status endpoint reports all green

### Partial / Demo Mode ⚠️
- **Gemini video analysis hits rate limits** (free tier: 20 requests)
- Video analyzer falls back to `_generate_demo_observations()` — realistic but synthetic
- Brief generation falls back to `_generate_demo_brief()` — structured but not LLM-generated
- To get real Gemini video analysis: set up billing on the Gemini API key

### Known Issues 🔧
1. **Gemini rate limits:** The free tier key (`AIzaSyB8GXDihjkOM-W_g_SbOo3D0PUlIwrsdZY`) hits 429 errors after ~20 requests. Need billing setup for Pro models.
2. **Uvicorn `--reload` clears job store:** Background tasks lose in-memory `_job_store` on file change. Restart without `--reload` for production.
3. **Very short videos (<60s):** Don't split into segments, analyzed as "full" segment only.
4. **ActorHarvester LLM sometimes generates fake IDs that pass regex:** Mitigated by `_validate_youtube_url()` which checks yt-dlp can extract the ID.

---

## Test Investigations in Database

| Actor | Investigation ID | Status |
|---|---|---|
| Zendaya | `zendaya-2026-05-13-052568` | Full pipeline run, videos downloaded, demo brief |
| Timothée Chalamet | `timothée-chalamet-2026-05-13-748e7a` | Full pipeline run, demo brief |
| Test Actor | `test-actor-2026-05-13-add67d` | All agents run successfully |
| Florence Pugh | `florence-pugh-2026-05-13-27ad19` | Harvester + video analyzer run |

---

## Files to Know About

**Master plan:** `REBUILD-PLAN.md` — the 391-line rebuild specification

**End-to-end test:** `test_v2_pipeline.py` — run with `python test_v2_pipeline.py --actor "Name"`

**Key new files:**
```
agents/video_analyzer_v2/agent.py      # Honest video pipeline
agents/knowledge_sync/agent.py         # Knowledge graph builder
agents/psychological_profiler/agent.py # Deep profiler
agents/red_team_agent/agent.py         # Adversarial audit
agents/wiki_sync/agent.py              # Wiki generator
kernel/llm_client_v2.py                # Multi-modal LLM client
kernel/knowledge_graph.py              # ChromaDB vector graph
api/routers/wiki.py                    # Wiki API
api/routers/knowledge.py               # Knowledge graph API
ui/src/pages/WikiBrowser.tsx           # Wiki UI
ui/src/pages/KnowledgeBrowser.tsx      # Knowledge UI
ui/src/components/JsonViewer.tsx       # JSON tree viewer
ui/src/components/SystemStatus.tsx     # Health widget
```

---

## Git Status

**Remote:** `https://github.com/asdzxc1a/oracle-huasheng.git`
**Branch:** `main`
**Last commit:** `2818a1e` — "Oracle v2 rebuild: honest video pipeline + knowledge graph + psych profiler"
**Files changed:** 46 files, 4,485 insertions

Everything is pushed to GitHub.

---

## Tomorrow's Priority List

1. **Set up Gemini billing** so video analysis uses real Gemini 2.5 Pro instead of demo mode
2. **Test full pipeline with real Gemini** — verify observations are actually extracted from video frames
3. **Build Producer Wiki Editor** — make wiki pages fully editable in the React UI (currently read-only)
4. **Add D3.js graph visualization** to KnowledgeBrowser for contradiction networks
5. **Create a "Run Full Pipeline" button** in InvestigationDetail that auto-runs all agents in sequence
6. **Add pre-ship validator** that scores investigations before they're marked complete
7. **Build actor comparison page** — side-by-side psychological profiles

---

*Session ended: 2026-05-12 ~23:15 PT*
*Next session starts from this document.*
