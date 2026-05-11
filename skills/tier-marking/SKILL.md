---
name: tier-marking
description: |
  Tag every claim with its evidentiary tier (A/B/C/F) and apply access-level 
  caps. Use after generating claims and before compiling the brief. Ensures 
  no SCRIPTED source produces Tier A claims.
---

# Tier Marking

## Quick Start
For every claim generated during analysis:
1. Assign tier based on evidence strength
2. Apply access-level cap (auto-downgrade if needed)
3. Tag text with tier markers
4. Produce claim registry

## Tier Definitions

| Tier | Criteria | Confidence |
|---|---|---|
| **A** | Directly observed, multiple sources converge | High |
| **B** | Inferred from converging indirect evidence | Moderate |
| **C** | Single-source, speculative, acknowledged inference | Low |
| **F** | Fabricated, unverifiable, PR disinformation | Discard |

## Access Level Caps

| Access | Tier Cap | Rule |
|---|---|---|
| RAW | A | Can produce Tier A |
| MANAGED | A | Can produce Tier A (downgrade if PR interference) |
| SCRIPTED | C | Capped at Tier C |
| NOT_FOUND | F | Discard |

## Workflow

1. Review all generated claims
2. Assign tier based on evidence strength
3. Apply access-level cap (auto-downgrade if needed)
4. Tag text with tier markers
5. Produce claim registry

## Output Format

```markdown
# Tier Marking Key

## Claim Registry

| # | Claim | Tier | Source | Access |
|---|---|---|---|---|
| 1 | [Claim text] | A | [source_type] | RAW |
```

## Quality Checklist
- [ ] No Tier A claims from SCRIPTED sources
- [ ] Every claim has a tier
- [ ] Every Tier C claim uses hedging language
- [ ] Claim registry is complete

## Scripts
- Auto-tagger: `scripts/tagger.py`
