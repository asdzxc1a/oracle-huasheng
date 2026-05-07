# Source Reliability Matrix — Video Analysis Agent

## Matrix

| Source Type | Access Level | Signal Density | Tier Cap | Notes |
|-------------|-------------|----------------|----------|-------|
| Festival Q&A (unscripted) | MANAGED | Very High | A | Spontaneous questions, actor less guarded |
| Long-form podcast | MANAGED | High | A | Extended exposure, fatigue reveals baseline |
| Behind-the-scenes (raw) | RAW | Very High | A | Unfiltered behavior, highest signal |
| Behind-the-scenes (studio) | SCRIPTED | Low | C | Everything approved, baseline comparison only |
| Press conference | MANAGED | Moderate | B | Some spontaneity, PR present |
| Late-night interview | SCRIPTED | Low | C | Pure performance, zero diagnostic value |
| Social media (personal) | RAW | High | B | Ephemeral, may be curated, still useful |
| Social media (fan clips) | RAW | Moderate | B | May be out of context, verify source |
| Print interview | N/A | Low | C | No behavioral data, claims only |

## Tier Cap Rules
- RAW sources can produce Tier A claims
- MANAGED sources cap at Tier A (but downgrade if PR interference detected)
- SCRIPTED sources cap at Tier C
- Print sources (no video) cap at Tier B for claims, C for behavior

## Contradiction Weighting
When two sources contradict:
- RAW + MANAGED → Trust RAW, note MANAGED as possible PR position
- MANAGED + SCRIPTED → Trust MANAGED, SCRIPTED is likely cover story
- RAW + SCRIPTED → Trust RAW heavily, SCRIPTED may be damage control
- Two RAW sources → Preserve contradiction. Human adjudicates.
