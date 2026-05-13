# Oracle Rebuild Plan
## From Fake Video Analysis to Real Forensic Intelligence

**Date:** 2026-05-13
**Goal:** Fix the lie, build the knowledge graph, make the video agent real, and add deep psychological prediction.
**Build Order:** Honest Video Pipeline → Pinecone Knowledge Graph → Actor Wiki → Deep Psychological Profiler
**LLM:** Gemini 3.1 Pro (paid tier) — reasoning, text, structured output
**Video Analysis:** Gemini 2.5 Pro native video understanding — upload full 45-min interviews
**Vector DB:** Pinecone (with graph relationships)

---

## PART 1: HONEST AUDIT — WHAT IS BROKEN

### The Lie
The current Oracle generates briefs that *pretend* to analyze video frames, body language, and transcripts. In reality:
- Video catalog URLs are YouTube **search result pages**, not actual videos
- `process_videos: false` skips the entire download pipeline
- `yt-dlp` and `ffmpeg` are installed but never called
- Whisper is never called (no OpenAI key)
- Claims are generated from **text descriptions** of videos + the user's initial read
- The brief hallucinates specific observations ("she touched her neck 15 times") with zero frame-level evidence

### The Truth
The architecture works. The agents run. The Huasheng checks happen. But the **evidence layer is hollow**.

---

## PART 2: THE BUILD ORDER

We build in 4 phases. Each phase produces a working system, not a half-built dependency.

```
PHASE 1: Honest Video Pipeline (Foundation)
    ↓
PHASE 2: Pinecone Knowledge Graph (Memory)
    ↓
PHASE 3: Actor Wiki System (Presentation)
    ↓
PHASE 4: Deep Psychological Profiler (Crown Jewel)
```

---

## PHASE 1: HONEST VIDEO PIPELINE

### Goal
When a producer reads the brief, every claim about body language, voice, or facial expression must trace to a real video file, a real timestamp, and a real Gemini analysis of that moment.

### What We Change

#### 1.1 Fix the Actor Harvester
**Current:** Generates `youtube.com/results?search_query=...` links
**New:** Finds actual video URLs using `yt-dlp --print urls` + YouTube Data API fallback

**Implementation:**
- File: `oracle/agents/actor_harvester/agent.py`
- Function: `find_videos()`
- Output: `video-catalog.json` with real `watch?v=` URLs, not search pages
- Validation: Reject any URL containing `/results?search_query=`

#### 1.2 Build the Honest Video Pipeline
**Current:** `process_videos: false` skips everything
**New:** `process_videos: true` by default. Full pipeline runs.

**Pipeline Steps:**
1. **Download** — `yt-dlp` downloads the video (720p, max 500MB, 45-min cap)
2. **Segment** — Split 45-min interview into 3 clips:
   - Clip A: Minutes 0-5 (baseline, relaxed)
   - Clip B: Minutes 15-25 (under sustained pressure)
   - Clip C: Minutes 35-45 (fatigue, recovery)
3. **Upload to Gemini** — Send each clip to `gemini-2.5-pro` via `generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent` with video inline
4. **Analyze** — Ask Gemini: *"Describe body language, facial expressions, voice tone, stress signals, and social calibration at each timestamp"*
5. **Store** — Save Gemini's raw analysis as `analysis_{clip_id}.json`
6. **No frames. No Whisper.** Gemini sees the video natively.

**Why Gemini Native Video?**
- Current pipeline: Download → ffmpeg frames → ffmpeg audio → Whisper transcript → analyze text + frames separately (4 steps, 3 tools, fragile)
- New pipeline: Download → upload to Gemini → get analysis (2 steps, 1 tool, robust)
- Gemini 2.5 Pro understands motion, micro-expressions, vocal prosody, and spatial behavior in one pass
- No need for OpenAI key. No Whisper. No frame extraction.

**Files:**
- `oracle/kernel/video_pipeline_v2.py` — new honest pipeline
- `oracle/agents/video_analysis/agent.py` — updated to use v2 pipeline
- `oracle/investigations/{id}/sources/clips/` — downloaded videos
- `oracle/investigations/{id}/sources/analysis/` — Gemini analysis JSONs

#### 1.3 Evidence Audit Trail
Every brief must include an **Evidence Audit** section:
```
## Evidence Audit
- Videos requested: 5
- Videos downloaded: 5
- Videos analyzed by Gemini: 5
- Total minutes analyzed: 127
- Claims traceable to video: 8/8
- Claims based on text context only: 0/8
- Download failures: 0
```

**Rule:** If a claim cannot trace to a specific video + timestamp, it is rejected by pre-ship validation.

---

## PHASE 2: PINECONE KNOWLEDGE GRAPH

### Goal
Every actor, claim, contradiction, source, and investigation becomes a node in a searchable graph. Producers can ask: *"Show me actors who are confident in action scenes but insecure in interviews."*

### Architecture

#### 2.1 Pinecone Indexes
We create 3 indexes in Pinecone:

| Index | Dimensions | What It Stores | Search Use |
|---|---|---|---|
| `oracle-actors` | 768 | Actor psychological profiles | *"Find actors like Florence Pugh"* |
| `oracle-claims` | 384 | Individual claims (Tier A/B/C) | *"Find all 'fight response' claims"* |
| `oracle-sources` | 384 | Video sources + analysis | *"Find all Comic-Con panel analyses"* |

#### 2.2 Graph Structure (JSON-LD on Disk)
Each investigation produces a `knowledge_graph.json`:
```json
{
  "nodes": [
    {"id": "milly-alcock", "type": "actor", "embedding_id": "pc_id_123"},
    {"id": "claim_001", "type": "claim", "text": "Exhibits fawn response in interviews", "tier": "C"},
    {"id": "source_001", "type": "source", "url": "youtube.com/watch?v=abc", "access_level": "MANAGED"}
  ],
  "edges": [
    {"from": "claim_001", "to": "milly-alcock", "relation": "about"},
    {"from": "claim_001", "to": "source_001", "relation": "supported_by"},
    {"from": "claim_001", "to": "claim_002", "relation": "contradicts"}
  ]
}
```

#### 2.3 Actor Profile Embedding
When an investigation completes, the actor's full psychological profile is embedded into Pinecone:
```python
profile_text = f"""
Actor: {actor}
Stress Response: {stress_response}
Attachment Style: {attachment}
Contextual Behavior:
- Press conferences: {press_behavior}
- Action scenes: {action_behavior}
- Intimate drama: {drama_behavior}
Contradictions: {contradiction_summary}
Comparables: {comparable_actors}
"""
embedding = gemini_embedding_model.encode(profile_text)
index.upsert(vectors=[(actor_slug, embedding, {"name": actor, "last_updated": date})])
```

**Why this matters:**
- Query: *"Find actors psychologically similar to Saoirse Ronan"* → Returns Milly Alcock (72% similarity)
- Query: *"Find actors where we found 'confidence vs. insecurity' contradictions"* → Returns all matching actors
- Query: *"How has Milly Alcock's profile changed since 2022?"* → Pulls historical embeddings, compares

#### 2.4 Integration Point
After the Video Analysis Agent finishes, a new **Knowledge Graph Sync Agent** runs:
1. Reads the brief + research files
2. Extracts nodes (actor, claims, sources, contradictions)
3. Generates embeddings via Gemini
4. Upserts to Pinecone
5. Writes `knowledge_graph.json` to disk

**File:** `oracle/agents/knowledge_sync/agent.py`

---

## PHASE 3: ACTOR WIKI SYSTEM

### Goal
A living Wikipedia page for every actor. Producers can read it in the browser. It auto-updates after every new investigation.

### Design

#### 3.1 Wiki Page Structure
Each actor gets `wiki/{actor-slug}.md`:
```markdown
# Milly Alcock

## Psychological Profile (Latest)
**Stress Response:** Flight-to-Fawn
**Attachment Style:** Secure-Avoidant (mixed)
**Narcissistic Defense:** Vulnerable-adaptive
**Temporal Stability:** Evolving

## Career Timeline
| Year | Project | Role | Psychological Notes |
|------|---------|------|---------------------|
| 2019 | Upright | Meg | Baseline: unguarded, comedic |
| 2022 | HOTD | Rhaenyra | Breakthrough: rapid emotional access |
| 2025 | Sirens | Simone | Post-fame: increased deflection |
| 2026 | Supergirl | Kara | Franchise test: TBD |

## Contradictions (Preserved)
1. **Fawn vs. Grounded** — Interviews show mirroring; BTS shows stability
2. **Internal Regulation vs. External Validation** — Fast recovery on set; needs interviewer praise in public

## Predictions
| Context | Predicted Behavior | Confidence |
|---------|-------------------|------------|
| Unscripted press tour | Fawn response, deflective humor | 85% |
| Action stunt sequence | Fight response, high commitment | 70% |
| Intimate drama | Freeze response, slow recovery | 60% |

## Investigations
- [2026-05-13] Can she carry a $150M DC franchise lead? → [Brief](../investigations/...)

## Similar Actors (Pinecone)
1. Florence Pugh (78% similarity)
2. Saoirse Ronan (71% similarity)
3. Emilia Clarke (64% similarity)
```

#### 3.2 Auto-Generation
After every investigation, the Wiki Sync Agent:
1. Reads the brief
2. Extracts the 5 psychological dimensions
3. Appends to the career timeline
4. Updates contradictions
5. Regenerates predictions
6. Re-queries Pinecone for similar actors
7. Writes the updated `wiki/milly-alcock.md`

#### 3.3 Client-Facing UI
The React frontend gets a new **Wiki tab**:
- Renders the markdown wiki with the Oracle Dark design system
- Shows the knowledge graph visualization (D3.js force-directed graph)
- Lets producers click on contradictions to see the evidence
- Lets producers compare 2 actors side-by-side

**Files:**
- `oracle/wiki/` — markdown wiki files
- `oracle/ui/src/pages/WikiPage.tsx` — wiki viewer
- `oracle/ui/src/components/KnowledgeGraph.tsx` — graph visualization

---

## PHASE 4: DEEP PSYCHOLOGICAL PROFILER

### Goal
An agent that predicts how an actor will behave in contexts we haven't seen yet. Not just *"what did they do?"* but *"what will they do?"*

### The 5 Dimensions

#### Dimension 1: Stress Response Archetype
Analyzes behavior across contexts to determine the dominant stress response:
- **Fight** — Dominates, argues, asserts control
- **Flight** — Withdraws, deflects, uses humor
- **Freeze** — Goes blank, long pauses, minimal movement
- **Fawn** — Mirrors, agrees, seeks approval

**Prediction:** *"In a hostile press conference, she will default to Fawn for 3-5 minutes, then shift to Flight if pressed further."*

#### Dimension 2: Attachment Style
- **Secure** — Comfortable with intimacy, stable eye contact
- **Anxious** — Seeks validation, fills silence, over-explains
- **Avoidant** — Intellectualizes, deflects personal questions
- **Disorganized** — Mixed signals, inconsistent behavior

**Prediction:** *"In a co-star chemistry read with a dominant actor, she will show Anxious markers (seeking approval). With a passive co-star, she will show Secure markers (taking leadership)."*

#### Dimension 3: Narcissistic Defense Profile
- **Grandiose** — Projects superiority, dominates conversations
- **Vulnerable** — Self-deprecates, needs external validation
- **Adaptive** — Uses both strategically depending on context
- **None** — Genuine humility without performance

**Prediction:** *"During a box office flop press tour, her Vulnerable defense will intensify. She will need 2x more validation from the director than during a hit film tour."*

#### Dimension 4: Temporal Stability
- **Consistent** — Same behavior across years
- **Evolving** — Improving coping mechanisms over time
- **Volatile** — Unpredictable shifts
- **Regressing** — Getting worse under pressure

**Prediction:** *"Comparing her 2019 Upright interviews to 2026 CinemaCon footage: her stress response has shifted from Freeze (2019) to Flight (2022) to Fawn (2026). This is an Evolving profile, but the trajectory suggests increasing need for external validation."*

#### Dimension 5: Contextual Adaptability
How much does behavior change between managed vs. raw settings?
- **Rigid** — Same behavior everywhere (predictable but one-dimensional)
- **Adaptive** — Shifts significantly (versatile but hard to cast)
- **Chameleon** — Completely different person (high risk, high reward)
- **Stable** — Core personality consistent, surface behavior flexible

**Prediction:** *"She is Adaptive. In a Craig Gillespie film (collaborative, messy), she will thrive. In a Zack Snyder film (rigid, visual), she will struggle without strong AD support."*

### Implementation

**File:** `oracle/agents/psychological_profiler/agent.py`

**Inputs:**
- Full video analysis results (Gemini native video analysis of all clips)
- All previous investigations for this actor (from Pinecone)
- Comparable actor profiles (from Pinecone similarity search)

**Process:**
1. **Cross-context analysis** — Compare behavior in Comic-Con vs. Late Night vs. BTS vs. Film Scene
2. **Temporal comparison** — Compare 2019 → 2022 → 2025 → 2026 footage
3. **Comparable mapping** — Find actors with similar 5-dimension profiles. Did they succeed in franchises?
4. **Prediction generation** — For each context type, predict behavior + confidence

**Output:**
- `research/psychological_profile.json` — structured 5-dimension data
- `research/predictions.md` — human-readable prediction table
- Updates Pinecone with the full psychological embedding

### The Red Team Validation
After the profiler finishes, a **Profiler Red Team Agent** attacks:
1. *"Your prediction says 'Fawn at press tours.' But she was dominant at CinemaCon. Explain."*
2. *"You compared her to Florence Pugh. But Pugh had 3 years of indie film experience before franchise. Alcock had zero. False comparable."*
3. *"Your confidence on action scene prediction is 70%. But you only have 4.5 months of training data. That confidence is inflated."*

If the Red Team finds holes, the profiler must revise or downgrade confidence.

---

## PART 4: TECH STACK DECISIONS

| Component | Choice | Why |
|---|---|---|
| **LLM (text)** | Gemini 3.1 Pro Preview | Best reasoning, long context, strict system prompt adherence |
| **LLM (video)** | Gemini 2.5 Pro | Native video understanding up to 1M tokens (~1 hour video) |
| **LLM (embedding)** | Gemini embedding-001 | Same ecosystem, consistent semantics |
| **Vector DB** | Pinecone | Graph relationships, hybrid search, scalable |
| **Video download** | yt-dlp | Already installed, proven |
| **Video format** | MP4 720p | Balance of quality and upload speed to Gemini |
| **Transcription** | None — use Gemini native | Whisper is unnecessary; Gemini hears the audio |
| **Frame extraction** | None — use Gemini native | ffmpeg frames are unnecessary; Gemini sees motion |
| **Wiki format** | Markdown | Simple, versionable, human-editable |
| **Wiki UI** | React + D3.js | Graph visualization, Oracle Dark design |
| **Evidence provenance** | SHA-256 + timestamp | Already in proof-architecture/ |

---

## PART 5: IMPLEMENTATION ROADMAP

### Week 1: Fix the Lie
- [ ] Update `llm_client.py` — prioritize Gemini 3.1 Pro for text, Gemini 2.5 Pro for video
- [ ] Fix `actor_harvester` — find real YouTube URLs
- [ ] Build `video_pipeline_v2.py` — download + Gemini native analysis
- [ ] Update `video_analysis/agent.py` — use v2 pipeline, `process_videos: true`
- [ ] Add Evidence Audit section to every brief
- [ ] Test end-to-end with Milly Alcock

### Week 2: Pinecone Knowledge Graph
- [ ] Set up Pinecone indexes (3 indexes)
- [ ] Build `knowledge_sync` agent
- [ ] Create embedding pipeline (actor profiles, claims, sources)
- [ ] Build similarity search API endpoint
- [ ] Test: *"Find actors like Florence Pugh"*

### Week 3: Actor Wiki
- [ ] Build `wiki_sync` agent
- [ ] Create wiki markdown templates
- [ ] Build Wiki page React component
- [ ] Build Knowledge Graph visualization (D3.js)
- [ ] Test: Producer opens wiki, sees graph, clicks contradiction

### Week 4-5: Deep Psychological Profiler
- [ ] Build `psychological_profiler` agent
- [ ] Implement 5-dimension analysis
- [ ] Build prediction engine
- [ ] Build Profiler Red Team agent
- [ ] Test: Full Milly Alcock profile + predictions

### Week 6: Integration + Cannes Prep
- [ ] Wire all agents into single pipeline
- [ ] Build export pipeline (PDF brief, PowerPoint deck)
- [ ] Mobile-responsive UI polish
- [ ] Stress test with 10 actors
- [ ] Demo rehearsal

---

## PART 6: WHAT SUCCESS LOOKS LIKE

When a producer opens the Oracle for Milly Alcock, they see:

1. **The Wiki** — A living document with her career timeline, psychological profile, and predictions
2. **The Knowledge Graph** — A visual web of claims, sources, and contradictions they can explore
3. **The Brief** — A forensic report where every claim about body language traces to a real video + timestamp + Gemini analysis
4. **The Predictions** — A table showing how she will behave in contexts the producer cares about
5. **The Evidence Audit** — Honest disclosure of what was analyzed, what failed, and what we don't know

**The brief no longer lies.**
