---
name: contradiction-detection
description: |
  Find and preserve ≥2 contradiction pairs across actor claims. 
  A contradiction is when two claims point to opposite conclusions 
  about the same trait. Use before shipping the brief. Never smooth 
  contradictions — the human adjudicates.
---

# Contradiction Detection

## Quick Start
For any set of claims about an actor:
1. Read all generated claims
2. Find pairs with opposite implications
3. Name the tension explicitly
4. Explain the implication for casting
5. Write to contradictions.md

## What Is a Contradiction?

Two claims about the same actor that point in opposite directions:
- Confidence vs. insecurity
- Risk-taking vs. safety-seeking
- Authenticity vs. performance
- Consistency vs. transformation

## Workflow

1. Read all generated claims
2. Find pairs with opposite implications
3. Name the tension explicitly
4. Explain the implication for casting
5. Write to contradictions.md

## Output Format

```markdown
### Contradiction: [Short Label]

- **Signal A:** [Claim text]
  - *Source:* [source_type] ([access_level])
- **Signal B:** [Claim text]
  - *Source:* [source_type] ([access_level])
- **Tension:** [Named tension]
- **Implication:** [Casting implication]
- **Resolution Strategy:** PRESERVED — human adjudicates
```

## Quality Checklist
- [ ] ≥2 contradiction pairs found
- [ ] Each pair is genuinely opposite (not just different)
- [ ] Tension is named explicitly
- [ ] Implication is casting-relevant
- [ ] Human adjudication required

## Scripts
- Core detection: `scripts/detect.py`
- Heuristic patterns: `references/heuristic-patterns.md`
