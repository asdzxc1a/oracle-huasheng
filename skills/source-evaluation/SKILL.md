---
name: source-evaluation
description: |
  Evaluate video sources for actor analysis by access level and reliability.
  Tag every source as RAW, MANAGED, or SCRIPTED. Assess signal density.
  Use before any analysis to ensure evidence quality.
---

# Source Evaluation

## Access Levels

| Level | Description | Tier Cap |
|---|---|---|
| **RAW** | Unfiltered, unscripted, off-camera | Tier A |
| **MANAGED** | PR present, spontaneous answers possible | Tier A |
| **SCRIPTED** | Every word vetted | Tier C |

## Signal Density

| Rating | Criteria |
|---|---|
| Very High | Unscripted + long-form + emotional stakes |
| High | Semi-scripted + substantive content |
| Moderate | Managed but reveals baseline |
| Low | Purely performative |

## Workflow
1. Inspect source type (festival Q&A, podcast, BTS, press junket, late night)
2. Assign access level based on context
3. Rate signal density
4. Document why_relevant for each source
5. Ensure source diversity: ≥1 RAW, ≥2 MANAGED, ≤1 SCRIPTED

## Quality Checklist
- [ ] Every source has access_level assigned
- [ ] Every source has signal_density rated
- [ ] Source diversity meets minimums
- [ ] No fabricated URLs (use search URLs if exact unavailable)

## References
- Reliability matrix: `references/reliability-matrix.md`
